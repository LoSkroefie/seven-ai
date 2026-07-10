"""Notes, tasks, facts, goals — backed by Memory."""
from __future__ import annotations

from typing import Optional

_memory = None


def set_memory(memory):
    global _memory
    _memory = memory


def remember_fact(value: str, key: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    _memory.remember(value, key=key or None, source="tool")
    return f"OK remembered: {key + ': ' if key else ''}{value}"


def search_memory(query: str) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    hits = _memory.search_facts(query, limit=10)
    if not hits:
        return f"No facts matching '{query}'"
    return "\n".join(f"[{h['id']}] {h.get('key') or ''}: {h['value']}" for h in hits)


def add_task(title: str, due_at: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    tid = _memory.add_task(title, due_at=due_at or None)
    return f"OK task #{tid}: {title}"


def list_tasks() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    tasks = _memory.open_tasks()
    if not tasks:
        return "No open tasks."
    return "\n".join(
        f"[{t['id']}] {t['title']}" + (f" due={t['due_at']}" if t.get("due_at") else "")
        for t in tasks
    )


def complete_task(task_id: int) -> str:
    if not _memory:
        return "ERROR: memory not ready"
    _memory.complete_task(int(task_id))
    return f"OK completed task #{task_id}"


def add_goal(title: str, detail: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    gid = _memory.add_goal(title, detail)
    return f"OK goal #{gid}: {title}"


def update_goal(goal_id: int, progress: float, last_action: str = "", status: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    kwargs = {"progress": float(progress)}
    if last_action:
        kwargs["last_action"] = last_action
    if status:
        kwargs["status"] = status
    _memory.update_goal(int(goal_id), **kwargs)
    return f"OK goal #{goal_id} updated progress={progress} status={status or 'unchanged'}"


def list_goals() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    goals = _memory.active_goals()
    if not goals:
        return "No active goals."
    return "\n".join(
        f"[{g['id']}] {g['title']} {g['progress']:.0f}% last={g.get('last_action') or '-'}"
        for g in goals
    )


def add_note(body: str, title: str = "") -> str:
    if not _memory:
        return "ERROR: memory not ready"
    nid = _memory.add_note(body, title=title)
    return f"OK note #{nid}"


def list_notes() -> str:
    if not _memory:
        return "ERROR: memory not ready"
    notes = _memory.list_notes(15)
    if not notes:
        return "No notes."
    return "\n".join(f"[{n['id']}] {n.get('title') or ''}: {n['body'][:200]}" for n in notes)


def register(reg, memory=None):
    from seven.tools.registry import Tool
    if memory is not None:
        set_memory(memory)

    reg.register(Tool(
        name="remember_fact",
        description="Store a long-term fact about the user, environment, or preferences.",
        parameters={
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "key": {"type": "string"},
            },
            "required": ["value"],
        },
        handler=remember_fact,
    ))
    reg.register(Tool(
        name="search_memory",
        description="Search long-term facts.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        handler=search_memory,
    ))
    reg.register(Tool(
        name="add_task",
        description="Create a todo/task.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_at": {"type": "string"},
            },
            "required": ["title"],
        },
        handler=add_task,
    ))
    reg.register(Tool(
        name="list_tasks",
        description="List open tasks.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_tasks(),
    ))
    reg.register(Tool(
        name="complete_task",
        description="Mark a task done by id.",
        parameters={
            "type": "object",
            "properties": {"task_id": {"type": "integer"}},
            "required": ["task_id"],
        },
        handler=complete_task,
    ))
    reg.register(Tool(
        name="add_goal",
        description="Create an autonomous goal Seven should work on over time.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["title"],
        },
        handler=add_goal,
    ))
    reg.register(Tool(
        name="update_goal",
        description="Update goal progress only after real work was done. progress 0-100.",
        parameters={
            "type": "object",
            "properties": {
                "goal_id": {"type": "integer"},
                "progress": {"type": "number"},
                "last_action": {"type": "string"},
                "status": {"type": "string", "description": "active|done|blocked"},
            },
            "required": ["goal_id", "progress"],
        },
        handler=update_goal,
    ))
    reg.register(Tool(
        name="list_goals",
        description="List active goals.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_goals(),
    ))
    reg.register(Tool(
        name="add_note",
        description="Save a note.",
        parameters={
            "type": "object",
            "properties": {
                "body": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["body"],
        },
        handler=add_note,
    ))
    reg.register(Tool(
        name="list_notes",
        description="List recent notes.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: list_notes(),
    ))
