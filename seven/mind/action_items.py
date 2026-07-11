"""Local, deterministic conversation-to-action candidate extraction."""
from __future__ import annotations

import re

_PATTERNS = (
    re.compile(r"(?i)(?:^|[.!?]\s+)(?:todo\s*[:\-]|remind me to)\s+(.+?)(?=$|[.!?](?:\s|$))"),
    re.compile(r"(?i)(?:^|[.!?]\s+)(?:i|we)\s+(?:need|have)\s+to\s+(.+?)(?=$|[.!?](?:\s|$))"),
)


def extract_action_items(text: str, min_length: int = 4, limit: int = 5) -> list[str]:
    """Extract only explicit commitments; never calls or sends text to an LLM."""
    candidates: list[tuple[int, str]] = []
    for pattern in _PATTERNS:
        for match in pattern.finditer(text or ""):
            candidates.append((match.start(1), match.group(1)))
    candidates.sort(key=lambda candidate: candidate[0])
    found: list[str] = []
    seen: set[str] = set()
    for _, raw in candidates:
        item = re.sub(r"\s+", " ", raw).strip(" \t\r\n,;:-")
        item = re.sub(r"(?i)\s+(?:please|thanks|thank you)$", "", item).strip()
        key = item.casefold()
        if len(item) >= min_length and key not in seen:
            seen.add(key)
            found.append(item)
            if len(found) >= limit:
                return found
    return found


def capture(memory, message_id: int, text: str) -> list[int]:
    ids: list[int] = []
    for item in extract_action_items(text):
        item_id = memory.add_action_item(item, source_message_id=message_id)
        if item_id is not None:
            ids.append(item_id)
    return ids
