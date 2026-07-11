import json

from seven.runtime.process import ProcessResult
from seven.runtime import notifications


def test_unavailable_backend_is_truthful(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)
    result = notifications.submit_notification("title", "body", "linux")
    assert result["ok"] is False
    assert result["state"] == "unavailable"


def test_linux_submission_contract(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: "/usr/bin/notify-send")
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return ProcessResult(command, 0, "", "")
    monkeypatch.setattr(notifications, "run_tracked", run)
    result = notifications.submit_notification("Seven", "Wake up", "linux")
    assert result["state"] == "submitted"
    assert calls[0][0] == ["/usr/bin/notify-send", "--app-name=Seven", "Seven", "Wake up"]


def test_windows_message_is_passed_via_environment(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: "C:/PowerShell/pwsh.exe" if name == "pwsh" else None)
    captured = {}
    def run(command, **kwargs):
        captured.update(command=command, env=kwargs["env"])
        return ProcessResult(command, 0, "", "")
    monkeypatch.setattr(notifications, "run_tracked", run)
    result = notifications.submit_notification("<Seven>", "don't leak & break", "win32")
    assert result["ok"] is True
    assert captured["env"]["SEVEN_NOTIFY_TITLE"] == "<Seven>"
    assert captured["env"]["SEVEN_NOTIFY_BODY"] == "don't leak & break"
    assert "don't leak" not in " ".join(captured["command"])


def test_failed_backend_is_not_claimed_delivered(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: "/usr/bin/notify-send")
    monkeypatch.setattr(
        notifications, "run_tracked",
        lambda command, **kwargs: ProcessResult(command, 1, "", "display unavailable"),
    )
    result = notifications.submit_notification("Seven", "body", "linux")
    assert result["ok"] is False
    assert result["state"] == "failed"
    assert "display unavailable" in result["error"]
