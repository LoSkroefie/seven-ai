"""
Self-model — what Seven believes about her own capabilities and limits.
Updated from runtime signals, not random emotion theater.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from seven import config, __version__


def sense_self(
    world: Optional[Dict[str, Any]] = None,
    tools_active: Optional[List[str]] = None,
    tools_total: Optional[int] = None,
    work_session: Optional[str] = None,
    last_reflection: Optional[str] = None,
) -> Dict[str, Any]:
    world = world or {}
    oll = world.get("ollama") or {}
    res = world.get("resources") or {}

    ram_pct = res.get("ram_used_pct") or 0
    ollama_ok = bool(oll.get("ok"))

    # crude energy: inverse of resource pressure + ollama health
    energy = 1.0
    if ram_pct > 90:
        energy -= 0.35
    elif ram_pct > 80:
        energy -= 0.2
    if not ollama_ok:
        energy -= 0.5
    energy = max(0.05, min(1.0, energy))

    mode = "full"
    if not ollama_ok:
        mode = "degraded_no_llm"
    elif energy < 0.4:
        mode = "conserving"
    elif (world.get("time") or {}).get("is_quiet_hours"):
        mode = "quiet_hours"

    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "identity": {
            "name": config.BOT_NAME,
            "version": __version__,
            "nature": "local_autonomous_agent",
        },
        "capabilities": {
            "tools_active": tools_active or [],
            "tools_active_count": len(tools_active or []),
            "tools_total": tools_total,
            "tier": config.TOOL_TIER,
            "voice": config.ENABLE_VOICE,
            "provider": config.LLM_PROVIDER,
            "text_model": config.OLLAMA_MODEL,
            "vision_model": config.OLLAMA_VISION_MODEL,
        },
        "limits": {
            "vram_note": "8GB class: avoid dual text+vision load",
            "autonomy_level": config.AUTONOMY_LEVEL,
            "quiet_hours": (world.get("time") or {}).get("is_quiet_hours"),
        },
        "state": {
            "energy": round(energy, 2),
            "mode": mode,
            "ollama_ok": ollama_ok,
            "work_session": work_session,
            "last_reflection": last_reflection,
        },
        "intent": _intent(mode, world),
    }


def _intent(mode: str, world: Dict[str, Any]) -> str:
    work = world.get("work") or {}
    if mode == "degraded_no_llm":
        return "Recover: ensure Ollama is running; log health; skip heavy goals."
    goals = work.get("active_goals") or []
    tasks = work.get("open_tasks") or []
    if goals:
        g = goals[0]
        return f"Advance goal #{g['id']}: {g.get('title')}"
    if tasks:
        return f"Handle open tasks ({len(tasks)})"
    if mode == "quiet_hours":
        return "Quiet hours: light sense only unless overdue work."
    if mode == "conserving":
        return "Resources tight: prefer small steps, avoid vision."
    return "Idle: maintain world model; accept user work; optional self-improvement only if cheap."


def self_summary(self_state: Dict[str, Any]) -> str:
    st = self_state.get("state") or {}
    cap = self_state.get("capabilities") or {}
    ident = self_state.get("identity") or {}
    return (
        f"{ident.get('name')} v{ident.get('version')} mode={st.get('mode')} "
        f"energy={st.get('energy')} tools={cap.get('tools_active_count')}/{cap.get('tools_total')} "
        f"intent={self_state.get('intent')}"
    )
