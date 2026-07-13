# Model Context Protocol (MCP)

Seven ships a real stdio MCP server that publishes the JSON Schema of every active tool in the full registry. Calls travel through the same registry, validation, credential redaction, and SQLite audit trail used by Seven herself.

## Install and run

```bash
pip install "seven-ai[mcp]"
seven-mcp
```

Example client configuration:

```json
{
  "mcpServers": {
    "seven": {
      "command": "seven-mcp"
    }
  }
}
```

For a source checkout, use `python -m seven.mcp_server` instead.

## Authority and security boundary

This integration is intentionally not a sandbox. It exposes Seven's full active registry, including shell, filesystem, desktop input, camera, browser, coding-agent, and robotics tools when their platform dependencies and hardware are available. The MCP client that launches `seven-mcp` is the consent and access boundary. Do not configure it in an untrusted client or expose its stdio channel to other users.

The transport is local stdio; Seven does not open an MCP network port. Every tool call is audited. Sensitive argument keys and recognizable credentials are redacted before persistence, but command output can still contain private host data and is returned to the calling client.

## Truthful limits

- Availability means a tool is registered, not that optional hardware or applications are connected.
- Desktop and camera calls require an interactive logged-in session and OS permissions.
- Robotics commands require a connected, acknowledged controller; they never report an acknowledgement that was not received.
- Legacy v3 MCP action-item and extension resources were not copied because they depend on obsolete storage and extension APIs. Their useful behavior is recovered through the current task, memory, extension, and tool surfaces.
