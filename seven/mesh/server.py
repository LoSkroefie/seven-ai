"""Authenticated HTTP rendezvous and message relay for Seven Mesh."""
from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from seven.mesh.security import MeshAuthError, verify_request
from seven.mesh.store import MeshStore


logger = logging.getLogger("seven.mesh.server")
MAX_BODY_BYTES = 64 * 1024


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MeshHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"
    request_queue_size = 32

    def __init__(
        self,
        address,
        *,
        secret: str,
        store: MeshStore,
        max_skew_seconds: int = 120,
        message_ttl_seconds: int = 86400,
    ):
        self.mesh_secret = secret
        self.mesh_store = store
        self.mesh_max_skew_seconds = max_skew_seconds
        self.mesh_message_ttl_seconds = message_ttl_seconds
        self.mesh_thread: threading.Thread | None = None
        super().__init__(address, MeshRequestHandler)

    def start(self) -> None:
        if self.mesh_thread and self.mesh_thread.is_alive():
            return
        self.mesh_thread = threading.Thread(
            target=self.serve_forever,
            name="seven-mesh-http",
            daemon=True,
        )
        self.mesh_thread.start()

    def stop(self) -> None:
        if self.mesh_thread and self.mesh_thread.is_alive():
            self.shutdown()
            self.mesh_thread.join(timeout=10)
        self.server_close()


class MeshRequestHandler(BaseHTTPRequestHandler):
    server_version = "SevenMesh/1"

    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, OSError):
            logger.info("mesh client disconnected before response completed")

    def _read_body(self) -> bytes:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError(f"body must contain 1 to {MAX_BODY_BYTES} bytes")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValueError("incomplete request body")
        return raw

    @staticmethod
    def _json(raw: bytes) -> dict:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("malformed UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _auth(self, route: str, body: bytes) -> str | None:
        try:
            return verify_request(
                self.server.mesh_secret,
                self.headers,
                self.command,
                route,
                body,
                self.server.mesh_store.claim_nonce,
                max_skew_seconds=self.server.mesh_max_skew_seconds,
            )
        except MeshAuthError as exc:
            logger.warning("mesh authentication rejected: %s", exc)
            self._send(401, {"ok": False, "error": "mesh authentication failed"})
            return None

    def do_GET(self):
        route = urlparse(self.path).path
        if route in {"/", "/health", "/v1/health"}:
            self._send(200, {"ok": True, "service": "seven-mesh", "protocol": 1})
            return
        node_id = self._auth(route, b"")
        if node_id is None:
            return
        if route == "/v1/peers":
            self._send(200, {"ok": True, "peers": self.server.mesh_store.peers()})
        elif route == "/v1/inbox":
            messages = self.server.mesh_store.take_relay(node_id, limit=50)
            self._send(200, {"ok": True, "messages": messages})
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        route = urlparse(self.path).path
        if route not in {"/v1/presence", "/v1/messages"}:
            self._send(404, {"ok": False, "error": "not found"})
            return
        try:
            raw = self._read_body()
            payload = self._json(raw)
        except ValueError as exc:
            self._send(400, {"ok": False, "error": str(exc)})
            return
        node_id = self._auth(route, raw)
        if node_id is None:
            return
        if route == "/v1/presence":
            if str(payload.get("node_id") or "") != node_id:
                self._send(403, {"ok": False, "error": "node identity mismatch"})
                return
            peer = {
                "node_id": node_id,
                "name": payload.get("name"),
                "hostname": payload.get("hostname"),
                "platform": payload.get("platform"),
                "endpoint": payload.get("endpoint"),
                "capabilities": payload.get("capabilities"),
            }
            self.server.mesh_store.upsert_peer(peer, source="hub")
            self._send(
                200,
                {"ok": True, "peers": self.server.mesh_store.peers()},
            )
            return

        target = str(payload.get("target_node_id") or "")
        content = payload.get("content")
        context = payload.get("context") or {}
        kind = str(payload.get("kind") or "message")
        if len(target) != 32 or target == node_id:
            self._send(400, {"ok": False, "error": "valid different target node required"})
            return
        if not isinstance(content, str) or not content.strip():
            self._send(400, {"ok": False, "error": "message content required"})
            return
        if len(content) > 16000:
            self._send(413, {"ok": False, "error": "message exceeds 16000 characters"})
            return
        if not isinstance(context, dict):
            self._send(400, {"ok": False, "error": "message context must be an object"})
            return
        message = {
            "message_id": uuid.uuid4().hex,
            "sender_node_id": node_id,
            "target_node_id": target,
            "kind": kind[:64],
            "content": content.strip(),
            "context": context,
            "created_at": _utcnow(),
        }
        try:
            self.server.mesh_store.queue_relay(
                message,
                ttl_seconds=self.server.mesh_message_ttl_seconds,
            )
        except Exception:
            logger.exception("mesh relay queue failed")
            self._send(500, {"ok": False, "error": "message queue failed"})
            return
        self._send(202, {"ok": True, "message": message})

    def _method_not_allowed(self):
        self._send(405, {"ok": False, "error": "method not allowed"})

    do_PUT = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_OPTIONS = _method_not_allowed
