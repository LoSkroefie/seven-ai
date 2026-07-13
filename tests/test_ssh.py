import json

from seven.runtime.process import ProcessResult
import seven.tools.ssh as ssh


def test_status_never_claims_connection_or_password_storage(monkeypatch):
    monkeypatch.setattr(ssh.shutil, "which", lambda name: f"/usr/bin/{name}")
    status = json.loads(ssh.ssh_status())
    assert status["strict_host_key_checking"] is True
    assert status["password_storage"] is False
    assert "connected" not in status


def test_run_builds_strict_noninteractive_argv(monkeypatch, tmp_path):
    identity = tmp_path / "id_ed25519"
    known = tmp_path / "known_hosts"
    identity.write_text("test", encoding="utf-8")
    known.write_text("host key", encoding="utf-8")
    captured = {}

    def fake_run(args, timeout):
        captured.update(args=args, timeout=timeout)
        return ProcessResult(args, 0, "remote output", "")

    monkeypatch.setattr(ssh.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(ssh, "run_tracked", fake_run)
    result = json.loads(ssh.ssh_run("server.example", "seven-user", "uname -a", 2222, str(identity), str(known), 17))
    args = captured["args"]
    assert result["ok"] is True and result["stdout"] == "remote output"
    assert "BatchMode=yes" in args
    assert "StrictHostKeyChecking=yes" in args
    assert "PasswordAuthentication=no" in args
    assert args[-2:] == ["seven-user@server.example", "uname -a"]
    assert captured["timeout"] == 17


def test_invalid_target_and_missing_identity_never_start(monkeypatch, tmp_path):
    monkeypatch.setattr(ssh.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert json.loads(ssh.ssh_run("-oProxyCommand=bad", "user", "true"))["state"] == "not_started"
    result = json.loads(ssh.ssh_run("host", "user", "true", identity_file=str(tmp_path / "missing")))
    assert result["state"] == "not_started"
    assert "identity file not found" in result["error"]


def test_timeout_and_output_bounds_are_visible(monkeypatch):
    monkeypatch.setattr(ssh.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(ssh, "run_tracked", lambda args, timeout: ProcessResult(args, -9, "x" * 60000, "y" * 30000, True, (10, 11)))
    result = json.loads(ssh.ssh_run("host", "user", "sleep 99", timeout=2))
    assert result["ok"] is False
    assert result["timed_out"] is True
    assert result["terminated_pids"] == [10, 11]
    assert result["output_truncated"] is True
    assert len(result["stdout"]) == 50000


def test_copy_directions_and_local_preconditions(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ssh.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(ssh, "run_tracked", lambda args, timeout: calls.append(args) or ProcessResult(args, 0, "", ""))
    source = tmp_path / "source.txt"
    source.write_text("seven", encoding="utf-8")
    assert json.loads(ssh.ssh_copy_to("host", "user", str(source), "/tmp/remote file"))["ok"] is True
    assert calls[-1][-2:] == [str(source.resolve()), "user@host:/tmp/remote file"]
    assert "-s" in calls[-1] and "--" in calls[-1]
    missing = json.loads(ssh.ssh_copy_to("host", "user", str(tmp_path / "missing"), "/tmp/x"))
    assert missing["state"] == "not_started"

    destination = tmp_path / "nested" / "download.txt"
    def download(args, timeout):
        destination.write_text("received", encoding="utf-8")
        calls.append(args)
        return ProcessResult(args, 0, "", "")
    monkeypatch.setattr(ssh, "run_tracked", download)
    result = json.loads(ssh.ssh_copy_from("host", "user", "/tmp/x", str(destination)))
    assert result["ok"] is True and result["local_bytes"] == 8
    assert calls[-1][-2:] == ["user@host:/tmp/x", str(destination.resolve())]
