from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(?:auth|cookie|password|passwd|secret|token|api[_-]?key|prompt|reply|content)",
    re.IGNORECASE,
)
_SENSITIVE_TEXT = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)((?:password|secret|token|api[_-]?key)\s*[:=]\s*)\S+"),
)


def hash_password_scrypt(
    password: str,
    *,
    n: int = 2**15,
    r: int = 8,
    p: int = 1,
    salt: bytes | None = None,
) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=32,
        maxmem=128 * 1024 * 1024,
    )
    return "scrypt${}${}${}${}${}".format(
        n,
        r,
        p,
        base64.urlsafe_b64encode(salt).decode("ascii").rstrip("="),
        base64.urlsafe_b64encode(digest).decode("ascii").rstrip("="),
    )


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    try:
        from argon2 import PasswordHasher
    except ImportError:
        return hash_password_scrypt(password)
    return str(PasswordHasher().hash(password))


def _b64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_password(password: str, encoded: str) -> bool:
    if encoded.startswith("$argon2id$"):
        try:
            from argon2 import PasswordHasher
            from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
        except ImportError:
            return False
        try:
            return bool(PasswordHasher().verify(encoded, password))
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False
    try:
        scheme, n, r, p, salt, expected = encoded.split("$", 5)
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(_b64(expected)),
            maxmem=128 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, _b64(expected))
    except (ValueError, TypeError):
        return False


def token_digest(token: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): ("[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else sanitize(item))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        text = value[:500]
        for pattern in _SENSITIVE_TEXT:
            text = pattern.sub(r"\1[REDACTED]", text)
        return text
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:200]


def safe_json(value: Any) -> str:
    return json.dumps(sanitize(value), ensure_ascii=True, separators=(",", ":"))


class RateLimiter:
    def __init__(self, max_keys: int = 10_000):
        self._entries: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._max_keys = max_keys

    def allow(self, bucket: str, identity: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        key = (bucket, identity)
        with self._lock:
            if key not in self._entries and len(self._entries) >= self._max_keys:
                return False
            values = self._entries[key]
            while values and values[0] <= cutoff:
                values.popleft()
            if len(values) >= limit:
                return False
            values.append(now)
            return True
