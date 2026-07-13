import pytest

from seven.mcp_server import SevenMCP, create_server
from seven.memory.store import Memory
from seven.tools.registry import Tool, ToolRegistry


def _adapter(tmp_path):
    memory = Memory(tmp_path / "mcp.db")
    registry = ToolRegistry(memory=memory, tier="full")
    registry.register(Tool(
        name="echo_real",
        description="Echo text through the real registry.",
        parameters={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
        handler=lambda text: f"echo:{text}",
    ))
    return SevenMCP(memory=memory, registry=registry)


def test_adapter_exposes_exact_registry_schema_and_audits(tmp_path):
    adapter = _adapter(tmp_path)
    assert adapter.tool_specs()[0]["name"] == "echo_real"
    assert adapter.call("echo_real", {"text": "seven"}) == "echo:seven"
    audit = adapter.memory.recent_audit(1)[0]
    assert audit["tool"] == "echo_real"
    assert audit["ok"] == 1


def test_low_level_server_lists_and_calls_tools(tmp_path):
    pytest.importorskip("mcp")
    server = create_server(_adapter(tmp_path))
    options = server.create_initialization_options()
    assert options.server_name == "seven-ai"
    assert options.capabilities.tools is not None
    assert server.seven_adapter.call("echo_real", {"text": "mcp"}) == "echo:mcp"
