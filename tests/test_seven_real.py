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
from seven.tools.registry import (
    CORE_TOOL_NAMES,
    Tool,
    ToolRegistry,
    build_default_registry,
    tool_result_ok,
)
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


def test_tool_result_ok_classifies_structured_and_text_failures():
    assert tool_result_ok('{"ok": true, "value": 1}')
    assert tool_result_ok({"ok": True, "value": 1})
    assert tool_result_ok("exit_code=0\nseven-real-ok")
    assert not tool_result_ok({"ok": False, "error": "missing file"})
    assert not tool_result_ok('{"ok": false, "error": "missing file"}')
    assert not tool_result_ok('{"error": "connection refused"}')
    assert not tool_result_ok('{"status": "failed"}')
    assert not tool_result_ok("ERROR: command failed")
    assert not tool_result_ok("exit_code=7")


def test_registry_audits_json_failure_and_shell_outcomes(tmp_path):
    memory = Memory(tmp_path / "tool-truth.db")
    registry = ToolRegistry(memory=memory, tier="full")
    registry.register(Tool(
        name="json_failure",
        description="test only",
        parameters={"type": "object", "properties": {}},
        handler=lambda: '{"ok": false, "error": "missing file"}',
    ))
    registry.register(Tool(
        name="shell_success",
        description="test only",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "exit_code=0\nseven-real-ok",
    ))
    registry.register(Tool(
        name="shell_failure",
        description="test only",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "ERROR: exit_code=7",
    ))

    registry.execute("json_failure")
    registry.execute("shell_success")
    registry.execute("shell_failure")
    rows = list(reversed(memory.recent_audit(3)))
    assert [(row["tool"], row["ok"]) for row in rows] == [
        ("json_failure", 0),
        ("shell_success", 1),
        ("shell_failure", 0),
    ]


def test_real_music_and_ssh_validation_failures_are_audited_failed(tmp_path):
    memory = Memory(tmp_path / "real-tool-failures.db")
    registry = build_default_registry(memory, brain=None, tier="full")

    music_result = registry.execute(
        "play_local_audio",
        {"path": str(tmp_path / "does-not-exist.wav")},
    )
    ssh_result = registry.execute(
        "ssh_run",
        {"host": "invalid;host", "username": "seven", "command": "true"},
    )

    assert not tool_result_ok(music_result)
    assert not tool_result_ok(ssh_result)
    rows = list(reversed(memory.recent_audit(2)))
    assert [(row["tool"], row["ok"]) for row in rows] == [
        ("play_local_audio", 0),
        ("ssh_run", 0),
    ]


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


def test_tool_tier_lean_exposes_cognition_without_removing_tools(tmp_path):
    m = Memory(tmp_path / "lean-tier.db")
    reg = build_default_registry(m, brain=None, tier="lean")
    active = set(reg.names())
    assert {
        "get_system_info",
        "remember_fact",
        "search_memory",
        "save_skill",
        "run_skill",
        "add_goal",
        "submit_goal_evidence",
    } <= active
    assert "run_shell" not in active
    assert "capture_webcam" not in active
    assert len(active) < 20
    assert len(reg.all_names()) > len(active)
    # Tier limits prompt schemas, not the registered/executable capability set.
    out = reg.execute("get_system_info", {})
    assert "os=" in out or "time=" in out


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


def test_sanitize_drops_model_hallucinated_args_for_zero_arg_tool():
    assert sanitize_arguments(
        {"goals": [], "unexpected": "value"},
        properties={},
        required=[],
    ) == {}
    assert sanitize_arguments(
        {"untyped": "preserved"},
        properties=None,
        required=[],
    ) == {"untyped": "preserved"}


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


def test_ollama_normalization_preserves_thinking():
    messages = [{
        "role": "assistant",
        "content": "",
        "thinking": "private reasoning state",
        "tool_calls": [],
    }]
    normalized = Brain._normalize_messages_for_ollama(messages)
    assert normalized[0]["thinking"] == "private reasoning state"


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


def test_memory_compaction_preserves_legacy_history(tmp_path):
    m = Memory(tmp_path / "legacy.db")
    for i in range(20):
        m.add_message(
            "user",
            f"legacy {i}",
            meta={
                "source": "legacy_history",
                "provenance": {"classification": "history_not_fact"},
            },
        )
    for i in range(10):
        m.add_message("user", f"live {i}")
        m.add_message("assistant", f"reply {i}")
    summary = m.compact_history(keep_recent=8)
    assert summary
    messages = m.recent_messages(100)
    assert sum(item["content"].startswith("legacy ") for item in messages) == 20
    assert all(
        fact["source"] != "compaction"
        for fact in m.search_facts("legacy", limit=20)
    )


def test_freewill_rejects_failed_and_unverifiable_goal_proposals(tmp_path):
    from types import SimpleNamespace
    from seven.mind.freewill import FreeWill

    memory = Memory(tmp_path / "freewill.db")

    class FailedBrain:
        def generate(self, *args, **kwargs):
            raise TimeoutError("offline")

    agent = SimpleNamespace(
        memory=memory,
        brain=FailedBrain(),
        living=SimpleNamespace(context_for_prompt=lambda: ""),
    )
    freewill = FreeWill(agent)
    assert freewill._invent_and_maybe_speak() is None
    assert memory.active_goals() == []
    assert memory.recent_events(1)[0]["event_type"] == "autonomy_goal_proposal_failed"
    assert freewill._parse_goal_json('{"title":"x","detail":"y","say":"z"}') is None
    proposal = freewill._parse_goal_json(
        '{"title":"Inspect","detail":"Check a file",'
        '"acceptance_criteria":["file hash recorded"],"say":"I will inspect it."}'
    )
    assert proposal == (
        "Inspect",
        "Check a file",
        ["file hash recorded"],
        "I will inspect it.",
    )


def test_freewill_can_invent_and_persist_goal_without_work_command(tmp_path):
    from types import SimpleNamespace
    from seven.mind.freewill import Decision, FreeWill

    memory = Memory(tmp_path / "freewill-invent.db")

    class GoalBrain:
        def generate(self, *args, **kwargs):
            return (
                '{"title":"Inventory local workspace",'
                '"detail":"Record a bounded inventory of the workspace",'
                '"acceptance_criteria":["inventory note exists","file count recorded"],'
                '"say":"I chose to inventory the local workspace."}'
            )

    actions = []
    first_steps = []
    agent = SimpleNamespace(
        memory=memory,
        brain=GoalBrain(),
        tools=SimpleNamespace(
            execute=lambda name, arguments: '{"ok":true,"projects":[]}'
        ),
        living=SimpleNamespace(
            context_for_prompt=lambda: "local workspace available",
            record_action=lambda action, reflection="": actions.append(
                (action, reflection)
            ),
        ),
        planner=SimpleNamespace(
            create_from_goal=lambda goal_id: None,
            execute_next_step=lambda plan_id: None,
        ),
        autonomy=SimpleNamespace(
            min_work_interval=60,
            run_goal_step=lambda goal_id, reason: first_steps.append(
                (goal_id, reason)
            ),
        ),
    )

    utterance = FreeWill(agent).execute(
        Decision("invent_goal", "scripted Gate 1 proof")
    )

    goals = memory.active_goals()
    assert utterance == "I chose to inventory the local workspace."
    assert len(goals) == 1
    assert goals[0]["title"] == "Inventory local workspace"
    assert memory.search_facts("Self-chosen goal")
    assert actions[0][0].startswith("invent_goal#")
    assert first_steps == [(goals[0]["id"], "freewill")]


def test_mock_brain_tool_round(tmp_path, monkeypatch):
    """Integration: mocked Brain tool_calls → registry executes real tool."""
    from seven.agent import loop as loop_mod

    # Isolate memory path via injected instance after construct
    s = loop_mod.Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "int.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")

    calls = {"n": 0, "thinking_seen": False}

    def fake_chat(messages, tools=None, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "role": "assistant",
                "content": None,
                "thinking": "inspect system before answering",
                "tool_calls": [
                    {"id": "1", "name": "get_system_info", "arguments": {}},
                ],
            }
        calls["thinking_seen"] = any(
            message.get("thinking") == "inspect system before answering"
            for message in messages
        )
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
    assert calls["thinking_seen"] is True


def test_handle_repairs_prompt_echo_without_persisting_it(tmp_path):
    from seven.agent.loop import Seven

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "echo-repair.db")
    prompt = "State the verified result in one short sentence."
    replies = iter((prompt, "The verified result is ready."))
    s.brain.chat = lambda messages, tools=None, **kw: {  # type: ignore
        "role": "assistant",
        "content": next(replies),
        "tool_calls": [],
    }

    assert s.handle(prompt) == "The verified result is ready."
    rows = s.memory.recent_messages(10)
    assert [row["content"] for row in rows] == [
        prompt,
        "The verified result is ready.",
    ]


def test_handle_repairs_internal_markup_after_tool_result(tmp_path):
    from seven.agent.loop import Seven

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "markup-repair.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    replies = iter((
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "goals-1",
                "name": "list_goals",
                "arguments": {},
            }],
        },
        {
            "role": "assistant",
            "content": (
                "<goals>Use list_goals.</goals>"
                "<tool_result>No active goals.</tool_result>"
            ),
            "tool_calls": [],
        },
        {
            "role": "assistant",
            "content": "There are no active goals.",
            "tool_calls": [],
        },
    ))
    s.brain.chat = lambda messages, tools=None, **kw: next(replies)  # type: ignore

    assert s.handle("Check my goals.") == (
        "There are no active goals.\n\n"
        "Verified action results:\n"
        "- list_goals: completed — No active goals."
    )
    assert any(
        row["tool"] == "list_goals" and row["ok"]
        for row in s.memory.recent_audit(5)
    )
    persisted = "\n".join(
        row["content"] for row in s.memory.recent_messages(10)
    )
    assert "<goals>" not in persisted
    assert "<tool_result>" not in persisted


def test_handle_bounds_repeated_invalid_responses(tmp_path):
    from seven.agent.loop import Seven

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "bounded-repair.db")
    calls = {"count": 0}

    def invalid_chat(messages, tools=None, **kw):
        calls["count"] += 1
        return {
            "role": "assistant",
            "content": "<thinking>still planning</thinking>",
            "tool_calls": [],
        }

    s.brain.chat = invalid_chat  # type: ignore
    reply = s.handle("Give me the result.")

    assert calls["count"] == 3
    assert reply == (
        "The local model did not produce a clean final response after two "
        "repair attempts. Please retry."
    )
    persisted = "\n".join(
        row["content"] for row in s.memory.recent_messages(10)
    )
    assert "<thinking>" not in persisted


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
    names = set(reg.all_names())
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
    assert "no successful outcome evidence" in out


def test_autonomy_records_tool_evidence_without_inventing_progress(tmp_path):
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
    assert g["progress"] == 0
    assert "candidate evidence recorded" in out
    notes = s.memory.list_notes(5)
    assert any(n.get("title") == "autonomy" for n in notes)


def test_failed_shell_is_audited_failed_and_does_not_advance_goal(tmp_path):
    from seven.agent.loop import Seven
    from seven.agent.autonomy import AutonomyEngine

    s = Seven(tool_tier="core")
    s.memory = Memory(tmp_path / "auto-fail.db")
    s.tools = build_default_registry(s.memory, brain=None, tier="core")
    s.autonomy = AutonomyEngine(s)
    gid = s.memory.add_goal("Fail safely", "do not count a failed command")
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
                    "arguments": {"command": "exit /b 7"},
                }],
            }
        return {"role": "assistant", "content": "The command failed.", "tool_calls": []}

    s.brain.chat = fake_chat  # type: ignore
    out = s.autonomy.run_goal_step(goal_id=gid, reason="manual")
    assert s.memory.get_goal(gid)["progress"] == 0
    assert "failed=1" in out
    audit = s.memory.recent_audit(1)[0]
    assert audit["tool"] == "run_shell"
    assert audit["ok"] == 0
    assert audit["result_preview"].startswith("ERROR: exit_code=7")


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


def test_compact_prompt_is_honest_persistent_and_bounded(monkeypatch):
    from seven import config
    from seven.agent.prompt import build_system_prompt

    monkeypatch.setattr(config, "PROMPT_MEMORY_CHARS", 500)
    monkeypatch.setattr(config, "PROMPT_LIVING_CHARS", 300)
    p = build_system_prompt(
        memory_block="memory " * 2000,
        tool_names=["run_shell", "list_goals"],
        living_block="living " * 2000,
        profile="compact",
    )

    assert "You are Seven" in p
    assert "durable memory" in p.lower()
    assert "auditable evidence" in p
    assert "subjective consciousness" in p
    assert "list_tools" in p and "describe_tool" in p
    assert "SOUL.md" in p
    assert "get_system_info" in p
    assert "continues in durable storage" in p
    assert len(p) < 4000


def test_bounded_living_state_preserves_self_and_world(tmp_path):
    from seven.mind.state import LivingState

    living = LivingState(tmp_path / "living.json")
    living.self_state = {
        "identity": {"name": "Seven", "version": "4.4.4"},
        "state": {"mode": "full", "energy": 0.9},
        "intent": "continue the conversation",
    }
    living.world = {
        "host": {
            "hostname": "peanut.dedicated.co.za",
            "user": "seven",
            "os": "Linux",
        },
        "resources": {"ram_used_pct": 50, "cpu_pct": 10, "disk_free_gb": 100},
    }

    context = living.context_for_prompt(max_chars=180)

    assert "### Self" in context and "Seven" in context
    assert "### World" in context and "peanut" in context
    assert len(context) <= 180


def test_compact_prompt_rejects_generic_customer_service_filler():
    from seven.agent.loop import Seven

    assert Seven._invalid_final_response(
        "Hi! How can I assist you today?", "hi"
    )
    assert Seven._invalid_final_response(
        "None of the tools can be used to check system resources.", "resources"
    )
    assert Seven._invalid_final_response(
        "I'm here to help. Let me check the resources.", "resources"
    )
    assert Seven._invalid_final_response(
        "Hi Seven, I'm here and active.", "Hi Seven. How are you?"
    )
    assert Seven._invalid_final_response(
        "Feel free to ask if you have questions.", "what can you do?"
    )
    assert not Seven._invalid_final_response(
        "I'm Seven. I'm running locally and ready to continue our conversation.",
        "hi",
    )
    assert Seven._sanitize_final_response(
        "CPU is 12% and RAM is 48%. Let me know if I can help with anything!"
    ) == "CPU is 12% and RAM is 48%."
    assert Seven._sanitize_final_response(
        "I'm Seven and I'm running on Peanut. Let me know if I can"
    ) == "I'm Seven and I'm running on Peanut."
    assert Seven._sanitize_final_response(
        "I'm Seven, active on Peanut. Let me know if there's anything I can assist with!"
    ) == "I'm Seven, active on Peanut."
    assert not Seven._history_message_is_usable(
        "Internal error: Ollama request timed out"
    )
    assert not Seven._history_message_is_usable(
        "Hi! How can I assist you today?"
    )
    assert Seven._history_message_is_usable(
        "I'm Seven, running on Peanut with a full-energy state."
    )


def test_model_tool_result_bound_does_not_change_full_result(monkeypatch):
    from seven import config
    from seven.agent.loop import Seven

    monkeypatch.setattr(config, "MODEL_TOOL_RESULT_CHARS", 200)
    full = "evidence-" * 100

    bounded = Seven._model_tool_result(full)

    assert full.startswith(bounded.splitlines()[0])
    assert len(bounded) < len(full)
    assert "full result retained in audit" in bounded


def test_prioritized_memory_context_is_bounded_and_keeps_provenance(tmp_path):
    m = Memory(tmp_path / "prompt.db")
    goal_id = m.add_goal("Prove the real deployment " + "g" * 200)
    m.remember(
        "remembered claim " + "f" * 500,
        key="origin",
        source="test-source",
    )
    m.wm_add("active focus " + "w" * 300, kind="focus", priority=1.0)

    block = m.context_block(max_chars=1000)

    assert len(block) < 1060
    assert f"[{goal_id}]" in block
    assert "Working memory" in block
    assert "source=test-source" in block


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
        "list_windows", "active_window", "open_url", "open_app", "browser_get",
        "form_belief", "semantic_search", "plan_from_goal", "advance_plan",
        "wm_push", "save_skill", "write_digest",
    ):
        assert t in names, t
    out = reg.execute("form_belief", {"topic": "tests", "stance": "necessary", "confidence": 0.9})
    assert "OK belief" in out
