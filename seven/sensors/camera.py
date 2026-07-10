"""Webcam capture helpers."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from seven import config

logger = logging.getLogger("seven.camera")


def list_cameras(max_index: int = 6) -> List[dict]:
    """Probe camera indices 0..max_index-1."""
    try:
        import cv2
    except ImportError:
        return [{"error": "opencv-python not installed"}]

    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) if _is_windows() else cv2.VideoCapture(i)
        if not cap.isOpened():
            cap.release()
            continue
        ok, frame = cap.read()
        w = h = 0
        if ok and frame is not None:
            h, w = frame.shape[:2]
        cap.release()
        found.append({"index": i, "ok": bool(ok), "width": w, "height": h})
    return found


def _is_windows() -> bool:
    import platform
    return platform.system() == "Windows"


def capture_frame(
    path: Optional[str] = None,
    camera_index: Optional[int] = None,
    warmup_frames: int = 5,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Capture one frame. Returns (ok, message_or_path).
    Warms up a few frames so exposure settles.
    """
    try:
        import cv2
    except ImportError:
        return False, "ERROR: opencv-python not installed"

    idx = config.CAMERA_INDEX if camera_index is None else int(camera_index)
    out = Path(path) if path else (config.DATA_DIR / "webcam.jpg")
    out = out.expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    # CAP_DSHOW avoids long hangs on some Windows webcams
    if _is_windows():
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(idx)

    if not cap.isOpened():
        return False, f"ERROR: cannot open camera index {idx}. Try list_cameras / SEVEN_CAMERA_INDEX."

    try:
        if width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        if height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))

        frame = None
        ok = False
        for _ in range(max(1, warmup_frames)):
            ok, frame = cap.read()
        if not ok or frame is None:
            return False, "ERROR: failed to read frame from camera"

        # JPEG quality
        cv2.imwrite(str(out), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        h, w = frame.shape[:2]
        return True, f"OK webcam index={idx} size={w}x{h} path={out.resolve()}"
    finally:
        cap.release()
