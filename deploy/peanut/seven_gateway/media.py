from __future__ import annotations

import struct


def validate_jpeg(data: bytes, limit: int) -> dict:
    if not data or len(data) > limit:
        raise ValueError("jpeg_size")
    if len(data) < 4 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise ValueError("jpeg_format")
    width = height = None
    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if length < 2 or offset + length > len(data):
            raise ValueError("jpeg_structure")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7):
            if length < 7:
                raise ValueError("jpeg_structure")
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            break
        offset += length
    if not width or not height or width > 8192 or height > 8192:
        raise ValueError("jpeg_dimensions")
    return {"media": "jpeg", "bytes": len(data), "width": width, "height": height}


def validate_audio(data: bytes, content_type: str, limit: int) -> dict:
    if not data or len(data) > limit:
        raise ValueError("audio_size")
    expected = {
        "audio/wav": data.startswith(b"RIFF") and data[8:12] == b"WAVE",
        "audio/x-wav": data.startswith(b"RIFF") and data[8:12] == b"WAVE",
        "audio/ogg": data.startswith(b"OggS"),
        "audio/webm": data.startswith(b"\x1aE\xdf\xa3"),
        "audio/mp4": len(data) >= 12 and data[4:8] == b"ftyp",
    }
    if content_type not in expected or not expected[content_type]:
        raise ValueError("audio_format")
    return {"media": content_type, "bytes": len(data)}

