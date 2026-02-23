# Seven AI — Complete Code Audit v3.2.16
**Date:** February 23, 2026  
**Auditor:** Cascade  
**Scope:** All changes from v3.2.15 audit fixes + new extensions + new abilities

---

## Executive Summary

Thorough code examination of all v3.2.16 changes. Found and fixed **6 bugs** (3 critical, 3 medium). Added **2 more abilities** (screen capture, text summarizer). Verified all LLM calls are real (no hardcoded fakes). All extensions pass the plugin loader's AST security scan.

---

## Bugs Found & Fixed

### CRITICAL

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | **Shell command execution crash** — `run_pending_dangerous_script()` called `run_script(filepath=None)` for shell commands, causing "Script not found: None" | `self_scripting.py:301` | Added `is_shell_command` branch that runs via `subprocess.run()` directly |
| 2 | **auto_backup.py blocked by plugin loader** — imported `shutil` which is in `BLOCKED_MODULES`, causing extension to be rejected on load. `shutil` was also unused (dead import). | `extensions/auto_backup.py:9` | Removed dead `shutil` import |
| 3 | **pending_dangerous_script never initialized** — only set dynamically via attribute assignment, making `hasattr` checks fragile and error-prone on fresh instances | `self_scripting.py:__init__` | Added `self.pending_dangerous_script = None` in `__init__` |

### MEDIUM

| # | Bug | File | Fix |
|---|-----|------|-----|
| 4 | **"no" cancel too broad** — bare `"no"` substring match would trigger on "no problem", "know", "innovation", etc. when a pending script existed | `enhanced_bot.py:2593` | Changed to exact match `user_lower.strip() == "no"` plus specific phrases like "cancel", "abort" |
| 5 | **needs_ollama flag lies** — `motivation_engine`, `daily_digest`, `learning_journal`, `news_digest` all claimed `needs_ollama=True` but never called Ollama | Multiple extensions | Fixed flags. Upgraded `motivation_engine` to actually use LLM with fallbacks. |
| 6 | **news_digest docstring lie** — docstring said "summarizing headlines via Ollama" but no Ollama usage existed | `news_digest.py:4` | Fixed docstring to match actual behavior |

---

## Bugs Verified NOT Present

| Concern | Status | Detail |
|---------|--------|--------|
| Vector memory v2 init args | **OK** | `_safe_init(VectorMemory)` calls `EnhancedVectorMemory()` with no args — works because all params have defaults |
| Vector memory v1 compat | **OK** | `store()`, `search_similar()`, `get_relevant_context()` all implemented as shims in v2 |
| Plugin loader AST scan vs extensions | **OK** | All extensions now pass. `requests`, `feedparser`, `psutil` are NOT in `BLOCKED_MODULES` |
| Translation regex multi-word | **OK** | `translate\s+(.+?)\s+(?:to|into)\s+(\w+)` correctly captures "hello world" from "translate hello world to spanish" |
| notify_message return type | **OK** | Plugin loader checks `isinstance(result, str)` before appending — safe |
| Pending script ordering | **OK** | Confirmation check is first in `_handle_scripting_request`, before any other pattern matching |
| Memory.get_recent_conversations | **OK** | Method exists at line 118 of `core/memory.py` |

---

## LLM Usage Audit — Nothing Hardcoded

| Component | Uses Real LLM? | How |
|-----------|----------------|-----|
| `self_scripting.generate_script()` | **YES** | `ollama.generate()` with task-specific system prompt |
| `translation.translate()` | **YES** | `ollama.generate()` with translation prompt, temp=0.2 |
| `translation.detect_language()` | **YES** | `ollama.generate()` with language detection prompt |
| `text_summarizer.summarize()` | **YES** | `ollama.generate()` with style-specific summarization prompt |
| `motivation_engine._generate_llm_encouragement()` | **YES** | `ollama.generate()` with mood-aware encouragement prompt, falls back to hardcoded if Ollama unavailable |
| `_handle_scripting_request` code gen | **YES** | Routes through `self.scripting.generate_script()` → Ollama |
| Weather extension | N/A | Uses wttr.in REST API (no LLM needed) |
| News extension | N/A | Uses RSS feeds (no LLM needed) |
| System Health | N/A | Uses psutil (no LLM needed) |
| All other extensions | N/A | Data tracking only, no text generation |

---

## Extension Security Audit

All extensions pass the plugin loader's AST import scanner (`BLOCKED_MODULES`):

| Extension | Imports | Blocked? |
|-----------|---------|----------|
| daily_digest.py | logging, datetime | Clean |
| system_health.py | logging, platform, psutil (try/except) | Clean |
| auto_backup.py | logging, zipfile, datetime, pathlib | Clean (shutil removed) |
| conversation_analytics.py | logging, datetime, collections | Clean |
| learning_journal.py | logging, datetime | Clean |
| mood_tracker.py | logging, datetime, collections | Clean |
| motivation_engine.py | logging, random, datetime | Clean |
| weather_reporter.py | logging, json, datetime, requests (try/except) | Clean |
| news_digest.py | logging, datetime, feedparser/requests (try/except) | Clean |

---

## New Abilities Added (v3.2.16)

### From Previous Session (7 abilities)
1. **Toast Notifications** — `integrations/toast_notifications.py` — win10toast/plyer backend
2. **Clipboard History** — `integrations/clipboard_history.py` — 50-entry history with search
3. **Window Awareness** — `integrations/window_awareness.py` — active window, running apps, context hints
4. **PDF Generator** — `integrations/pdf_generator.py` — conversation/emotional/custom reports
5. **Translation** — `integrations/translation.py` — 32 languages via Ollama LLM
6. **Screen Capture** — `integrations/screen_capture.py` — mss/PIL backends, saves to ~/Documents/Seven/screenshots/
7. **Text Summarizer** — `integrations/text_summarizer.py` — concise/detailed/bullet/eli5 styles via Ollama LLM

### Voice/Text Command Coverage

| Ability | Trigger Phrases |
|---------|----------------|
| Translation | "translate X to Y", "what language is this: X", "available languages" |
| Clipboard | "clipboard history", "what did I copy", "search clipboard for X", "clear clipboard history" |
| Window | "what app am I using", "running apps", "is X running" |
| PDF | "generate report", "create PDF", "conversation report" |
| Screenshot | "take screenshot", "capture screen", "last screenshot" |
| Summarize | "summarize this: X", "summarize file X", "summarize clipboard", "summarize conversation" |

---

## Extensions Added (9 total)

| Extension | Schedule | LLM? | Function |
|-----------|----------|-------|----------|
| Daily Digest | 12h | No | Summarizes conversations, emotions, KG growth |
| System Health | 5min | No | CPU/RAM/disk/battery alerts via psutil |
| Auto-Backup | 24h | No | Zip backup of Seven's data, keeps last 7 |
| Conversation Analytics | passive | No | Tracks words, topics, hourly activity |
| Learning Journal | 8h | No | Tracks facts learned, corrections, observations |
| Mood Tracker | 1h | No | Emotional patterns, volatility, mood shifts |
| Motivation Engine | 30min | **Yes** | LLM-generated encouragement with hardcoded fallbacks |
| Weather Reporter | 3h | No | Weather via wttr.in, proactive context on weather questions |
| News Digest | 4h | No | RSS headlines from BBC/Reuters/TechCrunch/HN |

---

## Architecture Integrity

### Self-Scripting Safety Flow
```
User says "write and run a script that..."
  → generate_and_run() → generate_script() via Ollama
  → _scan_code_safety() → returns warnings (never blocks)
  → If warnings: store pending, ask user "say yes run it"
  → If clean: execute immediately
  
User says "yes run it"
  → run_pending_dangerous_script()
  → Shell command? → subprocess.run() directly
  → Script file? → run_script(filepath)
  → Code only? → run_script(code=code) → temp file → execute
```

### Vector Memory v2 Integration
```
Import chain: EnhancedVectorMemory as VectorMemory (fallback: v1 → dummy)
Init: _safe_init(VectorMemory) → EnhancedVectorMemory() with defaults
Store: self.vector_memory.store() → v1 compat shim → store_conversation()
Recall: self.vector_memory.get_relevant_context() → cross-collection search
Personality: trigger_memory_recall() → search_similar() → v1 compat shim → recall()
```

### Extension Notification Flow
```
User message → _process_input() → response generated
  → self.vector_memory.store(user_input, response, emotion)
  → self.plugin_loader.notify_message(user_input, response)
    → for each extension: ext.on_message(user_msg, bot_resp)
    → collect string returns into additional[] list
```

---

## Files Modified
- `integrations/self_scripting.py` — safety scan warns not blocks, pending script init, shell cmd fix
- `core/enhanced_bot.py` — v2 import, handler wiring, 6 new handler methods, ability init
- `core/vector_memory_v2.py` — v1 compat methods (store, search_similar)
- `extensions/auto_backup.py` — removed blocked shutil import
- `extensions/motivation_engine.py` — LLM-powered encouragement
- `extensions/daily_digest.py` — fixed needs_ollama flag
- `extensions/learning_journal.py` — fixed needs_ollama flag
- `extensions/news_digest.py` — fixed needs_ollama flag and docstring

## Files Created
- `extensions/daily_digest.py`, `system_health.py`, `auto_backup.py`, `conversation_analytics.py`
- `extensions/learning_journal.py`, `mood_tracker.py`, `motivation_engine.py`
- `extensions/weather_reporter.py`, `news_digest.py`
- `integrations/toast_notifications.py`, `clipboard_history.py`, `window_awareness.py`
- `integrations/pdf_generator.py`, `translation.py`, `screen_capture.py`, `text_summarizer.py`

## Files Removed
- `Seven-AI-v1.0.0.zip` (435KB old release)
- `Seven-AI-v2.0-Complete.zip` (289KB old release)

---

## Remaining Notes

1. **`bot_initializers.py`** — imported at line 102 but never called. Left in place (test references it). Could be removed in future cleanup.
2. **Plugin loader BLOCKED_MODULES** — still blocks `shutil`, `subprocess`, etc. in extensions. This is correct for user-created extensions but means Seven's own bundled extensions must avoid these imports. All current extensions are clean.
3. **Optional dependencies** — `win10toast`, `fpdf2`, `feedparser`, `mss`, `psutil`, `pyperclip`, `requests` are all optional. Each integration gracefully degrades if its dependency is missing.
