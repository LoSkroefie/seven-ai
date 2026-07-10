"""
Sanitize tool arguments from LLMs.
Models often pass "", "null", "None", wrong types, or stringified numbers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in ("", "null", "None", "undefined", "nil"):
        return True
    return False


def coerce_bool(value: Any, default: bool = False) -> bool:
    if is_blank(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def coerce_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if is_blank(value):
        return default
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if is_blank(value):
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def coerce_str(value: Any, default: Optional[str] = None) -> Optional[str]:
    if is_blank(value):
        return default
    return str(value)


def sanitize_arguments(
    arguments: Optional[Dict[str, Any]],
    properties: Optional[Dict[str, Any]] = None,
    required: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Clean kwargs for a tool handler.
    - Drop blank optional values
    - Coerce types from JSON schema when present
    - Keep required keys even if blank (handler may error clearly)
    """
    arguments = dict(arguments or {})
    properties = properties or {}
    required = list(required or [])
    out: Dict[str, Any] = {}

    keys = set(arguments.keys())
    if properties:
        keys = keys & set(properties.keys())

    for key in keys:
        raw = arguments.get(key)
        schema = properties.get(key) or {}
        typ = schema.get("type")
        is_req = key in required

        if is_blank(raw):
            if is_req:
                # keep empty string so handler can report missing
                out[key] = "" if typ == "string" else raw
            # else drop optional blank
            continue

        if typ == "integer":
            v = coerce_int(raw)
            if v is not None:
                out[key] = v
            elif is_req:
                out[key] = raw
        elif typ == "number":
            v = coerce_float(raw)
            if v is not None:
                out[key] = v
            elif is_req:
                out[key] = raw
        elif typ == "boolean":
            out[key] = coerce_bool(raw)
        elif typ == "string":
            out[key] = coerce_str(raw, "")
        elif typ == "array":
            if isinstance(raw, list):
                out[key] = raw
            elif isinstance(raw, str) and raw.strip():
                # comma-separated fallback
                out[key] = [p.strip() for p in raw.split(",") if p.strip()]
            elif is_req:
                out[key] = raw
        elif typ == "object":
            if isinstance(raw, dict):
                out[key] = raw
            elif is_req:
                out[key] = raw
        else:
            # unknown schema type — pass through non-blank
            out[key] = raw

    return out
