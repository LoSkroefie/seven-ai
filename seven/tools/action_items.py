"""Review controls for locally extracted action candidates."""
from __future__ import annotations

from seven.tools.registry import Tool


def register(reg, memory=None):
    def list_items(status: str = "pending", limit: int = 30) -> str:
        if status not in {"pending", "accepted", "dismissed"}:
            return "ERROR: status must be pending, accepted, or dismissed"
        rows = memory.list_action_items(status, limit)
        if not rows:
            return f"No {status} action candidates."
        return "\n".join(f"[{row['id']}] {row['text']}" for row in rows)

    def accept(item_id: int) -> str:
        row = memory.resolve_action_item(item_id, accept=True)
        if not row:
            return f"ERROR: pending action candidate #{item_id} not found"
        return f"OK accepted action #{item_id} as task #{row['task_id']}: {row['text']}"

    def dismiss(item_id: int) -> str:
        row = memory.resolve_action_item(item_id, accept=False)
        if not row:
            return f"ERROR: pending action candidate #{item_id} not found"
        return f"OK dismissed action #{item_id}: {row['text']}"

    reg.register(Tool("list_action_items", "List local conversation action candidates for review.", {
        "type": "object", "properties": {
            "status": {"type": "string", "enum": ["pending", "accepted", "dismissed"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
        }}, list_items))
    reg.register(Tool("accept_action_item", "Accept a pending action candidate and create a real task.", {
        "type": "object", "properties": {"item_id": {"type": "integer"}}, "required": ["item_id"]}, accept))
    reg.register(Tool("dismiss_action_item", "Dismiss a pending action candidate without creating a task.", {
        "type": "object", "properties": {"item_id": {"type": "integer"}}, "required": ["item_id"]}, dismiss))
