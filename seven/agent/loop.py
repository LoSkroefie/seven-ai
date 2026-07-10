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
from seven.mind.state import LivingState
from seven.tools.registry import ToolRegistry, build_default_registry

logger = logging.getLogger("seven.agent")


class Seven:
    """The living agent process."""

    def __init__(self, tool_tier: Optional[str] = None):
        self.memory = Memory()
        self.brain = Brain()
        tier = tool_tier or config.TOOL_TIER
        self.tools: ToolRegistry = build_default_registry(
            self.memory, brain=self.brain, tier=tier
        )
        self.living = LivingState()
        self.autonomy = AutonomyEngine(self)
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
            self._maybe_compact()

            # Local slash commands (no LLM)
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
        """Sense → decide → act → reflect. No greeting spam."""
        try:
            self.refresh_living_state()
        except Exception:
            logger.exception("living refresh failed")

        idle_min = (time.time() - self.last_user_ts) / 60.0
        if self.autonomy.session and self.autonomy.session.active():
            idle_min = max(idle_min, config.AUTONOMY_GOAL_IDLE_MIN)

        # Quiet / degraded modes: still sense, skip heavy LLM work unless overdue
        mode = (self.living.self_state.get("state") or {}).get("mode")
        if mode == "degraded_no_llm":
            self.living.record_action(
                "sense_only",
                reflection="Ollama down — cannot plan; waiting for recovery.",
            )
            logger.warning("Autonomy degraded: no LLM")
            return
        if mode == "quiet_hours" and not (
            self.autonomy.session and self.autonomy.session.active()
        ):
            # only act if overdue tasks exist
            work = self.autonomy.collect_work(idle_min)
            if not any("Overdue" in w for w in work):
                self.living.record_action("quiet_rest", reflection="Quiet hours; no overdue work.")
                return

        result = self.autonomy.heartbeat_tick(idle_min)
        if result:
            logger.info("Autonomous result: %s", (result or "")[:200])
            self.living.record_action(
                "autonomy_tick",
                reflection=(result or "")[:400],
            )
        else:
            self.living.record_action("idle", reflection="No actionable work this tick.")

    def shutdown(self):
        self.stop_heartbeat()
        try:
            self.living.record_action("shutdown", reflection="Agent process stopping.")
        except Exception:
            pass
        logger.info("Seven shut down")
