import logging
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

from seven import config
from seven.agent.loop import Seven
from seven.mind.freewill import Decision, FreeWill
from seven.runtime.utterance import DefaultUtteranceSink


def _freewill_agent(*, recent=None):
    memory = MagicMock()
    memory.context_block.return_value = "known facts"
    memory.recent_messages.return_value = recent or []
    return SimpleNamespace(
        brain=MagicMock(),
        affect=SimpleNamespace(
            status=lambda: {"dominant_emotion": "focused"},
        ),
        living=SimpleNamespace(
            self_state={"intent": "finish the companion"},
            context_for_prompt=lambda: "grounded context",
            record_action=MagicMock(),
        ),
        memory=memory,
    )


def test_speak_fallback_produces_text_and_updates_timestamp_only_for_text(
    monkeypatch,
):
    monkeypatch.setattr(config, "BACKGROUND_LLM", True)
    agent = _freewill_agent()
    agent.brain.generate.side_effect = RuntimeError("model offline")
    freewill = FreeWill(agent)
    freewill.last_speak_ts = 41.0

    text = freewill.execute(Decision("speak", "test"))

    assert text.startswith("I’m focused and present")
    assert freewill.last_utter_reason == "llm_failed_grounded"
    assert freewill.last_speak_ts > 41.0
    before = freewill.last_speak_ts
    assert freewill._accept_utter(None, "test_empty") is None
    assert freewill.last_speak_ts == before
    assert freewill.last_utter_reason == "test_empty"


def test_duplicate_grounded_line_uses_static_final_fallback(monkeypatch):
    monkeypatch.setattr(config, "BACKGROUND_LLM", False)
    repeated = (
        "I’m focused and present; my current intention is to finish the companion."
    )
    agent = _freewill_agent(
        recent=[
            {
                "role": "assistant",
                "content": repeated,
                "meta": {"freewill": True},
            }
        ]
    )
    freewill = FreeWill(agent)

    assert freewill.execute(Decision("speak", "test")) == "I'm still here."
    assert freewill.last_utter_reason == "llm_disabled_static"


def test_autonomous_speak_invokes_callback_and_logs_reason(monkeypatch, caplog):
    monkeypatch.setattr(config, "BACKGROUND_LLM", False)
    monkeypatch.setattr(config, "ENABLE_FREEWILL", True)
    spoken = []
    freewill = MagicMock()
    freewill.decide.return_value = Decision("speak", "test")
    freewill.execute.return_value = "I am speaking."
    freewill.last_utter_reason = "grounded"
    freewill.on_utter = spoken.append
    agent = SimpleNamespace(
        refresh_living_state=lambda: None,
        last_user_ts=time.time() - 600,
        _deliver_due_reminders=lambda: False,
        episodic=SimpleNamespace(maybe_daily_digest=lambda: None),
        memory=SimpleNamespace(active_plans=lambda: []),
        planner=MagicMock(),
        living=SimpleNamespace(tick_count=7),
        freewill=freewill,
        autonomy=MagicMock(),
    )

    caplog.set_level(logging.INFO, logger="seven.agent")
    Seven._autonomous_tick(agent)

    assert spoken == ["I am speaking."]
    assert "uttered=True utter_reason=grounded" in caplog.text


def test_default_sink_logs_and_notifies_without_voice(tmp_path):
    notifications = []

    def notify(title, body):
        notifications.append((title, body))
        return {"ok": True, "state": "submitted"}

    sink = DefaultUtteranceSink(
        data_dir=tmp_path,
        voice_enabled=False,
        notifier=notify,
    )

    result = sink("I'm still here.")

    assert result["ok"] is True
    assert result["reason"] == "notification_and_log"
    assert notifications == [("Seven", "I'm still here.")]
    assert "I'm still here." in (tmp_path / "utterances.log").read_text(
        encoding="utf-8"
    )
