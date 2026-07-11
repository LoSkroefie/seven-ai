"""
Minimal local REST API for Seven Real.
stdlib only — no FastAPI required.
Bind 127.0.0.1 only.
"""
from __future__ import annotations

import json
import hmac
import logging
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from seven import config, __version__
from seven.agent.loop import Seven

logger = logging.getLogger("seven.api")


def _token_path():
    return config.DATA_DIR / "api.token"


def get_or_create_api_token() -> str:
    """Return the API bearer token, creating a private local token if needed."""
    configured = os.getenv("SEVEN_API_TOKEN", "").strip()
    if configured:
        return configured
    path = _token_path()
    try:
        existing = path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass
    token = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        logger.warning("Could not restrict API token permissions: %s", path)
    return token


class _SevenAPIState:
    agent: Optional[Seven] = None
    lock = threading.RLock()


def _get_agent() -> Seven:
    with _SevenAPIState.lock:
        if _SevenAPIState.agent is None:
            _SevenAPIState.agent = Seven()
            _SevenAPIState.agent.start_heartbeat()
        return _SevenAPIState.agent


class SevenHandler(BaseHTTPRequestHandler):
    server_version = "SevenRealAPI/4.0"

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, body: dict, content_type: str = "application/json"):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > 1_048_576:
            raise ValueError("request body exceeds 1 MiB")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _authorized(self) -> bool:
        expected = getattr(self.server, "seven_api_token", "")
        auth = self.headers.get("Authorization", "")
        supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        supplied = supplied or self.headers.get("X-Seven-Token", "").strip()
        return bool(expected and supplied and hmac.compare_digest(expected, supplied))

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        self._send(401, {"error": "authentication required"})
        return False

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._send(200, {"ok": True, "service": "seven-real", "version": __version__})
            return
        if not self._require_auth():
            return
        agent = _get_agent()
        if path == "/status":
            text = agent.handle("/status")
            self._send(200, {"status": text})
            return
        if path == "/tools":
            text = agent.handle("/tools")
            self._send(200, {"tools": text, "names": agent.tools.names()})
            return
        self._send(404, {"error": "not found", "paths": ["/", "/health", "/status", "/tools", "POST /chat"]})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/chat":
            self._send(404, {"error": "not found"})
            return
        if not self._require_auth():
            return
        try:
            body = self._read_json()
        except ValueError as exc:
            self._send(413, {"error": str(exc)})
            return
        message = (body.get("message") or body.get("text") or "").strip()
        if not message:
            self._send(400, {"error": "message required"})
            return
        agent = _get_agent()
        with _SevenAPIState.lock:
            reply = agent.handle(message)
        self._send(200, {"reply": reply, "role": "assistant"})


def start_api_server(
    host: Optional[str] = None,
    port: Optional[int] = None,
    background: bool = True,
    agent: Optional[Seven] = None,
) -> ThreadingHTTPServer:
    host = host or config.API_HOST
    port = port or config.API_PORT
    if agent is not None:
        _SevenAPIState.agent = agent
    httpd = ThreadingHTTPServer((host, port), SevenHandler)
    httpd.seven_api_token = get_or_create_api_token()
    logger.info("API listening on http://%s:%s  (POST /chat, GET /status)", host, port)
    if background:
        t = threading.Thread(target=httpd.serve_forever, name="seven-api", daemon=True)
        t.start()
    return httpd


def run_api_blocking():
    httpd = start_api_server(background=False)
    print(f"Seven API http://{config.API_HOST}:{config.API_PORT}")
    print("POST /chat  {\"message\": \"...\"}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API")
        httpd.shutdown()
        if _SevenAPIState.agent:
            _SevenAPIState.agent.shutdown()
