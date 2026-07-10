# MCP Server

Seven exposes her memory to any **MCP** (Model Context Protocol) client via `seven_mcp.py` — a stdio server with 8 read-only tools.

Use this to let Claude Desktop, Cursor, Continue, or any MCP-aware AI query Seven's conversation history, moods, relationships, and promises.

---

## What MCP Is

MCP is Anthropic's open protocol for connecting AI tools to data sources. Any MCP client can connect to Seven's MCP server and use its 8 tools.

**Seven's MCP is read-only by design** — external tools can query her memory but can't modify it.

---

## Available Tools (8)

1. **`get_recent_conversations`** — last N conversation turns with mood/topic/sentiment
2. **`search_conversations`** — free-text search across conversation history
3. **`get_conversations_by_date`** — conversations in a date range
4. **`get_conversations_by_mood`** — filter by detected mood
5. **`get_mood_history`** — time-series of Seven's moods
6. **`get_topic_frequency`** — most-discussed topics
7. **`get_relationship_summary`** — Seven's view of the user relationship
8. **`get_promises`** — commitments Seven has made

All tools are annotated `readOnlyHint=True` — nothing mutates the DB.

---

## Setup — Option A: External Client Config

This is the common way. Seven doesn't need to be running — the MCP server spawns on-demand.

### Claude Desktop
Edit `claude_desktop_config.json` (on Windows: `%APPDATA%/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "seven": {
      "command": "python",
      "args": ["C:\\Users\\USER-PC\\Desktop\\seven-ai\\seven_mcp.py"]
    }
  }
}
```

Restart Claude Desktop. Seven's tools appear in the MCP section.

### Cursor
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "seven": {
      "command": "python",
      "args": ["<full-path>/seven_mcp.py"]
    }
  }
}
```

### Continue (VS Code)
`~/.continue/config.json`:
```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "python",
          "args": ["<full-path>/seven_mcp.py"]
        }
      }
    ]
  }
}
```

---

## Setup — Option B: Auto-Launch with Bot

New in **v3.2.20**: Seven can launch her own MCP server as a subprocess when the bot starts.

```python
# config.py
ENABLE_MCP_SERVER = True
MCP_PYTHON_EXECUTABLE = None   # None = use Seven's own Python
```

On `bot.start()`, Seven spawns `seven_mcp.py` as a child process. On `bot.stop()`, she terminates it (3s grace, then SIGKILL).

Use this if you want Seven's MCP server always-on while the bot is running. If you'd rather the MCP server launch only when an external client connects (Claude Desktop / Cursor), **leave `ENABLE_MCP_SERVER = False`** and use Option A.

---

## Transport

`seven_mcp.py` uses **stdio only** — no network sockets. This means:
- Safe from network attacks (no listener)
- Each client spawns its own subprocess (no multi-tenant complexity)
- Works offline

If you want a networked MCP transport, you'd need to wrap `seven_mcp.py` behind a proxy like `mcp-proxy`. Not supported in v3.2.20.

---

## Python Requirement

Seven's MCP server needs Python 3.11+ and the `mcp` package (pinned in `requirements.txt`). If the bot launches via `run_seven.bat` the right Python is used automatically.

If you're running `seven_mcp.py` standalone (Option A), make sure the `command` in your MCP client config points at the Python where `mcp` is installed. On Windows with the unsloth env:

```json
{
  "mcpServers": {
    "seven": {
      "command": "C:\\Users\\USER-PC\\.unsloth\\studio\\unsloth_studio\\Scripts\\python.exe",
      "args": ["C:\\Users\\USER-PC\\Desktop\\seven-ai\\seven_mcp.py"]
    }
  }
}
```

---

## Testing

Quick test — run the server directly and send it a `tools/list` over stdio:

```bash
cd seven-ai
python seven_mcp.py
```

It'll wait for JSON-RPC on stdin. Feed it:
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

You should see the 8 tools returned.

---

## Source

- Server: [`seven_mcp.py`](https://github.com/LoSkroefie/seven-ai/blob/main/seven_mcp.py)
- Auto-launch glue: [`core/enhanced_bot.py`](https://github.com/LoSkroefie/seven-ai/blob/main/core/enhanced_bot.py) (search `MCP server (FIX-5`)
- Memory backend: [`core/conversation_memory.py`](https://github.com/LoSkroefie/seven-ai/blob/main/core/conversation_memory.py)
