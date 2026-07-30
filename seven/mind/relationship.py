"""Durable owner relationship built from real interactions."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional

from seven import config
from seven.memory.store import Memory


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class RelationshipMind:
    def __init__(
        self,
        memory: Memory,
        *,
        user_key: str = "owner",
        display_name: Optional[str] = None,
    ):
        self.memory = memory
        self.user_key = user_key
        self.display_name = display_name or config.USER_NAME or "User"
        self.state = memory.get_relationship(user_key, self.display_name)

    def observe_turn(
        self,
        *,
        user_text: str,
        user_mood: str,
        response_ok: bool,
        tool_count: int = 0,
    ) -> Dict[str, Any]:
        state = dict(self.state)
        count = int(state.get("interaction_count") or 0) + 1
        state["interaction_count"] = count
        state["display_name"] = self.display_name
        state["familiarity"] = _clip(
            float(state.get("familiarity") or 0) + (0.012 if count <= 25 else 0.003)
        )
        state["last_user_mood"] = user_mood
        state["last_interaction_at"] = datetime.now(timezone.utc).isoformat()

        positive = user_mood == "positive"
        difficult = user_mood in {"frustrated", "sad", "worried"}
        if positive:
            state["positive_interactions"] = (
                int(state.get("positive_interactions") or 0) + 1
            )
        if difficult:
            state["difficult_interactions"] = (
                int(state.get("difficult_interactions") or 0) + 1
            )

        trust_delta = 0.002
        rapport_delta = 0.003
        lowered = user_text.casefold()
        if response_ok:
            trust_delta += 0.004 + min(0.008, max(0, tool_count) * 0.002)
            rapport_delta += 0.004
        else:
            trust_delta -= 0.012
            rapport_delta -= 0.006
        if positive:
            trust_delta += 0.004
            rapport_delta += 0.012
        if any(word in lowered for word in ("trust", "believe", "understanding")):
            trust_delta += 0.012
        if difficult:
            # Frustration is a reason to pay attention, not punish the owner.
            rapport_delta += 0.002 if response_ok else -0.004

        state["trust"] = _clip(float(state.get("trust") or 0.5) + trust_delta)
        state["rapport"] = _clip(float(state.get("rapport") or 0.3) + rapport_delta)

        experience = self._shared_experience(user_text, response_ok)
        shared = list(state.get("shared_experiences") or [])
        if experience and not any(item.get("summary") == experience for item in shared):
            shared.append(
                {
                    "summary": experience,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        state["shared_experiences"] = shared[-20:]
        self.memory.save_relationship(state)
        self.state = self.memory.get_relationship(self.user_key, self.display_name)
        return dict(self.state)

    @staticmethod
    def _shared_experience(text: str, response_ok: bool) -> str:
        if not response_ok:
            return ""
        normalized = re.sub(r"\s+", " ", (text or "").strip())
        lowered = normalized.casefold()
        significant = (
            "published",
            "deployed",
            "we did it",
            "it works",
            "finished",
            "new project",
            "remember this",
        )
        if any(cue in lowered for cue in significant):
            return normalized[:240]
        return ""

    def depth(self) -> str:
        familiarity = float(self.state.get("familiarity") or 0)
        count = int(self.state.get("interaction_count") or 0)
        if count >= 250 and familiarity >= 0.8:
            return "deeply established"
        if count >= 75 and familiarity >= 0.5:
            return "established"
        if count >= 20:
            return "developing"
        return "new"

    def context_for_prompt(self, max_chars: int = 380) -> str:
        state = self.state
        shared: List[Dict[str, Any]] = list(
            state.get("shared_experiences") or []
        )
        latest = shared[-1]["summary"] if shared else "none recorded"
        value = (
            f"owner={state.get('display_name')} relationship={self.depth()} "
            f"interactions={state.get('interaction_count')} "
            f"trust={float(state.get('trust') or 0):.2f} "
            f"rapport={float(state.get('rapport') or 0):.2f} "
            f"last_user_mood={state.get('last_user_mood') or 'unknown'} "
            f"latest_shared_experience={latest}"
        )
        return value[: max(120, int(max_chars))]

    def status(self) -> Dict[str, Any]:
        return {**self.state, "depth": self.depth()}
