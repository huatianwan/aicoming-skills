#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aic.py — AIComing 零依赖命令行(仅标准库,Python 3.8+)。

供 agent 直接用用户的 AIComing key 干活:列模型/对话/生图/查余额/视频任务。

用法:
  python aic.py models [关键词]              # 可用模型列表(需 key)
  python aic.py chat <model> <prompt...>     # 一次性对话,打印回复
  python aic.py image <model> <prompt...> [--size 1024x1024] [-o out.png]
  python aic.py balance                      # 钱包余额(CNY)
  python aic.py video <model> <prompt...>    # 提交视频任务并轮询到完成

key 来源(优先级): 环境变量 AICOMING_API_KEY > 文件 ~/.aicoming/key
base url: 环境变量 AICOMING_BASE_URL,默认 https://api.aicoming.top
          (生图/视频等长请求务必走默认直连域,经 CDN 的域名会被 100s 网关超时掐断)
"""
import base64
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.aicoming.top"


def api_key():
    k = os.environ.get("AICOMING_API_KEY", "").strip()
    if not k:
        p = os.path.join(os.path.expanduser("~"), ".aicoming", "key")
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                k = f.read().strip()
    if not k:
        sys.exit("未找到 API key: 请 export AICOMING_API_KEY=sk-... "
                 "(或写入 ~/.aicoming/key)。到 https://aicoming.top/console 创建。")
    return k


def base_url():
    return os.environ.get("AICOMING_BASE_URL", DEFAULT_BASE).rstrip("/")


def request(method, path, body=None, timeout=120, extra_headers=None):
    """带鉴权的 JSON 请求。容忍生图心跳的前导空白;200+error body 也按错误抛出。"""
    url = base_url() + path
    headers = {
        "Authorization": "Bearer " + api_key(),
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            err = json.loads(raw)
            msg = (err.get("error") or {}).get("message") or raw.decode("utf-8", "replace")[:300]
        except Exception:
            msg = raw.decode("utf-8", "replace")[:300]
        sys.exit("HTTP %d: %s" % (e.code, msg))
    except urllib.error.URLError as e:
        sys.exit("网络错误: %s" % e)
    obj = json.loads(raw)  # json.loads 天然容忍心跳的前导空白字节
    # 生图长等待期间网关已提交 200,失败会以 {"error":{...,"http_status":N}} 返回
    if isinstance(obj, dict) and obj.get("error"):
        err = obj["error"]
        sys.exit("上游错误(HTTP %s): %s" % (err.get("http_status", 200), err.get("message", err)))
    return obj


def cmd_models(args):
    kw = (args[0].lower() if args else "")
    obj = request("GET", "/v1/models", timeout=30)
    ids = sorted(m.get("id", "") for m in obj.get("data", []))
    hits = [i for i in ids if kw in i.lower()] if kw else ids
    for i in hits:
        print(i)
    print("-- %d 个模型%s" % (len(hits), (" 匹配 %r" % kw) if kw else ""))


def cmd_chat(args):
    if len(args) < 2:
        sys.exit("用法: aic.py chat <model> <prompt...>")
    model, prompt = args[0], " ".join(args[1:])
    obj = request("POST", "/v1/chat/completions", {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }, timeout=300)
    choices = obj.get("choices") or []
    if not choices:
        sys.exit("空响应: %s" % json.dumps(obj, ensure_ascii=False)[:300])
    print(choices[0].get("message", {}).get("content", ""))
    u = obj.get("usage") or {}
    print("-- tokens: in=%s out=%s" % (u.get("prompt_tokens", "?"), u.get("completion_tokens", "?")),
          file=sys.stderr)


def cmd_image(args):
    out, size, rest = None, None, []
    it = iter(args)
    for a in it:
        if a == "-o":
            out = next(it, None)
        elif a == "--size":
            size = next(it, None)
        else:
            rest.append(a)
    if len(rest) < 2:
        sys.exit("用法: aic.py image <model> <prompt...> [--size WxH] [-o out.png]")
    model, prompt = rest[0], " ".join(rest[1:])
    body = {"model": model, "prompt": prompt, "n": 1}
    if size:
        body["size"] = size
    # Idempotency-Key: 生图 60-300s,连接被网络/超时掐断后带同键重试直取结果,不重复扣费。
    idem = "aic-" + uuid.uuid4().hex
    print("提交生图(幂等键 %s),生成通常 1-3 分钟..." % idem, file=sys.stderr)
    obj = request("POST", "/v1/images/generations", body, timeout=600,
                  extra_headers={"Idempotency-Key": idem})
    data = (obj.get("data") or [{}])[0]
    out = out or ("aicoming-%d.png" % int(time.time()))
    if data.get("b64_json"):
        with open(out, "wb") as f:
            f.write(base64.b64decode(data["b64_json"]))
        print("已保存: %s" % out)
    elif data.get("url"):
        print("图片 URL: %s" % data["url"])
        try:
            urllib.request.urlretrieve(data["url"], out)
            print("已下载: %s" % out)
        except Exception as e:
            print("(下载失败 %s,可手动打开 URL)" % e, file=sys.stderr)
    else:
        sys.exit("响应无图: %s" % json.dumps(obj, ensure_ascii=False)[:300])


def cmd_balance(_args):
    obj = request("GET", "/v1/balance", timeout=30)
    d = obj.get("data") or obj
    print(json.dumps(d, ensure_ascii=False, indent=2))


def cmd_video(args):
    if len(args) < 2:
        sys.exit("用法: aic.py video <model> <prompt...>")
    model, prompt = args[0], " ".join(args[1:])
    obj = request("POST", "/v1/videos/generations",
                  {"model": model, "prompt": prompt}, timeout=120)
    d = obj.get("data") or obj
    task_id = d.get("id") or d.get("task_id")
    if not task_id:
        sys.exit("未拿到任务 id: %s" % json.dumps(obj, ensure_ascii=False)[:300])
    print("视频任务已提交: %s,轮询中(通常 1-5 分钟)..." % task_id, file=sys.stderr)
    for _ in range(150):  # 最多 ~12.5 分钟
        time.sleep(5)
        st = request("GET", "/v1/videos/generations/" + str(task_id), timeout=30)
        sd = st.get("data") or st
        status = str(sd.get("status", "")).lower()
        if status in ("completed", "succeeded", "success"):
            print(json.dumps(sd, ensure_ascii=False, indent=2))
            return
        if status in ("failed", "error", "canceled"):
            sys.exit("任务失败: %s" % json.dumps(sd, ensure_ascii=False)[:400])
        print("  状态: %s" % (status or "pending"), file=sys.stderr)
    sys.exit("轮询超时,任务可能仍在进行: GET /v1/videos/generations/%s" % task_id)


def main():
    cmds = {"models": cmd_models, "chat": cmd_chat, "image": cmd_image,
            "balance": cmd_balance, "video": cmd_video}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
