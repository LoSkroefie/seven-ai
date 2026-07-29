from types import SimpleNamespace

import pytest
import requests

from seven import config
from seven.brain.llm import Brain, BrainError


def test_ollama_vision_uses_bounded_configured_token_budget(monkeypatch):
    brain = Brain(provider="ollama", vision_model="vision-proof")
    observed = {}

    def fake_chat(
        messages,
        tools,
        temperature,
        max_tokens,
        model,
        keep_alive=None,
        allow_loaded_fallback=True,
    ):
        observed.update(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            keep_alive=keep_alive,
            allow_loaded_fallback=allow_loaded_fallback,
        )
        return {"content": "grounded description"}

    monkeypatch.setattr(brain, "_ollama_chat", fake_chat)

    assert brain.vision("Describe it.", "aW1hZ2U=") == "grounded description"
    assert observed["max_tokens"] == config.VISION_MAX_TOKENS
    assert 16 <= observed["max_tokens"] <= 512
    assert observed["model"] == "vision-proof"
    assert observed["messages"][-1]["images"] == ["aW1hZ2U="]
    assert observed["allow_loaded_fallback"] is False


def test_vision_timeout_never_substitutes_loaded_text_model(monkeypatch):
    brain = Brain(provider="ollama", model="text-only:1", vision_model="vision-proof")
    calls = []

    def timeout(url, json, timeout):
        calls.append(json["model"])
        raise requests.Timeout("vision model load timed out")

    monkeypatch.setattr(brain._session, "post", timeout)
    monkeypatch.setattr(brain, "_ollama_loaded_model", lambda: "text-only:1")

    with pytest.raises(BrainError, match="vision-proof"):
        brain._ollama_chat(
            [{"role": "user", "content": "Describe.", "images": ["aW1hZ2U="]}],
            None,
            0.2,
            64,
            "vision-proof",
            keep_alive="2m",
            allow_loaded_fallback=False,
        )

    assert calls == ["vision-proof"]


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
