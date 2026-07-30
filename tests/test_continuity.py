import json
import os
from concurrent.futures import ThreadPoolExecutor

from seven.agent.prompt import build_system_prompt
from seven.memory.store import Memory
from seven.mind.state import LivingState
from seven.tools.registry import Tool, ToolRegistry


def test_failure_survives_reopen_and_enters_next_prompt_context(tmp_path):
    db_path = tmp_path / "continuity.db"
    first = Memory(db_path)
    goal_id = first.add_goal(
        "Recover from tool failures",
        "Use durable evidence before retrying.",
    )
    first.remember("Owner is Jan.", key="identity.owner", source="owner")
    registry = ToolRegistry(memory=first, tier="full")
    registry.register(
        Tool(
            name="probe_service",
            description="test-only service probe",
            parameters={"type": "object", "properties": {}},
            handler=lambda: '{"ok":false,"error":"connection refused"}',
        )
    )

    registry.execute("probe_service")

    reopened = Memory(db_path)
    context = reopened.context_block()
    prompt = build_system_prompt(memory_block=context, living_block="booted")

    assert reopened.active_goals()[0]["id"] == goal_id
    assert reopened.search_facts("Jan")
    belief = reopened.search_beliefs("tool:probe_service")[0]
    assert belief["topic"] == "tool:probe_service"
    assert belief["source"] == "tool_outcome"
    assert "connection refused" in belief["evidence"]
    assert "Recover from tool failures" in context
    assert "probe_service" in context
    assert "connection refused" in context
    assert "tool:probe_service" in context
    assert "You are Seven" in prompt
    assert "Recover from tool failures" in prompt
    assert "connection refused" in prompt


def test_repeated_failure_updates_one_tool_belief(tmp_path):
    memory = Memory(tmp_path / "belief-update.db")
    memory.audit("unstable_tool", {}, "ERROR: first failure", ok=False)
    first = memory.search_beliefs("tool:unstable_tool")[0]
    memory.audit("unstable_tool", {}, "ERROR: later failure", ok=False)
    beliefs = [
        row
        for row in memory.list_beliefs(20)
        if row["topic"] == "tool:unstable_tool"
    ]

    assert len(beliefs) == 1
    assert beliefs[0]["id"] == first["id"]
    assert "later failure" in beliefs[0]["evidence"]

    memory.audit("unstable_tool", {}, "OK: retry succeeded", ok=True)
    recovered = memory.search_beliefs("tool:unstable_tool")[0]
    assert recovered["id"] == first["id"]
    assert recovered["stance"] == "The most recent audited execution succeeded."
    assert "retry succeeded" in recovered["evidence"]
    reopened = Memory(memory.db_path)
    assert reopened.recent_failures() == []
    assert "most recent audited execution succeeded" in (
        reopened.search_beliefs("tool:unstable_tool")[0]["stance"].lower()
    )
    assert "first failure" not in reopened.context_block()
    assert "later failure" not in reopened.context_block()


def test_living_state_parallel_writes_remain_valid(tmp_path):
    path = tmp_path / "living_state.json"
    states = [LivingState(path=path) for _ in range(4)]

    def write_many(worker: int):
        state = states[worker]
        for index in range(20):
            state.record_action(f"worker-{worker}-{index}", reflection="soak")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write_many, range(4)))

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["last_action"].startswith("worker-")
    assert [item for item in tmp_path.iterdir() if item.suffix == ".tmp"] == []


def test_living_state_retries_transient_windows_replace_failure(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "living_state.json"
    state = LivingState(path=path)
    real_replace = os.replace
    attempts = []

    def flaky_replace(source, target):
        attempts.append((source, target))
        if len(attempts) < 3:
            raise PermissionError("simulated Windows file lock")
        return real_replace(source, target)

    monkeypatch.setattr(os, "replace", flaky_replace)
    state.record_action("retry-proof", reflection="bounded retry succeeded")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(attempts) == 3
    assert payload["last_action"] == "retry-proof"
