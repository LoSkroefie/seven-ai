from __future__ import annotations

import json

from seven import config
from seven.agent.loop import Seven
from seven.memory.store import Memory
from seven.tools.registry import Tool, ToolRegistry


def agent_with_tool():
    registry = ToolRegistry(tier="full")
    registry.register(Tool(
        name="echo_value",
        description="Return a supplied value.",
        parameters={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        },
        handler=lambda value: f"echo:{value}",
    ))
    agent = Seven.__new__(Seven)
    agent.tools = registry
    return agent


def test_dispatcher_schema_is_compact_and_runs_registered_tool(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "dispatcher")
    agent = agent_with_tool()

    schemas = agent._model_tool_schemas()
    actual_name, output = agent._execute_model_tool(
        "seven_tool",
        {"name": "echo_value", "arguments": {"value": "proof"}},
    )

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "seven_tool"
    assert len(json.dumps(schemas)) < 1000
    assert actual_name == "echo_value"
    assert output == "echo:proof"


def test_conversation_fast_path_uses_refreshed_state_without_tool_protocol(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "dispatcher")
    agent = agent_with_tool()

    assert agent._model_tool_schemas("Hi Seven, how are you?") == []
    assert agent._model_tool_schemas("Check your current system resources") == []
    assert len(agent._model_tool_schemas("Write a file with this report")) == 1
    assert agent._conversation_resource_check("Check your current system resources")
    assert not agent._conversation_resource_check("How are you?")


def test_dispatcher_describes_tool_and_blocks_recursive_dispatch(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "dispatcher")
    agent = agent_with_tool()

    actual_name, description = agent._execute_model_tool(
        "seven_tool",
        {"name": "describe_tool", "arguments": {"name": "echo_value"}},
    )
    recursive_name, recursive = agent._execute_model_tool(
        "seven_tool",
        {"name": "seven_tool", "arguments": {}},
    )

    payload = json.loads(description)
    assert actual_name == "describe_tool"
    assert payload["name"] == "echo_value"
    assert payload["parameters"]["required"] == ["value"]
    assert recursive_name == "seven_tool"
    assert recursive.startswith("ERROR:")


def test_native_schema_mode_remains_default_compatible(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "native")
    agent = agent_with_tool()

    schemas = agent._model_tool_schemas()

    assert [schema["function"]["name"] for schema in schemas] == ["echo_value"]


def test_dispatcher_discovers_describes_and_runs_tools_outside_lean_tier(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "dispatcher")
    registry = ToolRegistry(tier="lean")
    registry.register(Tool(
        name="hidden_specialist",
        description="A full-tier specialist.",
        parameters={
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        },
        handler=lambda value: f"special:{value}",
    ))
    agent = Seven.__new__(Seven)
    agent.tools = registry

    _, listed = agent._execute_model_tool(
        "seven_tool",
        {"name": "list_tools", "arguments": {"filter": "special", "page": 1}},
    )
    _, described = agent._execute_model_tool(
        "seven_tool",
        {"name": "describe_tool", "arguments": {"name": "hidden_specialist"}},
    )
    actual_name, executed = agent._execute_model_tool(
        "seven_tool",
        {"name": "hidden_specialist", "arguments": {"value": "proof"}},
    )

    assert json.loads(listed)["tools"] == ["hidden_specialist"]
    assert json.loads(described)["parameters"]["required"] == ["value"]
    assert actual_name == "hidden_specialist"
    assert executed == "special:proof"


def test_dispatcher_schema_size_does_not_grow_with_registry(monkeypatch):
    monkeypatch.setattr(config, "TOOL_SCHEMA_MODE", "dispatcher")
    registry = ToolRegistry(tier="full")
    for index in range(104):
        registry.register(Tool(
            name=f"tool_{index:03d}",
            description="A deliberately verbose description " * 5,
            parameters={"type": "object", "properties": {}},
            handler=lambda: "ok",
        ))
    agent = Seven.__new__(Seven)
    agent.tools = registry

    schemas = agent._model_tool_schemas()

    assert len(json.dumps(schemas)) < 700


def test_dispatcher_maps_small_model_resource_and_listing_aliases():
    registry = ToolRegistry(tier="lean")
    registry.register(Tool(
        name="get_system_info",
        description="Return current system information.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "host=peanut ram=8GB",
    ))
    registry.register(Tool(
        name="list_dir",
        description="List a directory.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "workspace files",
    ))
    agent = Seven.__new__(Seven)
    agent.tools = registry

    resource_name, resource_output = agent._execute_model_tool(
        "seven_tool", {"name": "system_resources", "arguments": {}}
    )
    listing_name, listing_output = agent._execute_model_tool(
        "seven_tool", {"name": "ls", "arguments": {}}
    )

    assert (resource_name, resource_output) == (
        "get_system_info", "host=peanut ram=8GB"
    )
    assert (listing_name, listing_output) == ("list_dir", "workspace files")


def test_direct_text_protocol_aliases_and_meta_tools_are_resolved_and_audited(tmp_path):
    memory = Memory(tmp_path / "dispatcher.db")
    registry = ToolRegistry(memory=memory, tier="lean")
    registry.register(Tool(
        name="list_dir",
        description="List a directory.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "workspace files",
    ))
    agent = Seven.__new__(Seven)
    agent.memory = memory
    agent.tools = registry

    alias_name, alias_output = agent._execute_model_tool("ls", {})
    meta_name, meta_output = agent._execute_model_tool(
        "list_tools", {"filter": "list"}
    )

    assert (alias_name, alias_output) == ("list_dir", "workspace files")
    assert meta_name == "list_tools"
    assert json.loads(meta_output)["tools"] == ["list_dir"]
    audits = memory.recent_audit(2)
    assert {row["tool"] for row in audits} == {"list_dir", "list_tools"}


def test_project_inventory_intent_and_grounded_formatter():
    payload = json.dumps({
        "ok": True,
        "workspace": "/var/lib/seven/workspace",
        "registered_count": 0,
        "projects": [{
            "name": "seven-ai",
            "path": "/opt/seven-release",
            "status": "active",
            "source": "filesystem",
        }],
    })

    assert Seven._conversation_project_inventory("list all my projects please")
    assert Seven._conversation_project_inventory(
        "and you cannot create a list of the projects?"
    )
    assert not Seven._conversation_project_inventory(
        "please change the project dashboard color"
    )
    assert not Seven._conversation_project_inventory(
        "what changed in this project?"
    )
    assert not Seven._conversation_project_inventory(
        "what can you do for my project?"
    )
    rendered = Seven._format_project_inventory(payload)
    assert "seven-ai" in rendered
    assert "/opt/seven-release" in rendered
    assert "No additional owner projects" in rendered
