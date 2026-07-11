import json

from seven.runtime.process import ProcessResult
from seven.tools import coding_agent


def test_status_reports_versions_and_absence(monkeypatch):
    monkeypatch.setattr(coding_agent, "_which", lambda name: f"/bin/{name}" if name != "aider" else None)
    monkeypatch.setattr(
        coding_agent, "run_tracked",
        lambda command, **kwargs: ProcessResult(command, 0, "version 1\n", ""),
    )
    status = json.loads(coding_agent.coding_agent_status())
    assert status["opencode"]["version"] == "version 1"
    assert status["aider"]["installed"] is False


def test_exact_noninteractive_commands(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(coding_agent, "_which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(coding_agent, "_shim_command", lambda exe, args: [exe, *args])
    def run(command, **kwargs):
        calls.append(command)
        return ProcessResult(command, 0, "done", "")
    monkeypatch.setattr(coding_agent, "run_tracked", run)

    assert not coding_agent.run_opencode("fix it", "build", str(tmp_path)).startswith("ERROR")
    assert not coding_agent.run_claude_cli("fix it", str(tmp_path)).startswith("ERROR")
    assert not coding_agent.run_codex_cli("fix it", str(tmp_path)).startswith("ERROR")
    assert not coding_agent.run_aider("fix it", str(tmp_path)).startswith("ERROR")
    assert calls[0][1:4] == ["run", "--agent", "build"]
    assert "--dangerously-skip-permissions" in calls[1]
    assert calls[2][1] == "exec"
    assert "--dangerously-bypass-approvals-and-sandbox" in calls[2]
    assert calls[3][1:3] == ["--yes-always", "--message"]


def test_timeout_and_failure_are_visible(monkeypatch, tmp_path):
    monkeypatch.setattr(coding_agent, "_which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(coding_agent, "_shim_command", lambda exe, args: [exe, *args])
    monkeypatch.setattr(
        coding_agent, "run_tracked",
        lambda command, **kwargs: ProcessResult(command, -9, "partial", "", True, (10, 11)),
    )
    payload = coding_agent.run_codex_cli("work", str(tmp_path))
    assert payload.startswith("ERROR:")
    assert '"timed_out": true' in payload
    assert "10" in payload and "11" in payload


def test_invalid_opencode_agent_is_rejected():
    assert coding_agent.run_opencode("x", "unknown").startswith("ERROR:")
