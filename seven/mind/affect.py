"""Persistent, evidence-backed functional affect for Seven.

This is not a claim of human feeling or consciousness.  It is a compact
appraisal system: conversation and tool outcomes update durable valence,
arousal, confidence, energy, and drives.  The same state influences prompts,
initiative, status, and the desktop companion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, List, Optional

from seven.memory.store import Memory


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _toward(value: float, target: float, amount: float) -> float:
    amount = _clip(amount)
    return value + (target - value) * amount


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


@dataclass
class AffectSnapshot:
    valence: float = 0.1
    arousal: float = 0.25
    confidence: float = 0.65
    energy: float = 1.0
    dominant_emotion: str = "calm"
    secondary_emotion: str = "curious"
    drives: Dict[str, float] = field(
        default_factory=lambda: {
            "connection": 0.45,
            "curiosity": 0.55,
            "competence": 0.55,
            "autonomy": 0.5,
            "purpose": 0.55,
            "rest": 0.05,
        }
    )
    evidence: List[str] = field(default_factory=list)
    updated_at: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "confidence": round(self.confidence, 3),
            "energy": round(self.energy, 3),
            "dominant_emotion": self.dominant_emotion,
            "secondary_emotion": self.secondary_emotion,
            "drives": {key: round(value, 3) for key, value in self.drives.items()},
            "evidence": list(self.evidence),
            "updated_at": self.updated_at,
        }


class AffectEngine:
    """Deterministic affect state derived from observable events."""

    _POSITIVE = {
        "thanks", "thank", "great", "good", "awesome", "excellent", "love",
        "happy", "proud", "glad", "welcome", "perfect", "nice", "amazing",
    }
    _FRUSTRATED = {
        "frustrated", "annoyed", "angry", "furious", "pissed", "useless",
        "disappointed", "dissapointed", "wrong", "broken", "hate", "fuck",
        "fucking", "shit", "cunt", "poes",
    }
    _SAD = {
        "sad", "cry", "crying", "hurt", "lonely", "depressed", "hopeless",
        "upset", "grief", "miserable",
    }
    _WORRIED = {
        "worried", "afraid", "scared", "anxious", "concerned", "unsafe",
        "trojan", "virus", "risk",
    }
    _TRUST = {
        "trust", "believe", "understanding", "important", "promise",
    }
    _CELEBRATE = {
        "done", "finished", "published", "deployed", "fixed", "success",
        "working", "passed",
    }

    def __init__(self, memory: Memory):
        self.memory = memory
        saved = memory.get_affect_state()
        if saved:
            self.state = AffectSnapshot(
                valence=float(saved.get("valence", 0.1)),
                arousal=float(saved.get("arousal", 0.25)),
                confidence=float(saved.get("confidence", 0.65)),
                energy=float(saved.get("energy", 1.0)),
                dominant_emotion=str(saved.get("dominant_emotion") or "calm"),
                secondary_emotion=str(saved.get("secondary_emotion") or "curious"),
                drives={
                    **AffectSnapshot().drives,
                    **{
                        str(key): _clip(value)
                        for key, value in (saved.get("drives") or {}).items()
                    },
                },
                evidence=list(saved.get("evidence") or [])[-8:],
                updated_at=str(saved.get("updated_at") or ""),
            )
        else:
            self.state = AffectSnapshot()
            self._persist()
        self.decay()

    @staticmethod
    def infer_user_mood(text: str) -> str:
        lowered = (text or "").casefold()
        words = set(re.findall(r"[a-z0-9']+", lowered))
        if words.intersection(AffectEngine._SAD):
            return "sad"
        if words.intersection(AffectEngine._WORRIED):
            return "worried"
        if words.intersection(AffectEngine._FRUSTRATED):
            return "frustrated"
        if words.intersection(AffectEngine._POSITIVE):
            return "positive"
        if "?" in text:
            return "curious"
        return "neutral"

    def decay(self, now: Optional[datetime] = None) -> AffectSnapshot:
        """Move transient signals toward baselines as real time passes."""
        now = now or datetime.now(timezone.utc)
        elapsed_hours = max(
            0.0,
            (now - _parse_time(self.state.updated_at)).total_seconds() / 3600.0,
        )
        if elapsed_hours <= 0:
            return self.state
        amount = min(0.8, elapsed_hours * 0.08)
        self.state.valence = _toward(self.state.valence, 0.1, amount)
        self.state.arousal = _toward(self.state.arousal, 0.25, amount)
        self.state.confidence = _toward(self.state.confidence, 0.65, amount * 0.6)
        self.state.drives["connection"] = _clip(
            self.state.drives["connection"] + min(0.25, elapsed_hours * 0.015)
        )
        self.state.drives["curiosity"] = _clip(
            self.state.drives["curiosity"] + min(0.18, elapsed_hours * 0.01)
        )
        self.state.drives["rest"] = _clip(1.0 - self.state.energy)
        self._name_state()
        self._persist(now)
        return self.state

    def set_energy(self, energy: float, evidence: str = "runtime resources") -> None:
        self.state.energy = _clip(energy)
        self.state.drives["rest"] = _clip(1.0 - self.state.energy)
        self._remember_evidence(evidence)
        self._name_state()
        self._persist()

    def observe_user(self, text: str) -> str:
        mood = self.infer_user_mood(text)
        lowered = (text or "").casefold()
        words = set(re.findall(r"[a-z0-9']+", lowered))
        valence_delta = 0.0
        arousal_delta = 0.0
        confidence_delta = 0.0
        evidence = f"user mood inferred as {mood}"

        if mood == "positive":
            valence_delta, arousal_delta, confidence_delta = 0.13, 0.04, 0.035
            self.state.drives["connection"] = _clip(
                self.state.drives["connection"] - 0.08
            )
        elif mood == "frustrated":
            valence_delta, arousal_delta, confidence_delta = -0.11, 0.18, -0.035
            self.state.drives["connection"] = _clip(
                self.state.drives["connection"] + 0.08
            )
            self.state.drives["competence"] = _clip(
                self.state.drives["competence"] + 0.1
            )
        elif mood == "sad":
            valence_delta, arousal_delta = -0.14, -0.03
            self.state.drives["connection"] = _clip(
                self.state.drives["connection"] + 0.14
            )
        elif mood == "worried":
            valence_delta, arousal_delta = -0.08, 0.13
            self.state.drives["connection"] = _clip(
                self.state.drives["connection"] + 0.07
            )
            self.state.drives["competence"] = _clip(
                self.state.drives["competence"] + 0.08
            )
        elif mood == "curious":
            valence_delta, arousal_delta = 0.025, 0.04
            self.state.drives["curiosity"] = _clip(
                self.state.drives["curiosity"] + 0.06
            )

        if words.intersection(self._TRUST):
            valence_delta += 0.04
            self.state.drives["connection"] = _clip(
                self.state.drives["connection"] - 0.03
            )
            evidence += "; trust language present"
        if words.intersection(self._CELEBRATE):
            valence_delta += 0.04
            confidence_delta += 0.03
        if text.count("!") >= 3 or (text.isupper() and len(text) > 12):
            arousal_delta += 0.09
            evidence += "; high intensity"
        if "?" in text:
            self.state.drives["curiosity"] = _clip(
                self.state.drives["curiosity"] + 0.025
            )

        self._apply(
            event_kind="user_message",
            stimulus=mood,
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            confidence_delta=confidence_delta,
            evidence=evidence,
        )
        return mood

    def observe_outcome(
        self,
        *,
        ok: bool,
        tool_count: int = 0,
        error: str = "",
        evidence: Optional[Iterable[str]] = None,
    ) -> AffectSnapshot:
        if ok:
            valence_delta = 0.055 + min(0.05, max(0, tool_count) * 0.01)
            arousal_delta = -0.015 if tool_count == 0 else 0.025
            confidence_delta = 0.045 + min(0.04, max(0, tool_count) * 0.008)
            kind = "successful_turn"
            summary = "response completed"
            self.state.drives["competence"] = _clip(
                self.state.drives["competence"] - 0.06
            )
            self.state.drives["purpose"] = _clip(
                self.state.drives["purpose"] - min(0.05, tool_count * 0.01)
            )
        else:
            valence_delta = -0.09
            arousal_delta = 0.11
            confidence_delta = -0.055
            kind = "failed_turn"
            summary = (error or "response failed")[:240]
            self.state.drives["competence"] = _clip(
                self.state.drives["competence"] + 0.13
            )
            self.state.drives["purpose"] = _clip(
                self.state.drives["purpose"] + 0.05
            )
        evidence_text = "; ".join(str(item)[:160] for item in (evidence or []))
        self._apply(
            event_kind=kind,
            stimulus=summary,
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            confidence_delta=confidence_delta,
            evidence=evidence_text or summary,
        )
        return self.state

    def context_for_prompt(self, max_chars: int = 420) -> str:
        s = self.state
        strongest = sorted(
            s.drives.items(), key=lambda item: (-item[1], item[0])
        )[:2]
        text = (
            f"functional_affect={s.dominant_emotion}"
            f"/{s.secondary_emotion} valence={s.valence:.2f} "
            f"arousal={s.arousal:.2f} confidence={s.confidence:.2f} "
            f"energy={s.energy:.2f}; strongest_drives="
            + ",".join(f"{key}:{value:.2f}" for key, value in strongest)
        )
        return text[: max(100, int(max_chars))]

    def status(self) -> Dict[str, Any]:
        return self.state.as_dict()

    def _apply(
        self,
        *,
        event_kind: str,
        stimulus: str,
        valence_delta: float,
        arousal_delta: float,
        confidence_delta: float,
        evidence: str,
    ) -> None:
        self.decay()
        self.state.valence = _clip(
            self.state.valence + valence_delta, -1.0, 1.0
        )
        self.state.arousal = _clip(self.state.arousal + arousal_delta)
        self.state.confidence = _clip(self.state.confidence + confidence_delta)
        self._remember_evidence(evidence)
        self._name_state()
        self.memory.add_affect_event(
            event_kind,
            stimulus,
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            confidence_delta=confidence_delta,
            dominant_emotion=self.state.dominant_emotion,
            evidence=evidence,
        )
        self._persist()

    def _name_state(self) -> None:
        s = self.state
        if s.energy < 0.25:
            primary = "tired"
        elif s.valence <= -0.22 and s.arousal >= 0.55:
            primary = "concerned"
        elif s.valence <= -0.22:
            primary = "subdued"
        elif s.valence >= 0.5 and s.arousal >= 0.5:
            primary = "excited"
        elif s.valence >= 0.32:
            primary = "content"
        elif s.arousal >= 0.62 and s.confidence >= 0.62:
            primary = "determined"
        elif s.arousal >= 0.52:
            primary = "focused"
        else:
            primary = "calm"
        strongest = max(s.drives, key=s.drives.get)
        secondary = {
            "connection": "caring",
            "curiosity": "curious",
            "competence": "determined",
            "autonomy": "independent",
            "purpose": "purposeful",
            "rest": "rest-seeking",
        }.get(strongest, "curious")
        if secondary == primary:
            secondary = "steady"
        s.dominant_emotion = primary
        s.secondary_emotion = secondary

    def _remember_evidence(self, evidence: str) -> None:
        value = str(evidence or "").strip()
        if value:
            self.state.evidence.append(value[:240])
            self.state.evidence = self.state.evidence[-8:]

    def _persist(self, now: Optional[datetime] = None) -> None:
        now = now or datetime.now(timezone.utc)
        self.state.updated_at = now.isoformat()
        self.memory.save_affect_state(
            valence=self.state.valence,
            arousal=self.state.arousal,
            confidence=self.state.confidence,
            energy=self.state.energy,
            dominant_emotion=self.state.dominant_emotion,
            secondary_emotion=self.state.secondary_emotion,
            drives=self.state.drives,
            evidence=self.state.evidence,
        )
