"""
Vision tools: webcam, screenshot, image analysis via Ollama vision model.
VRAM-aware: images are downscaled before send; vision model keep_alive is short.
"""
from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
from typing import Optional

from seven import config
from seven.tools.sanitize import is_blank

logger = logging.getLogger("seven.vision")

_brain = None

# Max edge length for vision model (saves VRAM / bandwidth on 8GB cards)
MAX_IMAGE_EDGE = int(getattr(config, "VISION_MAX_EDGE", 1280) or 1280)
JPEG_QUALITY = int(getattr(config, "VISION_JPEG_QUALITY", 75) or 75)


def set_brain(brain):
    global _brain
    _brain = brain


def _prepare_image_b64(path: str) -> str:
    """Load image, downscale if huge, return JPEG base64."""
    p = Path(path).expanduser()
    data = p.read_bytes()
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        w, h = img.size
        edge = max(w, h)
        if edge > MAX_IMAGE_EDGE:
            scale = MAX_IMAGE_EDGE / float(edge)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        logger.warning("PIL resize failed (%s); sending raw bytes", e)
        return base64.b64encode(data).decode("ascii")


def capture_webcam(
    path: Optional[str] = None,
    camera_index: Optional[int] = None,
) -> str:
    from seven.sensors.camera import capture_frame
    if is_blank(path):
        path = None
    if is_blank(camera_index):
        camera_index = None
    else:
        try:
            camera_index = int(camera_index)
        except (TypeError, ValueError):
            camera_index = None
    ok, msg = capture_frame(path=path, camera_index=camera_index)
    return msg


def list_cameras() -> str:
    from seven.sensors.camera import list_cameras as _list
    cams = _list()
    if not cams:
        return "No cameras detected (or all probes failed)."
    return json.dumps(cams, indent=2)


def analyze_image(path: str, prompt: Optional[str] = None) -> str:
    if _brain is None:
        return "ERROR: vision brain not wired"
    if is_blank(path):
        return "ERROR: path is required"
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: image not found: {p}"
    if is_blank(prompt):
        prompt = "Describe what you see in detail. Note text, UI, people, and anything actionable."
    try:
        b64 = _prepare_image_b64(str(p))
        result = _brain.vision(
            str(prompt),
            b64,
            system=(
                "You are Seven's vision system on a local machine. "
                "Be precise, structured, and useful. Mention readable text when present."
            ),
        )
        if not result:
            return (
                "(empty vision response) — is Ollama vision model available? "
                f"Try: ollama pull {config.OLLAMA_VISION_MODEL}  |  see docs/VISION.md"
            )
        return result
    except Exception as e:
        return (
            f"ERROR vision: {e}\n"
            "VRAM tip on 8GB: unload other models (ollama stop), then retry. docs/VISION.md"
        )


def see_screen(prompt: Optional[str] = None) -> str:
    """Screenshot + vision model analysis."""
    if is_blank(prompt):
        prompt = (
            "Describe the screen contents. List open apps/windows if visible, "
            "main UI elements, and any text the user might care about."
        )
    path = config.DATA_DIR / "vision_screen.jpg"
    try:
        import pyautogui
        img = pyautogui.screenshot()
        img = img.convert("RGB")
        # Downscale huge 4K screens before save
        w, h = img.size
        edge = max(w, h)
        if edge > MAX_IMAGE_EDGE:
            scale = MAX_IMAGE_EDGE / float(edge)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(path), quality=JPEG_QUALITY)
    except Exception as e:
        return f"ERROR capturing screen: {e}"
    header = f"[screenshot saved {path}]\n"
    return header + analyze_image(str(path), str(prompt))


def see_webcam(prompt: Optional[str] = None, camera_index: Optional[int] = None) -> str:
    """Capture webcam then analyze with vision model."""
    if is_blank(prompt):
        prompt = "Describe the camera view. Is a person present? What is in the scene?"
    path = str(config.DATA_DIR / "vision_webcam.jpg")
    cap = capture_webcam(path=path, camera_index=camera_index)
    if cap.startswith("ERROR"):
        return cap
    return cap + "\n" + analyze_image(path, str(prompt))


def check_presence(camera_index: Optional[int] = None) -> str:
    """Fast local face presence (OpenCV Haar) — no LLM, no heavy VRAM."""
    from seven.sensors.presence import check_presence as _cp
    if is_blank(camera_index):
        camera_index = None
    else:
        try:
            camera_index = int(camera_index)
        except (TypeError, ValueError):
            camera_index = None
    result = _cp(camera_index=camera_index)
    return json.dumps(result, indent=2)


def register(reg, brain=None):
    from seven.tools.registry import Tool
    if brain is not None:
        set_brain(brain)

    reg.register(Tool(
        name="list_cameras",
        description="List available webcam indices and resolutions.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_cameras(),
        tier="core",
    ))
    reg.register(Tool(
        name="capture_webcam",
        description="Capture a frame from the webcam to a JPEG file. Returns path.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "camera_index": {"type": "integer"},
            },
        },
        handler=capture_webcam,
        tier="core",
    ))
    reg.register(Tool(
        name="analyze_image",
        description=(
            "Analyze an image file with the local vision model (Ollama llama3.2-vision). "
            "May swap VRAM on 8GB GPUs — first call can be slow."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "prompt": {"type": "string"},
            },
            "required": ["path"],
        },
        handler=analyze_image,
        tier="core",
    ))
    reg.register(Tool(
        name="see_screen",
        description=(
            "Screenshot the desktop and analyze with the vision model. "
            "VRAM-heavy on first use of vision model."
        ),
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
            },
        },
        handler=see_screen,
        tier="core",
    ))
    reg.register(Tool(
        name="see_webcam",
        description="Capture webcam and analyze with the vision model.",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "camera_index": {"type": "integer"},
            },
        },
        handler=see_webcam,
        tier="core",
    ))
    reg.register(Tool(
        name="check_presence",
        description=(
            "Fast local check if a person/face is in front of the webcam "
            "(OpenCV Haar — no LLM). Good for 'are you there?' without VRAM swap."
        ),
        parameters={
            "type": "object",
            "properties": {
                "camera_index": {"type": "integer"},
            },
        },
        handler=check_presence,
        tier="core",
    ))
