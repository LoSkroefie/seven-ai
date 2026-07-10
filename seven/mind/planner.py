"""
Multi-step planner — create and advance real plans (not single-shot theater).
"""
from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.planner")


class Planner:
    def __init__(self, agent: "Seven"):
        self.agent = agent

    def create_from_goal(self, goal_id: int) -> Optional[Dict[str, Any]]:
        goal = self.agent.memory.get_goal(goal_id)
        if not goal:
            return None
        title = goal.get("title") or f"goal {goal_id}"
        detail = goal.get("detail") or ""
        steps = self._llm_steps(title, detail)
        if not steps:
            steps = self._default_steps(title)
        pid = self.agent.memory.create_plan(title=f"Plan: {title}", steps=steps, goal_id=goal_id)
        plan = self.agent.memory.get_plan(pid)
        self.agent.memory.wm_add(f"Plan #{pid} for goal #{goal_id}: {title}", kind="plan", priority=0.9)
        return plan

    def _default_steps(self, title: str) -> List[dict]:
        return [
            {"action": "survey", "detail": f"Inspect environment related to: {title}", "done": False},
            {"action": "act", "detail": f"Do one concrete tool action for: {title}", "done": False},
            {"action": "record", "detail": f"Write findings to workspace/notes for: {title}", "done": False},
            {"action": "conclude", "detail": f"Form an opinion/conclusion about: {title}", "done": False},
        ]

    def _llm_steps(self, title: str, detail: str) -> List[dict]:
        try:
            raw = self.agent.brain.generate(
                f"Break this goal into 3-6 concrete tool-using steps for a local AI agent "
                f"with shell/files/web/desktop tools.\nGoal: {title}\nDetail: {detail}\n"
                'Return JSON array only: [{"action":"short","detail":"what to do"}]',
                system="Planner. JSON only. Steps must be executable with tools.",
                temperature=0.4,
                max_tokens=400,
            )
            raw = (raw or "").strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            data = json.loads(raw)
            if not isinstance(data, list):
                return []
            steps = []
            for item in data[:8]:
                if isinstance(item, dict):
                    steps.append({
                        "action": str(item.get("action") or "step")[:80],
                        "detail": str(item.get("detail") or "")[:400],
                        "done": False,
                    })
                elif isinstance(item, str):
                    steps.append({"action": "step", "detail": item[:400], "done": False})
            return steps
        except Exception as e:
            logger.debug("LLM plan failed: %s", e)
            return []

    def execute_next_step(self, plan_id: Optional[int] = None) -> str:
        plans = self.agent.memory.active_plans()
        plan = None
        if plan_id is not None:
            plan = self.agent.memory.get_plan(int(plan_id))
        elif plans:
            plan = plans[0]
        if not plan or plan.get("status") != "active":
            return "No active plan."

        steps = plan.get("steps") or []
        cur = int(plan.get("current_step") or 0)
        if cur >= len(steps):
            return f"Plan #{plan['id']} already complete."

        step = steps[cur] if isinstance(steps[cur], dict) else {"detail": str(steps[cur])}
        detail = step.get("detail") or step.get("action") or "do next step"
        prompt = (
            f"[PLAN/{plan['id']} step {cur + 1}/{len(steps)}] {plan.get('title')}\n"
            f"Current step: {step.get('action')} — {detail}\n"
            "Use tools to complete THIS step only. Then report results briefly.\n"
            "Do not greet. Act."
        )
        audit_before = 0
        rows = self.agent.memory.recent_audit(1)
        if rows:
            audit_before = int(rows[0]["id"])
        reply = self.agent.handle(prompt)
        new = self.agent.memory.audits_since(audit_before)
        # Any tool execution counts as work for plan progress (including sysinfo/list)
        real = [a for a in new if a.get("tool")]
        note = reply or ""

        # If the LLM only talked, force a concrete survey action so plans don't stall
        if not real:
            forced = []
            try:
                forced.append(
                    "list_dir: "
                    + self.agent.tools.execute("list_dir", {"path": str(
                        __import__("seven.config", fromlist=["WORKSPACE_DIR"]).WORKSPACE_DIR
                    )})[:400]
                )
                forced.append(
                    "get_system_info: "
                    + self.agent.tools.execute("get_system_info", {})[:300]
                )
                action = (step.get("action") or "").lower()
                if "web" in action or "research" in detail.lower() or "search" in detail.lower():
                    forced.append(
                        "web_search: "
                        + self.agent.tools.execute(
                            "web_search",
                            {"query": detail[:80], "max_results": 3},
                        )[:400]
                    )
                note = (note + "\n\n[forced tools]\n" + "\n".join(forced))[:2000]
                real = [{"tool": "forced_survey"}]
            except Exception as e:
                logger.warning("forced plan tools failed: %s", e)

        if real:
            advanced = self.agent.memory.advance_plan(int(plan["id"]), note=note[:400])
            if len(real) >= 2:
                try:
                    self.agent.memory.save_skill(
                        name=f"plan_{plan['id']}_step_{cur}",
                        description=detail[:200],
                        steps=[{"tool": a.get("tool"), "args": a.get("arguments")} for a in real[:6] if a.get("tool") != "forced_survey"],
                    )
                except Exception:
                    pass
            status = (advanced or {}).get("status")
            return (
                f"Plan #{plan['id']} step {cur + 1} done (tools={len(real)}). "
                f"status={status}\n{note[:400]}"
            )
        return f"Plan #{plan['id']} step {cur + 1} — no real tools ran. Unchanged.\n{note[:300]}"
