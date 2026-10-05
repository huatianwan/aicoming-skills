#!/usr/bin/env python3
"""AIComing zero-dependency, secret-safe command line client."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://api.gptcoming.cn"
DEFAULT_CONSOLE = "https://aicoming.top/console"
KEY_RE = re.compile(r"sk-[A-Za-z0-9._-]{6,}")
PERMISSION_ERRORS = {
    "model_not_allowed_for_key",
    "model_not_in_package",
    "package_quota_exhausted",
    "key_quota_exceeded",
    "no_favorited_providers",
    "key_has_no_route_providers",
    "providers_not_favorited",
    "model_not_supported_by_selected_providers",
    "pinned_provider_not_available",
}
PENDING = {"pending", "queued", "processing", "running", "in_progress"}
DONE = {"completed", "succeeded", "success"}
FAILED = {"failed", "error", "cancelled", "canceled", "timeout"}


def redact(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return KEY_RE.sub(lambda m: m.group(0)[:7] + "…", text)


def profile_name(raw: str) -> str:
    name = raw.strip() or "default"
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", name):
        raise ValueError("profile 只能包含字母、数字、下划线和短横线")
    return name


@dataclass
class Store:
    profile: str = "default"

    def __post_init__(self) -> None:
        root = os.environ.get("AICOMING_CONFIG_HOME")
        self.root = Path(root).expanduser() if root else Path.home() / ".aicoming"
        self.profile = profile_name(self.profile)
        self.dir = self.root if self.profile == "default" else self.root / self.profile
        self.key_path = self.dir / "key"
        self.config_path = self.dir / "config.json"
        self.tasks_dir = self.dir / "tasks"

    def prepare(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.tasks_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            os.chmod(self.dir, 0o700)
            os.chmod(self.tasks_dir, 0o700)

    def read_config(self) -> dict[str, Any]:
        try:
            return json.loads(self.config_path.read_text("utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write_config(self, config: dict[str, Any]) -> None:
        self.prepare()
        _atomic_private_write(self.config_path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")

    def read_key(self) -> str:
        env = os.environ.get("AICOMING_API_KEY", "").strip()
        if env:
            return env
        try:
            return self.key_path.read_text("utf-8").strip()
        except FileNotFoundError:
            return ""

    def write_key(self, key: str) -> None:
        self.prepare()
        _atomic_private_write(self.key_path, key.strip() + "\n")
        if os.name == "nt":
            user = os.environ.get("USERNAME", "")
            cmd = ["icacls", str(self.key_path), "/inheritance:r"]
            if user:
                cmd.extend(["/grant:r", f"{user}:R"])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.key_path.unlink(missing_ok=True)
                raise RuntimeError("无法收紧 Key 文件 ACL，已取消保存")

    def task_path(self, token: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", token)[:120]
        return self.tasks_dir / f"{safe}.json"

    def save_task(self, data: dict[str, Any]) -> Path:
        self.prepare()
        token = str(data.get("id") or data.get("idem_key"))
        path = self.task_path(token)
        _atomic_private_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        previous = data.get("record_path")
        if previous:
            previous_path = Path(str(previous))
            if previous_path != path and previous_path.parent == self.tasks_dir:
                previous_path.unlink(missing_ok=True)
        data["record_path"] = str(path.resolve())
        return path

    def load_task(self, token: str) -> tuple[dict[str, Any], Path]:
        direct = self.task_path(token)
        paths = [direct] if direct.exists() else list(self.tasks_dir.glob("*.json"))
        for path in paths:
            try:
                data = json.loads(path.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if token in {str(data.get("id", "")), str(data.get("idem_key", ""))}:
                return data, path
        raise FileNotFoundError(f"找不到任务记录：{token}")


def _atomic_private_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        os.replace(tmp, path)
        if os.name != "nt":
            os.chmod(path, 0o600)
    finally:
        tmp.unlink(missing_ok=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "拒绝携带凭据跟随重定向", headers, fp)


class APIError(RuntimeError):
    def __init__(self, status: int, message: str, error_type: str = ""):
        super().__init__(redact(message))
        self.status = status
        self.error_type = error_type


class Client:
    def __init__(self, base: str, key: str, bound_host: str = "", debug: bool = False):
        self.base = normalize_base(base)
        self.key = key.strip()
        self.host = urllib.parse.urlsplit(self.base).hostname or ""
        self.debug = debug
        if bound_host and self.host.lower() != bound_host.lower():
            raise ValueError(f"Key 绑定到 {bound_host}，拒绝发送到 {self.host}；请切换 profile 或重新登录")
        self.opener = urllib.request.build_opener(NoRedirect)

    def request(self, method: str, path: str, payload: Any = None, timeout: int = 30, auth: bool = True,
                headers: dict[str, str] | None = None) -> Any:
        url = self.base.rstrip("/") + "/" + path.lstrip("/")
        target = urllib.parse.urlsplit(url)
        if (target.hostname or "").lower() != self.host.lower():
            raise ValueError("请求主机与绑定主机不一致")
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        req_headers = {"Accept": "application/json"}
        if body is not None:
            req_headers["Content-Type"] = "application/json"
        if auth:
            if not self.key:
                raise ValueError("尚未登录：请先运行 aic.py login")
            req_headers["Authorization"] = f"Bearer {self.key}"
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, data=body, method=method.upper(), headers=req_headers)
        if self.debug:
            print(f"[debug] {method.upper()} {url}", file=sys.stderr)
        try:
            with self.opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            message, kind = parse_error(raw, exc.reason)
            raise APIError(exc.code, message, kind) from None
        except urllib.error.URLError as exc:
            raise APIError(0, f"网络请求失败：{exc.reason}") from None
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"text": raw.decode("utf-8", "replace")}

    def download(self, url: str, path: Path, timeout: int = 120) -> None:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError("拒绝从非 HTTPS 地址下载结果")
        headers = {"Accept": "*/*"}
        if (parsed.hostname or "").lower() == self.host.lower() and self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        req = urllib.request.Request(url, headers=headers)
        with self.opener.open(req, timeout=timeout) as resp:
            data = resp.read()
        if not data:
            raise RuntimeError("下载结果为空")
        path.write_bytes(data)


def normalize_base(raw: str) -> str:
    value = raw.strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (local and parsed.scheme == "http"):
        raise ValueError("API 地址必须使用 https；仅测试可使用 localhost/127.0.0.1 的 http")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("API 地址无效")
    return value


def resolve_base(args: argparse.Namespace, store: Store) -> str:
    return args.base or os.environ.get("AICOMING_BASE_URL") or store.read_config().get("base_url") or DEFAULT_BASE


def parse_error(raw: bytes, fallback: Any) -> tuple[str, str]:
    try:
        data = json.loads(raw)
        err = data.get("error", data)
        if isinstance(err, dict):
            return str(err.get("message") or fallback), str(err.get("type") or err.get("code") or "")
        return str(err), ""
    except (json.JSONDecodeError, UnicodeDecodeError):
        return str(fallback), ""


def extract_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        value = data.get("data", data.get("items", []))
        return value if isinstance(value, list) else []
    return data if isinstance(data, list) else []


def task_state(data: dict[str, Any]) -> str:
    return str(data.get("status") or data.get("state") or data.get("data", {}).get("status") or "").lower()


def task_id(data: dict[str, Any]) -> str:
    for node in (data, data.get("data", {}) if isinstance(data.get("data"), dict) else {}):
        for key in ("id", "task_id", "taskId"):
            if node.get(key):
                return str(node[key])
    return ""


def output_urls(data: Any) -> list[str]:
    found: list[str] = []
    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"url", "video_url", "download_url"} and isinstance(value, str) and value.startswith(("http://", "https://")):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(data)
    return list(dict.fromkeys(found))


def unique_path(directory: Path, stem: str, ext: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / f"{stem}.{ext}"
    i = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{i}.{ext}"
        i += 1
    return candidate.resolve()


def emit(args: argparse.Namespace, data: Any, human: str = "") -> None:
    if args.json:
        print(redact(json.dumps(data, ensure_ascii=False)))
    elif human:
        print(human)
    elif isinstance(data, (dict, list)):
        print(redact(json.dumps(data, ensure_ascii=False, indent=2)))
    else:
        print(redact(str(data)))


def make_client(args: argparse.Namespace, store: Store, require_key: bool = True) -> Client:
    config = store.read_config()
    key = store.read_key() if require_key else ""
    return Client(resolve_base(args, store), key, config.get("bound_host", ""), args.debug)


def cmd_login(args: argparse.Namespace, store: Store) -> None:
    if args.device:
        device_login(args, store)
        return
    key = (getpass.getpass("API Key: ") if sys.stdin.isatty() else sys.stdin.readline()).strip()
    if not key:
        raise ValueError("没有读取到 Key")
    base = resolve_base(args, store)
    client = Client(base, key, debug=args.debug)
    client.request("GET", "/v1/models", timeout=30)
    store.write_key(key)
    store.write_config({"base_url": client.base, "bound_host": client.host, "profile": store.profile})
    emit(args, {"ok": True, "host": client.host}, f"登录成功，Key 已安全保存并绑定到 {client.host}")


def device_login(args: argparse.Namespace, store: Store) -> None:
    client = Client(resolve_base(args, store), "", debug=args.debug)
    start = client.request("POST", "/api/v1/device_auth", {"channel": "aic.py", "client_label": args.label}, auth=False)
    print(f"验证码：{start['user_code']}\n请在浏览器打开：{start['verification_url']}", file=sys.stderr)
    interval = max(1, int(start.get("interval", 3)))
    deadline = time.time() + int(start.get("expires_in", 600))
    while time.time() < deadline:
        time.sleep(interval)
        result = client.request("POST", "/api/v1/device_auth/poll", {"device_code": start["device_code"]}, auth=False)
        status = str(result.get("status", ""))
        if status == "slow_down":
            interval += 2
        elif status == "approved":
            key = str(result.get("key", ""))
            approved_base = str(result.get("base_url") or client.base)
            verified = Client(approved_base, key)
            verified.request("GET", "/v1/models")
            store.write_key(key)
            store.write_config({"base_url": verified.base, "bound_host": verified.host, "profile": store.profile})
            emit(args, {"ok": True, "host": verified.host}, "设备授权完成，Key 已保存（不会回显）")
            return
        elif status in {"denied", "expired"}:
            raise RuntimeError("设备授权已拒绝或过期")
    raise RuntimeError("设备授权已过期")


def fetch_models(client: Client) -> list[dict[str, Any]]:
    return extract_items(client.request("GET", "/v1/models"))


def ensure_model(client: Client, model: str) -> dict[str, Any]:
    for item in fetch_models(client):
        if str(item.get("id") or item.get("name")) == model:
            return item
    raise ValueError(f"模型 {model} 不在这把 Key 的当次模型列表中，已停止提交")


def cmd_simple_get(args: argparse.Namespace, store: Store, path: str) -> None:
    emit(args, make_client(args, store).request("GET", path))


def cmd_models(args: argparse.Namespace, store: Store) -> None:
    items = fetch_models(make_client(args, store))
    if args.json:
        emit(args, {"data": items})
    else:
        for item in items:
            print(item.get("id") or item.get("name"))


def cmd_check_model(args: argparse.Namespace, store: Store) -> None:
    client = make_client(args, store)
    ensure_model(client, args.model)
    try:
        result = client.request("GET", f"/v1/models/{urllib.parse.quote(args.model, safe='')}/access")
    except APIError as exc:
        if exc.status == 404:
            result = {"model": args.model, "allowed": None, "message": "站点暂不支持无计费预检；图片或视频调用前请确认风险"}
        else:
            raise
    emit(args, result)


def cmd_chat(args: argparse.Namespace, store: Store) -> None:
    client = make_client(args, store)
    ensure_model(client, args.model)
    payload = {"model": args.model, "messages": [{"role": "user", "content": args.prompt}], "stream": False}
    if args.max_tokens:
        payload["max_tokens"] = args.max_tokens
    emit(args, client.request("POST", "/v1/chat/completions", payload, timeout=300))


def task_seed(store: Store, kind: str, model: str, idem: str, payload: dict[str, Any]) -> dict[str, Any]:
    now = int(time.time())
    record = {"id": "", "idem_key": idem, "kind": kind, "model": model, "status": "submitting",
              "created_at": now, "updated_at": now, "request": payload, "files": []}
    path = store.save_task(record)
    record["record_path"] = str(path.resolve())
    store.save_task(record)
    return record


def cmd_image(args: argparse.Namespace, store: Store) -> None:
    client = make_client(args, store)
    ensure_model(client, args.model)
    idem = args.idem_key or secrets.token_hex(16)
    payload = {"model": args.model, "prompt": args.prompt, "async": True}
    if args.size:
        payload["size"] = args.size
    record = task_seed(store, "image", args.model, idem, payload)
    response = client.request("POST", "/v1/images/generations", payload, timeout=600,
                              headers={"Idempotency-Key": idem})
    tid = task_id(response) or idem
    state = task_state(response)
    record.update({"id": tid, "status": state or "completed", "updated_at": int(time.time())})
    record["record_path"] = str(store.save_task(record).resolve())
    if state in PENDING:
        follow_task(args, store, client, record)
        return
    files = save_image_results(client, response, Path(args.output), tid)
    record["files"] = [str(path) for path in files]
    store.save_task(record)
    emit(args, {"task_id": tid, "idem_key": idem, "status": record["status"], "files": record["files"]},
         f"✔ 图片请求完成\n  提交      1 次\n  任务      {tid}\n  模型      {args.model}\n  文件      " + ("、".join(record["files"]) or "服务端未返回可下载文件"))


def save_image_results(client: Client, response: Any, directory: Path, tid: str) -> list[Path]:
    files: list[Path] = []
    items = extract_items(response)
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        if item.get("b64_json"):
            path = unique_path(directory, f"image-{tid}-{index}", "png")
            path.write_bytes(base64.b64decode(item["b64_json"]))
            files.append(path)
        elif item.get("url"):
            ext = Path(urllib.parse.urlsplit(item["url"]).path).suffix.lstrip(".") or "png"
            path = unique_path(directory, f"image-{tid}-{index}", ext)
            client.download(item["url"], path)
            files.append(path)
    return files


def cmd_video(args: argparse.Namespace, store: Store) -> None:
    client = make_client(args, store)
    ensure_model(client, args.model)
    idem = secrets.token_hex(16)
    payload = {"model": args.model, "prompt": args.prompt, "duration": args.duration, "resolution": args.resolution}
    record = task_seed(store, "video", args.model, idem, payload)
    response = client.request("POST", "/v1/videos/generations", payload, timeout=60,
                              headers={"Idempotency-Key": idem})
    tid = task_id(response)
    if not tid:
        raise RuntimeError("视频提交响应缺少任务 ID；不会自动重提")
    record.update({"id": tid, "status": task_state(response) or "pending", "updated_at": int(time.time())})
    record["record_path"] = str(store.save_task(record).resolve())
    follow_task(args, store, client, record)


def cmd_doctor(args: argparse.Namespace, store: Store) -> None:
    client = make_client(args, store, require_key=False)
    remote = client.request("GET", "/api/v1/skill-manifest", auth=False)
    snapshot_path = Path(__file__).resolve().parents[1] / "references" / "manifest.snapshot.json"
    try:
        local = json.loads(snapshot_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        local = {}
    same = bool(local) and remote.get("version") == local.get("version") and (
        not remote.get("content_hash") or remote.get("content_hash") == local.get("content_hash"))
    summary = {"ok": same, "local_version": local.get("version"), "remote_version": remote.get("version"),
               "remote_hash": remote.get("content_hash"), "base_url": remote.get("base_url")}
    emit(args, summary, "Skill 事实清单已是最新" if same else
         f"Skill 事实清单有更新：本地 {local.get('version', '未知')}，线上 {remote.get('version', '未知')}；请更新 Skill")


def follow_task(args: argparse.Namespace, store: Store, client: Client, record: dict[str, Any]) -> None:
    tid = str(record["id"])
    deadline = time.time() + args.wait
    last_print = 0.0
    while True:
        result = client.request("GET", f"/v1/tasks/{urllib.parse.quote(tid, safe='')}", timeout=30)
        state = task_state(result)
        record.update({"status": state, "updated_at": int(time.time()), "last_result": result})
        store.save_task(record)
        if state in DONE:
            files: list[str] = []
            for index, url in enumerate(output_urls(result), 1):
                ext = Path(urllib.parse.urlsplit(url).path).suffix.lstrip(".") or "mp4"
                path = unique_path(Path(args.output), f"{record['kind']}-{tid}-{index}", ext)
                try:
                    client.download(url, path)
                except Exception as exc:
                    record["download_error"] = redact(str(exc))
                    store.save_task(record)
                    raise RuntimeError(f"任务已完成但下载失败：{exc}；不会重新提交") from None
                files.append(str(path))
            record["files"] = files
            store.save_task(record)
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            summary = {
                "task_id": tid, "status": state, "model": record["model"], "files": files,
                "cost": usage.get("cost"), "currency": usage.get("currency"),
            }
            emit(args, summary,
                 f"✔ {record['kind']} 已生成并下载\n  提交      1 次\n  任务      {tid}\n  模型      {record['model']}\n"
                 f"  费用      {usage.get('cost', '服务端未提供')}\n  文件      " + ("、".join(files) or "无"))
            return
        if state in FAILED:
            error = result.get("error", {}) if isinstance(result, dict) else {}
            charged = result.get("usage", {}).get("cost") if isinstance(result, dict) else None
            raise RuntimeError(f"任务失败：{redact(error)}；费用：{charged if charged is not None else '未知'}；重试将再次计费，请先确认")
        if time.time() >= deadline:
            emit(args, {"task_id": tid, "status": state, "record": record.get("record_path")},
                 f"任务仍在进行：{tid}\n可用 aic.py task {tid} 找回；本次不会重新提交")
            return
        if time.time() - last_print >= 15 and not args.json:
            print(f"[{record['kind']}] {tid}  {state or 'pending'}", file=sys.stderr)
            last_print = time.time()
        time.sleep(args.poll_interval)


def cmd_task(args: argparse.Namespace, store: Store) -> None:
    record, _ = store.load_task(args.token)
    age = int(time.time()) - int(record.get("created_at", 0))
    if not record.get("id"):
        if age > 600:
            raise RuntimeError("该幂等记录已超过十分钟；重放可能重新计费，已停止自动重提")
        raise RuntimeError(f"请求提交状态未知。可在十分钟内使用同一幂等键 {record.get('idem_key')} 人工确认重放")
    follow_task(args, store, make_client(args, store), record)


def cmd_tasks(args: argparse.Namespace, store: Store) -> None:
    store.prepare()
    rows = []
    for path in sorted(store.tasks_dir.glob("*.json")):
        try:
            row = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if args.pending and str(row.get("status", "")).lower() not in PENDING | {"submitting", ""}:
            continue
        rows.append({k: row.get(k) for k in ("id", "idem_key", "kind", "model", "status", "created_at")})
    emit(args, {"tasks": rows})


def handle_api_error(exc: APIError) -> str:
    kind = exc.error_type
    if kind in PERMISSION_ERRORS:
        return f"{exc}（权限或路由限制，未提交生成且不应重试；请在控制台检查 Key、套餐或路由）"
    if exc.status == 402:
        return f"{exc}（余额不足，请在浏览器充值；Agent 不处理支付）"
    if exc.status == 404:
        return f"{exc}（模型或接口不存在；请重新获取模型列表，不要猜模型名）"
    return str(exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aic.py")
    parser.add_argument("--base")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login")
    login.add_argument("--device", action="store_true")
    login.add_argument("--label", default="本机")
    sub.add_parser("whoami")
    sub.add_parser("models")
    sub.add_parser("balance")
    usage = sub.add_parser("usage")
    usage.add_argument("--days", type=int, default=30)
    check = sub.add_parser("check-model")
    check.add_argument("model")
    chat = sub.add_parser("chat")
    chat.add_argument("--model", required=True)
    chat.add_argument("--prompt", required=True)
    chat.add_argument("--max-tokens", type=int, default=0)
    image = sub.add_parser("image")
    image.add_argument("--model", required=True)
    image.add_argument("--prompt", required=True)
    image.add_argument("--size")
    image.add_argument("--idem-key")
    image.add_argument("--output", default="aicoming-out")
    image.add_argument("--wait", type=int, default=600)
    image.add_argument("--poll-interval", type=float, default=3)
    video = sub.add_parser("video")
    video.add_argument("--model", required=True)
    video.add_argument("--prompt", required=True)
    video.add_argument("--duration", type=int, required=True)
    video.add_argument("--resolution", required=True)
    video.add_argument("--output", default="aicoming-out")
    video.add_argument("--wait", type=int, default=600)
    video.add_argument("--poll-interval", type=float, default=3)
    task = sub.add_parser("task")
    task.add_argument("token")
    task.add_argument("--output", default="aicoming-out")
    task.add_argument("--wait", type=int, default=600)
    task.add_argument("--poll-interval", type=float, default=3)
    tasks = sub.add_parser("tasks")
    tasks.add_argument("--pending", action="store_true")
    sub.add_parser("doctor")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(args.profile)
    try:
        if args.command == "login":
            cmd_login(args, store)
        elif args.command == "models":
            cmd_models(args, store)
        elif args.command == "balance":
            cmd_simple_get(args, store, "/v1/balance")
        elif args.command == "usage":
            cmd_simple_get(args, store, f"/v1/dashboard/billing/usage?days={max(1, min(args.days, 366))}")
        elif args.command == "whoami":
            cmd_simple_get(args, store, "/v1/dashboard/billing/summary")
        elif args.command == "check-model":
            cmd_check_model(args, store)
        elif args.command == "chat":
            cmd_chat(args, store)
        elif args.command == "image":
            cmd_image(args, store)
        elif args.command == "video":
            cmd_video(args, store)
        elif args.command == "task":
            cmd_task(args, store)
        elif args.command == "tasks":
            cmd_tasks(args, store)
        elif args.command == "doctor":
            cmd_doctor(args, store)
        return 0
    except APIError as exc:
        print(redact(handle_api_error(exc)), file=sys.stderr)
    except (ValueError, RuntimeError, FileNotFoundError, KeyError) as exc:
        print(redact(str(exc)), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
