"""Authenticated, loopback-only stdlib REST API for Seven."""
from __future__ import annotations

import hmac
import json
import logging
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

from seven import config, __version__
from seven.agent.loop import Seven

logger = logging.getLogger("seven.api")


def _token_path():
    return config.DATA_DIR / "api.token"


def get_or_create_api_token() -> str:
    """Return a strong environment token or atomically create a private file."""
    configured = os.getenv("SEVEN_API_TOKEN", "").strip()
    if configured:
        if len(configured) < 32:
            raise ValueError("SEVEN_API_TOKEN must contain at least 32 characters")
        return configured
    path = _token_path()
    try:
        existing = path.read_text(encoding="utf-8").strip()
        if len(existing) >= 32:
            try:
                path.chmod(0o600)
            except OSError:
                logger.warning("Could not restrict API token permissions: %s", path)
            return existing
        if existing:
            raise RuntimeError(f"API token file is too short; remove and regenerate it: {path}")
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        token = secrets.token_urlsafe(32)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(token + "\n")
        return token
    except FileExistsError:
        for _ in range(100):
            existing = path.read_text(encoding="utf-8").strip()
            if len(existing) >= 32:
                return existing
            time.sleep(0.01)
        raise RuntimeError(f"concurrently created API token is invalid: {path}")


class APIRequestError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class SevenAPIServer(ThreadingHTTPServer):
    daemon_threads = True
    # Permit an immediate clean restart after accepted connections enter
    # TIME_WAIT; an actively listening instance still owns the port.
    allow_reuse_address = True

    def __init__(self, address, handler, token: str, agent: Optional[Seven] = None):
        self.seven_api_token = token
        self.seven_agent = agent
        self.seven_owns_agent = agent is None
        self.seven_agent_lock = threading.RLock()
        self.seven_slots = threading.BoundedSemaphore(max(1, config.API_MAX_CONCURRENT_REQUESTS))
        self.seven_active = 0
        self.seven_active_condition = threading.Condition()
        self.seven_thread: threading.Thread | None = None
        self.seven_shutdown_lock = threading.Lock()
        self.seven_closed = False
        super().__init__(address, handler)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(max(1.0, config.API_SOCKET_TIMEOUT))
        return request, address

    def get_agent(self) -> Seven:
        with self.seven_agent_lock:
            if self.seven_agent is None:
                self.seven_agent = Seven()
                self.seven_agent.start_heartbeat()
            return self.seven_agent

    def shutdown_cleanly(self) -> None:
        with self.seven_shutdown_lock:
            if self.seven_closed:
                return
            self.seven_closed = True
        if self.seven_thread and self.seven_thread.is_alive():
            self.shutdown()
            self.seven_thread.join(timeout=10)
        self.server_close()
        deadline = time.monotonic() + 10
        with self.seven_active_condition:
            while self.seven_active and time.monotonic() < deadline:
                self.seven_active_condition.wait(timeout=0.1)
            active = self.seven_active
        if self.seven_owns_agent and self.seven_agent is not None and not active:
            self.seven_agent.shutdown()
            self.seven_agent = None
        elif active:
            logger.error("API closed with %s active request(s); owned agent left intact", active)

    def admit(self) -> bool:
        if not self.seven_slots.acquire(blocking=False):
            return False
        with self.seven_active_condition:
            self.seven_active += 1
        return True

    def release_request(self) -> None:
        with self.seven_active_condition:
            self.seven_active -= 1
            self.seven_active_condition.notify_all()
        self.seven_slots.release()


class SevenHandler(BaseHTTPRequestHandler):
    server_version = f"SevenRealAPI/{__version__}"

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if code == 401:
            self.send_header("WWW-Authenticate", 'Bearer realm="Seven"')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            logger.info("client disconnected before API response completed")

    def _read_json(self) -> dict:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise APIRequestError(411, "Content-Length required")
        try:
            length = int(raw_length)
        except ValueError:
            raise APIRequestError(400, "invalid Content-Length")
        if length <= 0:
            raise APIRequestError(400, "non-empty JSON body required")
        if length > max(1, config.API_MAX_BODY_BYTES):
            raise APIRequestError(413, f"request body exceeds {config.API_MAX_BODY_BYTES} bytes")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise APIRequestError(400, "incomplete request body")
        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise APIRequestError(400, "malformed UTF-8 JSON")
        if not isinstance(body, dict):
            raise APIRequestError(400, "JSON body must be an object")
        return body

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
        if not self.server.admit():
            self._send(503, {"error": "request concurrency limit reached"})
            return
        try:
            self._get()
        finally:
            self.server.release_request()

    def _get(self):
        path = urlparse(self.path).path
        if path in ("/", "/health"):
            self._send(200, {"ok": True, "service": "seven-real", "version": __version__})
            return
        if not self._require_auth():
            return
        try:
            agent = self.server.get_agent()
        except Exception:
            logger.exception("API agent initialization failed")
            self._send(503, {"error": "agent unavailable"})
            return
        if path == "/status":
            try:
                self._send(200, {"status": agent.handle("/status")})
            except Exception:
                logger.exception("API status failed")
                self._send(500, {"error": "agent request failed"})
        elif path == "/tools":
            try:
                self._send(200, {"tools": agent.handle("/tools"), "names": agent.tools.names()})
            except Exception:
                logger.exception("API tools failed")
                self._send(500, {"error": "agent request failed"})
        else:
            self._send(404, {"error": "not found", "paths": ["/health", "/status", "/tools", "POST /chat"]})

    def do_POST(self):
        if not self.server.admit():
            self._send(503, {"error": "request concurrency limit reached"})
            return
        try:
            self._post()
        finally:
            self.server.release_request()

    def _post(self):
        if urlparse(self.path).path != "/chat":
            self._send(404, {"error": "not found"})
            return
        if not self._require_auth():
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._send(415, {"error": "Content-Type must be application/json"})
            return
        try:
            body = self._read_json()
        except APIRequestError as exc:
            self._send(exc.status, {"error": str(exc)})
            return
        message = body.get("message") or body.get("text") or ""
        if not isinstance(message, str) or not message.strip():
            self._send(400, {"error": "message required"})
            return
        message = message.strip()
        if len(message) > max(1, config.API_MAX_MESSAGE_CHARS):
            self._send(413, {"error": f"message exceeds {config.API_MAX_MESSAGE_CHARS} characters"})
            return
        try:
            agent = self.server.get_agent()
            with self.server.seven_agent_lock:
                reply = agent.handle(message)
        except Exception:
            logger.exception("API chat failed")
            self._send(500, {"error": "agent request failed"})
            return
        self._send(200, {"reply": reply, "role": "assistant"})

    def _method_not_allowed(self):
        if not self.server.admit():
            self._send(503, {"error": "request concurrency limit reached"})
            return
        try:
            self._send(405, {"error": "method not allowed"})
        finally:
            self.server.release_request()

    do_PUT = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_OPTIONS = _method_not_allowed


def start_api_server(host: Optional[str] = None, port: Optional[int] = None, background: bool = True, agent: Optional[Seven] = None) -> SevenAPIServer:
    host = host or config.API_HOST
    port = config.API_PORT if port is None else int(port)
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Seven API supports loopback binding only")
    httpd = SevenAPIServer((host, port), SevenHandler, get_or_create_api_token(), agent=agent)
    bound_host, bound_port = httpd.server_address[:2]
    logger.info("API listening on http://%s:%s", bound_host, bound_port)
    if background:
        thread = threading.Thread(target=httpd.serve_forever, name="seven-api", daemon=True)
        httpd.seven_thread = thread
        thread.start()
    return httpd


def run_api_blocking() -> int:
    try:
        httpd = start_api_server(background=False)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Seven API failed to start: {exc}")
        return 1
    host, port = httpd.server_address[:2]
    print(f"Seven API http://{host}:{port}")
    print('POST /chat  {"message": "..."}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API")
    finally:
        httpd.shutdown_cleanly()
    return 0
