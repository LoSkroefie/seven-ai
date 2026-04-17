# Seven AI — Code Audit v3.2.19
**Date:** April 17, 2026
**Auditor:** Cascade
**Scope:** MCP server — exposes Seven's episodic memory (v3.2.17) over the Model Context Protocol so any MCP-aware client (Claude Desktop, Claude Code, Cursor, Continue, opencode, or any of Seven's own future integrations) can query her brain directly.

---

## Executive Summary

One new file at project root, one line added to `requirements.txt`. No config changes needed. Seven is now queryable over stdio as a standard MCP server with 8 read-only tools. All 7 protocol smoke tests pass end-to-end on target machine, including the real stdio JSON-RPC handshake that external clients perform.

The big idea: v3.2.17 gave Seven a memory. v3.2.18 made her act on it. v3.2.19 makes that memory *exportable* — any external tool can now ask "what has Jan been working on this week?" and get a structured answer. This unlocks every future Claude session, every MCP-aware editor, and eventually Seven's own subagent delegation to tools like opencode.

---

## Files Created

| File | Purpose | Lines |
|---|---|---|
| `seven_mcp.py` | FastMCP server exposing 8 read-only tools over conversation_memory. stdio transport. Stderr-only logging. Path-bootstraps Seven's modules so it runs from any cwd. | ~700 |

## Files Modified

| File | Change |
|---|---|
| `requirements.txt` | Appended `mcp>=1.0.0` (Anthropic's official Python MCP SDK — FastMCP is bundled inside it, no separate install). |

## Files Temporary (removed)

`_verify_v3219.py`, `_verify_v3219_stdio.py`, `_dump_response.py`, `_probe_mcp.py` — used for end-to-end verification, deleted after success.

---

## Architecture

### What MCP is, briefly

The Model Context Protocol is a JSON-RPC spec for letting AI clients call external tools. A server advertises tools with JSON schemas; a client calls them with structured arguments and gets structured results back. `stdio` transport means the client spawns the server as a subprocess and talks to it over stdin/stdout — no networking, no auth, no attack surface.

Seven's server is read-only by design. Every tool is annotated `readOnlyHint=True` and nothing in the handler code writes to the database. Clients can query, but they can't delete, modify, or corrupt Seven's memory.

### What FastMCP is, briefly

FastMCP is the decorator-based Python framework bundled inside Anthropic's `mcp` package. You annotate a function with `@mcp.tool(...)` and it auto-generates the JSON schema from your type hints. It handles all the JSON-RPC plumbing, leaving you to write normal Python.

### The 8 tools

All return either JSON (default) or markdown via a `response_format` parameter:

| Tool | What it does |
|---|---|
| `seven_recent_conversations` | Newest-first list with filters for `source` (direct/ambient/imported) and `finalized_only`. Paginatable via `limit`. |
| `seven_get_conversation` | One episode in full, including transcript of individual utterances with timestamps, speakers, and Whisper confidence scores. |
| `seven_search_conversations` | Free-text search over both summaries AND raw utterances. Case-insensitive. |
| `seven_conversations_by_date` | Filter by a specific day. Accepts `YYYY-MM-DD`, `today`, or `yesterday`. |
| `seven_action_items` | Aggregate open TODOs from the last N days (1-365), filterable by source. |
| `seven_memory_stats` | Rollup: total / finalized / today / by-source / DB path. |
| `seven_today_digest` | Curated daily digest combining summaries, topics, sentiment distribution, and extracted action items. Markdown by default. |
| `seven_list_extensions` | Introspection — what plugin_loader finds in `extensions/` (runs AST security scan). |

### Path bootstrap

`seven_mcp.py` prepends its own directory to `sys.path` before importing Seven's modules. This means it can be invoked from *any* working directory (e.g., `python C:\Users\USER-PC\Desktop\seven-ai\seven_mcp.py` from somewhere else) and still find `config`, `core.conversation_memory`, and `utils.plugin_loader`. Important for MCP clients that may launch it from the user's home directory or a shell-default cwd.

### Stderr-only logging

MCP uses stdin/stdout for the JSON-RPC protocol — anything printed to stdout that isn't valid JSON-RPC corrupts the stream. The server's `logging.basicConfig(stream=sys.stderr, ...)` guarantees all logs go to stderr, keeping stdout clean. This matters because Seven's `conversation_memory`, `PluginLoader`, and `AmbientListenerExtension` all emit INFO logs on import — without this guard, the handshake would fail.

### Shared helpers (DRY)

`_conv_brief`, `_conv_list_markdown`, `_render_conversation_markdown`, `_apply_source_filter`, `_filter_action_items_by_source`, `_as_json`, `_trim_iso` — all shared across tools to avoid duplication. Follows the MCP builder skill guide's composability principle.

---

## Critical Bug Found & Fixed: FastMCP Schema Pattern

The skill guide recommended the pattern `async def tool(params: InputModel)` where `InputModel` is a Pydantic class. This **does not work** with FastMCP 3.2.3 (the version bundled in modern `mcp>=1.0`). The schema it generates has a top-level `params` key, but MCP clients send arguments flat. Every `tools/call` was failing with:

```
Error executing tool seven_memory_stats: 1 validation error for seven_memory_statsArguments
params
  Field required [type=missing, input_value={'response_format': 'json'}, input_type=dict]
```

**Fix applied**: switched every tool to the modern flat-parameter pattern using `typing.Annotated[type, Field(...)]` on individual function parameters. FastMCP generates the correct flat schema from that, and clients send flat arguments that validate cleanly.

```python
# Broken (old skill pattern):
class RecentInput(BaseModel):
    limit: int = Field(...)
async def seven_recent_conversations(params: RecentInput) -> str: ...

# Working (modern FastMCP):
async def seven_recent_conversations(
    limit: Annotated[int, Field(description="...", ge=1, le=100)] = 10,
    ...
) -> str: ...
```

All 8 tools were refactored. Behavior is identical; only the signatures changed.

---

## LLM Usage Audit — None

This server does not call Ollama. It's a pure query interface over the existing `conversation_memory` tables. Seven's cognitive stack remains the only LLM consumer.

---

## Security Audit

The server runs with Seven's full Python privileges (it's not sandboxed — it's a local-only stdio process), but:

- **Read-only by design** — zero `INSERT`/`UPDATE`/`DELETE` in any tool handler.
- **Input validation** — every parameter has a Pydantic `Field` with constraints. Exceeding `le=100` on `limit` returns `isError: true` without touching the DB. Verified: `limit=500` rejected cleanly.
- **No network** — stdio transport only. Nothing listens on any port.
- **No shell-out** — pure Python, no `subprocess` anywhere.
- **Errors don't leak internals** — all exceptions caught, formatted as `{error: "TypeName: message"}` JSON, logged with traceback to stderr.

---

## Runtime Verification on Target Machine

Ran full stdio protocol test (the same handshake Claude Desktop performs):

```
[1] initialize:
    server: {'name': 'seven_mcp', 'version': '1.27.0'}
    protocol: 2024-11-05

[2] tools/list: 8 tool(s)
    - seven_recent_conversations  [readOnly=True]
    - seven_get_conversation  [readOnly=True]
    - seven_search_conversations  [readOnly=True]
    - seven_conversations_by_date  [readOnly=True]
    - seven_action_items  [readOnly=True]
    - seven_memory_stats  [readOnly=True]
    - seven_today_digest  [readOnly=True]
    - seven_list_extensions  [readOnly=True]

[3] seven_memory_stats:
    total_conversations=1   (the test seed)
    finalized=1
    today=1
    db_path=C:\Users\USER-PC\.chatbot\memory.db

[4] seven_today_digest returned valid markdown digest

[5] seven_recent_conversations: count=1

[6] Invalid limit=500: isError=True   (validation works)

[7] Nonexistent tool seven_nonexistent_tool: error returned
```

All 7 checks green.

**Note**: Your `~/.chatbot/memory.db` now contains 1 test conversation seeded during verification (id=1, "Jan asked Seven to test the MCP server end-to-end"). It's harmless and will be naturally displaced once real conversations start accumulating, but if you want a clean slate, delete `memory.db` before first real launch — the tables will be recreated on first use.

---

## Activation Instructions

### 1. Install the dep (one-time)

```powershell
cd C:\Users\USER-PC\Desktop\seven-ai
pip install -r requirements.txt
```

This picks up `mcp>=1.0.0`. FastMCP is bundled inside it.

### 2. Test the server stands up

```powershell
python C:\Users\USER-PC\Desktop\seven-ai\seven_mcp.py
```

It should print a "Starting seven_mcp — db=... — 8 tools registered" line to stderr and then silently wait for JSON-RPC input on stdin. Ctrl-C to exit.

### 3. Wire it into a client

**Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`):

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

**Claude Code** / **Cursor** / **Continue**: each has a similar `mcpServers` config block. Same `command` + `args` structure.

**opencode** (once integrated per v3.2.20 plan below): Seven's own integration layer will invoke `seven_mcp.py` as a subprocess under her own control.

### 4. Verify from the client

In Claude Desktop, ask: "Use the seven MCP server to show me Seven's memory stats." The client should call `seven_memory_stats` and display the results.

---

## What This Unlocks

Before v3.2.19, Seven's memory was private — only accessible through her own chat interface. Now:

- Every future Claude session can query "what has Jan been working on?" without me copy-pasting context into chat.
- Any editor with MCP support can show Seven's recent action items in its sidebar.
- **Seven can invoke her own MCP server from inside an integration** — meaning v3.2.20's opencode bridge can feed Seven's memory context to opencode agents so they understand what Jan cares about before acting.

This last point is the real unlock. Seven is no longer just a local assistant — she's a **queryable memory substrate** that other AI tools can build on.

---

## Future Work (v3.2.20+)

- **opencode bridge** (see recommendation below): Seven delegates menial coding tasks to opencode as a subagent, captures the output, folds it into her conversation memory.
- **MCP resource exposure**: turn conversations into MCP `resources` with URIs like `seven://conversations/42` so clients can subscribe rather than poll.
- **Write tools (with explicit opt-in)**: `seven_add_action_item`, `seven_mark_done` — risky, OFF by default, behind a separate `ENABLE_WRITE_TOOLS` flag.
- **HTTP transport alongside stdio**: expose the same tools at `http://127.0.0.1:7778` so the existing FastAPI + web UI can consume them.
