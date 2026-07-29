from __future__ import annotations

import json

from seven import config
from seven.memory.store import Memory
from seven.tools import projects as project_tools
from seven.tools.projects import discover_projects, list_projects
from seven.tools.registry import ToolRegistry


def test_project_catalog_persists_registered_projects(tmp_path):
    memory = Memory(tmp_path / "projects.db")

    first = memory.register_project(
        "Mortem",
        path="C:/Game Servers",
        description="DayZ project",
        source="owner",
    )
    same = memory.register_project(
        "mortem",
        path="C:/Game Servers",
        description="Updated",
        status="paused",
        source="owner",
    )

    rows = memory.list_projects()
    assert first == same
    assert len(rows) == 1
    assert rows[0]["description"] == "Updated"
    assert rows[0]["status"] == "paused"


def test_project_discovery_is_bounded_to_roots_and_immediate_children(tmp_path):
    root = tmp_path / "workspace"
    direct = root / "direct"
    nested = direct / "nested"
    direct.mkdir(parents=True)
    nested.mkdir()
    (direct / "pyproject.toml").write_text(
        '[project]\nname = "direct-project"\n',
        encoding="utf-8",
    )
    (nested / "package.json").write_text(
        '{"name":"nested-project"}',
        encoding="utf-8",
    )

    projects = discover_projects([root])

    assert [item["name"] for item in projects] == ["direct-project"]
    assert projects[0]["markers"] == ["pyproject.toml"]


def test_list_projects_combines_registered_and_discovered_without_duplicates(tmp_path):
    root = tmp_path / "workspace"
    project = root / "seven"
    project.mkdir(parents=True)
    (project / "package.json").write_text('{"name":"seven-web"}', encoding="utf-8")
    memory = Memory(tmp_path / "projects.db")
    memory.register_project("Seven", path=str(project), source="owner")

    payload = json.loads(
        list_projects(memory, refresh=True, max_projects=20)
    )

    assert payload["ok"] is True
    # The configured roots may discover the source repository too, but the
    # registered path itself must never be duplicated.
    same_path = [
        item for item in payload["projects"]
        if item.get("path") == str(project)
    ]
    assert len(same_path) == 1
    assert same_path[0]["source"] == "owner"


def test_blocked_goal_hides_its_still_active_plan(tmp_path):
    memory = Memory(tmp_path / "plans.db")
    goal_id = memory.add_goal("Grounded work", "Do verified work")
    memory.create_plan("Plan", [{"action": "survey"}], goal_id=goal_id)

    assert len(memory.active_plans()) == 1
    memory.update_goal(goal_id, status="blocked", last_action="No evidence")
    assert memory.active_plans() == []


def test_register_project_tool_requires_real_marked_path_inside_allowed_root(
    tmp_path, monkeypatch
):
    root = tmp_path / "allowed"
    real = root / "real"
    fake = root / "unmarked"
    real.mkdir(parents=True)
    fake.mkdir()
    (real / "go.mod").write_text("module example.test/real\n", encoding="utf-8")
    monkeypatch.setattr(config, "PROJECT_ROOTS", [root])
    memory = Memory(tmp_path / "projects.db")
    registry = ToolRegistry(memory=memory, tier="full")
    project_tools.register(registry, memory=memory)

    missing = registry.execute(
        "register_project", {"path": str(root / "missing")}
    )
    unmarked = registry.execute("register_project", {"path": str(fake)})
    valid = registry.execute("register_project", {"path": str(real)})

    assert missing.startswith("ERROR:")
    assert unmarked.startswith("ERROR:")
    assert valid.startswith("OK project #")
    assert memory.list_projects()[0]["source"] == "filesystem_verified"
