import json
from types import SimpleNamespace

from seven import config
from seven.agent.loop import Seven
from seven.brain.model_lifecycle import ModelLifecycle


class FakeBrain:
    def __init__(self):
        self.provider = "ollama"
        self.model = "known:1"
        self.ollama_url = "http://127.0.0.1:11434"
        self.prompts = []

    def chat(self, messages, tools=None, model=None, **kwargs):
        self.prompts.append(messages[-1]["content"])
        if tools:
            return {
                "content": None,
                "thinking": "tool reasoning",
                "tool_calls": [{
                    "name": "seven_probe",
                    "arguments": {"value": "benchmark-ok"},
                }],
            }
        return {
            "content": "SEVEN_MODEL_OK",
            "thinking": "text reasoning",
            "tool_calls": [],
        }

    def list_ollama_models(self):
        return ["known:1"]

    def ping(self):
        return {
            "ok": True,
            "provider": "ollama",
            "model": self.model,
            "has_primary": True,
            "has_vision": False,
            "loaded": [self.model],
        }


class FakeMemory:
    def __init__(self):
        self.events = []

    def add_event(self, *args):
        self.events.append(args)


class FakeTools:
    tier = "lean"

    @staticmethod
    def names():
        return []


def test_benchmark_activate_and_rollback(tmp_path):
    brain = FakeBrain()
    lifecycle = ModelLifecycle(brain, tmp_path / "models.json")
    result = lifecycle.benchmark("gpt-oss:20b")
    assert result["ok"] is True
    assert result["thinking_preserved"] is True
    activated = lifecycle.activate("gpt-oss:20b")
    assert activated == {
        "ok": True,
        "active": "gpt-oss:20b",
        "known_good": "known:1",
    }
    assert brain.model == "gpt-oss:20b"
    rolled_back = lifecycle.rollback()
    assert rolled_back["active"] == "known:1"
    assert brain.model == "known:1"


def test_activation_requires_passing_benchmark(tmp_path):
    lifecycle = ModelLifecycle(FakeBrain(), tmp_path / "models.json")
    try:
        lifecycle.activate("untested:latest")
        assert False, "untested model must not activate"
    except ValueError:
        pass


def test_explicit_environment_model_wins_over_persisted_state(
    tmp_path, monkeypatch
):
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps({"version": 1, "active": "persisted:1"}),
        encoding="utf-8",
    )
    brain = FakeBrain()
    monkeypatch.setattr(config, "OLLAMA_MODEL", "configured:1")
    monkeypatch.setenv("OLLAMA_MODEL", "operator:2")

    result = ModelLifecycle(brain, path).select_startup_model(installed=[])

    assert result["ok"] is True
    assert result["source"] == "environment"
    assert brain.model == config.OLLAMA_MODEL == "operator:2"


def test_valid_available_persisted_model_is_restored(tmp_path, monkeypatch):
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "active": "persisted:1",
                "known_good": "known:1",
                "benchmarks": {"persisted:1": {"ok": True}},
            }
        ),
        encoding="utf-8",
    )
    brain = FakeBrain()
    monkeypatch.setattr(config, "OLLAMA_MODEL", "configured:1")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    result = ModelLifecycle(brain, path).select_startup_model(
        installed=["other:1", "persisted:1"]
    )

    assert result == {
        "ok": True,
        "source": "persisted",
        "active": "persisted:1",
        "reason": "validated persisted active model",
    }
    assert brain.model == config.OLLAMA_MODEL == "persisted:1"


def test_unavailable_persisted_model_fails_closed_for_caller_fallback(
    tmp_path, monkeypatch
):
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps({"version": 1, "active": "missing:9"}),
        encoding="utf-8",
    )
    brain = FakeBrain()
    monkeypatch.setattr(config, "OLLAMA_MODEL", "configured:1")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    result = ModelLifecycle(brain, path).select_startup_model(
        installed=["known:1"]
    )

    assert result["ok"] is False
    assert result["active"] == "missing:9"
    assert result["reason"] == "persisted active model is not installed"
    assert brain.model == "known:1"
    assert config.OLLAMA_MODEL == "configured:1"


def test_saved_setup_model_does_not_override_benchmarked_persisted_model(
    tmp_path, monkeypatch
):
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "active": "persisted:1",
                "benchmarks": {"persisted:1": {"ok": True}},
            }
        ),
        encoding="utf-8",
    )
    brain = FakeBrain()
    monkeypatch.setenv("OLLAMA_MODEL", "saved:1")
    monkeypatch.setenv("SEVEN_OLLAMA_MODEL_SOURCE", "saved")

    result = ModelLifecycle(brain, path).select_startup_model(
        installed=["saved:1", "persisted:1"]
    )

    assert result["source"] == "persisted"
    assert brain.model == "persisted:1"


def test_persisted_model_without_passing_benchmark_fails_closed(
    tmp_path, monkeypatch
):
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "active": "persisted:1",
                "benchmarks": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("SEVEN_OLLAMA_MODEL_SOURCE", raising=False)

    result = ModelLifecycle(FakeBrain(), path).select_startup_model(
        installed=["persisted:1"]
    )

    assert result["ok"] is False
    assert result["reason"] == "persisted active model has no passing benchmark"


def test_benchmark_records_and_requests_configured_text_protocol(
    tmp_path, monkeypatch
):
    brain = FakeBrain()
    monkeypatch.setattr(config, "OLLAMA_TOOL_PROTOCOL", "text")

    result = ModelLifecycle(brain, tmp_path / "models.json").benchmark(
        "known:1"
    )

    assert result["ok"] is True
    assert result["tool_protocol"] == "text"
    assert "configured text tool protocol" in brain.prompts[-1]


def test_seven_boot_restores_persisted_model_without_environment_override(
    tmp_path, monkeypatch
):
    state = tmp_path / "model_state.json"
    state.write_text(
        json.dumps(
            {
                "version": 1,
                "active": "known:1",
                "benchmarks": {"known:1": {"ok": True}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "MODEL_STATE_PATH", state)
    monkeypatch.setattr(config, "AUTO_SELECT_MODEL", False)
    monkeypatch.setattr(config, "OLLAMA_MODEL", "configured:1")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    agent = SimpleNamespace(
        brain=FakeBrain(),
        memory=FakeMemory(),
        tools=FakeTools(),
        model_startup={},
    )

    Seven._boot_checks(agent)

    assert agent.brain.model == "known:1"
    assert agent.model_startup["source"] == "persisted"
    assert agent.memory.events == []


def test_seven_boot_records_visible_fallback_for_unavailable_persisted_model(
    tmp_path, monkeypatch
):
    state = tmp_path / "model_state.json"
    state.write_text(
        json.dumps({"version": 1, "active": "missing:9"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "MODEL_STATE_PATH", state)
    monkeypatch.setattr(config, "AUTO_SELECT_MODEL", False)
    monkeypatch.setattr(config, "OLLAMA_MODEL", "configured:1")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    brain = FakeBrain()
    brain.model = "configured:1"
    agent = SimpleNamespace(
        brain=brain,
        memory=FakeMemory(),
        tools=FakeTools(),
        model_startup={},
    )

    Seven._boot_checks(agent)

    assert agent.brain.model == "configured:1"
    assert agent.model_startup["active"] == "missing:9"
    assert agent.model_startup["fallback"] == "configured:1"
    assert agent.memory.events[0][0] == "model_startup_fallback"
