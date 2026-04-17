"""
Seven MCP Server

Exposes Seven AI's episodic conversation memory (v3.2.17) as an MCP server
over stdio so that any MCP-aware client — Claude Desktop, Claude Code,
Cursor, Continue, opencode, or Jan's own tools — can query Seven's brain.

Read-only by design. This server is a safe window into Seven's memory,
not a remote control for her actions. Every tool is annotated with
`readOnlyHint=True`; nothing here mutates the database.

Transport: stdio (default — one subprocess per client, no networking).
Run directly for testing:
    python seven_mcp.py

Or wire into an MCP-aware client via its config file:
    {
      "mcpServers": {
        "seven": {
          "command": "python",
          "args": ["C:\\\\Users\\\\USER-PC\\\\Desktop\\\\seven-ai\\\\seven_mcp.py"]
        }
      }
    }

Dependency: `mcp` (Anthropic's official MCP Python SDK). Seven pins this
in requirements.txt. FastMCP is bundled inside `mcp.server.fastmcp` — no
separate install needed.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

# --- Path bootstrap --------------------------------------------------------
# Allow invocation from any directory by adding Seven's project root
# (same folder as this file) to sys.path before importing Seven's modules.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pydantic import Field

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:  # pragma: no cover
    sys.stderr.write(
        "seven_mcp: the 'mcp' package is required. Install with: pip install mcp\n"
        f"Original error: {e}\n"
    )
    raise

import config  # noqa: E402
from core.conversation_memory import ConversationMemory  # noqa: E402


# ---------------------------------------------------------------------------
# Logging — MCP uses stdio for protocol, logs MUST go to stderr only
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [seven_mcp] %(levelname)s: %(message)s",
)
logger = logging.getLogger("seven_mcp")


# ---------------------------------------------------------------------------
# Module-level state — one ConversationMemory per process; it's thread-safe
# ---------------------------------------------------------------------------

_memory = ConversationMemory()
mcp = FastMCP("seven_mcp")


# ---------------------------------------------------------------------------
# Enums & helpers
# ---------------------------------------------------------------------------

class ResponseFormat(str, Enum):
    """Output encoding for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class SourceFilter(str, Enum):
    """Which kind of conversation to include."""
    ANY = "any"
    DIRECT = "direct"      # user <-> Seven
    AMBIENT = "ambient"    # passive room audio
    IMPORTED = "imported"  # externally sourced


def _as_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def _trim_iso(ts: Optional[str], length: int = 19) -> str:
    if not ts:
        return ""
    return str(ts).replace("T", " ")[:length]


def _conv_brief(conv: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": conv.get("id"),
        "started_at": conv.get("started_at"),
        "ended_at": conv.get("ended_at"),
        "source": conv.get("source"),
        "participants": conv.get("participants") or [],
        "summary": conv.get("summary"),
        "topics": conv.get("topics") or [],
        "action_items": conv.get("action_items") or [],
        "sentiment": conv.get("sentiment"),
        "mood": conv.get("mood"),
        "utterance_count": conv.get("utterance_count"),
        "word_count": conv.get("word_count"),
        "finalized": bool(conv.get("finalized")),
    }


def _conv_list_markdown(convs: List[Dict[str, Any]], header: str) -> str:
    if not convs:
        return f"# {header}\n\n_No conversations found._\n"
    lines = [f"# {header}", f"_{len(convs)} conversation(s)_\n"]
    for c in convs:
        started = _trim_iso(c.get("started_at"), 16)
        summary = c.get("summary") or "_(not summarized yet)_"
        participants = ", ".join(c.get("participants") or []) or "—"
        topics = ", ".join(c.get("topics") or []) or "—"
        actions = c.get("action_items") or []
        lines.append(f"## #{c.get('id')} · {started} · {c.get('source', '?')}")
        lines.append(f"- **Participants:** {participants}")
        lines.append(f"- **Topics:** {topics}")
        if c.get("sentiment"):
            lines.append(
                f"- **Sentiment:** {c.get('sentiment')} · "
                f"**Mood:** {c.get('mood') or '—'}"
            )
        lines.append(
            f"- **Utterances:** {c.get('utterance_count')} · "
            f"**Words:** {c.get('word_count')}"
        )
        lines.append(f"- **Summary:** {summary}")
        if actions:
            lines.append("- **Action items:**")
            for a in actions:
                lines.append(f"  - {a}")
        lines.append("")
    return "\n".join(lines)


def _apply_source_filter(
    convs: List[Dict[str, Any]], source: SourceFilter
) -> List[Dict[str, Any]]:
    if source == SourceFilter.ANY:
        return convs
    return [c for c in convs if c.get("source") == source.value]


def _filter_action_items_by_source(
    items: List[Dict[str, Any]], source: SourceFilter
) -> List[Dict[str, Any]]:
    if source == SourceFilter.ANY or not items:
        return items
    keep_ids = set()
    for cid in {it.get("conversation_id") for it in items}:
        if cid is None:
            continue
        conv = _memory.get_conversation(cid)
        if conv and conv.get("source") == source.value:
            keep_ids.add(cid)
    return [it for it in items if it.get("conversation_id") in keep_ids]


def _render_conversation_markdown(payload: Dict[str, Any]) -> str:
    conv = payload.get("conversation") or {}
    utterances = payload.get("utterances") or []
    started = _trim_iso(conv.get("started_at"), 16)
    lines = [
        f"# Conversation #{conv.get('id')} · {conv.get('source', '?')}",
        f"_Started {started}_  ·  _{conv.get('utterance_count', 0)} utterances_\n",
        "## Summary",
        conv.get("summary") or "_(not summarized yet)_",
        "",
    ]
    if conv.get("topics"):
        lines.append("**Topics:** " + ", ".join(conv["topics"]))
    if conv.get("sentiment"):
        lines.append(
            f"**Sentiment:** {conv.get('sentiment')} · "
            f"**Mood:** {conv.get('mood') or '—'}"
        )
    if conv.get("action_items"):
        lines.append("\n## Action items")
        for a in conv["action_items"]:
            lines.append(f"- {a}")
    if utterances:
        lines.append("\n## Transcript")
        for u in utterances:
            t = _trim_iso(u.get("timestamp"), 19)
            speaker = u.get("speaker", "?")
            conf = u.get("confidence")
            conf_s = (
                f" _(conf {conf:.2f})_"
                if isinstance(conf, (int, float))
                else ""
            )
            lines.append(f"- **{t} · {speaker}**{conf_s}: {u.get('text', '')}")
    return "\n".join(lines)


# ===========================================================================
# Tools
# ===========================================================================

@mcp.tool(
    name="seven_recent_conversations",
    annotations={
        "title": "List Seven's recent conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_recent_conversations(
    limit: Annotated[
        int,
        Field(description="Max number of conversations to return (1-100).",
              ge=1, le=100),
    ] = 10,
    source: Annotated[
        SourceFilter,
        Field(description=(
            "Conversation source filter: 'any' (default), 'direct' for "
            "user↔Seven chats, 'ambient' for passive room audio, "
            "'imported' for externally-sourced transcripts."
        )),
    ] = SourceFilter.ANY,
    finalized_only: Annotated[
        bool,
        Field(description=(
            "If true, only return conversations that have been finalized "
            "(summary + topics + action items populated by Ollama)."
        )),
    ] = False,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """List Seven's most recent conversation episodes, newest first.

    Each conversation is an episodic memory object with a summary, topics,
    action items, and sentiment, produced when Seven finalized it via Ollama.
    """
    try:
        convs = _memory.get_recent(
            limit=limit,
            source=source.value if source != SourceFilter.ANY else None,
            finalized_only=finalized_only,
        )
        briefs = [_conv_brief(c) for c in convs]
        if response_format == ResponseFormat.MARKDOWN:
            return _conv_list_markdown(briefs, "Recent conversations")
        return _as_json({"count": len(briefs), "conversations": briefs})
    except Exception as e:
        logger.exception("seven_recent_conversations failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_get_conversation",
    annotations={
        "title": "Get one of Seven's conversations in full",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_get_conversation(
    conversation_id: Annotated[
        int,
        Field(description="The numeric conversation ID (e.g. 42).", ge=1),
    ],
    include_transcript: Annotated[
        bool,
        Field(description=(
            "If true (default), include the full ordered list of utterances. "
            "Set false to get only episode metadata and summary."
        )),
    ] = True,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """Retrieve a single conversation episode, optionally with its full transcript.

    Use this after `seven_recent_conversations` or `seven_search_conversations`
    when you need to read what was actually said.
    """
    try:
        conv = _memory.get_conversation(conversation_id)
        if not conv:
            return _as_json({
                "error": (
                    f"No conversation with id={conversation_id}. "
                    "Use seven_recent_conversations to find valid ids."
                ),
            })

        payload: Dict[str, Any] = {"conversation": _conv_brief(conv)}
        if include_transcript:
            payload["utterances"] = _memory.get_utterances(conversation_id)

        if response_format == ResponseFormat.MARKDOWN:
            return _render_conversation_markdown(payload)
        return _as_json(payload)
    except Exception as e:
        logger.exception("seven_get_conversation failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_search_conversations",
    annotations={
        "title": "Search Seven's conversations by text",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_search_conversations(
    query: Annotated[
        str,
        Field(description=(
            "Free text to look for. Matched case-insensitively against "
            "conversation summaries AND individual utterance text."
        ), min_length=1, max_length=500),
    ],
    limit: Annotated[
        int,
        Field(description="Max conversations to return (1-100).",
              ge=1, le=100),
    ] = 20,
    source: Annotated[
        SourceFilter,
        Field(description="Filter: any / direct / ambient / imported."),
    ] = SourceFilter.ANY,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """Full-text search over Seven's episodic memory.

    Useful when you want to know if Seven has heard about a topic before
    (e.g. "DayZ", "Pieter", "v3.2.17", "the bank").
    """
    try:
        hits = _memory.search(query, limit=limit)
        hits = _apply_source_filter(hits, source)
        briefs = [_conv_brief(c) for c in hits]
        if response_format == ResponseFormat.MARKDOWN:
            return _conv_list_markdown(
                briefs, f"Search results for: {query!r}"
            )
        return _as_json({
            "query": query, "count": len(briefs), "conversations": briefs,
        })
    except Exception as e:
        logger.exception("seven_search_conversations failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_conversations_by_date",
    annotations={
        "title": "Get Seven's conversations for a specific day",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_conversations_by_date(
    date: Annotated[
        str,
        Field(description=(
            "A single calendar date to fetch conversations for. "
            "Accepted forms: 'YYYY-MM-DD' (absolute), 'today', 'yesterday'."
        ), min_length=3, max_length=10),
    ],
    source: Annotated[
        SourceFilter,
        Field(description="Filter: any / direct / ambient / imported."),
    ] = SourceFilter.ANY,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """Fetch all conversations from a single calendar day.

    Answers things like 'what happened yesterday' or 'show me April 17'.
    """
    try:
        date_s = date.strip().lower()
        if date_s == "today":
            convs = _memory.get_today()
            iso = datetime.now().strftime("%Y-%m-%d")
        elif date_s == "yesterday":
            convs = _memory.get_yesterday()
            iso = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return _as_json({
                    "error": (
                        f"Invalid date: {date!r}. "
                        "Use 'YYYY-MM-DD', 'today', or 'yesterday'."
                    ),
                })
            convs = _memory.get_by_date(date)
            iso = date

        convs = _apply_source_filter(convs, source)
        briefs = [_conv_brief(c) for c in convs]
        if response_format == ResponseFormat.MARKDOWN:
            return _conv_list_markdown(briefs, f"Conversations on {iso}")
        return _as_json({
            "date": iso, "count": len(briefs), "conversations": briefs,
        })
    except Exception as e:
        logger.exception("seven_conversations_by_date failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_action_items",
    annotations={
        "title": "List action items Seven extracted from recent conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_action_items(
    days_back: Annotated[
        int,
        Field(description="How many days of history to scan (1-365).",
              ge=1, le=365),
    ] = 7,
    source: Annotated[
        SourceFilter,
        Field(description="Filter: any / direct / ambient / imported."),
    ] = SourceFilter.ANY,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """List open TODOs Seven pulled out of recent conversations.

    Seven's conversation finalizer asks Ollama to extract action items as
    structured data. This tool aggregates them across a time window.
    """
    try:
        items = _memory.get_action_items(days_back=days_back)
        items = _filter_action_items_by_source(items, source)

        if response_format == ResponseFormat.MARKDOWN:
            if not items:
                return (
                    f"# Action items\n\n_No action items in the last "
                    f"{days_back}d._\n"
                )
            lines = [f"# Action items — last {days_back}d ({len(items)})\n"]
            for it in items:
                when = _trim_iso(it.get("started_at"), 10)
                lines.append(
                    f"- **[{when}]** (conv #{it.get('conversation_id')}) "
                    f"{it.get('item', '')}"
                )
            return "\n".join(lines)

        return _as_json({
            "days_back": days_back, "count": len(items), "items": items,
        })
    except Exception as e:
        logger.exception("seven_action_items failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_memory_stats",
    annotations={
        "title": "Seven's conversation memory stats",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_memory_stats(
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """Rollup of Seven's conversation-memory footprint.

    Returns total conversations, finalized count, utterance count, breakdown
    by source (direct/ambient/imported), and today's conversation count.
    """
    try:
        stats = _memory.get_stats()
        stats["db_path"] = str(_memory.db_path)
        stats["bot_name"] = getattr(config, "DEFAULT_BOT_NAME", "Seven")
        stats["user_name"] = getattr(config, "USER_NAME", "user")

        if response_format == ResponseFormat.MARKDOWN:
            by_source = stats.get("by_source", {}) or {}
            lines = [
                "# Seven's memory stats", "",
                f"- **DB:** `{stats['db_path']}`",
                f"- **Total conversations:** {stats.get('total_conversations', 0)}",
                f"- **Finalized:** {stats.get('finalized_conversations', 0)}",
                f"- **Utterances:** {stats.get('total_utterances', 0)}",
                f"- **Today:** {stats.get('today', 0)}", "",
                "## By source",
            ]
            if by_source:
                for k, v in by_source.items():
                    lines.append(f"- **{k}:** {v}")
            else:
                lines.append("_(empty)_")
            return "\n".join(lines)
        return _as_json(stats)
    except Exception as e:
        logger.exception("seven_memory_stats failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_today_digest",
    annotations={
        "title": "Seven's daily digest — a curated rollup",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_today_digest(
    days_back: Annotated[
        int,
        Field(description=(
            "How many days back to include (1 = today only, 7 = past week). "
            "Range 1-30."
        ), ge=1, le=30),
    ] = 1,
    max_conversations: Annotated[
        int,
        Field(description="Max conversations to include in the digest (1-50).",
              ge=1, le=50),
    ] = 10,
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'markdown' (default) or 'json'."),
    ] = ResponseFormat.MARKDOWN,
) -> str:
    """Compose a 'what happened' digest from Seven's recent memory.

    Combines conversation summaries, extracted action items, sentiment
    distribution, and topic frequency into a single human-readable report.
    Good for morning stand-ups and end-of-day reviews.
    """
    try:
        now = datetime.now()
        cutoff = now - timedelta(days=days_back)

        all_recent = _memory.get_recent(limit=200)
        in_window = [
            c for c in all_recent
            if c.get("started_at") and c["started_at"] >= cutoff.isoformat()
        ][:max_conversations]

        action_items = _memory.get_action_items(days_back=days_back)

        topic_counts: Dict[str, int] = {}
        sentiment_counts: Dict[str, int] = {}
        source_counts: Dict[str, int] = {}
        for c in in_window:
            for t in (c.get("topics") or []):
                topic_counts[t] = topic_counts.get(t, 0) + 1
            s = c.get("sentiment") or "neutral"
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
            src = c.get("source") or "unknown"
            source_counts[src] = source_counts.get(src, 0) + 1

        top_topics = sorted(
            topic_counts.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        briefs = [_conv_brief(c) for c in in_window]

        if response_format == ResponseFormat.JSON:
            return _as_json({
                "days_back": days_back,
                "generated_at": now.isoformat(),
                "conversation_count": len(briefs),
                "conversations": briefs,
                "action_items": action_items,
                "top_topics": top_topics,
                "sentiment_counts": sentiment_counts,
                "source_counts": source_counts,
            })

        label = "today" if days_back == 1 else f"last {days_back}d"
        lines = [
            f"# Seven's digest — {label}",
            f"_Generated {now.strftime('%Y-%m-%d %H:%M')}_\n",
        ]
        lines.append(f"**Conversations:** {len(briefs)}")
        if source_counts:
            lines.append(
                "**By source:** "
                + " · ".join(f"{k}: {v}" for k, v in source_counts.items())
            )
        if sentiment_counts:
            lines.append(
                "**Sentiment mix:** "
                + " · ".join(f"{k}: {v}" for k, v in sentiment_counts.items())
            )
        if top_topics:
            lines.append(
                "**Top topics:** "
                + ", ".join(f"{t} ({n})" for t, n in top_topics)
            )
        lines.append("")

        lines.append("## Action items")
        if action_items:
            for it in action_items:
                when = _trim_iso(it.get("started_at"), 10)
                lines.append(
                    f"- [{when}] {it.get('item', '')}  "
                    f"_(conv #{it.get('conversation_id')})_"
                )
        else:
            lines.append("_None extracted in this window._")
        lines.append("")

        lines.append("## Conversations")
        if not briefs:
            lines.append("_No conversations in this window._")
        else:
            for c in briefs:
                started = _trim_iso(c.get("started_at"), 16)
                summary = c.get("summary") or "_(not summarized yet)_"
                lines.append(
                    f"- **#{c.get('id')} · {started} · "
                    f"{c.get('source', '?')}**  \n  {summary}"
                )
        return "\n".join(lines)
    except Exception as e:
        logger.exception("seven_today_digest failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


@mcp.tool(
    name="seven_list_extensions",
    annotations={
        "title": "List the extensions Seven has loaded",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def seven_list_extensions(
    response_format: Annotated[
        ResponseFormat,
        Field(description="Output format: 'json' (default) or 'markdown'."),
    ] = ResponseFormat.JSON,
) -> str:
    """Introspect Seven's plugin system — what extensions are installed,
    their versions, and authors.

    Runs the plugin loader's discovery + AST security scan in a read-only
    way (no extension's `run` or `start` is executed).
    """
    try:
        from utils.plugin_loader import PluginLoader

        loader = PluginLoader(bot=None)
        loader.load_all()
        rows = loader.list_extensions()
        loader.stop_all()

        if response_format == ResponseFormat.MARKDOWN:
            if not rows:
                return "# Seven's extensions\n\n_No extensions loaded._\n"
            lines = [f"# Seven's extensions ({len(rows)})\n"]
            for r in rows:
                lines.append(
                    f"- **{r.get('name')}** v{r.get('version')}  "
                    f"— {r.get('description', '')}"
                )
                if r.get("author"):
                    lines.append(f"  _by {r.get('author')}_")
            return "\n".join(lines)
        return _as_json({"count": len(rows), "extensions": rows})
    except Exception as e:
        logger.exception("seven_list_extensions failed")
        return _as_json({"error": f"{type(e).__name__}: {e}"})


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    logger.info(
        "Starting seven_mcp — db=%s — 8 tools registered",
        _memory.db_path,
    )
    mcp.run()


if __name__ == "__main__":
    main()
