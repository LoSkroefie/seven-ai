from __future__ import annotations

import http.client
import json
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest

from seven_gateway.config import GatewayConfig
from seven_gateway.http import create_server
from seven_gateway.security import hash_password_scrypt

ORIGIN = "https://seven.example.test"
PASSWORD = "correct horse battery staple"
INTERNAL_TOKEN = "internal-token-that-never-enters-a-browser-123456789"
SESSION_SECRET = "independent-session-secret-with-more-than-32-characters"


class FakeUpstream:
    def __init__(self):
        self.messages: list[str] = []
        self.speech_texts: list[str] = []

    def chat(self, message: str) -> str:
        self.messages.append(message)
        return f"received: {message}"

    def vision(self, image: bytes, prompt: str) -> str:
        assert image.startswith(b"\xff\xd8")
        assert "snapshot" in prompt
        return "I can see a one-pixel test image."

    def speech(self, text: str, *, timeout: int, audio_limit_bytes: int) -> bytes:
        assert 0 < timeout <= 300
        assert audio_limit_bytes >= 1024
        self.speech_texts.append(text)
        return b"ID3" + text.encode("utf-8")


class FakeTranscriber:
    def transcribe(self, audio: bytes) -> dict:
        assert audio.startswith(b"RIFF")
        return {
            "transcript": "verified local words",
            "language": "en",
            "language_probability": 0.99,
        }


class SecretFailureUpstream:
    def chat(self, _message: str) -> str:
        raise RuntimeError(f"should never leak {INTERNAL_TOKEN}")

    def speech(self, *_args, **_kwargs):
        raise RuntimeError(f"should never leak {INTERNAL_TOKEN}")


def base_config(tmp_path: Path, **changes) -> GatewayConfig:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<h1>Seven</h1>", encoding="utf-8")
    cfg = GatewayConfig(
        bind_host="127.0.0.1",
        bind_port=0,
        public_origin=ORIGIN,
        internal_url="http://127.0.0.1:18765",
        internal_token=INTERNAL_TOKEN,
        owner_password_hash=hash_password_scrypt(PASSWORD, n=2**14),
        session_secret=SESSION_SECRET,
        database_path=tmp_path / "gateway.sqlite3",
        static_path=static,
        sse_hold_seconds=1,
    )
    return replace(cfg, **changes)


class RunningGateway:
    def __init__(self, config, upstream=None):
        self.server = create_server(
            config,
            upstream=upstream or FakeUpstream(),
            transcriber=FakeTranscriber(),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.thread.join(timeout=3)
        self.server.server_close()

    @property
    def port(self):
        return self.server.server_address[1]

    def request(self, method, path, body=None, headers=None):
        raw = body
        if isinstance(body, (dict, list)):
            raw = json.dumps(body).encode()
            headers = {"Content-Type": "application/json", **(headers or {})}
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        conn.request(method, path, body=raw, headers=headers or {})
        response = conn.getresponse()
        data = response.read()
        result_headers = dict(response.getheaders())
        conn.close()
        return response.status, result_headers, data


def login(gateway: RunningGateway) -> tuple[str, str]:
    status, headers, raw = gateway.request(
        "POST", "/api/login", {"password": PASSWORD}, {"Origin": ORIGIN}
    )
    assert status == 200
    cookie = headers["Set-Cookie"]
    token_cookie = cookie.split(";", 1)[0]
    csrf = json.loads(raw)["csrf"]
    return token_cookie, csrf


def auth_headers(cookie: str, csrf: str | None = None) -> dict[str, str]:
    result = {"Origin": ORIGIN, "Cookie": cookie}
    if csrf:
        result["X-CSRF-Token"] = csrf
    return result


def test_auth_csrf_origin_cookie_and_queued_turn(tmp_path):
    upstream = FakeUpstream()
    with RunningGateway(base_config(tmp_path), upstream) as gateway:
        status, _, raw = gateway.request("GET", "/health")
        assert status == 200 and json.loads(raw)["ok"] is True

        status, _, raw = gateway.request(
            "POST",
            "/api/login",
            {"password": PASSWORD},
            {"Origin": "https://attacker.invalid"},
        )
        assert status == 403
        status, _, _ = gateway.request(
            "POST", "/api/login", {"password": "incorrect-password"}, {"Origin": ORIGIN}
        )
        assert status == 401

        cookie, csrf = login(gateway)
        # Same-origin browser GET and EventSource requests commonly omit
        # Origin.  The secure session cookie is sufficient for read-only
        # endpoints, while mutations remain origin + CSRF protected.
        status, _, raw = gateway.request(
            "GET", "/api/session", headers={"Cookie": cookie}
        )
        assert status == 200
        rotated_csrf = json.loads(raw)["csrf"]
        assert rotated_csrf
        csrf = rotated_csrf

        status, headers, _ = gateway.request(
            "POST",
            "/api/login",
            {"password": PASSWORD},
            {"Origin": ORIGIN},
        )
        assert status == 200
        set_cookie = headers["Set-Cookie"]
        assert set_cookie.startswith("__Host-seven_session=")
        assert "Domain=" not in set_cookie
        for attribute in ("Secure", "HttpOnly", "SameSite=Strict", "Path=/"):
            assert attribute in set_cookie

        status, _, raw = gateway.request(
            "GET",
            "/api/session",
            headers={"Cookie": f'broken="unterminated; {cookie}'},
        )
        assert status == 200
        csrf = json.loads(raw)["csrf"]
        assert csrf

        status, _, _ = gateway.request(
            "POST",
            "/api/turn",
            {"message": "hello"},
            {"Cookie": cookie, "X-CSRF-Token": csrf},
        )
        assert status == 403
        status, _, raw = gateway.request(
            "POST",
            "/api/turn",
            {"message": "hello"},
            auth_headers(cookie, csrf),
        )
        assert status == 202
        turn_id = json.loads(raw)["turn_id"]

        deadline = time.monotonic() + 3
        turn = {}
        while time.monotonic() < deadline:
            status, _, raw = gateway.request(
                "GET", f"/api/turn?id={turn_id}", headers=auth_headers(cookie)
            )
            turn = json.loads(raw).get("turn", {})
            if turn.get("status") == "complete":
                break
            time.sleep(0.03)
        assert turn["reply"] == "received: hello"
        assert upstream.messages == ["hello"]


def test_internal_token_never_leaks_to_http_activity_or_sse(tmp_path):
    with RunningGateway(base_config(tmp_path), SecretFailureUpstream()) as gateway:
        cookie, csrf = login(gateway)
        status, _, raw = gateway.request(
            "POST",
            "/api/turn",
            {"message": "trigger"},
            auth_headers(cookie, csrf),
        )
        turn_id = json.loads(raw)["turn_id"]
        time.sleep(0.15)
        responses = []
        responses.append(
            gateway.request(
                "GET", f"/api/turn?id={turn_id}", headers=auth_headers(cookie)
            )[2]
        )
        responses.append(
            gateway.request("GET", "/api/activity", headers=auth_headers(cookie))[2]
        )
        responses.append(
            gateway.request("GET", "/api/events", headers=auth_headers(cookie))[2]
        )
        combined = b"\n".join(responses)
        assert INTERNAL_TOKEN.encode() not in combined
        assert b"seven_internal_failure" in combined


def test_login_rate_limit(tmp_path):
    cfg = base_config(tmp_path, login_rate_per_10_minutes=1)
    with RunningGateway(cfg) as gateway:
        first = gateway.request(
            "POST", "/api/login", {"password": "wrong password"}, {"Origin": ORIGIN}
        )
        second = gateway.request(
            "POST", "/api/login", {"password": PASSWORD}, {"Origin": ORIGIN}
        )
        assert first[0] == 401
        assert second[0] == 429


def test_json_body_limit(tmp_path):
    cfg = base_config(tmp_path, body_limit_bytes=64)
    with RunningGateway(cfg) as gateway:
        status, _, raw = gateway.request(
            "POST",
            "/api/login",
            {"password": PASSWORD, "padding": "x" * 100},
            {"Origin": ORIGIN},
        )
        assert status == 413
        assert json.loads(raw)["error"] == "body_too_large"


def test_media_validation_is_bounded_and_not_retained(tmp_path):
    with RunningGateway(base_config(tmp_path)) as gateway:
        cookie, csrf = login(gateway)
        headers = auth_headers(cookie, csrf)
        jpeg = (
            b"\xff\xd8\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03"
            b"\x01\x11\x00\x02\x11\x00\x03\x11\x00\xff\xd9"
        )
        status, _, raw = gateway.request(
            "POST",
            "/api/media/jpeg",
            jpeg,
            {"Content-Type": "image/jpeg", **headers},
        )
        assert status == 200
        image_result = json.loads(raw)
        assert image_result["status"] == "analyzed_not_retained"
        assert image_result["reply"] == "I can see a one-pixel test image."

        status, _, _ = gateway.request(
            "POST",
            "/api/media/jpeg",
            b"not-a-jpeg",
            {"Content-Type": "image/jpeg", **headers},
        )
        assert status == 415
        wav = b"RIFF" + (4).to_bytes(4, "little") + b"WAVE"
        status, _, raw = gateway.request(
            "POST",
            "/api/media/audio",
            wav,
            {"Content-Type": "audio/wav", **headers},
        )
        assert status == 200
        audio_result = json.loads(raw)
        assert audio_result["status"] == "transcribed_not_retained"
        assert audio_result["transcript"] == "verified local words"


def test_neural_speech_requires_owner_csrf_and_returns_bounded_mp3(tmp_path):
    upstream = FakeUpstream()
    with RunningGateway(
        base_config(tmp_path, tts_text_limit_chars=32),
        upstream=upstream,
    ) as gateway:
        cookie, csrf = login(gateway)
        status, _, raw = gateway.request(
            "POST",
            "/api/tts",
            {"text": "Hello from Seven."},
            {"Cookie": cookie, "Origin": ORIGIN},
        )
        assert status == 401
        assert json.loads(raw)["error"] == "authentication_required"

        status, headers, raw = gateway.request(
            "POST",
            "/api/tts",
            {"text": "Hello from Seven."},
            auth_headers(cookie, csrf),
        )
        assert status == 200
        assert headers["Content-Type"] == "audio/mpeg"
        assert raw == b"ID3Hello from Seven."
        assert upstream.speech_texts == ["Hello from Seven."]

        status, _, raw = gateway.request(
            "POST",
            "/api/tts",
            {"text": "x" * 33},
            auth_headers(cookie, csrf),
        )
        assert status == 413
        assert json.loads(raw)["error"] == "tts_text_too_large"


def test_config_rejects_non_loopback_internal_api(tmp_path):
    cfg = base_config(tmp_path, internal_url="https://example.test/api")
    with pytest.raises(ValueError, match="loopback"):
        cfg.validate()
