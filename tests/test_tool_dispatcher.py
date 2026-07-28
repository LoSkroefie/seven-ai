from __future__ import annotations

import json

from seven import config
from seven.agent.loop import Seven
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
