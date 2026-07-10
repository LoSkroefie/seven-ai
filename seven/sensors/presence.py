"""
Lightweight presence detection via OpenCV Haar face cascade.
Not OpenSeeFace (landmarks) — that can be layered later.
Answers: is a person visible in front of the camera?
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from seven import config
from seven.sensors.camera import capture_frame

logger = logging.getLogger("seven.presence")


def check_presence(
    camera_index: Optional[int] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Detect faces in a fresh webcam frame or an existing image.
    Returns structured dict (also stringified by tools).
    """
    try:
        import cv2
    except ImportError:
        return {"ok": False, "error": "opencv-python not installed", "present": False}

    path: Optional[Path] = None
    if image_path:
        path = Path(image_path).expanduser()
        if not path.exists():
            return {"ok": False, "error": f"image not found: {path}", "present": False}
    else:
        tmp = config.DATA_DIR / "presence.jpg"
        ok, msg = capture_frame(path=str(tmp), camera_index=camera_index)
        if not ok:
            return {"ok": False, "error": msg, "present": False}
        path = tmp

    img = cv2.imread(str(path))
    if img is None:
        return {"ok": False, "error": "failed to read image", "present": False}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        return {"ok": False, "error": "haar cascade missing", "present": False}

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
    boxes = [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in faces]

    return {
        "ok": True,
        "present": len(boxes) > 0,
        "face_count": len(boxes),
        "faces": boxes,
        "image": str(path.resolve()),
        "backend": "opencv_haar",
        "note": "Lightweight presence only. OpenSeeFace landmarks not wired yet.",
    }
