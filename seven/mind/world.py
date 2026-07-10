"""
World sensing — structured snapshot of machine + time + open work.
No LLM required. Cheap enough for every heartbeat.
"""
from __future__ import annotations

import os
import platform
import socket
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


def sense_world(
    memory=None,
    brain=None,
    last_user_ts: Optional[float] = None,
) -> Dict[str, Any]:
    now = time.time()
    idle_min = None
    if last_user_ts is not None:
        idle_min = round((now - last_user_ts) / 60.0, 2)

    snap: Dict[str, Any] = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "unix": now,
        "host": {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "user": os.environ.get("USERNAME") or os.environ.get("USER"),
            "cwd": os.getcwd(),
        },
        "user": {
            "idle_minutes": idle_min,
            "last_user_ts": last_user_ts,
        },
        "resources": _resources(),
        "ollama": _ollama(brain),
        "work": _work(memory),
        "time": {
            "local": datetime.now().strftime("%Y-%m-%d %H:%M:%S %A"),
            "hour": datetime.now().hour,
            "is_quiet_hours": _quiet_hours(),
        },
    }
    return snap


def _resources() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        import psutil
        vm = psutil.virtual_memory()
        out["ram_total_gb"] = round(vm.total / 1e9, 1)
        out["ram_used_pct"] = vm.percent
        out["cpu_pct"] = psutil.cpu_percent(interval=0.15)
        out["cpu_count"] = psutil.cpu_count()
        disk = psutil.disk_usage(os.path.expanduser("~"))
        out["disk_free_gb"] = round(disk.free / 1e9, 1)
        out["disk_used_pct"] = disk.percent
    except Exception as e:
        out["error"] = str(e)
    return out


def _ollama(brain) -> Dict[str, Any]:
    if brain is None:
        return {"ok": None}
    try:
        p = brain.ping()
        return {
            "ok": p.get("ok"),
            "model": p.get("model"),
            "loaded": p.get("loaded"),
            "has_vision": p.get("has_vision"),
            "hint": p.get("hint"),
            "error": p.get("error"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _work(memory) -> Dict[str, Any]:
    if memory is None:
        return {}
    try:
        goals = memory.active_goals()
        tasks = memory.open_tasks()
        return {
            "active_goals": [
                {"id": g["id"], "title": g.get("title"), "progress": g.get("progress")}
                for g in goals[:8]
            ],
            "open_tasks": [
                {"id": t["id"], "title": t.get("title"), "due_at": t.get("due_at")}
                for t in tasks[:8]
            ],
            "goal_count": len(goals),
            "task_count": len(tasks),
            "message_count": memory.message_count(),
            "recent_failures": _recent_failures(memory),
        }
    except Exception as e:
        return {"error": str(e)}


def _recent_failures(memory, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        rows = memory.recent_audit(30)
        fails = [r for r in rows if not r.get("ok")]
        out = []
        for r in fails[:limit]:
            out.append({
                "tool": r.get("tool"),
                "preview": (r.get("result_preview") or "")[:120],
                "at": r.get("created_at"),
            })
        return out
    except Exception:
        return []


def _quiet_hours() -> bool:
    """Default quiet: 23:00–07:00 local — autonomy still runs light."""
    h = datetime.now().hour
    return h >= 23 or h < 7


def world_summary(world: Dict[str, Any]) -> str:
    """One-screen text for prompts /status."""
    host = world.get("host") or {}
    res = world.get("resources") or {}
    oll = world.get("ollama") or {}
    work = world.get("work") or {}
    user = world.get("user") or {}
    t = world.get("time") or {}
    lines = [
        f"time={t.get('local')} quiet={t.get('is_quiet_hours')}",
        f"host={host.get('hostname')} user={host.get('user')} os={host.get('os')}",
        f"cpu={res.get('cpu_pct')}% ram={res.get('ram_used_pct')}% disk_free={res.get('disk_free_gb')}GB",
        f"ollama_ok={oll.get('ok')} model={oll.get('model')} loaded={oll.get('loaded')}",
        f"user_idle_min={user.get('idle_minutes')} goals={work.get('goal_count')} tasks={work.get('task_count')}",
    ]
    for g in (work.get("active_goals") or [])[:3]:
        lines.append(f"  goal #{g['id']}: {g.get('title')} ({g.get('progress')}%)")
    fails = work.get("recent_failures") or []
    if fails:
        lines.append(f"recent_tool_failures={len(fails)} last={fails[0].get('tool')}")
    return "\n".join(lines)
