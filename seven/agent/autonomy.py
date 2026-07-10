"""
Real autonomy helpers for Seven Real.
- Goal steps only count when tools actually ran (audit delta)
- Heartbeat logs notes, never empty greetings
- Work sessions focus one goal for N minutes
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from seven import config

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.autonomy")


@dataclass
class WorkSession:
    goal_id: int
    ends_at: float  # time.time()
    started_at: float = field(default_factory=time.time)
    steps_done: int = 0

    def active(self) -> bool:
        return time.time() < self.ends_at

    def remaining_min(self) -> float:
        return max(0.0, (self.ends_at - time.time()) / 60.0)


def format_audit(rows: List[Dict[str, Any]], limit: int = 20) -> str:
    """Pretty activity log for /audit."""
    if not rows:
        return "No tool activity recorded yet."
    lines = ["# Activity log (most recent first)", ""]
    for r in rows[:limit]:
        ok = "OK" if r.get("ok") else "FAIL"
        ts = (r.get("created_at") or "")[:19].replace("T", " ")
        tool = r.get("tool") or "?"
        preview = (r.get("result_preview") or "").replace("\n", " ")
        if len(preview) > 140:
            preview = preview[:140] + "…"
        args = r.get("arguments") or ""
        if isinstance(args, str) and len(args) > 80:
            args = args[:80] + "…"
        lines.append(f"## [{r.get('id')}] {ts}  {tool}  {ok}")
        if args:
            lines.append(f"  args: {args}")
        lines.append(f"  → {preview}")
        lines.append("")
    return "\n".join(lines)


class AutonomyEngine:
    """Attached to Seven; drives goal steps and heartbeat work."""

    def __init__(self, agent: "Seven"):
        self.agent = agent
        self.session: Optional[WorkSession] = None
        self.last_work_ts: float = 0.0
        self.min_work_interval = float(getattr(config, "AUTONOMY_MIN_INTERVAL", 60))

    # ── work sessions ──────────────────────────────────────────────────

    def start_session(self, goal_id: int, minutes: float = 15.0) -> str:
        goals = {g["id"]: g for g in self.agent.memory.active_goals()}
        if goal_id not in goals and not self.agent.memory.get_goal(goal_id):
            # allow closed goals lookup
            g = self.agent.memory.get_goal(goal_id)
            if not g:
                return f"ERROR: no goal #{goal_id}. Use list_goals / add_goal first."
        g = self.agent.memory.get_goal(goal_id) or goals.get(goal_id)
        minutes = max(1.0, min(float(minutes), 180.0))
        self.session = WorkSession(
            goal_id=int(goal_id),
            ends_at=time.time() + minutes * 60.0,
        )
        title = (g or {}).get("title") or f"goal {goal_id}"
        self.agent.memory.add_note(
            f"Work session started for goal #{goal_id}: {title} ({minutes:.0f} min)",
            title="autonomy",
        )
        return (
            f"Work session ON for goal #{goal_id} ({title}) — {minutes:.0f} min.\n"
            f"Heartbeat will focus this goal. /stopwork to end early. /workstatus for status."
        )

    def stop_session(self) -> str:
        if not self.session:
            return "No active work session."
        s = self.session
        self.session = None
        self.agent.memory.add_note(
            f"Work session stopped for goal #{s.goal_id} after {s.steps_done} steps.",
            title="autonomy",
        )
        return f"Work session stopped (goal #{s.goal_id}, steps={s.steps_done})."

    def session_status(self) -> str:
        if not self.session or not self.session.active():
            if self.session and not self.session.active():
                self.session = None
            return "No active work session."
        g = self.agent.memory.get_goal(self.session.goal_id)
        title = (g or {}).get("title", "?")
        prog = (g or {}).get("progress", 0)
        return (
            f"Work session: goal #{self.session.goal_id} ({title})\n"
            f"  progress={prog}%  steps_this_session={self.session.steps_done}\n"
            f"  remaining≈{self.session.remaining_min():.1f} min"
        )

    # ── goal step ──────────────────────────────────────────────────────

    def run_goal_step(self, goal_id: Optional[int] = None, reason: str = "manual") -> str:
        """
        Run one autonomous step on a goal. Progress updates only if tools ran.
        """
        now = time.time()
        if now - self.last_work_ts < self.min_work_interval and reason == "heartbeat":
            return "skipped: min interval"

        goal = None
        if goal_id is not None:
            goal = self.agent.memory.get_goal(int(goal_id))
        if goal is None and self.session and self.session.active():
            goal = self.agent.memory.get_goal(self.session.goal_id)
        if goal is None:
            active = self.agent.memory.active_goals()
            goal = active[0] if active else None
        if not goal:
            return "No active goals."

        if goal.get("status") not in (None, "active") and goal.get("status") != "active":
            if goal.get("status") == "done":
                return f"Goal #{goal['id']} already done."

        audit_before = self._latest_audit_id()
        prompt = self._step_prompt(goal, reason)
        logger.info("Autonomy step goal=#%s reason=%s", goal["id"], reason)

        # Use internal path that still goes through handle (tools + memory)
        reply = self.agent.handle(prompt)
        self.last_work_ts = time.time()

        new_audits = self.agent.memory.audits_since(audit_before)
        tools_ran = [a for a in new_audits if a.get("tool") not in ("", None)]
        real_work = [a for a in tools_ran if a.get("tool") not in ("remember_fact", "list_goals", "list_tasks", "list_notes", "search_memory", "get_system_info")]

        summary_bits = [
            f"goal=#{goal['id']} ({goal.get('title')})",
            f"reason={reason}",
            f"tools_total={len(tools_ran)} real_work={len(real_work)}",
        ]
        if real_work:
            names = ", ".join(a["tool"] for a in real_work[:6])
            summary_bits.append(f"tools=[{names}]")
            # Advance progress only after real tool work
            try:
                cur = float(goal.get("progress") or 0)
            except (TypeError, ValueError):
                cur = 0.0
            increment = min(15.0, 3.0 + 2.0 * len(real_work))
            new_prog = min(100.0, cur + increment)
            status = "done" if new_prog >= 100 else "active"
            last = f"{reason}: " + ", ".join(a["tool"] for a in real_work[:4])
            self.agent.memory.update_goal(
                int(goal["id"]),
                progress=new_prog,
                status=status,
                last_action=last[:200],
            )
            summary_bits.append(f"progress {cur:.0f}%→{new_prog:.0f}%")
            if status == "done":
                summary_bits.append("GOAL COMPLETE")
        else:
            summary_bits.append("no real tool work — progress unchanged")

        note_body = " | ".join(summary_bits) + "\n" + (reply or "")[:500]
        self.agent.memory.add_note(note_body, title="autonomy")

        if self.session and self.session.active() and self.session.goal_id == goal["id"]:
            self.session.steps_done += 1

        return note_body

    def _step_prompt(self, goal: Dict[str, Any], reason: str) -> str:
        detail = goal.get("detail") or ""
        last = goal.get("last_action") or "none"
        return (
            f"[AUTONOMY/{reason}] You are advancing goal #{goal['id']}: {goal.get('title')}\n"
            f"Detail: {detail}\n"
            f"Current progress: {goal.get('progress', 0)}%\n"
            f"Last action: {last}\n\n"
            "Rules:\n"
            "1. You MUST use tools (run_shell, read_file, write_file, run_python, web_search, etc.) "
            "to do ONE concrete step of real work.\n"
            "2. Do NOT only describe what you would do.\n"
            "3. After tools, briefly report results.\n"
            "4. Call update_goal only if you actually executed work tools.\n"
            "5. Do not greet. Do not ask how the user is.\n"
        )

    def _latest_audit_id(self) -> int:
        rows = self.agent.memory.recent_audit(1)
        if not rows:
            return 0
        return int(rows[0].get("id") or 0)

    # ── heartbeat planning ─────────────────────────────────────────────

    def collect_work(self, idle_min: float) -> List[str]:
        """Return human lines describing actionable work (empty if nothing)."""
        bits: List[str] = []
        mem = self.agent.memory

        # Active work session always counts
        if self.session and self.session.active():
            g = mem.get_goal(self.session.goal_id)
            if g and g.get("status") == "active":
                bits.append(
                    f"Work session goal #{g['id']}: {g.get('title')} "
                    f"({g.get('progress', 0):.0f}%, {self.session.remaining_min():.0f}m left)"
                )
            return bits
        if self.session and not self.session.active():
            self.session = None

        # Overdue tasks
        due = []
        now = datetime.now(timezone.utc)
        for t in mem.open_tasks():
            due_at = t.get("due_at")
            if not due_at:
                continue
            try:
                ds = due_at.replace("Z", "+00:00")
                dt = datetime.fromisoformat(ds)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt <= now:
                    due.append(t)
            except Exception:
                pass
        if due:
            bits.append(
                "Overdue tasks: " + "; ".join(f"#{t['id']} {t['title']}" for t in due[:5])
            )

        idle_need = float(getattr(config, "AUTONOMY_GOAL_IDLE_MIN", 10))
        if idle_min >= idle_need:
            goals = mem.active_goals()
            if goals:
                g = goals[0]
                bits.append(
                    f"Active goal #{g['id']}: {g.get('title')} at {g.get('progress', 0):.0f}%"
                )

        return bits

    def heartbeat_tick(self, idle_min: float) -> Optional[str]:
        """
        Run autonomous work if needed. Returns summary note or None if idle.
        Never greets.
        """
        work = self.collect_work(idle_min)
        if not work:
            logger.debug("heartbeat: nothing actionable (idle=%.1fm)", idle_min)
            return None

        # Prefer structured goal step when a goal is the work item
        goal_id = None
        if self.session and self.session.active():
            goal_id = self.session.goal_id
        else:
            for line in work:
                if line.startswith("Active goal #") or line.startswith("Work session goal #"):
                    try:
                        goal_id = int(line.split("#")[1].split(":")[0])
                    except (IndexError, ValueError):
                        pass

        if goal_id is not None:
            return self.run_goal_step(goal_id=goal_id, reason="heartbeat")

        # Task-only path: one handle turn
        audit_before = self._latest_audit_id()
        prompt = (
            "Autonomous heartbeat. User may be away. Real work only. "
            "Use tools. Do not greet. Do not ask how they are.\n"
            + "\n".join(work)
        )
        reply = self.agent.handle(prompt)
        self.last_work_ts = time.time()
        new_audits = self.agent.memory.audits_since(audit_before)
        note = f"heartbeat tasks tools={len(new_audits)}\n" + (reply or "")[:500]
        self.agent.memory.add_note(note, title="autonomy")
        return note
