import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "aic.py"
SPEC = importlib.util.spec_from_file_location("aic_cli", SCRIPT)
aic = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = aic
SPEC.loader.exec_module(aic)


class State:
    def __init__(self):
        self.requests = []
        self.mode = "ok"
        self.polls = 0
        self.downloads = 0


def handler_for(state, redirect_port=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _body(self):
            length = int(self.headers.get("Content-Length", "0"))
            return self.rfile.read(length) if length else b""

        def _json(self, status, data):
            raw = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            state.requests.append((self.command, self.path, self.headers.get("Authorization"), self._body()))
            if self.path == "/v1/models":
                if state.mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", f"http://127.0.0.1:{redirect_port}/stolen")
                    self.end_headers()
                    return
                self._json(200, {"data": [{"id": "video-model"}, {"id": "image-model"}, {"id": "chat-model"}]})
            elif self.path.startswith("/v1/tasks/"):
                state.polls += 1
                if state.mode == "failed":
                    self._json(200, {"id": "task-1", "status": "failed", "error": {"message": "bad"}})
                elif state.polls < 2:
                    self._json(200, {"id": "task-1", "status": "processing", "progress": 40})
                else:
                    self._json(200, {"id": "task-1", "status": "completed",
                                     "result": {"videos": [{"download_url": f"http://127.0.0.1:{self.server.server_port}/file.mp4"}]},
                                     "usage": {"cost": 0.84, "currency": "CNY"}})
            elif self.path == "/file.mp4":
                state.downloads += 1
                raw = b"video-bytes"
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            elif "/access" in self.path:
                self._json(200, {"allowed": True})
            else:
                self._json(200, {"ok": True})

        def do_POST(self):
            body = self._body()
            state.requests.append((self.command, self.path, self.headers.get("Authorization"), body))
            if self.path == "/v1/videos/generations":
                self._json(200, {"id": "task-1", "status": "pending"})
            elif self.path == "/v1/chat/completions":
                if state.mode == "permission":
                    self._json(403, {"error": {"type": "model_not_allowed_for_key", "message": "blocked"}})
                else:
                    self._json(200, {"choices": [{"message": {"content": "ok"}}]})
            else:
                self._json(200, {})

    return Handler


class Server:
    def __init__(self, state, redirect_port=None):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state, redirect_port))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base(self):
        return f"http://127.0.0.1:{self.httpd.server_port}"


class CLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name) / "cfg"
        self.output = Path(self.temp.name) / "out"
        self.env = mock.patch.dict(os.environ, {"AICOMING_CONFIG_HOME": str(self.config)}, clear=False)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def run_cli(self, argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(out), redirect_stderr(err):
            code = aic.main(argv)
        return code, out.getvalue(), err.getvalue()

    def login(self, base, key="sk-super-secret-value"):
        code, out, err = self.run_cli(["--base", base, "login"], key + "\n")
        self.assertEqual(code, 0, err)
        return out

    def test_login_has_no_key_argument_and_never_prints_key(self):
        state = State()
        with Server(state) as srv:
            out = self.login(srv.base)
        self.assertNotIn("super-secret", out)
        with self.assertRaises(SystemExit):
            aic.build_parser().parse_args(["login", "sk-on-command-line"])

    def test_redirect_does_not_forward_authorization(self):
        sink_state = State()
        with Server(sink_state) as sink:
            source_state = State()
            source_state.mode = "redirect"
            with Server(source_state, sink.httpd.server_port) as source:
                code, out, err = self.run_cli(["--base", source.base, "login"], "sk-redirect-secret\n")
        self.assertEqual(code, 1)
        self.assertEqual(sink_state.requests, [])
        self.assertNotIn("redirect-secret", out + err)

    def test_bound_host_rejects_before_network(self):
        store = aic.Store()
        store.write_key("sk-secret-bound")
        store.write_config({"base_url": "https://example.test", "bound_host": "example.test"})
        code, out, err = self.run_cli(["--base", "http://127.0.0.1:9", "models"])
        self.assertEqual(code, 1)
        self.assertIn("拒绝发送", err)
        self.assertNotIn("secret-bound", out + err)

    @unittest.skipIf(os.name == "nt", "POSIX mode assertion")
    def test_key_permissions_are_0600(self):
        store = aic.Store()
        store.write_key("sk-secret-mode")
        self.assertEqual(stat.S_IMODE(store.key_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(store.dir.stat().st_mode), 0o700)

    def test_video_pending_completed_download_and_no_overwrite(self):
        state = State()
        with Server(state) as srv:
            self.login(srv.base)
            argv = ["--base", srv.base, "video", "--model", "video-model", "--prompt", "p",
                    "--duration", "5", "--resolution", "720p", "--output", str(self.output),
                    "--poll-interval", "0.01", "--wait", "2"]
            code, out, err = self.run_cli(argv)
            self.assertEqual(code, 0, err)
            first = sorted(self.output.glob("*.mp4"))
            self.assertEqual(len(first), 1)
            self.assertGreater(first[0].stat().st_size, 0)
            state.polls = 0
            code, out, err = self.run_cli(argv)
            self.assertEqual(code, 0, err)
            second = sorted(self.output.glob("*.mp4"))
            self.assertEqual(len(second), 2)
            self.assertNotEqual(second[0].name, second[1].name)

    def test_failed_video_does_not_download(self):
        state = State()
        state.mode = "failed"
        with Server(state) as srv:
            self.login(srv.base)
            code, out, err = self.run_cli([
                "--base", srv.base, "video", "--model", "video-model", "--prompt", "p",
                "--duration", "5", "--resolution", "720p", "--output", str(self.output),
                "--poll-interval", "0.01", "--wait", "1",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(state.downloads, 0)
        self.assertIn("重试将再次计费", err)

    def test_stale_unknown_submission_is_not_replayed(self):
        store = aic.Store()
        store.save_task({"id": "", "idem_key": "old-idem", "status": "submitting", "created_at": int(time.time()) - 601})
        code, out, err = self.run_cli(["task", "old-idem", "--wait", "0"])
        self.assertEqual(code, 1)
        self.assertIn("超过十分钟", err)
        self.assertIn("停止自动重提", err)

    def test_unknown_model_is_rejected_before_post(self):
        state = State()
        with Server(state) as srv:
            self.login(srv.base)
            before = len(state.requests)
            code, out, err = self.run_cli([
                "--base", srv.base, "chat", "--model", "invented", "--prompt", "hi"
            ])
        self.assertEqual(code, 1)
        new_requests = state.requests[before:]
        self.assertEqual([r[0] for r in new_requests], ["GET"])
        self.assertIn("已停止提交", err)

    def test_permission_error_is_requested_once_and_no_secret_in_json(self):
        state = State()
        state.mode = "permission"
        with Server(state) as srv:
            self.login(srv.base)
            before = len(state.requests)
            code, out, err = self.run_cli([
                "--json", "--base", srv.base, "chat", "--model", "chat-model", "--prompt", "hi"
            ])
        self.assertEqual(code, 1)
        posts = [r for r in state.requests[before:] if r[0] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertIn("不应重试", err)
        self.assertNotIn("super-secret", out + err)


if __name__ == "__main__":
    unittest.main()
