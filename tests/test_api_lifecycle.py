import concurrent.futures
import threading
import time

import pytest
import requests

from seven.ui import api_server


class Tools:
    def names(self): return ["proof_tool"]


class FakeAgent:
    def __init__(self, block=False):
        self.tools = Tools()
        self.block = block
        self.entered = threading.Event()
        self.release = threading.Event()
        self.heartbeat = False
        self.stopped = False

    def start_heartbeat(self): self.heartbeat = True
    def shutdown(self): self.stopped = True
    def handle(self, message):
        if self.block and not message.startswith("/"):
            self.entered.set()
            self.release.wait(5)
        return "reply:" + message


def _start(tmp_path, monkeypatch, agent=None):
    monkeypatch.setattr(api_server.config, "DATA_DIR", tmp_path)
    monkeypatch.delenv("SEVEN_API_TOKEN", raising=False)
    server = api_server.start_api_server(port=0, agent=agent)
    return server, f"http://127.0.0.1:{server.server_address[1]}", server.seven_api_token


def test_real_socket_auth_routes_errors_and_shutdown(tmp_path, monkeypatch):
    agent = FakeAgent()
    server, base, token = _start(tmp_path, monkeypatch, agent)
    headers = {"Authorization": f"Bearer {token}"}
    port = server.server_address[1]
    try:
        health = requests.get(base + "/health", timeout=3)
        assert health.status_code == 200 and health.json()["ok"] is True
        assert health.headers["Cache-Control"] == "no-store"
        assert health.headers["X-Content-Type-Options"] == "nosniff"
        unauthorized = requests.get(base + "/status", timeout=3)
        assert unauthorized.status_code == 401
        assert unauthorized.headers["WWW-Authenticate"].startswith("Bearer")
        assert requests.get(base + "/tools", headers=headers, timeout=3).json()["names"] == ["proof_tool"]
        chat = requests.post(base + "/chat", headers=headers, json={"message": "hello"}, timeout=3)
        assert chat.status_code == 200 and chat.json()["reply"] == "reply:hello"
        malformed = requests.post(base + "/chat", headers={**headers, "Content-Type": "application/json"}, data="{", timeout=3)
        assert malformed.status_code == 400 and "malformed" in malformed.json()["error"]
        wrong_type = requests.post(base + "/chat", headers=headers, data="message=x", timeout=3)
        assert wrong_type.status_code == 415
        array = requests.post(base + "/chat", headers=headers, json=["x"], timeout=3)
        assert array.status_code == 400
        options = requests.options(base + "/chat", timeout=3)
        assert options.status_code == 405
        assert "Access-Control-Allow-Origin" not in options.headers
        assert requests.get(base + "/missing", headers=headers, timeout=3).status_code == 404
    finally:
        server.shutdown_cleanly()
    assert server.seven_thread.is_alive() is False
    server.shutdown_cleanly()  # idempotent
    assert agent.stopped is False  # the caller owns injected agents
    replacement = api_server.start_api_server(port=port, agent=FakeAgent())
    try:
        assert requests.get(f"http://127.0.0.1:{port}/health", timeout=3).status_code == 200
    finally:
        replacement.shutdown_cleanly()


def test_concurrency_limit_fails_fast_instead_of_queueing(tmp_path, monkeypatch):
    monkeypatch.setattr(api_server.config, "API_MAX_CONCURRENT_REQUESTS", 1)
    agent = FakeAgent(block=True)
    server, base, token = _start(tmp_path, monkeypatch, agent)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(requests.post, base + "/chat", headers=headers, json={"message": "block"}, timeout=5)
            assert agent.entered.wait(2)
            start = time.monotonic()
            overloaded = requests.get(base + "/health", timeout=2)
            assert overloaded.status_code == 503
            assert time.monotonic() - start < 1.5
            agent.release.set()
            assert first.result().status_code == 200
    finally:
        agent.release.set()
        server.shutdown_cleanly()


def test_owned_lazy_agent_is_started_and_stopped(tmp_path, monkeypatch):
    created = FakeAgent()
    monkeypatch.setattr(api_server, "Seven", lambda: created)
    server, base, token = _start(tmp_path, monkeypatch, agent=None)
    try:
        response = requests.get(base + "/status", headers={"X-Seven-Token": token}, timeout=3)
        assert response.status_code == 200
        assert created.heartbeat is True
    finally:
        server.shutdown_cleanly()
    assert created.stopped is True


def test_limits_loopback_port_conflict_and_strong_tokens(tmp_path, monkeypatch):
    monkeypatch.setattr(api_server.config, "DATA_DIR", tmp_path)
    monkeypatch.setenv("SEVEN_API_TOKEN", "short")
    with pytest.raises(ValueError, match="32"):
        api_server.get_or_create_api_token()
    monkeypatch.delenv("SEVEN_API_TOKEN")
    with pytest.raises(ValueError, match="loopback"):
        api_server.start_api_server(host="0.0.0.0", port=0, agent=FakeAgent())

    monkeypatch.setattr(api_server.config, "API_MAX_BODY_BYTES", 30)
    monkeypatch.setattr(api_server.config, "API_MAX_MESSAGE_CHARS", 5)
    server, base, token = _start(tmp_path, monkeypatch, FakeAgent())
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with pytest.raises(OSError):
            api_server.start_api_server(port=server.server_address[1], agent=FakeAgent())
        too_long = requests.post(base + "/chat", headers=headers, json={"message": "123456"}, timeout=3)
        assert too_long.status_code in {413}  # body or message bound, both explicit
    finally:
        server.shutdown_cleanly()


def test_concurrent_token_creation_converges_on_one_value(tmp_path, monkeypatch):
    monkeypatch.setattr(api_server.config, "DATA_DIR", tmp_path)
    monkeypatch.delenv("SEVEN_API_TOKEN", raising=False)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(lambda _: api_server.get_or_create_api_token(), range(24)))
    assert len(set(tokens)) == 1
    assert (tmp_path / "api.token").read_text(encoding="utf-8").strip() == tokens[0]


def test_agent_exception_is_json_500_without_details(tmp_path, monkeypatch):
    agent = FakeAgent()
    def fail(_message):
        raise RuntimeError("private internal detail")
    agent.handle = fail
    server, base, token = _start(tmp_path, monkeypatch, agent)
    try:
        response = requests.post(base + "/chat", headers={"Authorization": f"Bearer {token}"}, json={"message": "hello"}, timeout=3)
        assert response.status_code == 500
        assert response.json() == {"error": "agent request failed"}
        assert "private internal detail" not in response.text
    finally:
        server.shutdown_cleanly()
