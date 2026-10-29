"""Loopback-only dashboard. No dependencies, telemetry, remote assets, or cloud state."""
import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .core import ROOT, discover, preflight, run


class State:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.info = discover()
        self.active = False
        self.report = None
        self.history = []
        self.directory = ROOT / ".proof/reports"
        self.directory.mkdir(parents=True, exist_ok=True)
        for p in sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
            try:
                self.history.append(json.loads(p.read_text()))
            except (OSError, ValueError):
                pass
        if self.history:
            self.report = self.history[0]

    def publish(self, value):
        with self.lock:
            self.report = value

    def start(self, config):
        with self.lock:
            if self.active:
                return False
            self.active = True
            self.report = None
        def work():
            try:
                value = run(config, self.publish)
                path = self.directory / (value["id"] + ".json")
                path.write_text(json.dumps(value, indent=2) + "\n")
                path.chmod(0o600)
                with self.lock:
                    self.history.insert(0, value)
                    self.history = self.history[:10]
            finally:
                with self.lock:
                    self.active = False
        threading.Thread(target=work, daemon=True).start()
        return True


def serve(port=8741):
    state = State()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def trusted_host(self):
            try:
                host = urlsplit("http://" + self.headers.get("Host", "")).hostname
                return host in {"127.0.0.1", "localhost", "::1"}
            except ValueError:
                return False

        def send(self, data, status=200, kind="application/json", extra=None):
            body = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.trusted_host():
                return self.send({"error": "Loopback Host required"}, 403)
            path = urlsplit(self.path).path
            if path == "/api/state":
                with state.lock:
                    return self.send({"token": state.token, "info": state.info, "active": state.active,
                                      "report": state.report, "history": [{k:r.get(k) for k in ["id","status","mode","started_at","elapsed_s","suite"]} for r in state.history]})
            if path == "/api/report":
                with state.lock:
                    if not state.report:
                        return self.send({"error": "No report yet"}, 404)
                    return self.send(json.dumps(state.report, indent=2).encode(), extra={"Content-Disposition": 'attachment; filename="scout-offline-proof.json"'})
            assets = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/explore.js": ("explore.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8"), "/favicon.svg": ("favicon.svg", "image/svg+xml")}
            for family in ["mono", "sans"]:
                for weight in [400, 600]:
                    name = f"fonts/ibm-plex-{family}-{weight}.woff2"
                    assets["/" + name] = (name, "font/woff2")
            if path in assets:
                name, kind = assets[path]
                return self.send((ROOT / "web" / name).read_bytes(), kind=kind)
            return self.send({"error": "Not found"}, 404)

        def do_POST(self):
            if not self.trusted_host() or not hmac.compare_digest(self.headers.get("X-Scout-Token", ""), state.token):
                return self.send({"error": "Open this dashboard locally to authorize actions"}, 403)
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + self.headers.get("Host"):
                return self.send({"error": "Cross-origin request refused"}, 403)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("Request must be between 1 and 16384 bytes")
                config = json.loads(self.rfile.read(length))
                if not isinstance(config, dict):
                    raise ValueError("Expected a configuration object")
                config = {k: config.get(k, v) for k, v in state.info["defaults"].items()}
                if any(not isinstance(v, str) or len(v) > 4096 for v in config.values()):
                    raise ValueError("Configuration values must be short strings")
                if config["mode"] not in {"mlx", "harness"}:
                    raise ValueError("Choose MLX or harness mode")
                if self.path == "/api/preflight":
                    from .suites import describe, load_suite
                    checks = preflight(config)
                    suite = None
                    if next((c["passed"] for c in checks if c["label"] == "Task suite"), False):
                        suite = describe(load_suite(config["suite"]))
                    return self.send({"checks": checks, "suite": suite})
                if self.path == "/api/run":
                    if not state.start(config):
                        return self.send({"error": "A proof is already running"}, 409)
                    return self.send({"accepted": True}, 202)
                return self.send({"error": "Not found"}, 404)
            except (ValueError, OSError) as exc:
                return self.send({"error": str(exc)}, 400)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Scout Offline Proof · http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
