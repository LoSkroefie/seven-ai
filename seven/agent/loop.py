"""
Seven Real agent loop.
perceive (user/sensors) -> plan (LLM + tools) -> act (execute) -> remember
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from seven import config
from seven.agent.autonomy import AutonomyEngine, format_audit
from seven.agent.prompt import build_system_prompt
from seven.brain.llm import Brain, BrainError
from seven.memory.store import Memory
from seven.mind.episodic import EpisodicMemory
from seven.mind.freewill import FreeWill
from seven.mind.planner import Planner
from seven.mind.preferences import learn_from_utterance
from seven.mind.state import LivingState
from seven.memory.vector import SemanticMemory
from seven.tools.registry import ToolRegistry, build_default_registry
from seven.tools import mind_tools as mind_tools_mod

logger = logging.getLogger("seven.agent")


class Seven:
    """The living agent process — companion with free will, not a command shell."""

    def __init__(self, tool_tier: Optional[str] = None):
        self.memory = Memory()
        self.brain = Brain()
        tier = tool_tier or config.TOOL_TIER
        # tools need agent ref for plan/skill runners — build twice lightly
        self.tools: ToolRegistry = build_default_registry(
            self.memory, brain=self.brain, tier=tier, agent=None
        )
        self.living = LivingState()
        self.autonomy = AutonomyEngine(self)
        self.freewill = FreeWill(self)
        self.planner = Planner(self)
        self.episodic = EpisodicMemory(self)
        self.semantic = SemanticMemory(self.memory)
        # re-bind mind tools with agent
        mind_tools_mod.set_context(memory=self.memory, agent=self)
        self.tools = build_default_registry(
            self.memory, brain=self.brain, tier=tier, agent=self
        )
        self._lock = threading.RLock()
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: Optional[threading.Thread] = None
        self.last_user_ts = time.time()
        self.session_started = datetime.now(timezone.utc).isoformat()
        self._boot_checks()
        try:
            self.refresh_living_state()
        except Exception:
            logger.exception("initial living state failed")

    def _boot_checks(self):
        # Pick best local model (qwen2.5:7b preferred for tools)
        if getattr(config, "AUTO_SELECT_MODEL", True):
            try:
                from seven.brain.models import apply_best_model_to_config
                picked = apply_best_model_to_config()
                self.brain.model = config.OLLAMA_MODEL
                logger.info("Model auto-select: %s", picked)
            except Exception:
                logger.debug("model auto-select failed", exc_info=True)
        health = self.brain.ping()
        if not health.get("ok"):
            logger.error("LLM not reachable: %s", health)
        else:
            logger.info(
                "Brain ready provider=%s model=%s has_primary=%s has_vision=%s loaded=%s",
                health.get("provider"),
                health.get("model"),
                health.get("has_primary"),
                health.get("has_vision"),
                health.get("loaded"),
            )
            if health.get("hint"):
                logger.warning("Ollama hint: %s", health["hint"])
        logger.info(
            "Tools tier=%s active=%s: %s",
            self.tools.tier,
            len(self.tools.names()),
            ", ".join(self.tools.names()),
        )

    def refresh_living_state(self) -> dict:
        """Sense world + self; used by heartbeat and daemon."""
        ws = None
        if self.autonomy.session and self.autonomy.session.active():
            ws = self.autonomy.session_status().split("\n")[0]
        return self.living.refresh(
            memory=self.memory,
            brain=self.brain,
            last_user_ts=self.last_user_ts,
            tools_active=self.tools.names(),
            tools_total=len(self.tools.all_names()),
            work_session=ws,
        )

    # ── conversation ───────────────────────────────────────────────────

    def handle(self, user_text: str) -> str:
        """Process one user message end-to-end with tool rounds."""
        user_text = (user_text or "").strip()
        if not user_text:
            return ""

        with self._lock:
            self.last_user_ts = time.time()
            self.memory.add_message("user", user_text)
            try:
                learn_from_utterance(self, user_text)
            except Exception:
                logger.debug("preference learn failed", exc_info=True)
            try:
                self.semantic.index_message("user", user_text)
            except Exception:
                pass
            self._maybe_compact()

            # Local slash commands (no LLM) — power user only
            local = self._local_commands(user_text)
            if local is not None:
                self.memory.add_message("assistant", local)
                return local

            messages = self._build_messages()
            tools = self.tools.schemas()
            final_text = ""
            tool_trace: List[str] = []

            try:
                for round_i in range(config.MAX_TOOL_ROUNDS):
                    result = self.brain.chat(messages, tools=tools)
                    content = result.get("content")
                    tool_calls = result.get("tool_calls") or []
                    if not tool_calls and content:
                        from seven.brain.llm import Brain as _B
                        recovered = _B._extract_text_tool_calls(content)
                        if recovered:
                            tool_calls = recovered
                            content = None

                    if tool_calls:
                        messages.append({
                            "role": "assistant",
                            "content": content or "",
                            "tool_calls": [
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": tc["arguments"],
                                    },
                                }
                                for tc in tool_calls
                            ],
                        })
                        for tc in tool_calls:
                            name = tc["name"]
                            args = tc.get("arguments") or {}
                            if not isinstance(args, dict):
                                args = {"value": args}
                            logger.info("tool[%s] %s(%s)", round_i, name, args)
                            out = self.tools.execute(name, args)
                            tool_trace.append(f"{name}: {out[:300]}")
                            messages.append({
                                "role": "tool",
                                "name": name,
                                "content": out,
                            })
                        continue

                    final_text = (content or "").strip()
                    break
                else:
                    final_text = (
                        "I hit the tool-round limit. Here's what I did:\n"
                        + "\n".join(tool_trace[-8:])
                    )
            except BrainError as e:
                final_text = (
                    f"Brain error: {e}\n"
                    "Is Ollama running? Try: ollama serve && ollama run llama3.2\n"
                    "If hung: ollama ps — restart Ollama when a model is stuck Stopping…"
                )
            except Exception as e:
                logger.exception("handle failed")
                final_text = f"Internal error: {e}"

            if not final_text:
                if tool_trace:
                    final_text = "Done.\n" + "\n".join(tool_trace[-5:])
                else:
                    final_text = "…"

            self.memory.add_message("assistant", final_text, meta={"tools": tool_trace})
            try:
                self.semantic.index_message("assistant", final_text)
            except Exception:
                pass
            if tool_trace:
                try:
                    self.memory.wm_add(
                        "Tools: " + "; ".join(tool_trace[:4])[:200],
                        kind="action",
                        priority=0.7,
                    )
                except Exception:
                    pass
            return final_text

    def _maybe_compact(self):
        try:
            n = self.memory.message_count()
            if n >= config.COMPACT_AFTER_MESSAGES:
                summary = self.memory.compact_history(keep_recent=12)
                if summary:
                    logger.info("Compacted history (%s msgs) into fact", n)
        except Exception:
            logger.exception("compaction failed")

    def _local_commands(self, text: str) -> Optional[str]:
        t = text.strip().lower()
        raw = text.strip()
        if t in ("/help", "help!", "/?"):
            return (
                "Seven Real commands:\n"
                "  /status  — brain, tools, ollama loaded, memory\n"
                "  /tools   — list active tool schemas\n"
                "  /tools full|core — switch schema tier (exec still L4)\n"
                "  /memory  — facts/goals/tasks\n"
                "  /audit [n] — activity log (tool calls)\n"
                "  /goals   — list active goals\n"
                "  /world   — world model snapshot\n"
                "  /self    — self-model snapshot\n"
                "  /live    — living state (world+self)\n"
                "  /work <goal_id> [minutes] — start focused work session\n"
                "  /workstep [goal_id] — run one real goal step now\n"
                "  /workstatus — work session status\n"
                "  /stopwork — end work session\n"
                "  /clear   — clear chat history (keeps facts)\n"
                "  /quit    — exit\n"
                "Anything else is handled by the agent with real tools."
            )
        if t == "/status":
            from seven import __version__
            self.refresh_living_state()
            h = self.brain.ping()
            goals = len(self.memory.active_goals())
            tasks = len(self.memory.open_tasks())
            mode = (self.living.self_state.get("state") or {}).get("mode")
            energy = (self.living.self_state.get("state") or {}).get("energy")
            lines = [
                f"Seven Real {__version__}",
                f"provider={h.get('provider')} ok={h.get('ok')}",
                f"model={h.get('model')}",
                f"has_primary={h.get('has_primary')} has_vision={h.get('has_vision')}",
                f"loaded_in_vram={h.get('loaded')}",
                f"tool_tier={self.tools.tier} schemas={len(self.tools.names())} total_tools={len(self.tools.all_names())}",
                f"goals={goals} tasks={tasks} messages={self.memory.message_count()}",
                f"mode={mode} energy={energy} living_ticks={self.living.tick_count}",
                f"intent={self.living.self_state.get('intent')}",
                f"work_session={self.autonomy.session_status().split(chr(10))[0]}",
                f"data={config.DATA_DIR}",
                f"workspace={config.WORKSPACE_DIR}",
            ]
            if h.get("hint"):
                lines.append(f"HINT: {h['hint']}")
            if h.get("error"):
                lines.append(f"ERROR: {h['error']}")
            return "\n".join(lines)
        if t == "/world":
            self.refresh_living_state()
            from seven.mind.world import world_summary
            return world_summary(self.living.world)
        if t == "/self":
            self.refresh_living_state()
            from seven.mind.self_model import self_summary
            return self_summary(self.living.self_state)
        if t in ("/live", "/living"):
            self.refresh_living_state()
            return self.living.status_text()
        if t.startswith("/tools"):
            parts = t.split()
            if len(parts) == 2 and parts[1] in ("core", "full"):
                self.tools.set_tier(parts[1])
                return f"Tool schema tier set to '{parts[1]}'. Active schemas: {len(self.tools.names())}\n" + (
                    "- " + "\n- ".join(self.tools.names())
                )
            return (
                f"tier={self.tools.tier} (schemas shown to model)\n"
                f"Active ({len(self.tools.names())}):\n- "
                + "\n- ".join(self.tools.names())
                + f"\n\nAll registered ({len(self.tools.all_names())}) still executable if named."
            )
        if t == "/memory":
            return self.memory.context_block()
        if t == "/goals":
            goals = self.memory.active_goals()
            if not goals:
                return "No active goals. Ask Seven to add_goal or use tools."
            return "\n".join(
                f"#{g['id']} {g['title']} — {g.get('progress', 0):.0f}% last={g.get('last_action') or '-'}"
                for g in goals
            )
        if t.startswith("/audit"):
            parts = t.split()
            n = 20
            if len(parts) == 2 and parts[1].isdigit():
                n = min(50, int(parts[1]))
            return format_audit(self.memory.recent_audit(n), limit=n)
        if t.startswith("/workstep"):
            parts = raw.split()
            gid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            return self.autonomy.run_goal_step(goal_id=gid, reason="manual")
        if t.startswith("/work") and not t.startswith("/workstatus") and not t.startswith("/workstep"):
            # /work <goal_id> [minutes]
            parts = raw.split()
            if len(parts) < 2 or not parts[1].isdigit():
                return "Usage: /work <goal_id> [minutes]   e.g. /work 1 20"
            minutes = float(parts[2]) if len(parts) > 2 else config.WORK_SESSION_MINUTES
            return self.autonomy.start_session(int(parts[1]), minutes=minutes)
        if t == "/workstatus":
            return self.autonomy.session_status()
        if t == "/stopwork":
            return self.autonomy.stop_session()
        if t in ("/clear", "/reset"):
            self.memory.clear_session_messages()
            return "Session chat cleared. Long-term facts/goals kept."
        if t in ("/quit", "/exit", "quit", "exit"):
            return "__QUIT__"
        return None

    def _build_messages(self) -> List[Dict[str, Any]]:
        living_block = ""
        try:
            living_block = self.living.context_for_prompt()
        except Exception:
            pass
        system = build_system_prompt(
            memory_block=self.memory.context_block(),
            tool_names=self.tools.names(),
            living_block=living_block,
        )
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        history = self.memory.recent_messages(config.MAX_HISTORY_TURNS)
        max_chars = config.MAX_MESSAGE_CHARS
        for m in history:
            if m["role"] not in ("user", "assistant"):
                continue
            content = m["content"] or ""
            if len(content) > max_chars:
                content = content[:max_chars] + "\n…[truncated for context]"
            messages.append({"role": m["role"], "content": content})
        return messages

    # ── heartbeat / autonomy ───────────────────────────────────────────

    def start_heartbeat(self):
        if not config.ENABLE_HEARTBEAT:
            return
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name="seven-heartbeat", daemon=True
        )
        self._heartbeat_thread.start()
        logger.info("Heartbeat every %ss", config.HEARTBEAT_SECONDS)

    def stop_heartbeat(self):
        self._heartbeat_stop.set()

    def _heartbeat_loop(self):
        while not self._heartbeat_stop.wait(config.HEARTBEAT_SECONDS):
            try:
                self._autonomous_tick()
            except Exception:
                logger.exception("heartbeat tick failed")

    def _autonomous_tick(self):
        """Free will tick: she chooses speak / work / invent / rest. No slash commands."""
        try:
            self.refresh_living_state()
        except Exception:
            logger.exception("living refresh failed")

        idle_min = (time.time() - self.last_user_ts) / 60.0

        if self._deliver_due_reminders():
            return

        # Episodic digest once per day when possible
        try:
            dig = self.episodic.maybe_daily_digest()
            if dig:
                logger.info("Daily digest written (%s chars)", len(dig))
        except Exception:
            logger.debug("digest skip", exc_info=True)

        # Active multi-step plans take priority over freewill invent
        try:
            plans = self.memory.active_plans()
            if plans and idle_min >= 1:
                out = self.planner.execute_next_step(plan_id=int(plans[0]["id"]))
                self.living.record_action("plan_step", reflection=(out or "")[:400])
                if self.freewill.on_utter and out and "done" in (out or "").lower():
                    try:
                        self.freewill.on_utter(out[:280])
                    except Exception:
                        pass
                return
        except Exception:
            logger.exception("plan step failed")

        # Prefer free will as the brain of initiative
        if getattr(config, "ENABLE_FREEWILL", True):
            try:
                decision = self.freewill.decide(idle_min)
                utter = self.freewill.execute(decision)
                if utter and self.freewill.on_utter:
                    try:
                        self.freewill.on_utter(utter)
                    except Exception:
                        logger.exception("on_utter failed")
                elif utter:
                    logger.info("Freewill would say: %s", utter[:200])
                return
            except Exception:
                logger.exception("freewill tick failed")

        # Fallback: legacy goal heartbeat if freewill disabled
        if self.autonomy.session and self.autonomy.session.active():
            idle_min = max(idle_min, config.AUTONOMY_GOAL_IDLE_MIN)
        result = self.autonomy.heartbeat_tick(idle_min)
        if result:
            self.living.record_action("autonomy_tick", reflection=(result or "")[:400])

    def _deliver_due_reminders(self) -> bool:
        """Deliver durable due tasks only when a real utterance channel exists."""
        due = self.memory.due_tasks()
        if not due:
            return False
        callback = self.freewill.on_utter
        if callback is None:
            if getattr(config, "ENABLE_DESKTOP_NOTIFICATIONS", True):
                from seven.runtime.notifications import submit_notification
                delivered = False
                for task in due:
                    result = submit_notification("Seven reminder", task["title"])
                    if result.get("ok"):
                        self.memory.mark_task_reminded(int(task["id"]))
                        self.memory.add_note(
                            f"Desktop notification submitted: {task['title']}",
                            title="reminder submitted",
                        )
                        delivered = True
                    else:
                        self.memory.record_reminder_attempt(int(task["id"]))
                        logger.warning("desktop reminder submission failed task=%s result=%s", task["id"], result)
                return delivered
            logger.info("%s reminder(s) due; notifications disabled and no utterance channel", len(due))
            return False
        delivered = False
        for task in due:
            message = f"Reminder: {task['title']}"
            try:
                callback(message)
                self.memory.mark_task_reminded(int(task["id"]))
                self.memory.add_note(message, title="reminder delivered")
                delivered = True
            except Exception:
                self.memory.record_reminder_attempt(int(task["id"]))
                logger.exception("reminder delivery failed task=%s", task["id"])
        return delivered

    def shutdown(self):
        self.stop_heartbeat()
        try:
            self.living.record_action("shutdown", reflection="Agent process stopping.")
        except Exception:
            pass
        logger.info("Seven shut down")
