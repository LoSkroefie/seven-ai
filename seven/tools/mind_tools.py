"""Tools for beliefs, working memory, skills, plans, semantic search, digests."""
from __future__ import annotations

import json
from typing import Optional

_memory = None
_agent = None


def set_context(memory=None, agent=None):
    global _memory, _agent
    if memory is not None:
        _memory = memory
    if agent is not None:
        _agent = agent


def form_belief(topic: str, stance: str, confidence: float = 0.6, evidence: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    bid = _memory.set_belief(topic, stance, confidence=confidence, evidence=evidence, source="tool")
    return f"OK belief #{bid}: {topic} => {stance} (conf={confidence})"


def list_beliefs() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    rows = _memory.list_beliefs(25)
    if not rows:
        return "No beliefs stored yet."
    return "\n".join(
        f"[{b['id']}] {b['topic']}: {b['stance']} conf={b.get('confidence', 0):.2f}"
        for b in rows
    )


def wm_push(content: str, kind: str = "item", priority: float = 0.5) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    i = _memory.wm_add(content, kind=kind, priority=priority)
    return f"OK working_memory #{i}"


def wm_show() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    rows = _memory.wm_list()
    if not rows:
        return "Working memory empty."
    return "\n".join(f"- [{r.get('kind')}] {r['content']}" for r in rows)


def save_skill(name: str, description: str, steps_json: str = "[]") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    try:
        steps = json.loads(steps_json) if steps_json else []
    except json.JSONDecodeError:
        steps = [{"detail": steps_json}]
    sid = _memory.save_skill(name, description, steps)
    return f"OK skill #{sid} name={name}"


def list_skills() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    rows = _memory.list_skills()
    if not rows:
        return "No skills saved."
    return "\n".join(f"- {r['name']}: {r.get('description')} (ok×{r.get('success_count', 0)})" for r in rows)


def run_skill(name: str) -> str:
    if not _agent or not _memory:
        return "ERROR: agent not ready"
    skill = _memory.get_skill(name)
    if not skill:
        return f"ERROR: unknown skill {name}"
    results = []
    for step in skill.get("steps") or []:
        if not isinstance(step, dict):
            continue
        tool = step.get("tool")
        args = step.get("args") or step.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if not tool:
            continue
        out = _agent.tools.execute(tool, args if isinstance(args, dict) else {})
        results.append(f"{tool}: {out[:300]}")
    _memory.skill_success(name)
    return "Skill ran:\n" + "\n".join(results) if results else "Skill had no executable steps."


def create_plan(title: str, steps_json: str, goal_id: int = 0) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    try:
        steps = json.loads(steps_json)
    except json.JSONDecodeError:
        steps = [{"action": "step", "detail": steps_json, "done": False}]
    if not isinstance(steps, list):
        return "ERROR: steps_json must be a JSON array"
    gid = int(goal_id) if goal_id else None
    pid = _memory.create_plan(title, steps, goal_id=gid)
    return f"OK plan #{pid} with {len(steps)} steps"


def plan_from_goal(goal_id: int) -> str:
    if not _agent:
        return "ERROR: agent not ready"
    plan = _agent.planner.create_from_goal(int(goal_id))
    if not plan:
        return f"ERROR: cannot plan goal {goal_id}"
    return f"OK plan #{plan['id']} steps={len(plan.get('steps') or [])} title={plan.get('title')}"


def advance_plan(plan_id: int = 0) -> str:
    if not _agent:
        return "ERROR: agent not ready"
    pid = int(plan_id) if plan_id else None
    return _agent.planner.execute_next_step(plan_id=pid)


def semantic_search(query: str) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    from seven.memory.vector import SemanticMemory
    return SemanticMemory(_memory).search_text(query)


def index_memory(text: str) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    from seven.memory.vector import SemanticMemory
    i = SemanticMemory(_memory).index(text, ref_type="manual")
    return f"OK indexed embedding #{i}"


def write_digest() -> str:
    if not _agent:
        return "ERROR: agent not ready"
    body = _agent.episodic.build_digest(period="manual")
    _agent.memory.add_digest("manual", body)
    return body[:2000]


def set_preference(key: str, value: str) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    _memory.set_preference(key, value)
    return f"OK preference {key}={value}"


def register(reg, memory=None, agent=None):
    from seven.tools.registry import Tool
    set_context(memory=memory, agent=agent)

    reg.register(Tool(
        name="form_belief",
        description="Store or update an opinion/belief with confidence 0-1 and evidence.",
        parameters={
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "stance": {"type": "string"},
                "confidence": {"type": "number"},
                "evidence": {"type": "string"},
            },
            "required": ["topic", "stance"],
        },
        handler=form_belief,
        tier="core",
    ))
    reg.register(Tool(
        name="list_beliefs",
        description="List Seven's stored beliefs and opinions.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_beliefs(),
        tier="core",
    ))
    reg.register(Tool(
        name="wm_push",
        description="Push an item into short working memory (max ~9 items).",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "kind": {"type": "string"},
                "priority": {"type": "number"},
            },
            "required": ["content"],
        },
        handler=wm_push,
        tier="core",
    ))
    reg.register(Tool(
        name="wm_show",
        description="Show working memory contents.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: wm_show(),
        tier="core",
    ))
    reg.register(Tool(
        name="save_skill",
        description="Save a reusable skill (name, description, steps_json array of tool steps).",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "steps_json": {"type": "string"},
            },
            "required": ["name", "description"],
        },
        handler=save_skill,
        tier="core",
    ))
    reg.register(Tool(
        name="list_skills",
        description="List saved skills.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_skills(),
        tier="core",
    ))
    reg.register(Tool(
        name="run_skill",
        description="Execute a saved skill by name.",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        handler=run_skill,
        tier="core",
    ))
    reg.register(Tool(
        name="create_plan",
        description="Create a multi-step plan. steps_json is a JSON array of {action, detail}.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "steps_json": {"type": "string"},
                "goal_id": {"type": "integer"},
            },
            "required": ["title", "steps_json"],
        },
        handler=create_plan,
        tier="core",
    ))
    reg.register(Tool(
        name="plan_from_goal",
        description="Auto-generate a multi-step plan from a goal id.",
        parameters={
            "type": "object",
            "properties": {"goal_id": {"type": "integer"}},
            "required": ["goal_id"],
        },
        handler=plan_from_goal,
        tier="core",
    ))
    reg.register(Tool(
        name="advance_plan",
        description="Execute the next step of an active multi-step plan (optional plan_id).",
        parameters={
            "type": "object",
            "properties": {"plan_id": {"type": "integer"}},
        },
        handler=advance_plan,
        tier="core",
    ))
    reg.register(Tool(
        name="semantic_search",
        description="Semantic search over indexed memory (local hashing embeddings).",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        handler=semantic_search,
        tier="core",
    ))
    reg.register(Tool(
        name="index_memory",
        description="Index free text into semantic memory.",
        parameters={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        handler=index_memory,
        tier="core",
    ))
    reg.register(Tool(
        name="write_digest",
        description="Write an episodic digest of recent activity into long-term memory.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: write_digest(),
        tier="core",
    ))
    reg.register(Tool(
        name="set_preference",
        description="Store a user preference key/value.",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["key", "value"],
        },
        handler=set_preference,
        tier="core",
    ))
