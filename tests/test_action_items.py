from seven.memory.store import Memory
from seven.mind.action_items import capture, extract_action_items
from seven.tools.action_items import register
from seven.tools.registry import ToolRegistry


def test_extracts_only_explicit_commitments():
    text = "Nice weather. I need to renew the licence. Remind me to call Sam! Maybe pizza?"
    assert extract_action_items(text) == ["renew the licence", "call Sam"]
    assert extract_action_items("Could you explain this? I like trains.") == []


def test_capture_is_deduplicated_in_sqlite(tmp_path):
    memory = Memory(tmp_path / "actions.db")
    mid = memory.add_message("user", "TODO: submit invoice")
    assert len(capture(memory, mid, "TODO: submit invoice")) == 1
    assert capture(memory, mid, "todo: SUBMIT   invoice") == []
    assert memory.list_action_items()[0]["text"] == "submit invoice"


def test_accept_and_dismiss_are_durable_and_one_shot(tmp_path):
    db = tmp_path / "actions.db"
    memory = Memory(db)
    first = memory.add_action_item("book service")
    second = memory.add_action_item("buy paint")
    accepted = memory.resolve_action_item(first, True)
    dismissed = memory.resolve_action_item(second, False)
    assert accepted["task_id"] == memory.open_tasks()[0]["id"]
    assert dismissed["status"] == "dismissed"
    assert memory.resolve_action_item(first, True) is None
    assert Memory(db).list_action_items("accepted")[0]["text"] == "book service"


def test_source_link_survives_message_clear_as_null(tmp_path):
    memory = Memory(tmp_path / "actions.db")
    message_id = memory.add_message("user", "I need to file the return")
    capture(memory, message_id, "I need to file the return")
    memory.clear_session_messages()
    assert memory.list_action_items()[0]["source_message_id"] is None


def test_review_tools_use_current_memory(tmp_path):
    memory = Memory(tmp_path / "actions.db")
    item_id = memory.add_action_item("file return")
    registry = ToolRegistry(memory=memory)
    register(registry, memory)
    assert "file return" in registry.execute("list_action_items")
    assert "as task" in registry.execute("accept_action_item", {"item_id": item_id})
    assert "file return" in registry.execute("list_action_items", {"status": "accepted"})
