from __future__ import annotations

from seven import config
from seven.brain.llm import Brain


class Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"message": {"content": "ok"}}
        self.text = ""

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []

    def post(self, _url, *, json, timeout):
        self.payloads.append(json)
        return self.responses.pop(0)


def test_ollama_thinking_false_is_sent_with_native_tools(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_THINK", False)
    brain = Brain(provider="ollama", model="qwen3:0.6b")
    session = Session([Response()])
    brain._session = session

    result = brain.chat(
        [{"role": "user", "content": "hello"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "status",
                "description": "Get status",
                "parameters": {"type": "object", "properties": {}},
            },
        }],
    )

    assert result["content"] == "ok"
    assert session.payloads[0]["think"] is False


def test_ollama_thinking_false_survives_text_tool_fallback(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_THINK", False)
    brain = Brain(provider="ollama", model="qwen3:0.6b")
    session = Session([
        Response(status_code=400),
        Response(payload={"message": {"content": "fallback ok"}}),
    ])
    brain._session = session

    result = brain.chat(
        [{"role": "user", "content": "hello"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "status",
                "description": "Get status",
                "parameters": {"type": "object", "properties": {}},
            },
        }],
    )

    assert result["content"] == "fallback ok"
    assert [payload["think"] for payload in session.payloads] == [False, False]


def test_ollama_thinking_auto_omits_field(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_THINK", None)
    brain = Brain(provider="ollama", model="llama3.2:latest")
    session = Session([Response()])
    brain._session = session

    brain.chat([{"role": "user", "content": "hello"}])

    assert "think" not in session.payloads[0]
