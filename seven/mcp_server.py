"""Model Context Protocol stdio server for Seven's live tool registry.

The MCP client owns the child process and therefore is the authority boundary.
Seven deliberately does not sandbox or downgrade tool calls made through it.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

from seven import __version__
from seven.memory.store import Memory
from seven.tools.registry import ToolRegistry, build_default_registry


class SevenMCP:
    """Protocol-independent adapter, kept directly testable without stdio."""

    def __init__(self, memory: Memory | None = None, registry: ToolRegistry | None = None):
        self.memory = memory or Memory()
        self.registry = registry or build_default_registry(self.memory, tier="full")

    def tool_specs(self) -> list[dict[str, Any]]:
        return [schema["function"] for schema in self.registry.schemas()]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        return self.registry.execute(name, arguments or {})


def create_server(adapter: SevenMCP | None = None):
    """Create the low-level SDK server with Seven's real JSON schemas."""
    try:
        import mcp.types as types
        from mcp.server import Server
    except ImportError as exc:  # pragma: no cover - exercised by packaging users
        raise RuntimeError("MCP support is not installed; run: pip install 'seven-ai[mcp]'") from exc

    seven = adapter or SevenMCP()
    server = Server("seven-ai", version=__version__, instructions=(
        "Seven's full-authority host tools. Calls are real and audited. "
        "The MCP client is responsible for user consent and process access."
    ))

    @server.list_tools()
    async def list_tools():
        return [
            types.Tool(
                name=spec["name"],
                description=spec.get("description", ""),
                inputSchema=spec.get("parameters") or {"type": "object", "properties": {}},
            )
            for spec in seven.tool_specs()
        ]

    @server.call_tool(validate_input=True)
    async def call_tool(name: str, arguments: dict[str, Any] | None):
        result = await asyncio.to_thread(seven.call, name, arguments)
        return [types.TextContent(type="text", text=result)]

    server.seven_adapter = seven
    return server


async def run_stdio() -> None:
    try:
        from mcp.server.stdio import stdio_server
    except ImportError as exc:
        raise RuntimeError("MCP support is not installed; run: pip install 'seven-ai[mcp]'") from exc

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> int:
    # stdout belongs exclusively to the MCP JSON-RPC transport.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    try:
        asyncio.run(run_stdio())
        return 0
    except (RuntimeError, KeyboardInterrupt) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
