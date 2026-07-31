from __future__ import annotations

from types import SimpleNamespace

from seven import config
from seven.runtime.companion_app import CompanionApp
from seven.ui.avatar import SevenAvatar, run_avatar


class FakeAffect:
    def status(self):
        return {"dominant_emotion": "calm", "secondary_emotion": "calm"}


class FakeAgent:
    def __init__(self):
        self.freewill = SimpleNamespace(on_utter=None)
        self.affect = FakeAffect()
        self.activity = "idle"
        self.last_response_ts = 0
        self.started = 0
        self.stopped = 0
        self.handled = []

    def start_heartbeat(self):
        self.started += 1

    def shutdown(self):
        self.stopped += 1

    def handle(self, text):
        self.handled.append(text)
        return f"answer:{text}"


class FakeVoice:
    def __init__(self, heard=None):
        self.tts_ok = True
        self.stt_ok = True
        self.is_speaking = False
        self.last_barge_in = False
        self.stt_backend = "test"
        self.heard = list(heard or [])
        self.spoken = []
        self.states = []
        self.runtime = None

    def listen_once(self, **_kwargs):
        self.states.append(self.runtime.activity_state)
        return self.heard.pop(0) if self.heard else None

    def speak(self, text):
        self.states.append(self.runtime.activity_state)
        self.spoken.append(text)
        return True

    def stop_speaking(self):
        return None


class FakeAvatar:
    def __init__(self, agent, *, runtime, on_quit):
        self.agent = agent
        self.runtime = runtime
        self.on_quit = on_quit
        self.ran = False

    def run(self):
        self.ran = True

    def request_close(self):
        return None


def test_companion_app_wires_one_agent_to_runtime_avatar_and_heartbeat(monkeypatch):
    agent = FakeAgent()
    voice = FakeVoice()
    app = CompanionApp(
        agent=agent,
        voice=voice,
        avatar_factory=FakeAvatar,
    )
    voice.runtime = app.runtime
    monkeypatch.setattr(app, "_listen_loop", lambda: None)

    avatar = app._make_avatar()
    app.avatar = avatar
    app.start()

    assert app.runtime.agent is agent
    assert avatar.agent is agent
    assert avatar.runtime is app.runtime
    assert agent.started == 1
    assert agent.freewill.on_utter == app.runtime.queue_unsolicited
    app.close()
    assert agent.stopped == 1
    assert agent.freewill.on_utter is None


def test_unified_conversation_uses_real_listening_thinking_speaking_states():
    agent = FakeAgent()
    voice = FakeVoice(["hello Seven"])
    app = CompanionApp(agent=agent, voice=voice, avatar_factory=FakeAvatar)
    voice.runtime = app.runtime
    observed = []
    original_handle = agent.handle

    def handle(text):
        observed.append(app.runtime.activity_state)
        return original_handle(text)

    agent.handle = handle
    result = app.conversation_step()

    assert result["heard"] == "hello Seven"
    assert result["result"]["reply"] == "answer:hello Seven"
    assert agent.handled == ["hello Seven"]
    assert voice.spoken == ["answer:hello Seven"]
    assert voice.states == ["listening", "speaking"]
    assert observed == ["thinking"]
    assert app.runtime.activity_state == "idle"


def test_avatar_pose_prefers_live_companion_state():
    avatar = SevenAvatar.__new__(SevenAvatar)
    avatar.agent = FakeAgent()
    avatar.runtime = SimpleNamespace(activity_state="listening")
    assert avatar._pose_for_state() == "listening"
    avatar.runtime.activity_state = "speaking"
    assert avatar._pose_for_state() == "speaking"
    avatar.runtime.activity_state = "thinking"
    assert avatar._pose_for_state() == "thinking"


def test_avatar_entrypoint_delegates_to_unified_companion(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "seven.runtime.companion_app.run_companion_app",
        lambda **kwargs: calls.append(kwargs),
    )

    run_avatar(enable_api=False)

    assert calls == [{"enable_api": False}]


def test_companion_cli_dispatches_unified_product_not_console(monkeypatch):
    import seven.__main__ as entry

    calls = []
    monkeypatch.setattr(entry, "apply_saved_environment", lambda: None)
    monkeypatch.setattr(entry, "setup_logging", lambda: None)
    monkeypatch.setattr(config, "ENABLE_VOICE", False)
    monkeypatch.setattr(config, "ENABLE_API", False)
    monkeypatch.setattr(
        "seven.runtime.companion_app.run_companion_app",
        lambda **kwargs: calls.append(("companion", kwargs)) or 0,
    )
    monkeypatch.setattr(
        "seven.ui.talk.run_talk",
        lambda **kwargs: calls.append(("console", kwargs)),
    )

    assert entry.main(["--companion"]) == 0

    assert calls == [("companion", {"enable_api": False})]


def test_talk_console_remains_an_explicit_fallback(monkeypatch):
    import seven.__main__ as entry

    calls = []
    monkeypatch.setattr(entry, "apply_saved_environment", lambda: None)
    monkeypatch.setattr(entry, "setup_logging", lambda: None)
    monkeypatch.setattr(config, "ENABLE_VOICE", False)
    monkeypatch.setattr(config, "ENABLE_API", False)
    monkeypatch.setattr(
        "seven.runtime.companion_app.run_companion_app",
        lambda **kwargs: calls.append(("companion", kwargs)) or 0,
    )
    monkeypatch.setattr(
        "seven.ui.talk.run_talk",
        lambda **kwargs: calls.append(("console", kwargs)),
    )

    assert entry.main(["--talk-console"]) == 0

    assert calls == [("console", {"quiet": False})]
