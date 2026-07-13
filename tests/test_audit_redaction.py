import json

from seven.memory.store import Memory


def test_audit_redacts_sensitive_argument_keys(tmp_path):
    memory = Memory(tmp_path / "seven.db")
    memory.audit(
        "web_fetch",
        {"url": "https://example.test", "headers": {"Authorization": "Bearer super-secret", "X-API-Key": "abc123"}},
        "ok",
        True,
    )
    row = memory.recent_audit(1)[0]
    args = json.loads(row["arguments"])
    assert args["url"] == "https://example.test"
    assert args["headers"]["Authorization"] == "[REDACTED]"
    assert args["headers"]["X-API-Key"] == "[REDACTED]"
    assert "super-secret" not in row["arguments"]


def test_audit_redacts_credentials_embedded_in_result(tmp_path):
    memory = Memory(tmp_path / "seven.db")
    memory.audit(
        "run_shell",
        {"command": "print status"},
        "Authorization: Bearer abcdefghijklmnop\napi_key=sk_example1234567890",
        True,
    )
    preview = memory.recent_audit(1)[0]["result_preview"]
    assert "abcdefghijklmnop" not in preview
    assert "sk_example1234567890" not in preview
    assert preview.count("[REDACTED]") == 2


def test_audit_preserves_non_secret_context(tmp_path):
    memory = Memory(tmp_path / "seven.db")
    memory.audit("run_shell", {"command": "echo hello", "cwd": "C:/work"}, "exit_code=0", True)
    row = memory.recent_audit(1)[0]
    assert "echo hello" in row["arguments"]
    assert row["result_preview"] == "exit_code=0"
