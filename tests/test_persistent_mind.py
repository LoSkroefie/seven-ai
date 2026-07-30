import time
from types import SimpleNamespace
from unittest.mock import MagicMock

from seven import config
from seven.agent.loop import Seven
from seven.memory.store import Memory
from seven.mind.affect import AffectEngine
from seven.mind.episodic import EpisodicMemory
from seven.mind.reflection import ReflectionEngine
from seven.mind.relationship import RelationshipMind


def test_affect_persists_real_appraisals(tmp_path):
    db = tmp_path / "mind.db"
    affect = AffectEngine(Memory(db))
    mood = affect.observe_user("I am frustrated because this is still broken!")
    affect.observe_outcome(ok=False, error="verified timeout")

    restored = AffectEngine(Memory(db)).status()
    assert mood == "frustrated"
    assert restored["dominant_emotion"] in {
        "concerned",
        "determined",
        "frustrated",
        "focused",
    }
    assert "user mood inferred as frustrated" in restored["evidence"]


def test_relationship_and_reflection_are_durable(tmp_path):
    db = tmp_path / "relationship.db"
    memory = Memory(db)
    relationship = RelationshipMind(memory, display_name="Jan")
    relationship.observe_turn(
        user_text="We did it; it works.",
        user_mood="positive",
        response_ok=True,
        tool_count=2,
    )
    reflection = ReflectionEngine(memory)
    learned = reflection.reflect_on_turn(
        user_text="I am worried.",
        user_mood="worried",
        response="I checked the evidence.",
        response_ok=True,
        tool_trace=["get_system_info: ok"],
    )

    reopened = Memory(db)
    saved = reopened.get_relationship("owner", "Jan")
    assert saved["interaction_count"] == 1
    assert saved["shared_experiences"][0]["summary"] == "We did it; it works."
    assert learned["kind"] == "relationship"
    assert reopened.recent_reflections(1)[0]["kind"] == "relationship"


def test_daily_digest_never_calls_model_when_background_llm_is_off(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BACKGROUND_LLM", False)
    brain = MagicMock()
    memory = Memory(tmp_path / "digest.db")
    memory.add_message("user", "A real event happened.")
    episodic = EpisodicMemory(SimpleNamespace(memory=memory, brain=brain))

    digest = episodic.build_digest(period="test")

    assert "A real event happened." in digest
    brain.generate.assert_not_called()


def test_heartbeat_does_not_advance_plans_when_background_llm_is_off(monkeypatch):
    monkeypatch.setattr(config, "BACKGROUND_LLM", False)
    monkeypatch.setattr(config, "ENABLE_FREEWILL", True)
    planner = MagicMock()
    freewill = MagicMock()
    freewill.decide.return_value = SimpleNamespace(action="wait")
    freewill.execute.return_value = None
    agent = SimpleNamespace(
        refresh_living_state=lambda: None,
        last_user_ts=time.time() - 600,
        _deliver_due_reminders=lambda: False,
        episodic=SimpleNamespace(maybe_daily_digest=lambda: None),
        memory=SimpleNamespace(active_plans=lambda: [{"id": 7}]),
        planner=planner,
        living=MagicMock(),
        freewill=freewill,
        autonomy=MagicMock(),
    )

    Seven._autonomous_tick(agent)

    planner.execute_next_step.assert_not_called()
