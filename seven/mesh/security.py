"""HMAC request and beacon authentication for Seven Mesh."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from typing import Callable, Mapping


_NODE_ID = re.compile(r"^[a-f0-9]{32}$")
_NONCE = re.compile(r"^[A-Za-z0-9_-]{16,96}$")


class MeshAuthError(ValueError):
    """An inbound mesh request failed authentication."""


def validate_secret(secret: str) -> str:
    value = str(secret or "")
    if len(value) < 32:
        raise ValueError("SEVEN_MESH_SECRET must contain at least 32 characters")
    return value


def _request_canonical(
    node_id: str,
    method: str,
    route: str,
    timestamp: str,
    nonce: str,
    body: bytes,
) -> bytes:
    body_hash = hashlib.sha256(body).hexdigest()
    return (
        f"seven-mesh-v1\n{node_id}\n{method.upper()}\n{route}\n"
        f"{timestamp}\n{nonce}\n{body_hash}"
    ).encode("utf-8")


def sign_request(
    secret: str,
    node_id: str,
    method: str,
    route: str,
    body: bytes = b"",
    *,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    validate_secret(secret)
    if not _NODE_ID.fullmatch(str(node_id)):
        raise ValueError("invalid Seven mesh node id")
    stamp = str(int(time.time() if timestamp is None else timestamp))
    request_nonce = nonce or secrets.token_urlsafe(18)
    canonical = _request_canonical(
        str(node_id), method, route, stamp, request_nonce, body
    )
    signature = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return {
        "X-Seven-Mesh-Version": "1",
        "X-Seven-Mesh-Node": str(node_id),
        "X-Seven-Mesh-Timestamp": stamp,
        "X-Seven-Mesh-Nonce": request_nonce,
        "X-Seven-Mesh-Signature": signature,
    }


def verify_request(
    secret: str,
    headers: Mapping[str, str],
    method: str,
    route: str,
    body: bytes,
    claim_nonce: Callable[[str, int], bool],
    *,
    max_skew_seconds: int = 120,
    now: int | None = None,
) -> str:
    validate_secret(secret)
    if str(headers.get("X-Seven-Mesh-Version", "")) != "1":
        raise MeshAuthError("unsupported mesh protocol")
    node_id = str(headers.get("X-Seven-Mesh-Node", ""))
    timestamp = str(headers.get("X-Seven-Mesh-Timestamp", ""))
    nonce = str(headers.get("X-Seven-Mesh-Nonce", ""))
    supplied = str(headers.get("X-Seven-Mesh-Signature", ""))
    if not _NODE_ID.fullmatch(node_id):
        raise MeshAuthError("invalid node identity")
    if not _NONCE.fullmatch(nonce):
        raise MeshAuthError("invalid request nonce")
    try:
        stamp = int(timestamp)
    except ValueError as exc:
        raise MeshAuthError("invalid request timestamp") from exc
    current = int(time.time() if now is None else now)
    if abs(current - stamp) > max(1, int(max_skew_seconds)):
        raise MeshAuthError("request timestamp outside allowed window")
    expected = sign_request(
        secret,
        node_id,
        method,
        route,
        body,
        timestamp=stamp,
        nonce=nonce,
    )["X-Seven-Mesh-Signature"]
    if not supplied or not hmac.compare_digest(expected, supplied):
        raise MeshAuthError("invalid request signature")
    if not claim_nonce(nonce, current):
        raise MeshAuthError("replayed request")
    return node_id


def sign_beacon(secret: str, payload: dict) -> dict:
    """Return a canonical signed LAN beacon."""
    validate_secret(secret)
    unsigned = dict(payload)
    unsigned.pop("signature", None)
    raw = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signature = hmac.new(
        secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return {**unsigned, "signature": signature}


def verify_beacon(
    secret: str,
    payload: dict,
    claim_nonce: Callable[[str, int], bool],
    *,
    max_skew_seconds: int = 120,
    now: int | None = None,
) -> dict:
    validate_secret(secret)
    if not isinstance(payload, dict):
        raise MeshAuthError("invalid LAN beacon")
    unsigned = dict(payload)
    supplied = str(unsigned.pop("signature", ""))
    node_id = str(unsigned.get("node_id", ""))
    nonce = str(unsigned.get("nonce", ""))
    if not _NODE_ID.fullmatch(node_id) or not _NONCE.fullmatch(nonce):
        raise MeshAuthError("invalid LAN beacon identity")
    try:
        stamp = int(unsigned.get("timestamp"))
    except (TypeError, ValueError) as exc:
        raise MeshAuthError("invalid LAN beacon timestamp") from exc
    current = int(time.time() if now is None else now)
    if abs(current - stamp) > max(1, int(max_skew_seconds)):
        raise MeshAuthError("LAN beacon timestamp outside allowed window")
    expected = sign_beacon(secret, unsigned)["signature"]
    if not supplied or not hmac.compare_digest(expected, supplied):
        raise MeshAuthError("invalid LAN beacon signature")
    if not claim_nonce(nonce, current):
        raise MeshAuthError("replayed LAN beacon")
    return unsigned
