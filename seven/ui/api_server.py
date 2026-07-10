"""
Minimal local REST API for Seven Real.
stdlib only — no FastAPI required.
Bind 127.0.0.1 only.
"""
from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from seven import config
from seven.agent.loop import Seven

logger = logging.getLogger("seven.api")


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
        self.send_header("Access-Control-Allow-Origin", "null")  # local file pages only if needed
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        agent = _get_agent()
        if path in ("/", "/health"):
            self._send(200, {"ok": True, "service": "seven-real", "version": "4.0.1"})
            return
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
        body = self._read_json()
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
