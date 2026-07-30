from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from seven.memory.store import Memory
from seven.mind.freewill import FreeWill
from seven.mind.planner import Planner


class _FreeWillMemory:
    @staticmethod
    def active_plans():
        return []


def _freewill_for_due_at(due_at: str) -> FreeWill:
    living = SimpleNamespace(
        self_state={"state": {"mode": "full", "energy": 1.0}},
        world={
            "work": {
                "active_goals": [],
                "open_tasks": [{"title": "Timed task", "due_at": due_at}],
            },
            "ollama": {"ok": True},
            "time": {"is_quiet_hours": False},
        },
    )
    agent = SimpleNamespace(
        living=living,
        memory=_FreeWillMemory(),
        refresh_living_state=lambda: None,
    )
    return FreeWill(agent)


def test_freewill_future_due_date_is_not_forced(monkeypatch):
    monkeypatch.setattr("seven.mind.freewill.config.BACKGROUND_LLM", True)
    future = datetime.now(timezone.utc) + timedelta(days=1)

    decision = _freewill_for_due_at(future.isoformat()).decide(idle_min=0)

    assert decision.action == "wait"
    assert "due task" not in decision.reason


def test_freewill_past_due_date_is_forced(monkeypatch):
    monkeypatch.setattr("seven.mind.freewill.config.BACKGROUND_LLM", True)
    past = datetime.now(timezone.utc) - timedelta(minutes=1)

    decision = _freewill_for_due_at(past.isoformat()).decide(idle_min=0)

    assert decision.action == "work"
    assert decision.reason == "due task: Timed task"


def _planner_with_audit(tmp_path, step, tool):
    memory = Memory(tmp_path / f"{tool}.db")

    def handle(_prompt, source):
        assert source == "planner"
        memory.audit(tool, {}, '{"ok": true}', True)
        return f"{tool} completed"

    agent = SimpleNamespace(memory=memory, handle=handle)
    plan_id = memory.create_plan("Truthful plan", [step])
    return Planner(agent), memory, plan_id


def test_planner_talk_only_forced_sysinfo_does_not_advance(tmp_path):
    planner, memory, plan_id = _planner_with_audit(
        tmp_path,
        {"action": "act", "detail": "Create the requested artifact", "done": False},
        "get_system_info",
    )

    result = planner.execute_next_step(plan_id)

    assert "unchanged" in result
    assert memory.get_plan(plan_id)["current_step"] == 0


def test_planner_real_tool_work_advances(tmp_path):
    planner, memory, plan_id = _planner_with_audit(
        tmp_path,
        {"action": "act", "detail": "Create the requested artifact", "done": False},
        "write_file",
    )

    result = planner.execute_next_step(plan_id)

    assert "step 1 done" in result
    assert memory.get_plan(plan_id)["current_step"] == 1


def test_planner_observation_advances_only_an_inspection_step(tmp_path):
    planner, memory, plan_id = _planner_with_audit(
        tmp_path,
        {"action": "inspect", "detail": "Inspect system resources", "done": False},
        "get_system_info",
    )

    result = planner.execute_next_step(plan_id)

    assert "step 1 done" in result
    assert memory.get_plan(plan_id)["current_step"] == 1


def test_goal_progress_uses_linked_plan_step_fraction(tmp_path):
    memory = Memory(tmp_path / "plan-progress.db")
    goal_id = memory.add_goal("Two evidenced steps")

    def handle(_prompt, source):
        assert source == "planner"
        memory.audit("write_file", {"path": "result.txt"}, "OK wrote result.txt", True)
        return "Wrote the requested result."

    agent = SimpleNamespace(memory=memory, handle=handle)
    plan_id = memory.create_plan(
        "Two-step plan",
        [
            {"action": "act", "detail": "Write result", "done": False},
            {"action": "act", "detail": "Verify result", "done": False},
        ],
        goal_id=goal_id,
    )

    Planner(agent).execute_next_step(plan_id)

    assert memory.get_plan(plan_id)["current_step"] == 1
    assert memory.get_goal(goal_id)["progress"] == 50.0


def test_tool_count_without_plan_does_not_change_goal_progress(tmp_path):
    memory = Memory(tmp_path / "no-plan-progress.db")
    goal_id = memory.add_goal("No percentage theater")

    memory.audit("write_file", {"path": "result.txt"}, "OK wrote result.txt", True)

    assert memory.get_goal(goal_id)["progress"] == 0.0
