from __future__ import annotations

import threading
from types import SimpleNamespace

from seven.runtime.companion import CompanionRuntime, normalize_unsolicited_mode
from seven.runtime.startup import _startup_environment
from seven.ui.talk import run_talk
from seven.voice.io import VoiceIO


class FakeVoice:
    def __init__(self, heard=None, *, barge_in=False, **_):
        self.tts_ok = True
        self.stt_ok = True
        self.is_speaking = False
        self.last_barge_in = barge_in
        self.heard = list(heard or [])
        self.spoken = []
        self.listen_calls = []
        self.events = []

    def listen_once(self, **kwargs):
        self.listen_calls.append(kwargs)
        self.events.append(("listen", threading.get_ident()))
        return self.heard.pop(0) if self.heard else None

    def speak(self, text):
        self.events.append(("speak", threading.get_ident()))
        self.spoken.append(text)
        return True

    def stop_speaking(self):
        self.events.append(("stop", threading.get_ident()))

    def status_line(self):
        return "tts=fake stt=fake barge_in=True"


class FakeAgent:
    def __init__(self):
        self.freewill = SimpleNamespace(on_utter=None)
        self.handled = []
        self.handle_threads = []
        self.living = SimpleNamespace(
            self_state={"state": {"mode": "degraded_no_llm"}}
        )
        self.memory = SimpleNamespace(add_message=lambda *args, **kwargs: None)

    def refresh_living_state(self):
        return None

    def handle(self, text):
        self.handled.append(text)
        self.handle_threads.append(threading.get_ident())
        return f"reply:{text}"


def test_continuous_listen_routes_speech_to_handle_and_tts_same_process():
    voice = FakeVoice(["hello Seven", "second phrase"])
    agent = FakeAgent()
    output = []
    runtime = CompanionRuntime(
        agent,
        voice=voice,
        listen_timeout=1.25,
        phrase_limit=9,
        output=output.append,
    )

    first = runtime.listen_once()
    result = runtime.handle_user_text(first)
    second = runtime.listen_once()

    assert first == "hello Seven"
    assert second == "second phrase"
    assert agent.handled == ["hello Seven"]
    assert voice.spoken == ["reply:hello Seven"]
    assert result["ok"] is True
    assert result["reason"] == "tts"
    assert voice.listen_calls == [
        {"timeout": 1.25, "phrase_time_limit": 9.0, "calibrate": 0.35},
        {"timeout": 1.25, "phrase_time_limit": 9.0, "calibrate": 0.05},
    ]
    thread_ids = [event[1] for event in voice.events]
    assert thread_ids == [threading.get_ident()] * 3
    assert agent.handle_threads == [threading.get_ident()]


def test_run_talk_continuously_hears_handles_and_speaks(monkeypatch):
    voice = FakeVoice(["hello Seven", "goodbye"])
    agent = FakeAgent()
    monkeypatch.setattr("seven.voice.io.VoiceIO", lambda **kwargs: voice)

    run_talk(agent=agent, listen_timeout=0.1, phrase_limit=1, quiet=False)

    assert agent.handled == ["hello Seven"]
    assert "reply:hello Seven" in voice.spoken
    assert len(voice.listen_calls) == 2
    assert agent.freewill.on_utter is None
    assert [event[0] for event in voice.events].count("listen") == 2
    assert [event[0] for event in voice.events].count("speak") == 3


def test_barge_in_is_reported_and_listening_can_resume():
    voice = FakeVoice(["interrupting"], barge_in=True)
    runtime = CompanionRuntime(FakeAgent(), voice=voice, output=lambda _: None)

    result = runtime.deliver("a long reply")
    heard_after = runtime.listen_once()

    assert result == {"ok": True, "reason": "tts_barged_in"}
    assert heard_after == "interrupting"
    assert [event[0] for event in voice.events] == ["speak", "listen"]


def test_unsolicited_free_queues_for_foreground_tts():
    voice = FakeVoice()
    agent = FakeAgent()
    runtime = CompanionRuntime(
        agent,
        voice=voice,
        unsolicited="free",
        output=lambda _: None,
    )
    runtime.attach()

    queued = agent.freewill.on_utter("autonomous thought")

    assert queued == {"ok": False, "reason": "queued_for_tts"}
    assert voice.spoken == []
    delivered = runtime.drain_unsolicited()
    assert voice.spoken == ["autonomous thought"]
    assert delivered[0]["reason"] == "tts"


def test_unsolicited_off_is_explicit_and_silent():
    voice = FakeVoice()
    runtime = CompanionRuntime(
        FakeAgent(), voice=voice, unsolicited="off", output=lambda _: None
    )

    result = runtime.queue_unsolicited("autonomous thought")

    assert result == {"ok": False, "reason": "unsolicited_off"}
    assert runtime.drain_unsolicited() == []
    assert voice.spoken == []


def test_unsolicited_ask_prompts_once_then_delivers_after_yes():
    voice = FakeVoice()
    runtime = CompanionRuntime(
        FakeAgent(), voice=voice, unsolicited="ask", output=lambda _: None
    )

    first = runtime.queue_unsolicited("first thought")
    second = runtime.queue_unsolicited("second thought")
    prompt = runtime.drain_unsolicited()
    permission = runtime.handle_user_text("yes")

    assert first["reason"] == "unsolicited_permission_pending"
    assert second["reason"] == "unsolicited_permission_pending"
    assert [item["kind"] for item in prompt] == ["permission"]
    assert voice.spoken == [
        "I have something to say. Want to hear it?",
        "first thought",
        "second thought",
    ]
    assert permission["reason"] == "unsolicited_permission_granted"


def test_voice_speaking_state_wraps_delivery_and_stop(monkeypatch):
    def init_tts(voice):
        voice.tts_ok = True
        voice.tts_engine_name = "edge"

    monkeypatch.setattr(VoiceIO, "_init_tts", init_tts)
    monkeypatch.setattr(VoiceIO, "_init_stt_probe", lambda voice: None)
    voice = VoiceIO()
    observed = []

    def fake_edge(text):
        observed.append((text, voice.is_speaking))
        voice.stop_speaking()

    monkeypatch.setattr(voice, "_speak_edge", fake_edge)

    assert voice.speak("hello") is True
    assert observed == [("hello", True)]
    assert voice.is_speaking is False
    assert voice._stop_speak.is_set()


def test_unsolicited_mode_validation_and_startup_env():
    assert normalize_unsolicited_mode("FREE") == "free"
    assert normalize_unsolicited_mode("invalid") == "ask"
    assert _startup_environment({"SEVEN_UNSOLICITED": "ask"}) == {
        "SEVEN_UNSOLICITED": "ask"
    }
