from __future__ import annotations

import logging
import time
from types import SimpleNamespace

from seven import config
from seven.agent.loop import Seven
from seven.memory.store import Memory
from seven.mind.freewill import Decision, FreeWill
from seven.mind.planner import Planner
from seven.runtime.companion import CompanionRuntime


class Voice:
    def __init__(self, heard=None):
        self.tts_ok = True
        self.stt_ok = True
        self.stt_backend = "test"
        self.is_speaking = False
        self.last_barge_in = False
        self.heard = list(heard or [])
        self.spoken = []

    def listen_once(self, **_kwargs):
        return self.heard.pop(0) if self.heard else None

    def speak(self, text):
        self.spoken.append(text)
        return True

    def stop_speaking(self):
        return None


class Agent:
    def __init__(self):
        self.freewill = SimpleNamespace(on_utter=None)
        self.handled = []
        self.memory = SimpleNamespace(add_message=lambda *_args, **_kwargs: None)

    def handle(self, text):
        self.handled.append(text)
        return f"reply:{text}"


def test_identical_unsolicited_text_is_rate_limited(monkeypatch):
    monkeypatch.setattr(config, "UNSOLICITED_REPEAT_GAP", 900)
    runtime = CompanionRuntime(Agent(), voice=Voice(), output=lambda _text: None)

    first = runtime.queue_unsolicited("same plan failure")
    second = runtime.queue_unsolicited("  SAME   plan failure ")

    assert first["reason"] == "queued_for_tts"
    assert second == {"ok": False, "reason": "duplicate_rate_limited"}
    assert len(runtime.drain_unsolicited()) == 1


def test_user_reply_defers_queued_unsolicited_until_reply_finishes():
    voice = Voice()
    agent = Agent()
    runtime = CompanionRuntime(agent, voice=voice, output=lambda _text: None)
    during_handle = []

    def handle(text):
        during_handle.extend(runtime.drain_unsolicited())
        return f"reply:{text}"

    agent.handle = handle
    runtime.queue_unsolicited("background plan update")

    reply = runtime.handle_user_text("hello")

    assert during_handle == []
    assert reply["reply"] == "reply:hello"
    assert voice.spoken == ["reply:hello"]
    runtime.drain_unsolicited()
    assert voice.spoken == ["reply:hello", "background plan update"]


def test_stt_phrase_is_logged_then_handled_and_replied(caplog):
    voice = Voice(["Seven can you hear me"])
    agent = Agent()
    runtime = CompanionRuntime(agent, voice=voice, output=lambda _text: None)

    with caplog.at_level(logging.INFO):
        heard = runtime.listen_once()
        result = runtime.handle_user_text(heard)

    assert heard == "Seven can you hear me"
    assert agent.handled == [heard]
    assert result["reply"] == f"reply:{heard}"
    assert voice.spoken == [f"reply:{heard}"]
    assert "companion heard speech" in caplog.text
    assert "companion reply delivered=True reason=tts" in caplog.text


def _freewill_agent(*, backed_off=False):
    living = SimpleNamespace(
        self_state={"state": {"mode": "full", "energy": 1.0}},
        world={
            "work": {
                "active_goals": [{"id": 1, "title": "stuck"}],
                "open_tasks": [],
            },
            "ollama": {"ok": True},
            "time": {"is_quiet_hours": False},
        },
    )
    return SimpleNamespace(
        _companion_active=True,
        living=living,
        refresh_living_state=lambda: None,
        memory=SimpleNamespace(active_plans=lambda: [{"id": 1}]),
        planner=SimpleNamespace(is_backed_off=lambda _plan_id: backed_off),
    )


def test_recent_conversation_prefers_listening(monkeypatch):
    monkeypatch.setattr(config, "COMPANION_RECENT_USER_SECONDS", 120)
    freewill = FreeWill(_freewill_agent())

    decision = freewill.decide(idle_min=0.5)

    assert decision.action == "wait"
    assert "listening first" in decision.reason


def test_backed_off_plan_does_not_force_work(monkeypatch):
    monkeypatch.setattr(config, "COMPANION_RECENT_USER_SECONDS", 120)
    freewill = FreeWill(_freewill_agent(backed_off=True))

    decision = freewill.decide(idle_min=10)

    assert decision.action == "wait"
    assert "backing off" in decision.reason


def test_planner_abandons_after_consecutive_failures(monkeypatch):
    monkeypatch.setattr(config, "PLAN_FAILURE_BACKOFF_SECONDS", 60)
    monkeypatch.setattr(config, "PLAN_FAILURE_ABANDON_AFTER", 3)
    cancelled = []
    memory = SimpleNamespace(
        cancel_plan=lambda plan_id, **kwargs: cancelled.append((plan_id, kwargs))
    )
    planner = Planner(SimpleNamespace(memory=memory))
    plan = {"id": 7, "goal_id": 4}

    first = planner._record_failure(plan)
    second = planner._record_failure(plan)
    third = planner._record_failure(plan)

    assert first["abandoned"] is False
    assert second["abandoned"] is False
    assert third["abandoned"] is True
    assert planner.failure_count(7) == 3
    assert planner.is_backed_off(7, now=time.time()) is True
    assert cancelled == [
        (
            7,
            {
                "reason": (
                    "plan #7 blocked after 3 consecutive steps without "
                    "successful outcome evidence"
                ),
                "block_linked_goal": True,
            },
        )
    ]


def test_cancel_plan_blocks_linked_goal_and_survives_reopen(tmp_path):
    db = tmp_path / "seven.db"
    memory = Memory(db)
    goal_id = memory.add_goal("stuck goal")
    plan_id = memory.create_plan(
        "stuck plan",
        [{"action": "run_shell", "detail": "do work", "done": False}],
        goal_id=goal_id,
    )

    cancelled = memory.cancel_plan(
        plan_id,
        reason="owner cancelled stuck plan",
        block_linked_goal=True,
    )
    reopened = Memory(db)

    assert cancelled["status"] == "cancelled"
    assert reopened.get_plan(plan_id)["status"] == "cancelled"
    assert reopened.get_goal(goal_id)["status"] == "blocked"
    assert reopened.active_plans() == []
    assert reopened.active_goals() == []


def test_plan_failure_voice_is_short_rate_limited_then_silent(monkeypatch):
    monkeypatch.setattr(config, "PLAN_FAILURE_VOICE_GAP", 900)
    monkeypatch.setattr(config, "PLAN_FAILURE_VOICE_LIMIT", 2)
    clock = [1000.0]
    monkeypatch.setattr("seven.mind.freewill.time.time", lambda: clock[0])
    freewill = FreeWill.__new__(FreeWill)
    note = (
        "Plan #1 step 1 — no successful outcome evidence; "
        "unchanged (failed_tools=1)."
    )

    first = freewill._summarize_work_for_voice(note)
    immediate_repeat = freewill._summarize_work_for_voice(note)
    clock[0] += 901
    second = freewill._summarize_work_for_voice(note)
    clock[0] += 901
    third = freewill._summarize_work_for_voice(note)

    assert first == "I'm stuck on a plan; say cancel plan if you want me to stop."
    assert immediate_repeat is None
    assert second == first
    assert third is None
    assert freewill.last_utter_reason == "plan_failure_voice_suppressed"


def test_natural_cancel_plan_command_blocks_linked_goal():
    calls = []
    agent = Seven.__new__(Seven)
    agent.memory = SimpleNamespace(
        active_plans=lambda: [{"id": 9}],
        cancel_plan=lambda plan_id, **kwargs: calls.append((plan_id, kwargs))
        or {"id": plan_id, "status": "cancelled"},
    )

    reply = agent._local_commands("cancel plan")

    assert "Plan #9 is cancelled" in reply
    assert calls == [
        (
            9,
            {
                "reason": "owner cancelled stuck plan #9",
                "block_linked_goal": True,
            },
        )
    ]


def test_heartbeat_does_not_advance_plan_while_companion_is_active(monkeypatch):
    monkeypatch.setattr(config, "BACKGROUND_LLM", True)
    monkeypatch.setattr(config, "ENABLE_FREEWILL", True)
    planner_calls = []
    agent = Seven.__new__(Seven)
    agent.last_user_ts = time.time() - 600
    agent._companion_active = True
    agent.refresh_living_state = lambda: None
    agent._deliver_due_reminders = lambda: False
    agent.living = SimpleNamespace(
        tick_count=1,
        record_action=lambda *_args, **_kwargs: None,
    )
    agent.episodic = SimpleNamespace(maybe_daily_digest=lambda: None)
    agent.memory = SimpleNamespace(active_plans=lambda: [{"id": 1}])
    agent.planner = SimpleNamespace(
        execute_next_step=lambda **_kwargs: planner_calls.append(True)
    )
    agent.freewill = SimpleNamespace(
        decide=lambda _idle: Decision("wait", "listening"),
        execute=lambda _decision: None,
        on_utter=None,
        last_utter_reason="not_attempted",
    )
    agent.autonomy = SimpleNamespace(session=None, heartbeat_tick=lambda _idle: None)

    Seven._autonomous_tick(agent)

    assert planner_calls == []


def test_heartbeat_respects_plan_failure_backoff(monkeypatch):
    monkeypatch.setattr(config, "BACKGROUND_LLM", True)
    monkeypatch.setattr(config, "ENABLE_FREEWILL", True)
    planner_calls = []
    agent = Seven.__new__(Seven)
    agent.last_user_ts = time.time() - 600
    agent._companion_active = False
    agent.refresh_living_state = lambda: None
    agent._deliver_due_reminders = lambda: False
    agent.living = SimpleNamespace(
        tick_count=1,
        record_action=lambda *_args, **_kwargs: None,
    )
    agent.episodic = SimpleNamespace(maybe_daily_digest=lambda: None)
    agent.memory = SimpleNamespace(active_plans=lambda: [{"id": 1}])
    agent.planner = SimpleNamespace(
        is_backed_off=lambda _plan_id: True,
        execute_next_step=lambda **_kwargs: planner_calls.append(True),
    )
    agent.freewill = SimpleNamespace(
        decide=lambda _idle: Decision("wait", "plan backoff"),
        execute=lambda _decision: None,
        on_utter=None,
        last_utter_reason="not_attempted",
    )
    agent.autonomy = SimpleNamespace(session=None, heartbeat_tick=lambda _idle: None)

    Seven._autonomous_tick(agent)

    assert planner_calls == []
