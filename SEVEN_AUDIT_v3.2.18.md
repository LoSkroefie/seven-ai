# Seven AI — Code Audit v3.2.18
**Date:** April 17, 2026
**Auditor:** Cascade
**Scope:** New `Action Item Digest` extension — proactive surfacing of TODOs extracted by v3.2.17's conversation memory system.

---

## Executive Summary

One new extension file, one config block. Pure consumer of the `conversation_memory` tables from v3.2.17 — no schema changes, no new dependencies beyond what's already in Seven. OFF by default.

Where v3.2.17 taught Seven to *remember*, v3.2.18 teaches her to *act* on what she remembers. The `action_items` JSON column that Ollama populates on conversation finalization is no longer just data at rest — the digest extension periodically mines it and proactively surfaces new TODOs via Windows toast (and optionally voice), with persistent deduplication so the same item never nags twice.

Build verified on target machine: compiles, passes AST security scanner, registers with `PluginLoader`, `ConversationMemory` handle wires up cleanly against live `~/.chatbot/memory.db`.

---

## Files Created

| File | Purpose | Lines |
|---|---|---|
| `extensions/action_item_digest.py` | Mines `ConversationMemory.get_action_items()`, dedupes against `~/.chatbot/action_items_seen.json`, surfaces via toast + voice. Voice-commandable retrieval. | 311 |

## Files Modified

| File | Change |
|---|---|
| `config.py` | Appended a 32-line `# ==================== ACTION ITEM DIGEST — v3.2.18 ====================` block with 7 new config keys, all safe defaults. |

## Files Temporary (cleanup)

- `_verify_v3218.py` — post-deploy integration check. Can be deleted.

---

## Architecture

### Data flow

```
ambient_listener / direct on_message hook
        │
        ▼
ConversationMemory.add_utterance(...)  (v3.2.17)
        │
        ▼
ConversationMemory.finalize_conversation(cid, ollama=bot.ollama)
        │ (Ollama extracts action_items into conversations.action_items JSON)
        ▼
──────────────────────────────────────── v3.2.18 picks up here ────
ActionItemDigestExtension.run()  (every ACTION_ITEM_INTERVAL_MINUTES)
        │
        ├─ ConversationMemory.get_action_items(days_back=lookback)
        │
        ├─ _filter_new() drops items whose fingerprint is in _seen set
        │
        ├─ _surface_items() delivers up to max_per_run:
        │     ├─ bot.toast.notify(...)  if available
        │     └─ bot._speak(...)        if use_voice=True and available
        │
        └─ _mark_seen(fingerprints) → persists to
                 ~/.chatbot/action_items_seen.json
```

### Fingerprinting

Each action item is hashed via SHA-1 over a normalized form (whitespace collapsed, lowercased), truncated to 16 hex chars. This makes "Email Pieter" and "email  pieter " and "EMAIL PIETER" all collide, which is the correct behavior — the same TODO phrased slightly differently by Ollama across two conversations shouldn't double-notify.

Seen fingerprints persist in `~/.chatbot/action_items_seen.json` as `{fingerprint: iso_timestamp}`. On load, the timestamps are used to prune entries older than 180 days so the state file doesn't grow unboundedly. Restarting Seven doesn't cause previously-surfaced items to re-toast — verified in smoke test (fresh extension instance loaded 6 seen fingerprints from disk and correctly reported "no new items").

### Batched delivery

`ACTION_ITEM_MAX_PER_RUN` (default 3) caps how many toasts fire per scheduled pass. If there are more new items than the cap, the remainder are queued for the next tick (naturally — they stay unfingerprinted in `_seen`, so the next `run()` picks them up). Keeps Seven from spam-blasting you if a week's worth of conversations finalize at once.

### Voice commands

All matched case-insensitive in `on_message`:

| Phrase | Behavior |
|---|---|
| `what's on my plate` / `whats on my plate` / `on my plate` / `my plate` | Grouped by day, full lookback window (default 3d) |
| `my action items` / `what do i need to do` | Same as "on my plate" |
| `action items today` | Only today's items |
| `clear action items` / `forget action items` | Mark all current items as seen — Seven won't re-surface them |
| `digest status` / `action item status` | Stats rollup (runs, surfaced, seen, errors) |

Items are displayed with `✓` (already surfaced / acknowledged) or `•` (new, pending).

---

## LLM Usage Audit — Nothing Hardcoded

This extension does not call Ollama directly. It consumes the `action_items` that v3.2.17's `ConversationMemory.finalize_conversation()` already extracted via Ollama JSON-prompt. `needs_ollama = False` is correctly declared.

---

## Extension Security Audit

Ran Seven's actual `PluginLoader._ast_scan_imports()` on `action_item_digest.py`:

```
AST scan: PASS
```

Imports used (none in `BLOCKED_MODULES`):
`hashlib`, `json`, `logging`, `re`, `datetime`, `pathlib`, `typing`, `utils.plugin_loader`, `config`, `core.conversation_memory`.

No `subprocess`, `shutil`, `ctypes`, `multiprocessing`, `socket`, `http.server`, `xmlrpc`, `ftplib`, `smtplib`.

---

## Runtime Verification on Target Machine

```
extensions/action_item_digest.py: OK
ENABLE_ACTION_ITEM_DIGEST = False
ACTION_ITEM_INTERVAL_MINUTES = 60
ACTION_ITEM_MAX_PER_RUN = 3
AST scan: PASS
Plugin load: stem=action_item_digest status=loaded
Extension: action_item_digest.ActionItemDigestExtension
  name=Action Item Digest version=1.0
  enabled=False lookback=3d max/run=3
  memory_available=True seen_items=0
  use_toast=True use_voice=False
```

Smoke test (isolated sandbox, mock Ollama returning 6 action items across 3 conversations):
- **Run 1**: surfaced 2 items (max_per_run cap), queued 4 for next tick.
- **Run 2**: surfaced 2 more (queued → surfaced).
- **Run 3**: surfaced final 2.
- **Run 4** (persistence check, fresh extension instance): loaded 6 fingerprints from disk, correctly reported "no new action items".
- **`clear action items`**: marked all 6 current items as acknowledged, returns `Acknowledged 6 action item(s). I won't surface them again.`
- **`digest status`**: returns full stats line with counts.

All behaviors match design.

---

## Configuration Additions

Block appended to `config.py` (all defaults safe — extension is OFF until explicitly enabled):

```python
ENABLE_ACTION_ITEM_DIGEST       = False    # master switch
ACTION_ITEM_INTERVAL_MINUTES    = 60       # schedule cadence
ACTION_ITEM_LOOKBACK_DAYS       = 3        # scan window
ACTION_ITEM_MAX_PER_RUN         = 3        # toasts per tick
ACTION_ITEM_USE_TOAST           = True
ACTION_ITEM_USE_VOICE           = False    # off by default — audible
ACTION_ITEM_MIN_LEN             = 4        # drop trivial items
```

---

## Activation

After v3.2.17 is live and `ENABLE_AMBIENT_LISTENER = True` (or the `on_message` direct-conversation path is accumulating data), enable this:

1. Edit `config.py`:
   ```python
   ENABLE_ACTION_ITEM_DIGEST = True
   ```

2. Optionally install toast backend (one of):
   ```
   pip install win10toast-persist
   pip install plyer
   ```

3. Restart Seven. Every 60 minutes (configurable), new action items extracted from your conversations will toast-notify you. Ask "what's on my plate" any time.

Disable at any time by flipping the flag back to `False`, or stop individual items surfacing with `clear action items` (one-off) or by lowering `ACTION_ITEM_MAX_PER_RUN = 0` (silent scan, still queryable).

---

## Dependency Note

| Dependency | Role | Required? |
|---|---|---|
| `core.conversation_memory.ConversationMemory` (v3.2.17) | Source of action items | Yes — hard requirement |
| `bot.toast` (`ToastNotificationManager` from `integrations/toast_notifications.py`) | Delivery | Optional — if absent, toasts silently skip |
| `bot._speak` | Voice delivery | Optional — only used if `ACTION_ITEM_USE_VOICE=True` |
| `bot.ollama` | Not used | N/A — Ollama already ran during finalization |

Graceful degradation: if `ConversationMemory` can't load, `run()` returns `{"status": "skipped", "message": "conversation memory unavailable"}`. If `bot.toast` isn't available, delivery is silent — `_format_status()` still reports stats.

---

## Future Work — Natural Extensions

This closes the v3.2.17 loop (memory → action). Next candidates on the same foundation:

- **Task manager integration**: route action items into `core/task_manager.py` (existing) as concrete tasks, not just toasts. Enables `mark done` / `snooze` / `defer to tomorrow`.
- **Due-date inference**: parse items like "email Pieter *tomorrow*" → schedule a `smart_reminders` entry automatically.
- **Priority scoring**: weight items by urgency keywords, speaker (user vs ambient), and repeat mentions across conversations.
- **MCP server surface**: expose `list_action_items`, `mark_done`, `snooze` over MCP so Claude / Cursor / the Claude-in-Chrome tool can query Seven's TODO list directly (this is item #5 from the omi-inspiration list).
