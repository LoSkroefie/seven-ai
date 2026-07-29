from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _loopback_host(value: str, field: str) -> str:
    host = value.strip().lower()
    if host == "localhost":
        return host
    try:
        if ipaddress.ip_address(host).is_loopback:
            return host
    except ValueError:
        pass
    raise ValueError(f"{field} must use a loopback address")


@dataclass(frozen=True)
class GatewayConfig:
    bind_host: str
    bind_port: int
    public_origin: str
    internal_url: str
    internal_token: str
    owner_password_hash: str
    session_secret: str
    database_path: Path
    static_path: Path
    session_ttl_seconds: int = 43_200
    session_idle_seconds: int = 3_600
    body_limit_bytes: int = 32_768
    message_limit_chars: int = 8_000
    jpeg_limit_bytes: int = 5_000_000
    audio_limit_bytes: int = 8_000_000
    queue_limit: int = 32
    rate_per_minute: int = 120
    login_rate_per_10_minutes: int = 10
    media_rate_per_minute: int = 12
    tts_rate_per_minute: int = 30
    upstream_timeout_seconds: int = 300
    sse_hold_seconds: int = 15
    cookie_secure: bool = True
    transcription_enabled: bool = False
    whisper_model: str = "tiny.en"
    whisper_download_root: Path = Path("/var/lib/seven-web/models")
    whisper_threads: int = 2
    tts_enabled: bool = True
    tts_voice: str = "en-US-AvaNeural"
    tts_rate: str = "-5%"
    tts_pitch: str = "+2Hz"
    tts_text_limit_chars: int = 4_000
    tts_timeout_seconds: int = 30
    tts_audio_limit_bytes: int = 4_000_000

    def validate(self) -> "GatewayConfig":
        _loopback_host(self.bind_host, "SEVEN_WEB_BIND")
        parsed = urlparse(self.internal_url)
        if parsed.scheme != "http" or not parsed.hostname:
            raise ValueError("SEVEN_INTERNAL_URL must be an http loopback URL")
        _loopback_host(parsed.hostname, "SEVEN_INTERNAL_URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("SEVEN_INTERNAL_URL must not contain credentials or query data")
        origin = urlparse(self.public_origin)
        if (
            origin.scheme != "https"
            or not origin.netloc
            or origin.path not in ("", "/")
            or origin.username
            or origin.password
            or origin.query
            or origin.fragment
        ):
            raise ValueError("SEVEN_PUBLIC_ORIGIN must be an HTTPS origin without a path")
        if len(self.internal_token) < 32:
            raise ValueError("SEVEN_INTERNAL_TOKEN must contain at least 32 characters")
        if len(self.session_secret) < 32:
            raise ValueError("SEVEN_SESSION_SECRET must contain at least 32 characters")
        if not (
            self.owner_password_hash.startswith("$argon2id$")
            or self.owner_password_hash.startswith("scrypt$")
        ):
            raise ValueError("SEVEN_OWNER_PASSWORD_HASH must be Argon2id or scrypt")
        if not self.tts_voice or len(self.tts_voice) > 128:
            raise ValueError("SEVEN_TTS_VOICE must be between 1 and 128 characters")
        if not self.tts_rate or len(self.tts_rate) > 32:
            raise ValueError("SEVEN_TTS_RATE must be between 1 and 32 characters")
        if not self.tts_pitch or len(self.tts_pitch) > 32:
            raise ValueError("SEVEN_TTS_PITCH must be between 1 and 32 characters")
        return self

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        package_root = Path(__file__).resolve().parent.parent
        cfg = cls(
            bind_host=os.getenv("SEVEN_WEB_BIND", "127.0.0.1"),
            bind_port=_positive_int("SEVEN_WEB_PORT", 18788),
            public_origin=os.environ["SEVEN_PUBLIC_ORIGIN"].rstrip("/"),
            internal_url=os.getenv("SEVEN_INTERNAL_URL", "http://127.0.0.1:18765").rstrip("/"),
            internal_token=os.environ["SEVEN_INTERNAL_TOKEN"],
            owner_password_hash=os.environ["SEVEN_OWNER_PASSWORD_HASH"],
            session_secret=os.environ["SEVEN_SESSION_SECRET"],
            database_path=Path(os.getenv("SEVEN_WEB_DB", "/var/lib/seven-web/gateway.sqlite3")),
            static_path=Path(os.getenv("SEVEN_WEB_STATIC", str(package_root / "static"))),
            session_ttl_seconds=_positive_int("SEVEN_SESSION_TTL", 43_200),
            session_idle_seconds=_positive_int("SEVEN_SESSION_IDLE", 3_600),
            body_limit_bytes=_positive_int("SEVEN_BODY_LIMIT", 32_768),
            message_limit_chars=_positive_int("SEVEN_MESSAGE_LIMIT", 8_000),
            jpeg_limit_bytes=_positive_int("SEVEN_JPEG_LIMIT", 5_000_000),
            audio_limit_bytes=_positive_int("SEVEN_AUDIO_LIMIT", 8_000_000),
            queue_limit=_positive_int("SEVEN_QUEUE_LIMIT", 32),
            rate_per_minute=_positive_int("SEVEN_RATE_PER_MINUTE", 120),
            login_rate_per_10_minutes=_positive_int("SEVEN_LOGIN_RATE_PER_10_MINUTES", 10),
            media_rate_per_minute=_positive_int("SEVEN_MEDIA_RATE_PER_MINUTE", 12),
            tts_rate_per_minute=_positive_int("SEVEN_TTS_RATE_PER_MINUTE", 30),
            upstream_timeout_seconds=_positive_int("SEVEN_UPSTREAM_TIMEOUT", 300),
            sse_hold_seconds=_positive_int("SEVEN_SSE_HOLD", 15),
            transcription_enabled=_bool("SEVEN_TRANSCRIPTION_ENABLED", False),
            whisper_model=os.getenv("SEVEN_WHISPER_MODEL", "tiny.en").strip(),
            whisper_download_root=Path(
                os.getenv("SEVEN_WHISPER_DOWNLOAD_ROOT", "/var/lib/seven-web/models")
            ),
            whisper_threads=_positive_int("SEVEN_WHISPER_THREADS", 2),
            tts_enabled=_bool("SEVEN_TTS_ENABLED", True),
            tts_voice=os.getenv("SEVEN_TTS_VOICE", "en-US-AvaNeural").strip(),
            tts_rate=os.getenv("SEVEN_TTS_RATE", "-5%").strip(),
            tts_pitch=os.getenv("SEVEN_TTS_PITCH", "+2Hz").strip(),
            tts_text_limit_chars=_positive_int("SEVEN_TTS_TEXT_LIMIT", 4_000),
            tts_timeout_seconds=_positive_int("SEVEN_TTS_TIMEOUT", 30),
            tts_audio_limit_bytes=_positive_int(
                "SEVEN_TTS_AUDIO_LIMIT", 4_000_000
            ),
        )
        return cfg.validate()
