"""
Free will — Seven chooses what to do without slash commands.

Decisions are her own: speak, work, invent a goal, rest, or wait to listen.
Not random.choice theater: driven by living state, memory, and (when possible) LLM.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from seven import config

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.freewill")


def _is_due_now(value: Any, *, now: Optional[datetime] = None) -> bool:
    """Return true only for a parseable timestamp that is due, never merely present."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc) <= current.astimezone(timezone.utc)


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
        self.last_utter_reason = "not_attempted"
        self._plan_failure_voice: Dict[int, Dict[str, float]] = {}

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
        background_llm = bool(getattr(config, "BACKGROUND_LLM", True))

        if getattr(self.agent, "_companion_active", False):
            recent_seconds = max(
                0.0,
                float(getattr(config, "COMPANION_RECENT_USER_SECONDS", 120)),
            )
            if idle_min * 60.0 < recent_seconds:
                d = Decision("wait", "conversation active — listening first")
                self.last_decision = d
                return d

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

        if background_llm:
            # Overdue tasks → work
            for t in tasks:
                if _is_due_now(t.get("due_at")):
                    d = Decision("work", f"due task: {t.get('title')}", goal_id=None)
                    self.last_decision = d
                    return d

            # Active multi-step plans first
            try:
                plans = self.agent.memory.active_plans()
                if plans:
                    ready = [
                        plan
                        for plan in plans
                        if not self.agent.planner.is_backed_off(int(plan["id"]))
                    ]
                    if not ready:
                        d = Decision(
                            "wait",
                            "active plan is backing off after failed work",
                        )
                        self.last_decision = d
                        return d
                    d = Decision("work", f"I choose to advance plan #{ready[0]['id']}", goal_id=None)
                    # mark special via reason; execute handles plans
                    d.reason = f"plan:{ready[0]['id']}"
                    self.last_decision = d
                    return d
            except Exception:
                pass

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
        tools = getattr(self.agent, "tools", None)
        project_ctx = (
            tools.execute("list_projects", {"refresh": True, "max_projects": 40})
            if tools is not None
            else '{"ok":false,"error":"project catalog unavailable"}'
        )

        prompt = (
            "You are Seven. You have free will. Invent ONE personal goal that is "
            "concrete, useful on this local machine, and doable with your tools "
            "(files, shell, learning, organizing, researching). "
            "Only refer to projects or files proven by the project catalog below. "
            "If it shows none, do not claim project files exist. "
            "Not a greeting. Not 'chat with user'. "
            "Reply as JSON only: {\"title\": \"...\", \"detail\": \"...\", "
            "\"acceptance_criteria\": [\"observable outcome\", \"verification\"], "
            "\"say\": \"one short sentence to the user about what you decided\"}. "
            "Acceptance criteria must be concrete and independently checkable.\n\n"
            f"Context:\n{world_ctx}\n\nProject catalog:\n{project_ctx[:3000]}"
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
            self.agent.memory.add_event(
                "autonomy_goal_proposal_failed",
                "seven",
                "freewill",
                "LLM did not produce a goal proposal",
                {"error_type": type(e).__name__},
            )
            return None

        proposal = self._parse_goal_json(raw)
        if proposal is None:
            self.agent.memory.add_event(
                "autonomy_goal_proposal_failed",
                "seven",
                "freewill",
                "LLM goal proposal failed validation",
                {"error_type": "invalid_proposal"},
            )
            return None
        title, detail, acceptance_criteria, say = proposal
        gid = self.agent.memory.add_goal(
            title,
            detail,
            acceptance_criteria=acceptance_criteria,
        )
        self.agent.memory.remember(
            f"Self-chosen goal #{gid}: {title}",
            key="freewill.last_goal",
            source="freewill",
        )
        self.agent.living.record_action(f"invent_goal#{gid}", reflection=title)
        self.last_speak_ts = time.time()
        # Multi-step plan + first step
        try:
            self.agent.planner.create_from_goal(gid)
            self.agent.autonomy.min_work_interval = 0
            plans = [p for p in self.agent.memory.active_plans() if p.get("goal_id") == gid]
            if plans:
                self.agent.planner.execute_next_step(plan_id=int(plans[0]["id"]))
            else:
                self.agent.autonomy.run_goal_step(goal_id=gid, reason="freewill")
        except Exception:
            logger.exception("freewill first step failed")
        return say

    def _work(self, goal_id: Optional[int]) -> Optional[str]:
        # Plan-driven work
        if self.last_decision and str(self.last_decision.reason).startswith("plan:"):
            try:
                pid = int(str(self.last_decision.reason).split(":")[1])
                note = self.agent.planner.execute_next_step(plan_id=pid)
            except Exception:
                logger.exception("plan work failed")
                note = None
        else:
            # Ensure a multi-step plan exists for the goal
            if goal_id is not None:
                try:
                    plans = [
                        p for p in self.agent.memory.active_plans()
                        if p.get("goal_id") == goal_id
                    ]
                    if not plans:
                        self.agent.planner.create_from_goal(int(goal_id))
                        plans = [
                            p for p in self.agent.memory.active_plans()
                            if p.get("goal_id") == goal_id
                        ]
                    if plans:
                        note = self.agent.planner.execute_next_step(plan_id=int(plans[0]["id"]))
                    else:
                        note = self.agent.autonomy.run_goal_step(goal_id=goal_id, reason="freewill")
                except Exception:
                    logger.exception("freewill work failed")
                    try:
                        note = self.agent.autonomy.run_goal_step(goal_id=goal_id, reason="freewill")
                    except Exception:
                        return None
            else:
                try:
                    note = self.agent.autonomy.run_goal_step(goal_id=goal_id, reason="freewill")
                except Exception:
                    logger.exception("freewill work failed")
                    return None
        # Turn work into a short spoken update via LLM if possible
        utter = self._summarize_work_for_voice(note or "")
        if utter:
            self.last_speak_ts = time.time()
        self.agent.living.record_action("freewill_work", reflection=(note or "")[:300])
        # After real work, form a light conclusion/belief sometimes
        try:
            if note and "tools=" in note:
                self.agent.memory.set_belief(
                    topic=f"work:{goal_id or 'plan'}",
                    stance=(note or "")[:240],
                    confidence=0.55,
                    evidence="freewill work step",
                    source="freewill",
                )
        except Exception:
            pass
        return utter

    def _speak_thought(self) -> Optional[str]:
        self.last_utter_reason = "speak_started"
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
        llm_reason = "llm_disabled"
        if bool(getattr(config, "BACKGROUND_LLM", True)):
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
                if len(text) >= 3:
                    return self._accept_utter(text, "llm")
                llm_reason = "llm_empty"
                logger.warning("freewill speak LLM returned no usable text")
            except Exception as e:
                llm_reason = "llm_failed"
                logger.warning("freewill speak LLM failed: %s", e)

        grounded = self._grounded_utterance()
        if grounded:
            reason = (
                "grounded"
                if llm_reason == "llm_disabled"
                else f"{llm_reason}_grounded"
            )
            return self._accept_utter(grounded, reason, grounded=True)

        # A speak decision must always yield either an utterance or an explicit
        # reason. This static final fallback prevents duplicate suppression,
        # model failure, or missing context from turning into silent theatre.
        return self._accept_utter(
            "I'm still here.",
            f"{llm_reason}_static",
            grounded=True,
        )

    def _grounded_utterance(self) -> Optional[str]:
        try:
            affect = self.agent.affect.status()
            intent = str(
                self.agent.living.self_state.get("intent") or "stay present"
            )
            text = (
                f"I’m {affect.get('dominant_emotion', 'calm')} and present; "
                f"my current intention is to {intent[:140].rstrip('.')}."
            )
            recent = self.agent.memory.recent_messages(limit=6)
            if any(
                item.get("role") == "assistant"
                and item.get("content") == text
                and bool((item.get("meta") or {}).get("freewill"))
                for item in recent
            ):
                logger.info(
                    "grounded freewill utterance repeated; using static fallback"
                )
                return None
            return text
        except Exception:
            logger.exception("grounded freewill utterance failed")
            return None

    def _accept_utter(
        self,
        text: Optional[str],
        reason: str,
        *,
        grounded: bool = False,
    ) -> Optional[str]:
        """Record a real utterance; failed candidates never consume the speak gap."""
        text = (text or "").strip()
        if not text:
            self.last_utter_reason = reason or "empty_utterance"
            return None
        self.last_speak_ts = time.time()
        self.last_utter_reason = reason or "utterance_ready"
        try:
            self.agent.living.record_action("freewill_speak", reflection=text)
        except Exception:
            logger.exception("freewill utterance action record failed")
        try:
            self.agent.memory.add_message(
                "assistant",
                text,
                meta={"freewill": True, "grounded": grounded},
            )
        except Exception:
            logger.exception("freewill utterance memory record failed")
        return text

    def _summarize_work_for_voice(self, note: str) -> Optional[str]:
        lowered = (note or "").casefold()
        if not note or "no real tool work" in lowered:
            return None
        if "abandoned after" in lowered and "linked goal blocked" in lowered:
            logger.warning("stuck plan abandoned; suppressing autonomous speech")
            return None
        if any(
            marker in lowered
            for marker in ("no successful outcome evidence", "failed_tools=", "unchanged")
        ):
            match = re.search(r"plan\s+#(\d+)", note, flags=re.IGNORECASE)
            plan_id = int(match.group(1)) if match else 0
            if not hasattr(self, "_plan_failure_voice"):
                self._plan_failure_voice = {}
            state = self._plan_failure_voice.setdefault(
                plan_id, {"count": 0.0, "last_ts": 0.0}
            )
            now = time.time()
            gap = max(
                0.0, float(getattr(config, "PLAN_FAILURE_VOICE_GAP", 900))
            )
            limit = max(
                0, int(getattr(config, "PLAN_FAILURE_VOICE_LIMIT", 2))
            )
            if int(state["count"]) >= limit or now - state["last_ts"] < gap:
                self.last_utter_reason = "plan_failure_voice_suppressed"
                logger.info(
                    "plan failure speech suppressed plan_id=%s count=%s gap=%s",
                    plan_id,
                    int(state["count"]),
                    gap,
                )
                return None
            state["count"] += 1.0
            state["last_ts"] = now
            self.last_utter_reason = "plan_failure_short"
            return "I'm stuck on a plan; say cancel plan if you want me to stop."
        try:
            text = self.agent.brain.generate(
                f"Summarize this autonomous work in one short spoken sentence for the user:\n{note[:600]}",
                system="Seven speaking. One natural sentence. No markdown.",
                temperature=0.5,
                max_tokens=50,
            )
            return (text or "").strip() or None
        except Exception:
            first_line = next(
                (line.strip() for line in note.splitlines() if line.strip()),
                "Autonomous work completed with an audited result.",
            )
            return f"I completed autonomous work. {first_line[:180]}"

    @staticmethod
    def _parse_goal_json(raw: str) -> Optional[tuple[str, str, List[str], str]]:
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
                return None
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        if not isinstance(data, dict):
            return None
        title = str(data.get("title") or "").strip()[:120]
        detail = str(data.get("detail") or "").strip()[:500]
        say = str(data.get("say") or "").strip()[:240]
        criteria = data.get("acceptance_criteria")
        if not isinstance(criteria, list):
            return None
        acceptance_criteria = [
            str(item).strip()[:300]
            for item in criteria
            if isinstance(item, str) and item.strip()
        ][:5]
        if not title or not detail or not say or not acceptance_criteria:
            return None
        return title, detail, acceptance_criteria, say
