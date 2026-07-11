import json

from seven.tools import ollama_manager


class Response:
    def __init__(self, payload=None, lines=None):
        self.payload = payload or {}
        self.lines = lines or []

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload

    def iter_lines(self, decode_unicode=False):
        return iter(self.lines)


def test_ollama_status_and_list(monkeypatch):
    def request(method, url, **kwargs):
        if url.endswith("/api/version"):
            return Response({"version": "1.2.3"})
        if url.endswith("/api/tags"):
            return Response({"models": [{"name": "qwen:7b", "size": 12}]})
        return Response({"models": [{"name": "qwen:7b"}]})
    monkeypatch.setattr(ollama_manager.requests, "request", request)
    status = json.loads(ollama_manager.ollama_status())
    assert status["version"] == "1.2.3"
    assert status["running"] == ["qwen:7b"]
    assert json.loads(ollama_manager.ollama_list())[0]["name"] == "qwen:7b"


def test_pull_consumes_stream(monkeypatch):
    monkeypatch.setattr(
        ollama_manager.requests, "request",
        lambda *a, **kw: Response(lines=['{"status":"pulling","completed":5}', '{"status":"success"}']),
    )
    result = json.loads(ollama_manager.ollama_pull("qwen:7b"))
    assert result["ok"] is True
    assert result["updates"] == 2


def test_load_unload_copy_delete_payloads(monkeypatch):
    calls = []
    def request(method, url, **kwargs):
        calls.append((method, url, kwargs.get("json")))
        return Response({})
    monkeypatch.setattr(ollama_manager.requests, "request", request)
    assert ollama_manager.ollama_load("qwen:7b").startswith("OK")
    assert ollama_manager.ollama_unload("qwen:7b").startswith("OK")
    assert ollama_manager.ollama_copy("qwen:7b", "seven:latest").startswith("OK")
    assert ollama_manager.ollama_delete("seven:latest").startswith("OK")
    assert calls[1][2]["keep_alive"] == 0
    assert calls[-1][0] == "DELETE"


def test_errors_are_visible(monkeypatch):
    def fail(*args, **kwargs):
        raise ollama_manager.requests.ConnectionError("offline")
    monkeypatch.setattr(ollama_manager.requests, "request", fail)
    assert ollama_manager.ollama_status().startswith("ERROR:")
    assert ollama_manager.ollama_pull("").startswith("ERROR:")
