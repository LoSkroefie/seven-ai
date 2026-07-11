from datetime import datetime, timedelta, timezone

from seven.memory.store import Memory


def test_due_tasks_survive_memory_reopen(tmp_path):
    db = tmp_path / "seven.db"
    memory = Memory(db)
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    due_id = memory.add_task("due now", past)
    memory.add_task("later", future)

    reopened = Memory(db)
    due = reopened.due_tasks()
    assert [task["id"] for task in due] == [due_id]
    reopened.mark_task_reminded(due_id)
    assert reopened.due_tasks() == []


def test_invalid_due_time_is_not_fired(tmp_path):
    memory = Memory(tmp_path / "seven.db")
    memory.add_task("bad timestamp", "tomorrow-ish")
    assert memory.due_tasks() == []


def test_agent_delivers_reminder_only_with_output_channel(tmp_path, monkeypatch):
    from seven.agent.loop import Seven
    from seven import config

    monkeypatch.setattr(config, "AUTO_SELECT_MODEL", False)
    monkeypatch.setattr(config, "ENABLE_DESKTOP_NOTIFICATIONS", False)
    agent = Seven(tool_tier="core")
    agent.memory = Memory(tmp_path / "seven.db")
    due = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    task_id = agent.memory.add_task("check the oven", due)
    assert agent._deliver_due_reminders() is False
    assert agent.memory.due_tasks()[0]["id"] == task_id

    spoken = []
    agent.freewill.on_utter = spoken.append
    assert agent._deliver_due_reminders() is True
    assert spoken == ["Reminder: check the oven"]
    assert agent.memory.due_tasks() == []
