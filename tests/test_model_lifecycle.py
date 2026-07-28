from seven.brain.model_lifecycle import ModelLifecycle


class FakeBrain:
    def __init__(self):
        self.model = "known:1"
        self.ollama_url = "http://127.0.0.1:11434"

    def chat(self, messages, tools=None, model=None, **kwargs):
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
