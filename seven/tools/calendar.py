"""Durable local RFC 5545 calendar tools.

The local calendar deliberately needs no cloud account or credential.  It
stores one portable ``calendar.ics`` file under Seven's data directory unless
``SEVEN_CALENDAR_PATH`` selects another owner-controlled file.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

MAX_EVENTS = 10_000
MAX_TEXT = 8_000
_UID = re.compile(r"^[A-Za-z0-9._@+-]{1,200}$")


def _path() -> Path:
    configured = os.getenv("SEVEN_CALENDAR_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    from seven import config

    return (config.DATA_DIR / "calendar.ics").resolve()


def _parse_time(value: str, label: str) -> datetime:
    raw = str(value or "").strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 date/time") from exc
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _unescape(value: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value):
            code = value[index + 1]
            output.append("\n" if code in {"n", "N"} else code)
            index += 2
            continue
        output.append(value[index])
        index += 1
    return "".join(output)


def _read_events(path: Path | None = None) -> list[dict]:
    source = path or _path()
    if not source.exists():
        return []
    text = source.read_text(encoding="utf-8-sig")
    events: list[dict] = []
    current: dict[str, str] | None = None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT" and current is not None:
            if current.get("UID") and current.get("DTSTART") and current.get("DTEND"):
                events.append(
                    {
                        "uid": current["UID"],
                        "title": _unescape(current.get("SUMMARY", "")),
                        "start": _ics_to_iso(current["DTSTART"]),
                        "end": _ics_to_iso(current["DTEND"]),
                        "description": _unescape(current.get("DESCRIPTION", "")),
                        "location": _unescape(current.get("LOCATION", "")),
                    }
                )
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        current[key.split(";", 1)[0].upper()] = value
    if len(events) > MAX_EVENTS:
        raise ValueError(f"calendar exceeds the {MAX_EVENTS}-event safety limit")
    return events


def _ics_to_iso(value: str) -> str:
    parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _write_events(events: list[dict], path: Path | None = None) -> None:
    destination = path or _path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    now = _stamp(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Seven AI//Local Calendar//EN",
        "CALSCALE:GREGORIAN",
    ]
    for event in sorted(events, key=lambda item: item["start"]):
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['uid']}",
                f"DTSTAMP:{now}",
                f"DTSTART:{_stamp(_parse_time(event['start'], 'start'))}",
                f"DTEND:{_stamp(_parse_time(event['end'], 'end'))}",
                f"SUMMARY:{_escape(event['title'])}",
                f"DESCRIPTION:{_escape(event.get('description', ''))}",
                f"LOCATION:{_escape(event.get('location', ''))}",
                "END:VEVENT",
            ]
        )
    lines.extend(["END:VCALENDAR", ""])
    payload = "\r\n".join(lines).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".calendar-", suffix=".tmp", dir=str(destination.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def calendar_status() -> str:
    path = _path()
    try:
        events = _read_events(path)
        return json.dumps(
            {
                "ok": True,
                "path": str(path),
                "exists": path.exists(),
                "events": len(events),
                "format": "RFC5545",
                "cloud_sync": False,
            },
            indent=2,
        )
    except (OSError, ValueError) as exc:
        return json.dumps({"ok": False, "path": str(path), "error": str(exc)})


def add_calendar_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    uid: str = "",
) -> str:
    title = str(title or "").strip()
    if not title or len(title) > 500:
        return "ERROR: title must contain 1-500 characters"
    if len(description or "") > MAX_TEXT or len(location or "") > 500:
        return "ERROR: description or location exceeds the calendar limits"
    try:
        start_at = _parse_time(start, "start")
        end_at = _parse_time(end, "end")
        if end_at <= start_at:
            return "ERROR: end must be after start"
        uid = str(uid or "").strip() or f"{uuid4()}@seven.local"
        if not _UID.fullmatch(uid):
            return "ERROR: uid contains unsupported characters"
        events = _read_events()
        if any(event["uid"] == uid for event in events):
            return f"ERROR: calendar event uid already exists: {uid}"
        if len(events) >= MAX_EVENTS:
            return f"ERROR: calendar reached the {MAX_EVENTS}-event safety limit"
        event = {
            "uid": uid,
            "title": title,
            "start": start_at.isoformat().replace("+00:00", "Z"),
            "end": end_at.isoformat().replace("+00:00", "Z"),
            "description": str(description or ""),
            "location": str(location or ""),
        }
        events.append(event)
        _write_events(events)
        return json.dumps({"ok": True, "event": event, "path": str(_path())}, indent=2)
    except (OSError, ValueError) as exc:
        return f"ERROR adding calendar event: {exc}"


def list_calendar_events(
    start: str = "",
    end: str = "",
    limit: int = 50,
) -> str:
    try:
        start_at = _parse_time(start, "start") if str(start or "").strip() else None
        end_at = _parse_time(end, "end") if str(end or "").strip() else None
        limit = max(1, min(int(limit), 500))
        events = _read_events()
        selected = []
        for event in events:
            event_start = _parse_time(event["start"], "event start")
            event_end = _parse_time(event["end"], "event end")
            if start_at and event_end < start_at:
                continue
            if end_at and event_start > end_at:
                continue
            selected.append(event)
        return json.dumps(
            {
                "ok": True,
                "path": str(_path()),
                "count": len(selected[:limit]),
                "truncated": len(selected) > limit,
                "events": selected[:limit],
            },
            indent=2,
        )
    except (OSError, ValueError) as exc:
        return f"ERROR listing calendar events: {exc}"


def remove_calendar_event(uid: str) -> str:
    uid = str(uid or "").strip()
    if not _UID.fullmatch(uid):
        return "ERROR: valid calendar event uid required"
    try:
        events = _read_events()
        kept = [event for event in events if event["uid"] != uid]
        if len(kept) == len(events):
            return f"ERROR: calendar event not found: {uid}"
        _write_events(kept)
        return json.dumps({"ok": True, "removed": uid, "remaining": len(kept)})
    except (OSError, ValueError) as exc:
        return f"ERROR removing calendar event: {exc}"


def register(reg) -> None:
    from seven.tools.registry import Tool

    reg.register(
        Tool(
            "calendar_status",
            "Report Seven's credential-free local RFC5545 calendar status.",
            {"type": "object", "properties": {}},
            calendar_status,
        )
    )
    reg.register(
        Tool(
            "add_calendar_event",
            "Add a durable event to Seven's local portable calendar.",
            {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start": {"type": "string", "description": "ISO-8601 date/time"},
                    "end": {"type": "string", "description": "ISO-8601 date/time"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                    "uid": {"type": "string"},
                },
                "required": ["title", "start", "end"],
            },
            add_calendar_event,
        )
    )
    reg.register(
        Tool(
            "list_calendar_events",
            "List events from Seven's local calendar, optionally within an ISO-8601 range.",
            {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                },
            },
            list_calendar_events,
        )
    )
    reg.register(
        Tool(
            "remove_calendar_event",
            "Remove one local calendar event by its exact UID.",
            {
                "type": "object",
                "properties": {"uid": {"type": "string"}},
                "required": ["uid"],
            },
            remove_calendar_event,
        )
    )
