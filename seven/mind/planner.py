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
                f"with shell/files/web/desktop tools. Use exact registered tool names, "
                f"including list_projects for project catalogs, list_dir for directories, "
                f"search_files for files, and run_shell for commands. Never write aliases "
                f"such as ls, find, or mkdir as tool names.\n"
                f"Goal: {title}\nDetail: {detail}\n"
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
        if plan.get("goal_id") is not None:
            goal = self.agent.memory.get_goal(int(plan["goal_id"]))
            if not goal or goal.get("status") not in {"active", "verifying"}:
                status = (goal or {}).get("status") or "missing"
                return (
                    f"Plan #{plan['id']} is paused because linked goal "
                    f"#{plan['goal_id']} is {status}."
                )

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
        reply = self.agent.handle(prompt, source="planner")
        new = self.agent.memory.audits_since(audit_before)
        observational = {
            "list_dir", "list_goals", "list_tasks", "list_notes",
            "list_projects", "list_tools", "describe_tool",
            "search_memory", "get_system_info",
        }
        real = [
            a for a in new
            if a.get("tool") and bool(a.get("ok")) and a.get("tool") not in observational
        ]
        note = reply or ""

        if real:
            advanced = self.agent.memory.advance_plan(int(plan["id"]), note=note[:400])
            if len(real) >= 2:
                try:
                    candidate_steps = []
                    for audit in real[:6]:
                        args = audit.get("arguments") or {}
                        if isinstance(args, str):
                            args = json.loads(args)
                        if not isinstance(args, dict):
                            raise ValueError("audit arguments are not structured")
                        candidate_steps.append({"tool": audit.get("tool"), "args": args})
                    self.agent.memory.propose_skill_candidate(
                        name=f"plan_{plan['id']}_step_{cur}",
                        description=detail[:200],
                        steps=candidate_steps,
                        source_goal_id=plan.get("goal_id"),
                        source_plan_id=int(plan["id"]),
                    )
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    logger.warning("skill candidate capture failed: %s", exc)
            status = (advanced or {}).get("status")
            return (
                f"Plan #{plan['id']} step {cur + 1} done (tools={len(real)}). "
                f"status={status}\n{note[:400]}"
            )
        failed = [a for a in new if a.get("tool") and not bool(a.get("ok"))]
        return (
            f"Plan #{plan['id']} step {cur + 1} — no successful outcome evidence; "
            f"unchanged (failed_tools={len(failed)}).\n{note[:300]}"
        )
