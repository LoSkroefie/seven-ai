from seven import config
from seven.memory.store import Memory
from seven.tools.registry import build_default_registry
from seven.tools import screen, vision


def test_capture_mode_off_removes_capture_tools_and_blocks_direct_calls(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(config, "ENABLE_CAMERA", False)
    monkeypatch.setattr(config, "ENABLE_SCREEN", False)
    registry = build_default_registry(Memory(tmp_path / "off.db"), tier="full")

    disabled = {
        "screenshot",
        "list_cameras",
        "capture_webcam",
        "see_screen",
        "see_webcam",
        "check_presence",
    }
    assert disabled <= set(registry.all_names())
    assert disabled.isdisjoint(registry.names())
    assert registry.execute("capture_webcam").startswith(
        "ERROR: tool 'capture_webcam' is disabled"
    )
    assert screen.screenshot().startswith("ERROR: screen capture is disabled")
    assert vision.capture_webcam().startswith("ERROR: webcam capture is disabled")
    assert vision.see_screen().startswith("ERROR: screen capture is disabled")


def test_capture_mode_both_registers_screen_and_webcam_tools(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ENABLE_CAMERA", True)
    monkeypatch.setattr(config, "ENABLE_SCREEN", True)
    registry = build_default_registry(Memory(tmp_path / "both.db"), tier="full")

    assert {
        "screenshot",
        "list_cameras",
        "capture_webcam",
        "see_screen",
        "see_webcam",
        "check_presence",
    } <= set(registry.names())
