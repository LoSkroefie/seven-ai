"""Evidence-based post-turn reflection.

Reflections are lessons derived from observable interaction and tool outcomes.
No random introspection, dream prose, or simulated growth is generated.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from seven.memory.store import Memory


class ReflectionEngine:
    def __init__(self, memory: Memory):
        self.memory = memory

    def reflect_on_turn(
        self,
        *,
        user_text: str,
        user_mood: str,
        response: str,
        response_ok: bool,
        tool_trace: Optional[Iterable[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        tools = [str(item)[:300] for item in (tool_trace or [])]
        lowered = (response or "").casefold()
        evidence: List[Any] = [
            {"user_mood": user_mood},
            {"response_ok": response_ok},
            {"tool_count": len(tools)},
        ]
        if tools:
            evidence.append({"tools": tools[:6]})

        kind = ""
        observation = ""
        lesson = ""
        confidence = 0.0

        if not response_ok:
            kind = "failure"
            observation = "The turn ended in a model, tool, or response failure."
            lesson = (
                "Keep the failure visible, preserve the evidence, and use a "
                "deterministic tool or smaller verified context before reassuring "
                "the owner."
            )
            confidence = 0.96
        elif user_mood == "frustrated":
            kind = "relationship"
            observation = "The owner expressed strong frustration during this turn."
            lesson = (
                "Lead with the verified outcome, avoid generic reassurance, and "
                "keep claims narrower than the evidence."
            )
            confidence = 0.92
        elif user_mood in {"sad", "worried"}:
            kind = "relationship"
            observation = f"The owner appeared {user_mood}."
            lesson = (
                "Acknowledge the concern directly, remain grounded, and take a "
                "concrete action when one is available."
            )
            confidence = 0.85
        elif tools:
            failed_tool = any(
                "error" in item.casefold()
                or "timed out" in item.casefold()
                or '"ok": false' in item.casefold()
                for item in tools
            )
            if failed_tool:
                kind = "tool_outcome"
                observation = "At least one audited tool result reported failure."
                lesson = (
                    "Do not summarize the overall task as successful until the "
                    "failed evidence is resolved or explicitly scoped out."
                )
                confidence = 0.98
            else:
                kind = "tool_outcome"
                observation = f"The turn used {len(tools)} audited tool result(s)."
                lesson = (
                    "Retain the concise evidence trail and report only the outcome "
                    "those tool results actually prove."
                )
                confidence = 0.9
        elif lowered.startswith(("brain error:", "internal error:")):
            kind = "failure"
            observation = "The response exposed an internal failure to the owner."
            lesson = "Diagnose the failing dependency before attempting another claim."
            confidence = 0.99

        if not kind:
            return None
        reflection_id = self.memory.add_reflection(
            kind,
            observation,
            lesson,
            confidence=confidence,
            evidence=evidence,
        )
        return {
            "id": reflection_id,
            "kind": kind,
            "observation": observation,
            "lesson": lesson,
            "confidence": confidence,
        }

    def context_for_prompt(self, max_chars: int = 420) -> str:
        rows = self.memory.recent_reflections(3)
        if not rows:
            return "No evidence-backed reflection recorded yet."
        text = " | ".join(
            f"{row['kind']}: {row['lesson']}"
            for row in rows
        )
        return text[: max(120, int(max_chars))]

    def status(self) -> Dict[str, Any]:
        rows = self.memory.recent_reflections(10)
        return {
            "count_sample": len(rows),
            "latest": rows[0] if rows else None,
        }
