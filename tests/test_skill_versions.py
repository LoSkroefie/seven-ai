import json
import sqlite3

from seven.memory.store import Memory
from seven.tools import mind_tools
from seven.tools.registry import Tool, ToolRegistry


class Agent:
    pass


def _registry(tmp_path):
    memory = Memory(tmp_path / "skills.db")
    registry = ToolRegistry(memory=memory)
    calls = []
    registry.register(Tool("echo", "echo", {"type": "object", "properties": {"text": {"type": "string"}}}, lambda text="": calls.append(text) or f"echo:{text}"))
    registry.register(Tool("fail", "fail", {"type": "object", "properties": {}}, lambda: "ERROR secret-output"))
    agent = Agent(); agent.tools = registry
    mind_tools.register(registry, memory=memory, agent=agent)
    return memory, registry, calls


def test_skill_versions_immutable_history_noop_and_rollback(tmp_path):
    memory, registry, _ = _registry(tmp_path)
    one = json.dumps([{"tool": "echo", "args": {"text": "one"}}])
    two = json.dumps([{"tool": "echo", "args": {"text": "two"}}])
    assert "version=1 saved" in registry.execute("save_skill", {"name": "demo", "description": "first", "steps_json": one})
    assert "version=2 saved" in registry.execute("save_skill", {"name": "demo", "description": "second", "steps_json": two})
    assert "version=2 unchanged" in registry.execute("save_skill", {"name": "demo", "description": "second", "steps_json": two})
    history = registry.execute("skill_history", {"name": "demo"})
    assert "v2" in history and "v1" in history
    assert "new v3" in registry.execute("rollback_skill", {"name": "demo", "version": 1})
    current = memory.get_skill("demo")
    assert current["current_version"] == 3
    assert current["steps"][0]["args"]["text"] == "one"
    revision_two = memory.get_skill_revision("demo", 2)
    assert revision_two["steps"][0]["args"]["text"] == "two"


def test_validation_rejects_placeholders_unknown_tools_and_recursion(tmp_path):
    _, registry, _ = _registry(tmp_path)
    cases = [
        "not-json",
        "[]",
        json.dumps([{"detail": "pretend"}]),
        json.dumps([{"tool": "missing", "args": {}}]),
        json.dumps([{"tool": "run_skill", "args": {"name": "self"}}]),
        json.dumps([{"tool": "echo", "args": [], "fake": True}]),
        json.dumps([{"tool": "echo", "args": {"api_key": "must-not-persist"}}]),
    ]
    for steps in cases:
        result = registry.execute("save_skill", {"name": "bad", "description": "bad", "steps_json": steps})
        assert result.startswith("ERROR"), result


def test_run_records_version_success_and_stops_on_failure_without_secret_storage(tmp_path):
    memory, registry, calls = _registry(tmp_path)
    good = json.dumps([{"tool": "echo", "args": {"text": "ran"}}])
    registry.execute("save_skill", {"name": "good", "description": "good", "steps_json": good})
    result = registry.execute("run_skill", {"name": "good"})
    assert "v1 completed" in result and calls == ["ran"]

    failing = json.dumps([
        {"tool": "fail", "args": {}},
        {"tool": "echo", "args": {"text": "must-not-run"}},
    ])
    registry.execute("save_skill", {"name": "bad-run", "description": "fails", "steps_json": failing})
    result = registry.execute("run_skill", {"name": "bad-run"})
    assert "failed" in result and "must-not-run" not in calls
    row = memory.get_skill("bad-run")
    assert row["failure_count"] == 1 and row["success_count"] == 0
    with sqlite3.connect(memory.db_path) as connection:
        stored = connection.execute("SELECT step_status_json FROM skill_runs ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert "secret-output" not in stored
    assert json.loads(stored) == [{"tool": "fail", "ok": False}]


def test_continue_on_error_runs_remaining_steps_but_run_stays_failed(tmp_path):
    memory, registry, calls = _registry(tmp_path)
    steps = json.dumps([
        {"tool": "fail", "args": {}, "continue_on_error": True},
        {"tool": "echo", "args": {"text": "continued"}},
    ])
    registry.execute("save_skill", {"name": "continue", "description": "continue", "steps_json": steps})
    result = registry.execute("run_skill", {"name": "continue"})
    assert "failed" in result and calls == ["continued"]
    assert memory.get_skill("continue")["failure_count"] == 1
