"""Learn preferences from natural conversation (no slash commands)."""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.preferences")

# Lightweight patterns — LLM can also set via tools
_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:call me|my name is|i'm|i am)\s+([A-Z][a-zA-Z]{1,20})\b", re.I), "user.name"),
    (re.compile(r"\bi (?:prefer|like|love)\s+(.{3,60}?)(?:\.|$)", re.I), "user.likes"),
    (re.compile(r"\bi (?:hate|dislike|don't like|do not like)\s+(.{3,60}?)(?:\.|$)", re.I), "user.dislikes"),
    (re.compile(r"\b(?:never|don't ever|do not)\s+(.{3,60}?)(?:\.|$)", re.I), "user.never"),
    (re.compile(r"\b(?:always)\s+(.{3,60}?)(?:\.|$)", re.I), "user.always"),
]


def learn_from_utterance(agent: "Seven", text: str) -> List[str]:
    learned = []
    text = (text or "").strip()
    if len(text) < 4:
        return learned
    for pat, key in _PATTERNS:
        m = pat.search(text)
        if m:
            val = m.group(1).strip()
            agent.memory.set_preference(key, val)
            agent.memory.remember(f"{key}={val}", key=key, source="preference")
            learned.append(f"{key}={val}")
    # corrections
    low = text.lower()
    if low.startswith("no,") or "actually" in low or "i meant" in low:
        agent.memory.wm_add(f"Correction: {text[:160]}", kind="correction", priority=0.85)
        learned.append("correction_noted")
    return learned
