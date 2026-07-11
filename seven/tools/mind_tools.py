"""Tools for beliefs, working memory, skills, plans, semantic search, digests."""
from __future__ import annotations

import json
from typing import Optional

_memory = None
_agent = None
_registry = None


def set_context(memory=None, agent=None, registry=None):
    global _memory, _agent, _registry
    if memory is not None:
        _memory = memory
    if agent is not None:
        _agent = agent
    if registry is not None:
        _registry = registry


def _validate_skill(name: str, description: str, steps) -> tuple[str, str, list] | str:
    name, description = (name or "").strip(), (description or "").strip()
    if not name or len(name) > 80 or any(ord(ch) < 32 for ch in name):
        return "ERROR: skill name must be 1-80 printable characters"
    if len(description) > 500:
        return "ERROR: skill description exceeds 500 characters"
    if not isinstance(steps, list) or not 1 <= len(steps) <= 50:
        return "ERROR: skill requires 1-50 tool steps"
    normalized = []
    active = set(_registry.names()) if _registry is not None else None
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            return f"ERROR: skill step {index} must be an object"
        unknown = set(step) - {"tool", "args", "arguments", "continue_on_error"}
        if unknown:
            return f"ERROR: skill step {index} has unsupported keys: {', '.join(sorted(unknown))}"
        tool = step.get("tool")
        args = step.get("args", step.get("arguments", {}))
        keep_going = step.get("continue_on_error", False)
        if not isinstance(tool, str) or not tool.strip() or len(tool) > 100:
            return f"ERROR: skill step {index} requires a valid tool name"
        tool = tool.strip()
        if tool == "run_skill":
            return f"ERROR: skill step {index} cannot recursively call run_skill"
        if active is not None and tool not in active:
            return f"ERROR: skill step {index} references unavailable tool '{tool}'"
        if not isinstance(args, dict):
            return f"ERROR: skill step {index} args must be an object"
        if not isinstance(keep_going, bool):
            return f"ERROR: skill step {index} continue_on_error must be boolean"
        normalized.append({"tool": tool, "args": args, "continue_on_error": keep_going})
    return name, description, normalized


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
        return "ERROR: steps_json must be valid JSON"
    validated = _validate_skill(name, description, steps)
    if isinstance(validated, str):
        return validated
    name, description, steps = validated
    try:
        saved = _memory.save_skill(name, description, steps, source="tool")
    except ValueError as exc:
        return f"ERROR: {exc}"
    state = "saved" if saved["changed"] else "unchanged"
    return f"OK skill #{saved['id']} name={name} version={saved['version']} {state}"


def list_skills() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    rows = _memory.list_skills()
    if not rows:
        return "No skills saved."
    return "\n".join(f"- {r['name']} v{r.get('current_version')}: {r.get('description')} (ok×{r.get('success_count', 0)} fail×{r.get('failure_count', 0)})" for r in rows)


def skill_history(name: str) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    rows = _memory.skill_history(name)
    if not rows:
        return f"ERROR: unknown skill {name}"
    return "\n".join(f"- v{row['version']} source={row['source']} at={row['created_at']} description={row.get('description') or ''}" for row in rows)


def rollback_skill(name: str, version: int) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    revision = _memory.get_skill_revision(name, int(version))
    if not revision:
        return f"ERROR: skill {name} version {version} not found"
    validated = _validate_skill(name, revision.get("description") or "", revision.get("steps"))
    if isinstance(validated, str):
        return f"ERROR: stored revision cannot be activated: {validated[7:] if validated.startswith('ERROR: ') else validated}"
    try:
        result = _memory.rollback_skill(name, int(version))
    except ValueError as exc:
        return f"ERROR: stored revision cannot be activated: {exc}"
    if result["changed"]:
        return f"OK skill {name} rolled back from v{version} as new v{result['version']}"
    return f"OK skill {name} already matches v{version}; current v{result['version']} unchanged"


def _result_ok(output: str) -> bool:
    if output.lstrip().upper().startswith("ERROR"):
        return False
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and parsed.get("ok") is False:
            return False
    except (TypeError, json.JSONDecodeError):
        pass
    return True


def run_skill(name: str) -> str:
    if not _agent or not _memory:
        return "ERROR: agent not ready"
    skill = _memory.get_skill(name)
    if not skill:
        return f"ERROR: unknown skill {name}"
    validated = _validate_skill(name, skill.get("description") or "", skill.get("steps"))
    if isinstance(validated, str):
        _memory.record_skill_run(name, int(skill.get("current_version") or 1), False, [{"stage": "preflight", "ok": False}])
        return f"ERROR: stored skill failed preflight: {validated[7:] if validated.startswith('ERROR: ') else validated}"
    _, _, steps = validated
    results, statuses = [], []
    all_ok = True
    for step in steps:
        out = _agent.tools.execute(step["tool"], step["args"])
        ok = _result_ok(out)
        statuses.append({"tool": step["tool"], "ok": ok})
        results.append(f"{step['tool']}: {out[:300]}")
        if not ok:
            all_ok = False
            if not step["continue_on_error"]:
                break
    version = int(skill.get("current_version") or 1)
    _memory.record_skill_run(name, version, all_ok, statuses)
    state = "completed" if all_ok else "failed"
    return f"Skill {name} v{version} {state}:\n" + "\n".join(results)


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
    set_context(memory=memory, agent=agent, registry=reg)

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
        name="skill_history",
        description="List immutable revisions of a saved skill.",
        parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        handler=skill_history,
        tier="core",
    ))
    reg.register(Tool(
        name="rollback_skill",
        description="Activate an older validated skill revision as a new revision; history is never deleted.",
        parameters={"type": "object", "properties": {"name": {"type": "string"}, "version": {"type": "integer", "minimum": 1}}, "required": ["name", "version"]},
        handler=rollback_skill,
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
