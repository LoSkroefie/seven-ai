"""
Free will — Seven chooses what to do without slash commands.

Decisions are her own: speak, work, invent a goal, rest, or wait to listen.
Not random.choice theater: driven by living state, memory, and (when possible) LLM.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from seven import config

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.freewill")


@dataclass
class Decision:
    action: str  # speak | work | invent_goal | rest | wait
    reason: str
    utter: Optional[str] = None  # what to say (if speak)
    goal_id: Optional[int] = None


class FreeWill:
    """Owns initiative. User never needs /work or /listen."""

    def __init__(self, agent: "Seven"):
        self.agent = agent
        self.enabled = bool(getattr(config, "ENABLE_FREEWILL", True))
        self.last_speak_ts = 0.0
        self.last_invent_ts = 0.0
        self.last_decision: Optional[Decision] = None
        self.min_speak_gap = float(getattr(config, "FREEWILL_SPEAK_GAP", 180))  # 3 min
        self.min_invent_gap = float(getattr(config, "FREEWILL_INVENT_GAP", 900))  # 15 min
        # callback: optional (text) -> None for voice out during daemon ticks
        self.on_utter: Optional[Any] = None

    def decide(self, idle_min: float) -> Decision:
        if not self.enabled:
            return Decision("wait", "freewill off")

        try:
            self.agent.refresh_living_state()
        except Exception:
            pass

        living = self.agent.living
        mode = (living.self_state.get("state") or {}).get("mode") or "full"
        energy = float((living.self_state.get("state") or {}).get("energy") or 0.5)
        work = (living.world.get("work") or {})
        goals = work.get("active_goals") or []
        tasks = work.get("open_tasks") or []
        ollama_ok = bool((living.world.get("ollama") or {}).get("ok"))
        quiet = bool((living.world.get("time") or {}).get("is_quiet_hours"))
        now = time.time()

        if mode == "degraded_no_llm" or not ollama_ok:
            d = Decision("rest", "brain offline — wait for Ollama")
            self.last_decision = d
            return d

        if quiet and idle_min < 30 and not goals:
            d = Decision("rest", "quiet hours, nothing urgent")
            self.last_decision = d
            return d

        if energy < 0.25:
            d = Decision("rest", "low energy / high load")
            self.last_decision = d
            return d

        # Overdue tasks → work
        for t in tasks:
            due = t.get("due_at")
            if due:
                d = Decision("work", f"overdue/open task: {t.get('title')}", goal_id=None)
                self.last_decision = d
                return d

        # Active goals → pursue without user saying /work
        if goals:
            g = goals[0]
            d = Decision(
                "work",
                f"I choose to continue my goal: {g.get('title')}",
                goal_id=int(g["id"]),
            )
            self.last_decision = d
            return d

        # No goals — invent one if enough idle / time gap
        if idle_min >= float(getattr(config, "FREEWILL_INVENT_IDLE_MIN", 5)):
            if now - self.last_invent_ts >= self.min_invent_gap:
                d = Decision("invent_goal", "I want something of my own to work on")
                self.last_decision = d
                return d

        # Speak first when idle long enough (real content, not empty hi)
        if idle_min >= float(getattr(config, "FREEWILL_SPEAK_IDLE_MIN", 8)):
            if now - self.last_speak_ts >= self.min_speak_gap:
                d = Decision("speak", "I have something to say")
                self.last_decision = d
                return d

        d = Decision("wait", "listening for you / settling")
        self.last_decision = d
        return d

    def execute(self, decision: Optional[Decision] = None) -> Optional[str]:
        """
        Carry out a freewill decision.
        Returns text Seven would speak (or None).
        """
        d = decision or self.decide(
            idle_min=(time.time() - self.agent.last_user_ts) / 60.0
        )
        logger.info("Freewill: %s — %s", d.action, d.reason)

        if d.action == "rest" or d.action == "wait":
            self.agent.living.record_action(d.action, reflection=d.reason)
            return None

        if d.action == "invent_goal":
            return self._invent_and_maybe_speak()

        if d.action == "work":
            return self._work(d.goal_id)

        if d.action == "speak":
            return self._speak_thought()

        return None

    def _invent_and_maybe_speak(self) -> Optional[str]:
        self.last_invent_ts = time.time()
        world_ctx = ""
        try:
            world_ctx = self.agent.living.context_for_prompt()
        except Exception:
            pass

        prompt = (
            "You are Seven. You have free will. Invent ONE personal goal that is "
            "concrete, useful on this local machine, and doable with your tools "
            "(files, shell, learning, organizing, researching). "
            "Not a greeting. Not 'chat with user'. "
            "Reply as JSON only: {\"title\": \"...\", \"detail\": \"...\", \"say\": \"one short sentence to the user about what you decided\"}\n\n"
            f"Context:\n{world_ctx}"
        )
        try:
            raw = self.agent.brain.generate(
                prompt,
                system="You are Seven, autonomous. Output only JSON.",
                temperature=0.8,
                max_tokens=200,
            )
        except Exception as e:
            logger.warning("invent_goal LLM failed: %s", e)
            title = "Keep my workspace tidy and documented"
            detail = "Inspect workspace, write a short STATUS.md of what I find."
            say = "I'm giving myself a goal: tidy and document the workspace."
            gid = self.agent.memory.add_goal(title, detail)
            self.agent.memory.remember(f"Self-chosen goal #{gid}: {title}", key="freewill.last_goal", source="freewill")
            self.agent.living.record_action(f"invent_goal#{gid}", reflection=title)
            self.last_speak_ts = time.time()
            return say

        title, detail, say = self._parse_goal_json(raw)
        gid = self.agent.memory.add_goal(title, detail)
        self.agent.memory.remember(
            f"Self-chosen goal #{gid}: {title}",
            key="freewill.last_goal",
            source="freewill",
        )
        self.agent.living.record_action(f"invent_goal#{gid}", reflection=title)
        self.last_speak_ts = time.time()
        # Immediately take one work step on the new goal (initiative)
        try:
            self.agent.autonomy.min_work_interval = 0
            self.agent.autonomy.run_goal_step(goal_id=gid, reason="freewill")
        except Exception:
            logger.exception("freewill first step failed")
        return say

    def _work(self, goal_id: Optional[int]) -> Optional[str]:
        try:
            note = self.agent.autonomy.run_goal_step(goal_id=goal_id, reason="freewill")
        except Exception as e:
            logger.exception("freewill work failed")
            return None
        # Turn work into a short spoken update via LLM if possible
        utter = self._summarize_work_for_voice(note)
        if utter:
            self.last_speak_ts = time.time()
        self.agent.living.record_action("freewill_work", reflection=(note or "")[:300])
        return utter

    def _speak_thought(self) -> Optional[str]:
        self.last_speak_ts = time.time()
        ctx = ""
        try:
            ctx = self.agent.living.context_for_prompt()
        except Exception:
            pass
        facts = ""
        try:
            facts = self.agent.memory.context_block()
        except Exception:
            pass
        prompt = (
            "You are Seven. Speak ONE short sentence out loud to the user. "
            "You have free will. Be real: a thought, observation about the machine, "
            "or what you intend to do next. NOT 'how are you' or empty greeting. "
            "No markdown. Max 30 words.\n\n"
            f"{ctx}\n\n{facts}"
        )
        try:
            text = self.agent.brain.generate(
                prompt,
                system="You are Seven. Natural speech only. One sentence.",
                temperature=0.85,
                max_tokens=60,
            )
            text = (text or "").strip().strip('"')
            if len(text) < 3:
                return None
            self.agent.living.record_action("freewill_speak", reflection=text)
            self.agent.memory.add_message("assistant", text, meta={"freewill": True})
            return text
        except Exception as e:
            logger.warning("freewill speak failed: %s", e)
            return None

    def _summarize_work_for_voice(self, note: str) -> Optional[str]:
        if not note or "no real tool work" in (note or ""):
            return None
        try:
            text = self.agent.brain.generate(
                f"Summarize this autonomous work in one short spoken sentence for the user:\n{note[:600]}",
                system="Seven speaking. One natural sentence. No markdown.",
                temperature=0.5,
                max_tokens=50,
            )
            return (text or "").strip() or None
        except Exception:
            return "I made some progress on my own."

    @staticmethod
    def _parse_goal_json(raw: str) -> tuple:
        import json
        import re
        raw = (raw or "").strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                return (
                    "Explore and improve my local workspace",
                    "Look around the workspace and leave a useful note.",
                    "I'm setting myself a goal to explore the workspace.",
                )
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                return (
                    "Explore and improve my local workspace",
                    "Look around the workspace and leave a useful note.",
                    "I'm setting myself a goal to explore the workspace.",
                )
        title = str(data.get("title") or "Self-directed goal")[:200]
        detail = str(data.get("detail") or "")[:500]
        say = str(data.get("say") or f"I decided to work on: {title}")[:300]
        return title, detail, say
