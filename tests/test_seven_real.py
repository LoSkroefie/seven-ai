"""Smoke + harden tests for Seven Real core (no live Ollama required)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seven.memory.store import Memory
from seven.tools.shell import run_shell
from seven.tools.files import write_file, read_file, list_dir
from seven.tools.registry import Tool, ToolRegistry, build_default_registry, CORE_TOOL_NAMES
from seven.tools.sanitize import sanitize_arguments, coerce_int, is_blank
from seven.brain.llm import Brain


def test_memory_roundtrip(tmp_path):
    db = tmp_path / "t.db"
    m = Memory(db)
    m.remember("User likes dark mode", key="pref.theme")
    m.add_task("Buy milk")
    m.add_goal("Learn Rust", "read book")
    m.add_message("user", "hello")
    m.add_message("assistant", "hi")
    assert m.search_facts("dark")
    assert m.open_tasks()
    assert m.active_goals()
    assert len(m.recent_messages(10)) == 2
    block = m.context_block()
    assert "dark" in block or "pref" in block


def test_shell_echo():
    out = run_shell("echo seven-real-ok")
    assert "seven-real-ok" in out or "exit_code=0" in out


def test_shell_blank_command():
    out = run_shell("")
    assert out.startswith("ERROR")


def test_disabled_tool_cannot_execute(tmp_path):
    memory = Memory(tmp_path / "disabled.db")
    registry = ToolRegistry(memory=memory, tier="full")
    called = []
    registry.register(Tool(
        name="dangerous_test_tool",
        description="test only",
        parameters={"type": "object", "properties": {}},
        handler=lambda: called.append(True) or "ran",
        enabled=False,
    ))
    assert "disabled" in registry.execute("dangerous_test_tool").lower()
    assert called == []
    assert memory.recent_audit(1)[0]["ok"] == 0


def test_shell_empty_optional_args():
    out = run_shell("echo hi", cwd="", timeout="")
    assert "hi" in out.lower() or "exit_code=0" in out


def test_files(tmp_path):
    p = tmp_path / "a.txt"
    write_file(str(p), "hello seven")
    assert "hello seven" in read_file(str(p))
    listing = list_dir(str(tmp_path))
    assert "a.txt" in listing


def test_registry_has_core_tools(tmp_path):
    m = Memory(tmp_path / "r.db")
    reg = build_default_registry(m, brain=None, tier="full")
    names = set(reg.names())
    for required in (
        "run_shell", "read_file", "write_file", "list_dir",
        "web_search", "get_system_info", "remember_fact",
        "run_python", "screenshot", "robot_status",
    ):
        assert required in names, f"missing {required}"
    out = reg.execute("get_system_info", {})
    assert "os=" in out or "time=" in out


def test_tool_tier_core_hides_robot_schema(tmp_path):
    m = Memory(tmp_path / "tier.db")
    reg = build_default_registry(m, brain=None, tier="core")
    active = set(reg.names())
    assert "run_shell" in active
    assert "robot_action" not in active  # schema hidden
    # But still executable at L4 if named
    out = reg.execute("robot_status", {})
    assert "available" in out.lower() or "robot" in out.lower() or out.startswith("{")


def test_sanitize_drops_blank_optionals():
    props = {
        "command": {"type": "string"},
        "cwd": {"type": "string"},
        "timeout": {"type": "integer"},
    }
    cleaned = sanitize_arguments(
        {"command": "echo x", "cwd": "", "timeout": "null"},
        properties=props,
        required=["command"],
    )
    assert cleaned["command"] == "echo x"
    assert "cwd" not in cleaned
    assert "timeout" not in cleaned
    assert coerce_int("12", None) == 12
    assert is_blank("None")


def test_registry_sanitizes_on_execute(tmp_path):
    m = Memory(tmp_path / "san.db")
    reg = build_default_registry(m, brain=None, tier="core")
    # empty optionals should not crash
    out = reg.execute("run_shell", {"command": "echo sanitized", "cwd": "", "timeout": ""})
    assert "sanitized" in out or "exit_code=0" in out


def test_brain_text_tool_parse():
    calls = Brain._extract_text_tool_calls(
        '{"tool_call": {"name": "run_shell", "arguments": {"command": "echo hi"}}}'
    )
    assert calls and calls[0]["name"] == "run_shell"
    assert calls[0]["arguments"]["command"] == "echo hi"
    # prose + parameters key (llama3.2 style)
    messy = (
        'I will search now.\n'
        '{"name": "web_search", "parameters": {"query": "cats", "max_results": "3"}}'
    )
    calls2 = Brain._extract_text_tool_calls(messy)
    assert calls2 and calls2[0]["name"] == "web_search"
    assert calls2[0]["arguments"].get("query") == "cats"


def test_memory_compaction(tmp_path):
    m = Memory(tmp_path / "c.db")
    for i in range(20):
        m.add_message("user", f"msg {i}")
        m.add_message("assistant", f"reply {i}")
    assert m.message_count() == 40
    summary = m.compact_history(keep_recent=8)
    assert summary
    assert m.message_count() == 8
    facts = m.search_facts("session")
    assert facts or "user:" in summary


def test_mock_brain_tool_round(tmp_path, monkeypatch):
    """Integration: mocked Brain tool_calls → registry executes real tool."""
    from seven.agent import loop as loop_mod

    # Isolate memory path via injected instance after construct
    s = loop_mod.Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "int.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")

    calls = {"n": 0}

    def fake_chat(messages, tools=None, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "1", "name": "get_system_info", "arguments": {}},
                ],
            }
        return {
            "role": "assistant",
            "content": "System looks fine.",
            "tool_calls": [],
        }

    s.brain.chat = fake_chat  # type: ignore
    reply = s.handle("Check the system please")
    assert "fine" in reply.lower() or "system" in reply.lower()
    audits = s.memory.recent_audit(5)
    assert any(a["tool"] == "get_system_info" for a in audits)


def test_local_commands(tmp_path):
    from seven.agent.loop import Seven
    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "cmd.db")
    tools_out = s.handle("/tools")
    assert "run_shell" in tools_out
    status = s.handle("/status")
    assert "tool_tier" in status or "Seven Real" in status
    assert s.handle("/clear")


def test_api_handler_chat(tmp_path, monkeypatch):
    """stdlib API /chat uses Seven.handle — no live network bind required for logic."""
    from seven.ui import api_server
    from seven.agent.loop import Seven

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "api.db")
    s.brain.chat = lambda messages, tools=None, **kw: {  # type: ignore
        "role": "assistant",
        "content": "api-ok",
        "tool_calls": [],
    }
    server = api_server.SevenAPIServer(("127.0.0.1", 0), api_server.SevenHandler, "x" * 32, agent=s)
    try:
        with server.seven_agent_lock:
            reply = server.get_agent().handle("ping-test")
        assert reply == "api-ok"
        assert server.seven_owns_agent is False
    finally:
        server.shutdown_cleanly()


def test_api_token_is_persistent_and_private(tmp_path, monkeypatch):
    from seven.ui import api_server

    monkeypatch.setattr(api_server.config, "DATA_DIR", tmp_path)
    monkeypatch.delenv("SEVEN_API_TOKEN", raising=False)
    first = api_server.get_or_create_api_token()
    second = api_server.get_or_create_api_token()
    assert first == second
    assert len(first) >= 32
    assert (tmp_path / "api.token").read_text(encoding="utf-8").strip() == first


def test_api_authorization_requires_matching_token():
    from seven.ui import api_server

    handler = object.__new__(api_server.SevenHandler)
    handler.server = type("Server", (), {"seven_api_token": "expected-token"})()
    handler.headers = {"Authorization": "Bearer expected-token"}
    assert handler._authorized() is True
    handler.headers = {"Authorization": "Bearer wrong-token"}
    assert handler._authorized() is False


def test_gui_module_imports():
    from seven.ui.chat_gui import SevenChatApp
    from seven.ui.desktop import run_desktop
    assert SevenChatApp is not None
    assert callable(run_desktop)


def test_voice_clean_for_speech():
    from seven.voice.io import VoiceIO
    cleaned = VoiceIO._clean_for_speech("Hello **world** and `code`\n\nmore", 100)
    assert "world" in cleaned
    assert "**" not in cleaned


def test_voice_hallucination_filter():
    from seven.voice.io import VoiceIO
    assert VoiceIO._filter_hallucination("you", {}) is None
    assert VoiceIO._filter_hallucination("Thanks for watching", {}) is None
    assert VoiceIO._filter_hallucination("Open the project folder", {}) is not None


def test_voice_status_without_load():
    from seven.voice.io import VoiceIO
    v = VoiceIO(lazy_whisper=True)
    s = v.status()
    assert "tts_ok" in s
    assert "stt_ok" in s
    line = v.status_line()
    assert "tts=" in line


def test_vision_prepare_image(tmp_path):
    from PIL import Image
    from seven.tools.vision import _prepare_image_b64
    p = tmp_path / "big.png"
    Image.new("RGB", (2000, 1000), color=(10, 20, 30)).save(p)
    b64 = _prepare_image_b64(str(p))
    assert isinstance(b64, str) and len(b64) > 100
    # decoded should be smaller JPEG than raw 2000px PNG typically
    import base64
    raw = base64.b64decode(b64)
    assert raw[:2] == b"\xff\xd8"  # JPEG


def test_vision_tools_registered(tmp_path):
    m = Memory(tmp_path / "vis.db")
    reg = build_default_registry(m, brain=None, tier="core")
    names = set(reg.names())
    for t in ("see_screen", "capture_webcam", "analyze_image", "check_presence", "list_cameras"):
        assert t in names, t


def test_presence_on_blank_image(tmp_path):
    from PIL import Image
    from seven.sensors.presence import check_presence
    p = tmp_path / "blank.jpg"
    Image.new("RGB", (320, 240), color=(40, 40, 40)).save(p)
    r = check_presence(image_path=str(p))
    assert r["ok"] is True
    assert r["present"] is False
    assert r["face_count"] == 0


def test_format_audit_pretty():
    from seven.agent.autonomy import format_audit
    text = format_audit([
        {"id": 1, "tool": "run_shell", "ok": 1, "created_at": "2026-07-10T00:00:00",
         "arguments": '{"command":"echo"}', "result_preview": "exit_code=0"},
    ])
    assert "Activity log" in text
    assert "run_shell" in text


def test_autonomy_progress_only_with_tools(tmp_path):
    """Progress must not advance if no real tools ran."""
    from seven.agent.loop import Seven
    from seven.agent.autonomy import AutonomyEngine

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "auto.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    s.autonomy = AutonomyEngine(s)
    gid = s.memory.add_goal("Test goal", "do something real")

    # Mock brain: final answer only, no tools
    s.brain.chat = lambda messages, tools=None, **kw: {  # type: ignore
        "role": "assistant",
        "content": "I would work on it.",
        "tool_calls": [],
    }
    out = s.autonomy.run_goal_step(goal_id=gid, reason="manual")
    g = s.memory.get_goal(gid)
    assert g["progress"] == 0 or g["progress"] == 0.0
    assert "no real tool work" in out


def test_autonomy_progress_with_real_tools(tmp_path):
    from seven.agent.loop import Seven
    from seven.agent.autonomy import AutonomyEngine

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "auto2.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    s.autonomy = AutonomyEngine(s)
    # lower min interval for test path via heartbeat skip not used
    s.autonomy.min_work_interval = 0
    gid = s.memory.add_goal("Write marker", "create a file")

    calls = {"n": 0}

    def fake_chat(messages, tools=None, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "1",
                    "name": "run_shell",
                    "arguments": {"command": "echo autonomy-ok"},
                }],
            }
        return {"role": "assistant", "content": "Did the shell step.", "tool_calls": []}

    s.brain.chat = fake_chat  # type: ignore
    out = s.autonomy.run_goal_step(goal_id=gid, reason="manual")
    g = s.memory.get_goal(gid)
    assert g["progress"] > 0
    assert "progress" in out
    notes = s.memory.list_notes(5)
    assert any(n.get("title") == "autonomy" for n in notes)


def test_work_session_commands(tmp_path):
    from seven.agent.loop import Seven
    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "ws.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    from seven.agent.autonomy import AutonomyEngine
    s.autonomy = AutonomyEngine(s)
    gid = s.memory.add_goal("Session goal", "focus")
    msg = s.handle(f"/work {gid} 5")
    assert "Work session ON" in msg
    assert "Work session" in s.handle("/workstatus")
    assert "stopped" in s.handle("/stopwork").lower()


def test_living_state_refresh(tmp_path):
    from seven.mind.state import LivingState
    path = tmp_path / "living_state.json"
    ls = LivingState(path=path)
    snap = ls.refresh(memory=Memory(tmp_path / "m.db"), brain=None, last_user_ts=None)
    assert "world" in snap and "self" in snap
    assert ls.tick_count >= 1
    assert path.exists()
    text = ls.status_text()
    assert "mode=" in text or "Seven" in text or "intent" in text.lower() or "living" in text.lower()


def test_world_and_self_sense():
    from seven.mind.world import sense_world, world_summary
    from seven.mind.self_model import sense_self, self_summary
    w = sense_world(memory=None, brain=None, last_user_ts=None)
    assert "host" in w and "resources" in w
    s = sense_self(world=w, tools_active=["run_shell"], tools_total=10)
    assert s["state"]["mode"] in ("full", "degraded_no_llm", "conserving", "quiet_hours")
    assert world_summary(w)
    assert self_summary(s)


def test_daemon_helpers(tmp_path, monkeypatch):
    from seven.runtime import daemon as d
    monkeypatch.setattr(d.config, "DATA_DIR", tmp_path)
    d.write_pid()
    assert d.read_pid() == __import__("os").getpid()
    assert "daemon status" in d.daemon_status().lower() or "Seven" in d.daemon_status()
    d.clear_pid()
    assert d.read_pid() is None


def test_freewill_decide_no_goals():
    from seven.agent.loop import Seven
    from seven.mind.freewill import FreeWill
    s = Seven(tool_tier="core")
    s.memory = Memory(__import__("pathlib").Path("nul") if False else __import__("tempfile").mkdtemp() + "/fw.db")
    # use tmp via Memory path
    import tempfile
    from pathlib import Path
    db = Path(tempfile.mkdtemp()) / "fw.db"
    s.memory = Memory(db)
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    s.freewill = FreeWill(s)
    s.living.refresh(memory=s.memory, brain=None, last_user_ts=s.last_user_ts)
    # force ollama ok for decision path
    s.living.world.setdefault("ollama", {})["ok"] = True
    s.living.self_state.setdefault("state", {})["mode"] = "full"
    s.living.self_state.setdefault("state", {})["energy"] = 0.9
    d = s.freewill.decide(idle_min=20)
    assert d.action in ("speak", "invent_goal", "work", "rest", "wait")


def test_prompt_is_companion_not_commands():
    from seven.agent.prompt import build_system_prompt
    p = build_system_prompt(memory_block="x", tool_names=["run_shell"], living_block="y")
    assert "FREE WILL" in p or "free will" in p.lower()
    assert "slash" in p.lower() or "not a menu" in p.lower() or "FREE WILL" in p


def test_beliefs_wm_skills_plans(tmp_path):
    m = Memory(tmp_path / "mind.db")
    bid = m.set_belief("coffee", "good in the morning", 0.8, evidence="said so")
    assert bid
    assert m.list_beliefs()
    m.wm_add("focus: tests", kind="focus", priority=0.9)
    assert m.wm_list()
    m.save_skill("echo_skill", "echo", [{"tool": "run_shell", "args": {"command": "echo skill-ok"}}])
    assert m.get_skill("echo_skill")
    pid = m.create_plan("p", [{"action": "a", "detail": "do a", "done": False}])
    p = m.advance_plan(pid, note="did it")
    assert p and p["status"] == "done"
    m.set_preference("tone", "direct")
    assert m.get_preference("tone") == "direct"
    block = m.context_block()
    assert "Beliefs" in block or "coffee" in block


def test_semantic_memory(tmp_path):
    from seven.memory.vector import SemanticMemory
    m = Memory(tmp_path / "sem.db")
    sm = SemanticMemory(m)
    sm.index("User loves dark mode and rust programming", ref_type="fact")
    sm.index("Seven installed ollama models today", ref_type="note")
    hits = sm.search("rust dark", limit=3)
    assert hits
    text = sm.search_text("ollama")
    assert "ollama" in text.lower() or "Semantic" in text


def test_desktop_and_mind_tools_registered(tmp_path):
    m = Memory(tmp_path / "reg2.db")
    reg = build_default_registry(m, brain=None, tier="full")
    names = set(reg.names())
    for t in (
        "list_windows", "active_window", "open_url", "browser_get",
        "form_belief", "semantic_search", "plan_from_goal", "advance_plan",
        "wm_push", "save_skill", "write_digest",
    ):
        assert t in names, t
    out = reg.execute("form_belief", {"topic": "tests", "stance": "necessary", "confidence": 0.9})
    assert "OK belief" in out
