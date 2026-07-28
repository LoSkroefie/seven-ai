from __future__ import annotations

import hmac
import ipaddress
import json
import logging
import mimetypes
import os
import queue
import secrets
import signal
import threading
import time
from email.utils import formatdate
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .config import GatewayConfig
from .media import validate_audio, validate_jpeg
from .security import RateLimiter, safe_json, token_digest, verify_password
from .service import TurnService
from .store import GatewayStore
from .transcription import (
    DisabledTranscriber,
    TranscriptionUnavailable,
    WhisperTranscriber,
)
from .upstream import SevenUpstream

LOGGER = logging.getLogger("seven.gateway")
COOKIE_NAME = "__Host-seven_session"


class RequestError(ValueError):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status = status
        self.code = code


class GatewayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address,
        config: GatewayConfig,
        *,
        store: GatewayStore | None = None,
        upstream: SevenUpstream | None = None,
        transcriber=None,
    ):
        self.config = config.validate()
        self.store = store or GatewayStore(config.database_path)
        self.upstream = upstream or SevenUpstream(
            config.internal_url, config.internal_token, config.upstream_timeout_seconds
        )
        self.turns = TurnService(self.store, self.upstream, config.queue_limit)
        self.transcriber = transcriber or (
            WhisperTranscriber(
                config.whisper_model,
                config.whisper_download_root,
                config.whisper_threads,
            )
            if config.transcription_enabled
            else DisabledTranscriber()
        )
        self.rates = RateLimiter()
        super().__init__(address, GatewayHandler)

    def server_close(self) -> None:
        self.turns.close()
        super().server_close()


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "SevenGateway"
    sys_version = ""

    def log_message(self, fmt, *args):
        LOGGER.info("%s %s", self._identity(), fmt % args)

    @property
    def cfg(self) -> GatewayConfig:
        return self.server.config

    def _identity(self) -> str:
        peer = self.client_address[0]
        try:
            peer_is_loopback = ipaddress.ip_address(peer).is_loopback
        except ValueError:
            peer_is_loopback = False
        if peer_is_loopback:
            forwarded = self.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
            if forwarded:
                try:
                    return str(ipaddress.ip_address(forwarded))
                except ValueError:
                    pass
        return peer

    def _rate(self, bucket: str, limit: int, seconds: int) -> None:
        if not self.server.rates.allow(bucket, self._identity(), limit, seconds):
            raise RequestError(429, "rate_limited")

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data: blob:; connect-src 'self'; media-src 'self' blob:; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )

    def _json(self, status: int, payload: dict, *, cookie: str | None = None) -> None:
        raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self._security_headers()
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, exc: RequestError) -> None:
        self._json(exc.status, {"ok": False, "error": exc.code})

    def _origin(self) -> None:
        supplied = self.headers.get("Origin", "")
        if not supplied or not hmac.compare_digest(supplied, self.cfg.public_origin):
            raise RequestError(403, "origin_rejected")

    def _read(self, limit: int) -> bytes:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise RequestError(411, "content_length_required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise RequestError(400, "invalid_content_length") from exc
        if length <= 0:
            raise RequestError(400, "empty_body")
        if length > limit:
            raise RequestError(413, "body_too_large")
        data = self.rfile.read(length)
        if len(data) != length:
            raise RequestError(400, "incomplete_body")
        return data

    def _read_json(self) -> dict:
        if self.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json":
            raise RequestError(415, "json_required")
        try:
            value = json.loads(self._read(self.cfg.body_limit_bytes).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestError(400, "invalid_json") from exc
        if not isinstance(value, dict):
            raise RequestError(400, "object_required")
        return value

    def _cookie_token(self) -> str:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception as exc:
            raise RequestError(401, "authentication_required") from exc
        morsel = cookie.get(COOKIE_NAME)
        if not morsel or not 32 <= len(morsel.value) <= 256:
            raise RequestError(401, "authentication_required")
        return morsel.value

    def _session(self, require_csrf: bool = False) -> tuple[str, str]:
        # Browsers do not consistently send Origin on same-origin GET/SSE
        # requests.  State-changing requests still require both an exact
        # Origin match and the per-session CSRF token.
        if require_csrf:
            self._origin()
        token = self._cookie_token()
        session_hash = token_digest(token, self.cfg.session_secret)
        csrf = self.headers.get("X-CSRF-Token", "")
        if len(csrf) > 256:
            raise RequestError(403, "csrf_rejected")
        csrf_hash = token_digest(csrf, self.cfg.session_secret) if csrf else None
        if not self.server.store.validate_session(
            session_hash, csrf_hash, self.cfg.session_idle_seconds, require_csrf
        ):
            raise RequestError(401, "authentication_required")
        return token, session_hash

    def _cookie(self, token: str, *, clear: bool = False) -> str:
        parts = [
            f"{COOKIE_NAME}={'' if clear else token}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
        ]
        if self.cfg.cookie_secure:
            parts.append("Secure")
        if clear:
            parts.extend(("Max-Age=0", "Expires=Thu, 01 Jan 1970 00:00:00 GMT"))
        else:
            parts.append(f"Max-Age={self.cfg.session_ttl_seconds}")
        return "; ".join(parts)

    def do_GET(self):
        try:
            self._rate("all", self.cfg.rate_per_minute, 60)
            self._get()
        except RequestError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            LOGGER.exception("request failed")
            self._json(500, {"ok": False, "error": "internal_error"})

    def _get(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            healthy = self.server.store.health() and self.server.turns.worker.is_alive()
            self._json(
                200 if healthy else 503,
                {"ok": healthy, "service": "seven-web", "version": __version__},
            )
            return
        if path == "/api/session":
            _, session_hash = self._session()
            csrf = secrets.token_urlsafe(32)
            if not self.server.store.rotate_csrf(
                session_hash, token_digest(csrf, self.cfg.session_secret)
            ):
                raise RequestError(401, "authentication_required")
            self._json(200, {"ok": True, "csrf": csrf})
            return
        if path == "/api/turn":
            _, session_hash = self._session()
            try:
                turn_id = int(parse_qs(parsed.query).get("id", [""])[0])
            except ValueError as exc:
                raise RequestError(400, "invalid_turn_id") from exc
            turn = self.server.store.get_turn(turn_id, session_hash)
            if not turn:
                raise RequestError(404, "turn_not_found")
            self._json(200, {"ok": True, "turn": turn})
            return
        if path == "/api/activity":
            self._session()
            try:
                after = int(parse_qs(parsed.query).get("after", ["0"])[0])
            except ValueError as exc:
                raise RequestError(400, "invalid_activity_id") from exc
            self._json(
                200, {"ok": True, "events": self.server.store.activity_since(after)}
            )
            return
        if path == "/api/events":
            self._session()
            self._sse()
            return
        self._static(path)

    def _static(self, path: str) -> None:
        relative = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
        if not relative or ".." in Path(relative).parts:
            raise RequestError(404, "not_found")
        target = (self.cfg.static_path / relative).resolve()
        root = self.cfg.static_path.resolve()
        if root not in target.parents and target != root:
            raise RequestError(404, "not_found")
        if not target.is_file():
            raise RequestError(404, "not_found")
        raw = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Last-Modified", formatdate(target.stat().st_mtime, usegmt=True))
        self._security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def _sse(self) -> None:
        try:
            after = int(self.headers.get("Last-Event-ID", "0") or "0")
        except ValueError:
            after = 0
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self._security_headers()
        self.end_headers()
        self.close_connection = True
        deadline = time.monotonic() + self.cfg.sse_hold_seconds
        while time.monotonic() < deadline:
            events = self.server.store.activity_since(after)
            if events:
                for event in events:
                    after = event["id"]
                    block = (
                        f"id: {after}\n"
                        f"event: {event['kind']}\n"
                        f"data: {safe_json(event)}\n\n"
                    ).encode("utf-8")
                    self.wfile.write(block)
                self.wfile.flush()
                return
            with self.server.turns.activity_condition:
                self.server.turns.activity_condition.wait(timeout=1)
        self.wfile.write(b": keepalive\n\n")
        self.wfile.flush()

    def do_POST(self):
        try:
            self._rate("all", self.cfg.rate_per_minute, 60)
            self._post()
        except RequestError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            LOGGER.exception("request failed")
            self._json(500, {"ok": False, "error": "internal_error"})

    def _post(self):
        path = urlparse(self.path).path
        if path == "/api/login":
            self._origin()
            self._rate("login", self.cfg.login_rate_per_10_minutes, 600)
            body = self._read_json()
            password = body.get("password", "")
            if not isinstance(password, str) or not verify_password(
                password, self.cfg.owner_password_hash
            ):
                time.sleep(0.05)
                raise RequestError(401, "invalid_credentials")
            session = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            session_hash = token_digest(session, self.cfg.session_secret)
            self.server.store.create_session(
                session_hash,
                token_digest(csrf, self.cfg.session_secret),
                self.cfg.session_ttl_seconds,
            )
            self.server.store.add_activity("owner_login", {"status": "success"})
            self._json(
                200,
                {"ok": True, "csrf": csrf},
                cookie=self._cookie(session),
            )
            return
        if path == "/api/logout":
            _, session_hash = self._session(require_csrf=True)
            self.server.store.destroy_session(session_hash)
            self.server.store.add_activity("owner_logout", {"status": "success"})
            self._json(200, {"ok": True}, cookie=self._cookie("", clear=True))
            return
        if path == "/api/turn":
            _, session_hash = self._session(require_csrf=True)
            body = self._read_json()
            message = body.get("message", "")
            if not isinstance(message, str):
                raise RequestError(400, "message_required")
            message = "".join(ch for ch in message.strip() if ch >= " " or ch in "\n\t")
            if not message:
                raise RequestError(400, "message_required")
            if len(message) > self.cfg.message_limit_chars:
                raise RequestError(413, "message_too_large")
            try:
                turn_id = self.server.turns.enqueue(session_hash, message)
            except queue.Full as exc:
                raise RequestError(503, "queue_full") from exc
            self._json(202, {"ok": True, "turn_id": turn_id, "status": "queued"})
            return
        if path in ("/api/media/jpeg", "/api/media/audio"):
            self._rate("media", self.cfg.media_rate_per_minute, 60)
            self._session(require_csrf=True)
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
            try:
                raw = self._read(
                    self.cfg.jpeg_limit_bytes
                    if path.endswith("/jpeg")
                    else self.cfg.audio_limit_bytes
                )
                if path.endswith("/jpeg"):
                    if content_type != "image/jpeg":
                        raise ValueError("jpeg_content_type")
                    result = validate_jpeg(raw, self.cfg.jpeg_limit_bytes)
                else:
                    result = validate_audio(raw, content_type, self.cfg.audio_limit_bytes)
            except ValueError as exc:
                raise RequestError(415, str(exc)) from exc
            if path.endswith("/jpeg"):
                try:
                    reply = self.server.upstream.vision(
                        raw,
                        "Describe what you can observe in this owner-provided snapshot. "
                        "Be concise and distinguish observation from inference.",
                    )
                except Exception:
                    LOGGER.exception("vision request failed")
                    raise RequestError(503, "vision_unavailable") from None
                response = {
                    "ok": True,
                    "status": "analyzed_not_retained",
                    "reply": reply,
                }
            else:
                try:
                    transcript = self.server.transcriber.transcribe(raw)
                except TranscriptionUnavailable as exc:
                    raise RequestError(503, str(exc)) from None
                response = {
                    "ok": True,
                    "status": "transcribed_not_retained",
                    **transcript,
                }
            event_id = self.server.store.add_activity(
                "media_processed", {**result, "status": response["status"]}
            )
            self.server.turns.notify_activity()
            self._json(200, {**response, "event_id": event_id})
            return
        raise RequestError(404, "not_found")

    def do_OPTIONS(self):
        self._json(405, {"ok": False, "error": "method_not_allowed"})

    do_PUT = do_OPTIONS
    do_PATCH = do_OPTIONS
    do_DELETE = do_OPTIONS


def create_server(
    config: GatewayConfig,
    *,
    store: GatewayStore | None = None,
    upstream: SevenUpstream | None = None,
    transcriber=None,
) -> GatewayServer:
    return GatewayServer(
        (config.bind_host, config.bind_port),
        config,
        store=store,
        upstream=upstream,
        transcriber=transcriber,
    )


def run() -> int:
    logging.basicConfig(
        level=os.getenv("SEVEN_WEB_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        config = GatewayConfig.from_env()
        server = create_server(config)
    except (KeyError, OSError, ValueError) as exc:
        LOGGER.error("gateway configuration failed: %s", exc)
        return 2

    stop = threading.Event()

    def request_stop(_signum, _frame):
        stop.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    LOGGER.info("Seven gateway listening on %s:%s", config.bind_host, config.bind_port)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
    return 0
