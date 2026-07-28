from types import SimpleNamespace

from seven import config
from seven.brain.llm import Brain


def test_ollama_vision_uses_bounded_configured_token_budget(monkeypatch):
    brain = Brain(provider="ollama", vision_model="vision-proof")
    observed = {}

    def fake_chat(messages, tools, temperature, max_tokens, model, keep_alive=None):
        observed.update(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            keep_alive=keep_alive,
        )
        return {"content": "grounded description"}

    monkeypatch.setattr(brain, "_ollama_chat", fake_chat)

    assert brain.vision("Describe it.", "aW1hZ2U=") == "grounded description"
    assert observed["max_tokens"] == config.VISION_MAX_TOKENS
    assert 16 <= observed["max_tokens"] <= 512
    assert observed["model"] == "vision-proof"
    assert observed["messages"][-1]["images"] == ["aW1hZ2U="]


def test_ollama_vision_generate_uses_same_token_budget(monkeypatch):
    brain = Brain(provider="ollama", vision_model="vision-proof")
    observed = {}

    def fake_post(url, json, timeout):
        observed.update(url=url, payload=json, timeout=timeout)
        return SimpleNamespace(
            status_code=200,
            json=lambda: {"response": "fallback description"},
        )

    monkeypatch.setattr(brain._session, "post", fake_post)

    reply = brain._ollama_vision_generate(
        "Describe it.",
        "aW1hZ2U=",
        "Be accurate.",
        "2m",
    )

    assert reply == "fallback description"
    assert observed["payload"]["options"]["num_predict"] == config.VISION_MAX_TOKENS
    assert observed["payload"]["model"] == "vision-proof"
