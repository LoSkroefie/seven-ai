import json
from pathlib import Path

from seven import setup_wizard as setup
from seven import __main__ as main_module


def options(tmp_path, **overrides):
    values = {
        "assistant_name": "Seven",
        "user_name": "Tester",
        "workspace": tmp_path / "workspace",
        "text_model": "qwen2.5:7b",
        "vision_model": "llama3.2-vision",
        "voice_engine": "none",
        "camera_mode": "off",
        "startup_mode": "unchanged",
        "data_dir": tmp_path / "data",
        "dry_run": False,
        "noninteractive": True,
    }
    values.update(overrides)
    return setup.SetupOptions(**values)


def healthy_doctor(**kwargs):
    return {
        "ok": True,
        "ready": True,
        "warnings": [],
        "errors": [],
        "ollama": {"ready": True, "models": []},
    }


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    result = setup.run_setup(options(tmp_path, dry_run=True, startup_mode="talk"))
    assert result["ok"] is True
    assert result["status"] == "planned"
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "workspace").exists()


def test_settings_are_atomic_non_secret_and_preserve_unknown_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text(
        json.dumps({"future_field": {"keep": True}}), encoding="utf-8"
    )
    result = setup.run_setup(
        options(
            tmp_path,
            assistant_name="Astra",
            voice_engine="edge",
            camera_mode="both",
        )
    )
    assert result["ok"] is True
    saved = json.loads((data / "settings.json").read_text(encoding="utf-8"))
    assert saved["future_field"] == {"keep": True}
    assert saved["identity"] == {"assistant_name": "Astra", "user_name": "Tester"}
    assert saved["models"]["text"] == "qwen2.5:7b"
    assert "api_key" not in json.dumps(saved).lower()
    assert not list(data.glob(".settings-*.tmp"))


def test_preexisting_secret_field_is_not_rewritten(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    data = tmp_path / "data"
    data.mkdir()
    original = json.dumps({"provider": {"api_key": "do-not-copy"}})
    (data / "settings.json").write_text(original, encoding="utf-8")
    result = setup.run_setup(options(tmp_path))
    assert result["ok"] is False
    assert "credential-like" in " ".join(result["errors"])
    assert (data / "settings.json").read_text(encoding="utf-8") == original


def test_invalid_values_fail_before_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    result = setup.run_setup(options(tmp_path, text_model="../bad model"))
    assert result["ok"] is False
    assert result["status"] == "invalid"
    assert not (tmp_path / "data").exists()


def test_missing_ollama_is_visible_but_settings_can_be_saved(tmp_path, monkeypatch):
    def missing(**kwargs):
        return {
            "ok": True,
            "ready": False,
            "warnings": ["Ollama is not responding."],
            "errors": [],
            "ollama": {"ready": False, "error": "connection refused", "models": []},
        }

    monkeypatch.setattr(setup, "doctor", missing)
    result = setup.run_setup(options(tmp_path))
    assert result["ok"] is True
    assert result["doctor"]["ready"] is False
    assert "Ollama is not responding." in result["warnings"]
    assert (tmp_path / "data" / "settings.json").exists()


def test_missing_ollama_model_pull_fails_visibly_without_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    monkeypatch.setattr(
        setup,
        "pull_model",
        lambda model: {"ok": False, "model": model, "error": "Ollama not found"},
    )
    result = setup.run_setup(options(tmp_path, pull_models=True))
    assert result["ok"] is False
    assert result["status"] == "external_action_failed"
    assert "Ollama not found" in " ".join(result["errors"])
    assert not (tmp_path / "data").exists()


def test_startup_choice_uses_supported_startup_installer(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, "doctor", healthy_doctor)
    calls = []

    def startup(mode):
        calls.append(mode)
        return {"ok": True, "changed": True, "mode": mode}

    monkeypatch.setattr(setup, "_configure_startup", startup)
    result = setup.run_setup(options(tmp_path, startup_mode="quiet"))
    assert result["ok"] is True
    assert calls == ["quiet"]


def test_saved_environment_never_overrides_explicit_values(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text(
        json.dumps(
            {
                "identity": {"assistant_name": "Seven", "user_name": "Tester"},
                "workspace": str(tmp_path / "workspace"),
                "models": {"text": "qwen2.5:7b", "vision": "llama3.2-vision"},
                "voice": {"engine": "edge"},
                "camera": {"mode": "webcam"},
            }
        ),
        encoding="utf-8",
    )
    environment = {"SEVEN_NAME": "Explicit"}
    setup.apply_saved_environment(data, environ=environment)
    assert environment["SEVEN_NAME"] == "Explicit"
    assert environment["SEVEN_USER_NAME"] == "Tester"
    assert environment["SEVEN_CAMERA"] == "1"
    assert environment["SEVEN_CAPTURE_MODE"] == "webcam"
    assert environment["SEVEN_OLLAMA_MODEL_SOURCE"] == "saved"


def test_explicit_model_environment_is_not_marked_as_saved(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text(
        json.dumps({"models": {"text": "saved:1"}}),
        encoding="utf-8",
    )
    environment = {"OLLAMA_MODEL": "operator:2"}

    setup.apply_saved_environment(data, environ=environment)

    assert environment["OLLAMA_MODEL"] == "operator:2"
    assert "SEVEN_OLLAMA_MODEL_SOURCE" not in environment


def test_normal_startup_fails_visibly_for_corrupt_saved_setup(
    tmp_path, monkeypatch, capsys
):
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text("{bad-json", encoding="utf-8")
    monkeypatch.setenv("SEVEN_DATA_DIR", str(data))

    result = main_module.main(["--status"])

    assert result == 2
    assert "cannot safely load" in capsys.readouterr().err
