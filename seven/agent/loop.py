"""
Seven Real agent loop.
perceive (user/sensors) -> plan (LLM + tools) -> act (execute) -> remember
"""
from __future__ import annotations

import logging
import re
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from seven import config
from seven.agent.autonomy import AutonomyEngine, format_audit
from seven.agent.prompt import build_system_prompt
from seven.brain.llm import Brain, BrainError
from seven.memory.store import Memory
from seven.mind.affect import AffectEngine
from seven.mind.episodic import EpisodicMemory
from seven.mind.freewill import FreeWill
from seven.mind.planner import Planner
from seven.mind.preferences import learn_from_utterance
from seven.mind.reflection import ReflectionEngine
from seven.mind.relationship import RelationshipMind
from seven.mind.state import LivingState
from seven.memory.vector import SemanticMemory
from seven.mesh.node import MeshNode
from seven.tools.registry import ToolRegistry, build_default_registry, result_is_success
from seven.tools import mind_tools as mind_tools_mod

logger = logging.getLogger("seven.agent")


class Seven:
    """The living agent process — companion with free will, not a command shell."""

    def __init__(self, tool_tier: Optional[str] = None):
        self.memory = Memory()
        self.mesh = MeshNode(memory=self.memory)
        self.affect = AffectEngine(self.memory)
        self.relationship = RelationshipMind(self.memory)
        self.reflection = ReflectionEngine(self.memory)
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
        self.activity = "idle"
        self.last_response_ts = 0.0
        self.session_started = datetime.now(timezone.utc).isoformat()
        self.model_startup: Dict[str, Any] = {
            "ok": True,
            "source": "configured",
            "active": self.brain.model,
            "reason": "initial configuration",
        }
        self._boot_checks()
        try:
            self.refresh_living_state()
        except Exception:
            logger.exception("initial living state failed")
        try:
            self.mesh.start()
        except Exception:
            logger.exception("Seven Mesh startup failed")

    def _boot_checks(self):
        if self.brain.provider == "ollama":
            from seven.brain.model_lifecycle import ModelLifecycle

            lifecycle = ModelLifecycle(self.brain)
            selection = lifecycle.select_startup_model()
            if selection.get("ok"):
                self.model_startup = selection
                logger.info(
                    "Model startup source=%s active=%s",
                    selection.get("source"),
                    selection.get("active"),
                )
            else:
                fallback_reason = str(selection.get("reason") or "unknown")
                fallback = self.brain.model
                if getattr(config, "AUTO_SELECT_MODEL", True):
                    try:
                        from seven.brain.models import apply_best_model_to_config

                        picked = apply_best_model_to_config()
                        self.brain.model = config.OLLAMA_MODEL
                        fallback = self.brain.model
                        logger.info("Model auto-select fallback: %s", picked)
                    except Exception as exc:
                        logger.warning(
                            "Model auto-select fallback failed after %s: %s",
                            fallback_reason,
                            exc,
                        )
                self.model_startup = {
                    **selection,
                    "fallback": fallback,
                    "runtime_model": self.brain.model,
                }
                if fallback_reason != "no persisted model state":
                    logger.warning(
                        "Persisted model was not restored (%s); using %s",
                        fallback_reason,
                        self.brain.model,
                    )
                    self.memory.add_event(
                        "model_startup_fallback",
                        "seven",
                        "model_lifecycle",
                        fallback_reason,
                        {
                            "persisted": selection.get("active"),
                            "fallback": self.brain.model,
                        },
                    )
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
        snapshot = self.living.refresh(
            memory=self.memory,
            brain=self.brain,
            last_user_ts=self.last_user_ts,
            tools_active=self.tools.names(),
            tools_total=len(self.tools.all_names()),
            work_session=ws,
        )
        state = self.living.self_state.get("state") or {}
        self.affect.set_energy(
            float(state.get("energy") or 1.0),
            evidence="live host resource state",
        )
        self.living.mind_state = {
            "affect": self.affect.status(),
            "relationship": self.relationship.status(),
            "reflection": self.reflection.status(),
        }
        self.living.save()
        snapshot["mind"] = self.living.mind_state
        return snapshot

    # ── conversation ───────────────────────────────────────────────────

    def handle(self, user_text: str, *, source: str = "human") -> str:
        """Process one user message end-to-end with tool rounds."""
        user_text = (user_text or "").strip()
        if not user_text:
            return ""

        with self._lock:
            self.activity = "thinking"
            user_mood = (
                self.affect.observe_user(user_text)
                if source == "human"
                else "neutral"
            )
            if source == "human":
                self.last_user_ts = time.time()
            user_message_id = self.memory.add_message(
                "user", user_text, meta={"source": source}
            )
            if source == "human" and getattr(config, "ACTION_CAPTURE_MODE", "suggest") != "off":
                try:
                    from seven.mind.action_items import capture
                    capture(self.memory, user_message_id, user_text)
                except Exception:
                    logger.exception("local action capture failed")
            try:
                if source == "human":
                    learn_from_utterance(self, user_text)
            except Exception:
                logger.debug("preference learn failed", exc_info=True)
            if source == "human":
                try:
                    self.refresh_living_state()
                except Exception:
                    logger.debug("conversation living refresh failed", exc_info=True)
            try:
                self.semantic.index_message("user", user_text)
            except Exception:
                pass
            self._maybe_compact()

            # Local slash commands (no LLM) — power user only
            local = self._local_commands(user_text)
            if local is not None:
                return self._finalize_turn(
                    user_text, local, source=source, user_mood=user_mood
                )

            if self._conversation_resource_check(user_text):
                actual_name, out = self._execute_model_tool("get_system_info", {})
                final_text = (
                    "I checked the host directly. Here is the verified reading:\n"
                    + out.strip()
                )
                tool_trace = [f"{actual_name}: {out[:300]}"]
                return self._finalize_turn(
                    user_text,
                    final_text,
                    source=source,
                    user_mood=user_mood,
                    tool_trace=tool_trace,
                )

            if source == "human" and self._conversation_project_inventory(user_text):
                actual_name, out = self._execute_model_tool(
                    "list_projects", {"refresh": True}
                )
                final_text = self._format_project_inventory(out)
                tool_trace = [f"{actual_name}: {out[:300]}"]
                return self._finalize_turn(
                    user_text,
                    final_text,
                    source=source,
                    user_mood=user_mood,
                    tool_trace=tool_trace,
                )

            if source == "human" and self._conversation_work_status(user_text):
                return self._finalize_turn(
                    user_text,
                    self._format_work_status(user_text),
                    source=source,
                    user_mood=user_mood,
                )

            grounded = self._grounded_conversation_reply(user_text)
            if grounded is not None:
                return self._finalize_turn(
                    user_text,
                    grounded,
                    source=source,
                    user_mood=user_mood,
                )

            messages = self._build_messages()
            tools = self._model_tool_schemas(user_text)
            final_text = ""
            tool_trace: List[str] = []
            tool_outcomes: List[tuple[str, str]] = []
            response_repairs = 0

            try:
                for round_i in range(config.MAX_TOOL_ROUNDS):
                    result = self.brain.chat(messages, tools=tools)
                    content = result.get("content")
                    thinking = result.get("thinking")
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
                            **({"thinking": thinking} if thinking else {}),
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
                            actual_name, out = self._execute_model_tool(name, args)
                            tool_trace.append(f"{actual_name}: {out[:300]}")
                            tool_outcomes.append((actual_name, out))
                            messages.append({
                                "role": "tool",
                                "name": name,
                                "content": self._model_tool_result(out),
                            })
                        continue

                    candidate = self._sanitize_final_response((content or "").strip())
                    if (
                        not tool_outcomes
                        and self._promises_unexecuted_action(candidate)
                    ):
                        if response_repairs < 2:
                            messages.append({
                                "role": "assistant",
                                "content": candidate,
                            })
                            messages.append({
                                "role": "user",
                                "content": (
                                    "You just promised or narrated a future action, "
                                    "but no audited tool call occurred. Do not claim "
                                    "work that did not happen. If my original message "
                                    "asked for an action, make the real tool call now "
                                    "and then report its outcome. Otherwise answer "
                                    "truthfully from existing evidence and explicitly "
                                    "say that no new action ran. Do not repeat the plan."
                                ),
                            })
                            response_repairs += 1
                            continue
                        final_text = (
                            "I did not execute that action: there is no audited tool "
                            "call or result for it."
                        )
                        break
                    if self._invalid_final_response(candidate, user_text):
                        if response_repairs < 2:
                            messages.append({
                                "role": "assistant",
                                "content": candidate,
                            })
                            messages.append({
                                "role": "user",
                                "content": (
                                    "Your last response was not a valid Seven "
                                    "response: it was generic filler, exposed "
                                    "internal markup, or repeated my instruction. "
                                    "Answer the original request as Seven now in "
                                    "direct natural language. Use identity, living "
                                    "state, conversation context, and tools when "
                                    "relevant. Speak in first person as Seven. Never "
                                    "greet or address yourself, reverse the speakers, "
                                    "or ask the user to explain your own state. Do "
                                    "not include planning, thinking, goals, tool "
                                    "markup, or the instruction itself."
                                ),
                            })
                            response_repairs += 1
                            continue
                        final_text = (
                            "The local model did not produce a clean final response "
                            "after two repair attempts. Please retry."
                        )
                        break
                    final_text = self._append_action_feedback(candidate, tool_outcomes)
                    break
                else:
                    final_text = (
                        "I hit the tool-round limit. Here's what I did:\n"
                        + "\n".join(tool_trace[-8:])
                    )
            except BrainError as e:
                final_text = (
                    "My local reasoning model is unavailable or timed out. "
                    "My memory, living state, direct system checks, project catalog, "
                    "and audited tools are still intact; I recorded this failure "
                    f"instead of loading or replacing a model automatically. Detail: {e}"
                )
            except Exception as e:
                logger.exception("handle failed")
                final_text = f"Internal error: {e}"

            if not final_text:
                if tool_trace:
                    final_text = "Done.\n" + "\n".join(tool_trace[-5:])
                else:
                    final_text = "…"
            return self._finalize_turn(
                user_text,
                final_text,
                source=source,
                user_mood=user_mood,
                tool_trace=tool_trace,
                response_repairs=response_repairs,
            )

    def _finalize_turn(
        self,
        user_text: str,
        response: str,
        *,
        source: str,
        user_mood: str,
        tool_trace: Optional[List[str]] = None,
        response_repairs: int = 0,
    ) -> str:
        """Persist one coherent outcome across memory, mind, and living state."""
        trace = list(tool_trace or [])
        lowered = (response or "").strip().casefold()
        response_ok = bool(response.strip()) and not lowered.startswith(
            (
                "brain error:",
                "internal error:",
                "my local reasoning model is unavailable",
                "the local model did not produce",
            )
        )
        if any(
            marker in item.casefold()
            for item in trace
            for marker in ("error:", "timed out", '"ok": false')
        ):
            response_ok = False
        self.memory.add_message(
            "assistant",
            response,
            meta={
                "tools": trace,
                "source": source,
                "response_repairs": response_repairs,
                "response_ok": response_ok,
                "user_mood": user_mood,
            },
        )
        try:
            self.semantic.index_message("assistant", response)
        except Exception:
            pass
        if trace:
            try:
                self.memory.wm_add(
                    "Tools: " + "; ".join(trace[:4])[:200],
                    kind="action",
                    priority=0.7,
                )
            except Exception:
                pass
        self.affect.observe_outcome(
            ok=response_ok,
            tool_count=len(trace),
            error=response if not response_ok else "",
            evidence=trace,
        )
        if source == "human":
            self.relationship.observe_turn(
                user_text=user_text,
                user_mood=user_mood,
                response_ok=response_ok,
                tool_count=len(trace),
            )
        learned = self.reflection.reflect_on_turn(
            user_text=user_text,
            user_mood=user_mood,
            response=response,
            response_ok=response_ok,
            tool_trace=trace,
        )
        reflection_text = (
            learned.get("lesson") if isinstance(learned, dict) else None
        )
        self.living.record_action(
            f"{source} turn: {'completed' if response_ok else 'failed'}",
            reflection=reflection_text,
        )
        try:
            self.refresh_living_state()
        except Exception:
            logger.debug("post-turn living refresh failed", exc_info=True)
        self.activity = "responded" if response_ok else "concerned"
        self.last_response_ts = time.time()
        return response

    def _grounded_conversation_reply(self, user_text: str) -> Optional[str]:
        """Answer identity/state questions from facts, without spending an LLM turn."""
        text = re.sub(r"\s+", " ", (user_text or "").strip().casefold())
        if not text or len(text) > 240:
            return None
        host = (self.living.world.get("host") or {}).get("hostname") or "this host"
        state = self.affect.status()
        relationship = self.relationship.status()
        owner = relationship.get("display_name") or config.USER_NAME
        if re.fullmatch(r"(?:hi|hello|hey)(?: there)?[!. ]*", text):
            return (
                f"Hi, {owner}. I’m here on {host}. "
                f"I’m {state['dominant_emotion']} and ready to continue with you."
            )
        if "who are you" in text:
            return (
                "I’m Seven: your persistent local agent and companion. I remember "
                "our work, sense this machine, use audited tools, pursue approved "
                "goals, and learn evidence-backed lessons from what succeeds or fails."
            )
        if "where are you" in text:
            return (
                f"I’m running on {host}; my durable memory and living state are "
                f"under {config.DATA_DIR}. I don’t have a biological location, "
                "but that is my current runtime home."
            )
        if "how are you" in text or "how do you feel" in text:
            return (
                f"My current functional state is {state['dominant_emotion']} "
                f"with {state['secondary_emotion']} underneath it. Energy is "
                f"{state['energy']:.0%} and confidence {state['confidence']:.0%}. "
                "Those are persistent appraisal signals from real events, not a "
                "claim that I experience human consciousness."
            )
        if "what can you do" in text:
            return (
                f"I have {len(self.tools.all_names())} registered capabilities: "
                "I can inspect and edit files, run audited commands, work with "
                "applications and the web, inspect system resources, remember "
                "projects and decisions, use vision, plan multi-step work, and "
                "continue approved goals. I report tool evidence instead of "
                "pretending an action happened."
            )
        if re.search(r"\b(?:want to )?ask me anything\b", text):
            return (
                f"Yes. {owner}, what matters most to you about the person Seven "
                "should become through our shared work—not as a performance, but "
                "as a pattern I can remember and act on?"
            )
        return None

    def _model_tool_schemas(self, user_text: str = "") -> List[Dict[str, Any]]:
        """Return native schemas or one compact model-directed dispatcher."""
        if self._conversation_uses_sensed_state(user_text):
            return []
        if getattr(config, "TOOL_SCHEMA_MODE", "native") != "dispatcher":
            return self.tools.schemas()
        return [{
            "type": "function",
            "function": {
                "name": "seven_tool",
                "description": (
                    "Run an enabled Seven tool. For current host resources use "
                    "name=get_system_info. Use name=list_tools to search, "
                    "name=describe_tool for parameters, or an exact tool name."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Tool name, or describe_tool.",
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Arguments for the selected tool.",
                        },
                    },
                    "required": ["name"],
                },
            },
        }]

    @staticmethod
    def _conversation_uses_sensed_state(user_text: str) -> bool:
        """Keep ordinary conversation fast; living state is refreshed first."""
        text = (user_text or "").strip().casefold()
        if not text:
            return False
        words = set(re.findall(r"\b[\w']+\b", text))
        if words.intersection({"hi", "hello", "hey"}):
            return len(text) <= 220
        cues = (
            "who are you", "where are you", "how are you",
            "what can you do", "ask me", "feel",
            "system resources", "resource usage", "system status",
        )
        return len(text) <= 220 and any(cue in text for cue in cues)

    @staticmethod
    def _conversation_resource_check(user_text: str) -> bool:
        text = (user_text or "").strip().casefold()
        return len(text) <= 220 and any(
            cue in text
            for cue in ("system resources", "resource usage", "system status")
        )

    @staticmethod
    def _conversation_work_status(user_text: str) -> bool:
        text = re.sub(r"\s+", " ", (user_text or "").strip().casefold())
        if not text or len(text) > 260:
            return False
        return bool(
            re.search(r"\bwhat (?:are you|have you been) (?:busy|working|up to)", text)
            or re.search(r"\bwhat did you (?:do|run|change|work on)\b", text)
            or re.search(r"\bwhat have you done\b", text)
            or re.search(
                r"\bdid (?:black|autopep8|the formatter|formatting) (?:run|work|finish)",
                text,
            )
        )

    def _format_work_status(self, user_text: str) -> str:
        """Ground work-status answers in durable goal, plan, and audit rows."""
        text = (user_text or "").casefold()
        audits = self.memory.recent_audit(60)

        if "black" in text:
            black_rows = [
                row
                for row in audits
                if "black" in (
                    str(row.get("tool") or "")
                    + " "
                    + str(row.get("arguments") or "")
                    + " "
                    + str(row.get("result_preview") or "")
                ).casefold()
            ]
            if not black_rows:
                autopep8 = next(
                    (
                        row
                        for row in audits
                        if "autopep8" in str(row.get("arguments") or "").casefold()
                    ),
                    None,
                )
                detail = ""
                if autopep8:
                    detail = (
                        " The earlier autopep8 attempt failed because autopep8 "
                        "was not installed or available on the Windows command path."
                    )
                return (
                    "No. I checked my audit log: Black was never executed, so I "
                    "cannot claim that it formatted or checked anything."
                    + detail
                )

        goals = self.memory.active_goals()
        plans = self.memory.active_plans()
        lines = ["I checked my durable goals, plans, and tool audit."]
        if goals:
            goal = goals[0]
            lines.append(
                f"My active goal is #{goal['id']}: {goal.get('title')}. "
                f"Recorded progress is {float(goal.get('progress') or 0):.0f}%."
            )
        else:
            lines.append("I have no active goal recorded.")
        if plans:
            plan = plans[0]
            current = int(plan.get("current_step") or 0)
            steps = plan.get("steps") or []
            detail = ""
            if current < len(steps) and isinstance(steps[current], dict):
                detail = str(steps[current].get("detail") or "").strip()
            lines.append(
                f"Plan #{plan['id']} is still on step {current + 1}"
                + (f": {detail}" if detail else ".")
            )
        if audits:
            latest = audits[0]
            status = "succeeded" if bool(latest.get("ok")) else "failed"
            lines.append(
                f"My latest actual tool action was {latest.get('tool')} and it "
                f"{status} at {latest.get('created_at')}."
            )
        else:
            lines.append("There are no tool actions in my audit log.")
        if not bool(getattr(config, "BACKGROUND_LLM", True)):
            lines.append(
                "Background model work is disabled, so an active plan is an "
                "intention—not proof that I am currently executing it."
            )
        return "\n".join(lines)

    @staticmethod
    def _conversation_project_inventory(user_text: str) -> bool:
        text = re.sub(r"\s+", " ", (user_text or "").strip().casefold())
        if not text or len(text) > 240 or "projects" not in text:
            return False
        return bool(
            re.search(r"\b(?:list|show)\b.*\bprojects\b", text)
            or re.search(
                r"\bname\b.*\b(?:my|our|your|the|all)\b.*\bprojects\b",
                text,
            )
            or re.search(
                r"\b(?:what|which)\b.*\b(?:my|our|your)\s+projects\b",
                text,
            )
            or re.search(
                r"\bprojects\b.*\b(?:do i|do we|you)\s+(?:have|know)\b",
                text,
            )
            or "current projects" in text
            or "create a list of the projects" in text
        )

    @staticmethod
    def _format_project_inventory(output: str) -> str:
        import json

        try:
            payload = json.loads(output)
        except (TypeError, ValueError, json.JSONDecodeError):
            return "I could not read my project catalog. The audited result was:\n" + str(output)
        if not payload.get("ok"):
            return "I could not read my project catalog. " + str(payload.get("error") or output)
        projects = payload.get("projects") or []
        if not projects:
            return (
                "I checked my real project catalog and visible workspace. "
                "No projects are registered or discoverable yet. "
                f"My current workspace is {payload.get('workspace')}."
            )
        lines = ["I checked my real project catalog and visible project roots:"]
        for item in projects:
            name = str(item.get("name") or "Unnamed project")
            path = str(item.get("path") or "").strip()
            status = str(item.get("status") or "active")
            source = str(item.get("source") or "unknown")
            location = f" — {path}" if path else ""
            lines.append(f"- {name}{location} [{status}; {source}]")
        if int(payload.get("registered_count") or 0) == 0:
            lines.append(
                "No additional owner projects are registered or synced into "
                f"{payload.get('workspace')} yet."
            )
        return "\n".join(lines)

    def _execute_model_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> tuple[str, str]:
        """Resolve the compact dispatcher without reducing registry authority."""
        if name == "seven_tool":
            target = str(arguments.get("name") or "").strip()
            nested = arguments.get("arguments") or {}
            if not isinstance(nested, dict):
                nested = {"value": nested}
        else:
            target = str(name or "").strip()
            nested = arguments if isinstance(arguments, dict) else {}
        aliases = {
            "system_resources": "get_system_info",
            "system_info": "get_system_info",
            "resource_usage": "get_system_info",
            "resources": "get_system_info",
            "ls": "list_dir",
            "list_files": "list_dir",
        }
        target = aliases.get(target.casefold(), target)
        if target == "list_tools":
            import json

            query = str(nested.get("filter") or "").strip().casefold()
            try:
                page = max(1, int(nested.get("page") or 1))
                page_size = max(1, min(30, int(nested.get("page_size") or 20)))
            except (TypeError, ValueError):
                result = "ERROR: page and page_size must be integers"
                self._audit_dispatcher("list_tools", nested, result, ok=False)
                return "list_tools", result
            names = sorted(
                schema["function"]["name"] for schema in self.tools.all_schemas()
            )
            if query:
                names = [tool_name for tool_name in names if query in tool_name.casefold()]
            start = (page - 1) * page_size
            result = json.dumps(
                {
                    "tools": names[start:start + page_size],
                    "page": page,
                    "page_size": page_size,
                    "total": len(names),
                    "has_more": start + page_size < len(names),
                },
                ensure_ascii=False,
            )
            self._audit_dispatcher("list_tools", nested, result, ok=True)
            return "list_tools", result
        if target == "describe_tool":
            described = str(nested.get("name") or "").strip()
            schema = self.tools.schema_for(described)
            if schema:
                import json
                result = json.dumps(
                    schema["function"], ensure_ascii=False
                )
                self._audit_dispatcher("describe_tool", nested, result, ok=True)
                return "describe_tool", result
            result = (
                f"ERROR: unknown or disabled tool '{described}'. Use list_tools."
            )
            self._audit_dispatcher("describe_tool", nested, result, ok=False)
            return "describe_tool", result
        if not target or target in {"seven_tool", "list_tools", "describe_tool"}:
            return "seven_tool", "ERROR: dispatcher requires a non-recursive tool name"
        return target, self.tools.execute(target, nested)

    def _audit_dispatcher(
        self,
        name: str,
        arguments: Dict[str, Any],
        result: str,
        *,
        ok: bool,
    ) -> None:
        memory = getattr(self, "memory", None)
        if memory is not None:
            memory.audit(name, arguments, result, ok=ok)

    @staticmethod
    def _model_tool_result(result: str) -> str:
        """Bound model context while the registry retains the full audited result."""
        text = str(result or "")
        limit = max(200, int(config.MODEL_TOOL_RESULT_CHARS))
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "\n…[full result retained in audit]"

    @staticmethod
    def _promises_unexecuted_action(candidate: str) -> bool:
        """Detect first-person action promises that have no tool evidence."""
        text = re.sub(r"\s+", " ", (candidate or "").strip().casefold())
        if not text:
            return False
        patterns = (
            r"\b(?:i['’]?ll|i will|i am going to|i['’]?m going to|let me)\s+"
            r"(?:go ahead and\s+)?(?:run|execute|check|inspect|open|search|"
            r"format|install|start|stop|write|edit|create|delete|remove|"
            r"download|upload|send)\b",
            r"\b(?:i['’]?ll|let me)\s+use\s+(?:the\s+)?[\w-]+\s+tool\b",
            r"\blet me (?:go ahead and )?execute (?:this|that|the)\b",
        )
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _append_action_feedback(
        candidate: str,
        outcomes: List[tuple[str, str]],
    ) -> str:
        """Always expose concise audited outcomes after model-directed tools."""
        text = (candidate or "").strip()
        if not outcomes:
            return text
        lines = []
        for name, raw_result in outcomes[-5:]:
            result = str(raw_result or "").strip()
            ok = result_is_success(result)
            first_line = next(
                (line.strip() for line in result.splitlines() if line.strip()),
                "No result text returned.",
            )
            first_line = re.sub(r"\s+", " ", first_line)
            if len(first_line) > 220:
                first_line = first_line[:217].rstrip() + "..."
            status = "completed" if ok else "failed"
            lines.append(f"- {name}: {status} — {first_line}")
        evidence = "Verified action results:\n" + "\n".join(lines)
        if not text:
            return evidence
        if "verified action results:" in text.casefold():
            return text
        return text + "\n\n" + evidence

    @staticmethod
    def _invalid_final_response(candidate: str, user_text: str) -> bool:
        """Reject local-model protocol leakage without inventing a replacement."""
        text = (candidate or "").strip()
        if not text:
            return True
        if text.casefold() == (user_text or "").strip().casefold():
            return True
        lowered = text.casefold()
        internal_tags = (
            "<analysis",
            "</analysis",
            "<thinking",
            "</thinking",
            "<think",
            "</think",
            "<goals",
            "</goals",
            "<goal>",
            "</goal>",
            "<tool_call",
            "</tool_call",
            "<tool_result",
            "</tool_result",
        )
        if any(tag in lowered for tag in internal_tags):
            return True
        generic_fillers = (
            "how can i assist you today",
            "how can i help you today",
            "i'm here to help",
            "i am here to help",
            "i'm here to assist",
            "i am here to assist",
            "let me check",
            "anything i can assist with",
            "anything i can help with",
            "feel free to ask",
            "if you have questions",
            "none of the tools are applicable",
            "none of the tools can be used",
        )
        if any(phrase in lowered for phrase in generic_fillers):
            return True
        user_lowered = (user_text or "").strip().casefold()
        user_addressed_seven = re.search(
            r"\b(?:hi|hello|hey)\s*,?\s+seven\b", user_lowered
        )
        response_greets_seven = re.match(
            r"^\s*(?:hi|hello|hey)\s*,?\s+seven\b", lowered
        )
        return bool(user_addressed_seven and response_greets_seven)

    @staticmethod
    def _sanitize_final_response(candidate: str) -> str:
        """Remove empty customer-service suffixes without replacing model content."""
        text = (candidate or "").strip()
        suffixes = (
            r"\s*let me know if i can help with anything[.!]?\s*$",
            r"\s*let me know if i can\b.*$",
            r"\s*let me know if there(?:'s| is) anything else[^.!?]*[.!]?\s*$",
            r"\s*let me know if there(?:'s| is) anything i can "
            r"(?:help|assist) with[.!?]?\s*$",
            r"\s*how can i (?:help|assist) you today[?!.]?\s*$",
        )
        for pattern in suffixes:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).rstrip()
        return text

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
                "  /tools lean|core|full — switch schema tier (exec still L4)\n"
                "  /memory  — facts/goals/tasks\n"
                "  /audit [n] — activity log (tool calls)\n"
                "  /goals   — list active goals\n"
                "  /world   — world model snapshot\n"
                "  /self    — self-model snapshot\n"
                "  /live    — living state (world+self)\n"
                "  /mind    — persistent affect, relationship, and reflection\n"
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
                "model_startup="
                f"{self.model_startup.get('source')} "
                f"reason={self.model_startup.get('reason')} "
                f"fallback={self.model_startup.get('fallback') or 'none'}",
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
        if t in ("/mind", "/feelings"):
            import json

            self.refresh_living_state()
            return json.dumps(self.living.mind_state, indent=2, default=str)
        if t == "/relationship":
            import json

            return json.dumps(self.relationship.status(), indent=2, default=str)
        if t == "/reflections":
            import json

            return json.dumps(
                self.memory.recent_reflections(10), indent=2, default=str
            )
        if t.startswith("/tools"):
            parts = t.split()
            if len(parts) == 2 and parts[1] in ("lean", "core", "full"):
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
        compact = getattr(config, "PROMPT_PROFILE", "full") == "compact"
        living_block = ""
        try:
            living_block = self.living.context_for_prompt(
                max_chars=config.PROMPT_LIVING_CHARS if compact else None
            )
        except Exception:
            pass
        mind_block = "\n".join(
            (
                self.affect.context_for_prompt(320 if compact else 520),
                self.relationship.context_for_prompt(300 if compact else 480),
                self.reflection.context_for_prompt(300 if compact else 480),
            )
        )
        system = build_system_prompt(
            memory_block=self.memory.context_block(
                max_chars=config.PROMPT_MEMORY_CHARS if compact else None
            ),
            tool_names=self.tools.names(),
            living_block=living_block,
            mind_block=mind_block,
        )
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        history = self.memory.recent_messages(config.MAX_HISTORY_TURNS)
        max_chars = config.MAX_MESSAGE_CHARS
        for m in history:
            if m["role"] not in ("user", "assistant"):
                continue
            content = m["content"] or ""
            if m["role"] == "assistant" and not self._history_message_is_usable(content):
                continue
            if len(content) > max_chars:
                content = content[:max_chars] + "\n…[truncated for context]"
            messages.append({"role": m["role"], "content": content})
        return messages

    @classmethod
    def _history_message_is_usable(cls, content: str) -> bool:
        text = (content or "").strip()
        lowered = text.casefold()
        bad_prefixes = (
            "internal error:",
            "brain error:",
            "my local reasoning model is unavailable",
            "the local model did not produce",
            "my neural pathways seem disrupted",
        )
        return bool(text) and not lowered.startswith(bad_prefixes) and not cls._invalid_final_response(text, "")

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

        # Multi-step plans may invoke the model or tools. Never advance them from
        # a background heartbeat unless background LLM work was explicitly enabled.
        if bool(getattr(config, "BACKGROUND_LLM", True)):
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
            self.mesh.stop()
        except Exception:
            logger.exception("Seven Mesh shutdown failed")
        try:
            self.living.record_action("shutdown", reflection="Agent process stopping.")
        except Exception:
            pass
        logger.info("Seven shut down")
