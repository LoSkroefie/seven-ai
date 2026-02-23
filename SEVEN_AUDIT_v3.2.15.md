# Seven AI — Complete Code Audit v3.2.15
**Date:** February 23, 2026  
**Auditor:** Clawd (AI pair programmer)  
**Codebase:** ~192KB enhanced_bot.py + 80+ modules, 47,000+ lines  

---

## SECTION 1: BUGS & BROKEN WIRING

### BUG-1: Self-scripting SKIPS safety scan before execution
- **Severity:** HIGH (security)
- **Location:** `enhanced_bot.py:2534-2541`
- **Issue:** `_handle_scripting_request` calls `self.scripting.run_script()` directly, BYPASSING the safety scanner. The `generate_and_run()` method (which includes `_scan_code_safety()`) is **never called** from anywhere.
- **Impact:** Seven can generate and execute scripts containing `os.system()`, `eval()`, `subprocess` calls etc. without any safety check.
- **Fix:** Replace the "run the script" handler to call `generate_and_run()`, or always run `_scan_code_safety()` before `run_script()`.

### BUG-2: vector_memory_v2 initialized but never used
- **Severity:** MODERATE (wasted resources + missed functionality)
- **Location:** `enhanced_bot.py:779-783` (init) vs `enhanced_bot.py:23,1389,1596,3092` (usage)
- **Issue:** `self.vector_memory_v2 = EnhancedVectorMemory()` is initialized, but ALL actual vector memory calls use `self.vector_memory` (v1). The v2 has 5-collection emotion-weighted storage — significantly better.
- **Fix:** Replace v1 usage with v2, or remove v2 init to save memory.

### BUG-3: performance_monitor initialized but never used
- **Severity:** LOW (wasted init)
- **Location:** `enhanced_bot.py:821-824`
- **Issue:** `self.performance_monitor = PerformanceMonitor()` is created but `.` is never called anywhere. Has threading support, metric collection — all dead.
- **Fix:** Wire it into the main loop, or remove init.

### BUG-4: Extensions can't react to messages
- **Severity:** MODERATE (feature broken)
- **Location:** `plugin_loader.py:491-511` (has `notify_message`), `enhanced_bot.py` (never calls it)
- **Issue:** `PluginLoader.notify_message()` is fully implemented — it calls `on_message()` on every loaded extension. But it's **never called** from the bot's main loop. Extensions loaded and started but can never react to conversations.
- **Fix:** Add `self.plugin_loader.notify_message(user_input, response)` after each response in the main loop.

### BUG-5: bot_initializers.py imported but never called
- **Severity:** LOW (dead code)
- **Location:** `enhanced_bot.py:99` imports `from core import bot_initializers`
- **Issue:** `bot_initializers.py` (497 lines) contains `init_communication_clients()`, `init_sentience_v2()` etc. — but these functions are NEVER called. All that init code is **duplicated** inline in `enhanced_bot.py __init__`. Two copies of the same logic.
- **Fix:** Either use `bot_initializers` or delete it.

### BUG-6: Self-scripting edit_file/read_file not wired
- **Severity:** LOW (missing feature)
- **Location:** `self_scripting.py:280-336` (implemented), `enhanced_bot.py:2499-2561` (handler)
- **Issue:** `scripting.edit_file()` and `scripting.read_file()` are implemented but `_handle_scripting_request` has no voice triggers for "read file X" or "edit file X". Only create/delete are wired.
- **Fix:** Add regex patterns for read/edit in the handler.

### BUG-7: Dream System shows inactive (⬜) even when Phase5 is running
- **Severity:** LOW (cosmetic in web UI)
- **Location:** `web_ui.py` checks `self.bot.dream_system`, `enhanced_bot.py` never sets it
- **Issue:** The DreamSystem lives inside `self.phase5.dream_system` (Phase5Integration), but the web UI checks `self.bot.dream_system` which doesn't exist on the bot instance.
- **Fix:** Expose `self.dream_system = self.phase5.dream_system` after Phase5 init, or fix web UI to check `self.bot.phase5.dream_system`.

---

## SECTION 2: DEAD CODE & CLEANUP

### DEAD-1: Deprecated files in core/
- `core/tool_library_backup.py.deprecated` (11.5 KB)
- `core/tool_library_fixed.py.deprecated` (3.3 KB)
- **Action:** Delete both.

### DEAD-2: Development utility scripts in root
These are one-time analysis/debug scripts, not part of Seven:
- `_analyze_convos.py`, `_analyze_db.py`, `_analyze_session.py`
- `analyze_code.py`, `scan_code.py`
- `fix_config.py`, `verify_gui_fix.py`
- `find_cameras.py`, `discover_cameras.py`
- `launch_v2_test.py`, `test_neat.py`, `test_v3.py`
- `create_desktop_shortcut.py`, `create_shortcut.py` (superseded by `create_shortcuts.ps1`)
- **Action:** Move to a `dev_tools/` folder or delete from release.

### DEAD-3: Old zip releases in repo
- `Seven-AI-v1.0.0.zip` (435 KB)
- `Seven-AI-v2.0-Complete.zip` (289 KB)
- **Action:** Remove from repo. Releases belong on GitHub Releases, not in source.

### DEAD-4: Markdown docs in core/v2/
- `SEVEN_COMPLETE_EVALUATION.md`, `SEVEN_V2_DEPLOYMENT_COMPLETE.md`
- `STEP1_COMPLETE.md`, `STEP2_COMPLETE.md`, `STEP3_PROGRESS.md`
- **Action:** Development notes, not runtime code. Move to `docs/` or delete.

### DEAD-5: Multiple distribution scripts
- `create_distribution.bat`, `create_distribution.ps1`, `create_distribution_v2.ps1`
- `create_package.bat`, `create_package_v2.ps1`, `build_package.ps1`
- **Action:** Consolidate to one or remove (we use `_build_deploy.py` now).

### DEAD-6: bot_initializers.py — 497 lines of duplicated code
- Contains `init_communication_clients()`, `init_sentience_v2()`, etc.
- All duplicated inline in `enhanced_bot.py __init__`
- **Action:** Either refactor to USE it, or delete it.

---

## SECTION 3: SELF-SCRIPTING ANALYSIS

### Current State:
- ✅ `generate_script()` — works, generates Python/VB.NET/C# via Ollama
- ✅ `run_script()` — works, executes with timeout
- ✅ `_scan_code_safety()` — works, blocks dangerous imports/patterns
- ✅ `generate_and_run()` — works (generate + scan + run) but **NEVER CALLED**
- ✅ `create_file()`, `delete_file()` — wired to voice
- ❌ `edit_file()`, `read_file()` — implemented but NOT wired
- ✅ Tool registry — persists to `~/Documents/Seven/scripts/tool_registry.json`
- ✅ Execution history — in-memory, capped at 100

### Critical Gap: Self-Scripting ↔ Extensions Bridge
- Self-scripting saves to `~/Documents/Seven/scripts/`
- Extensions live in `extensions/`
- **Seven cannot create her own extensions.** She can write scripts but they don't become extensions.
- **Fix:** Add `scripting.create_extension()` that generates a `SevenExtension` subclass and saves to `extensions/`, then calls `plugin_loader.reload_all()`.

### Can Seven Maintain Her Scripts?
**Partially.** She can:
- Generate new scripts ✅
- Run them ✅  
- List her tools ✅
- Create/delete files ✅

She **cannot**:
- Edit existing scripts via voice (edit_file not wired) ❌
- Read a script back via voice (read_file not wired) ❌
- Debug a failed script (no retry/fix loop) ❌
- Auto-improve scripts based on execution results ❌
- Create extensions from scripts ❌

---

## SECTION 4: IMPROVEMENT OPPORTUNITIES

### IMP-1: Use vector_memory_v2 instead of v1
The v2 (`EnhancedVectorMemory`) has:
- 5 separate collections (conversations, facts, emotions, goals, context)
- Emotion-weighted retrieval
- Automatic categorization
Currently unused. Should replace v1 entirely.

### IMP-2: Wire performance_monitor
`PerformanceMonitor` has response time tracking, LLM call metrics, system resource monitoring. Wire it into:
- `_ask_ollama_enhanced()` for response time tracking
- Main loop for interaction metrics  
- Web UI System tab for display

### IMP-3: Fix extension message notifications
One-line fix: after response generation in main loop, add:
```python
if self.plugin_loader:
    self.plugin_loader.notify_message(user_input, response)
```
This enables extensions to react to every conversation.

### IMP-4: Self-scripting → Extension bridge
Add `create_extension(name, description, task, schedule_minutes)` to SelfScriptingEngine that:
1. Generates a SevenExtension subclass via Ollama
2. Saves to `extensions/`
3. Triggers hot-reload

### IMP-5: Script debugging loop
When a script fails, Seven should:
1. Read the error
2. Feed error + original code to Ollama
3. Get fixed version
4. Retry (max 3 attempts)

### IMP-6: Consolidate enhanced_bot.py
At 192KB/3817 lines, this file is massive. Consider:
- Move handler methods to separate files (like enhancement_commands.py pattern)
- Use bot_initializers.py properly instead of duplicating

---

## SECTION 5: NEW ABILITIES / EXTENSIONS TO BUILD

### Pre-Built Extensions (ready to create):

**1. Daily Digest Extension**
- Summarizes: today's conversations, emotional trends, KG growth, goals progress
- Schedule: once daily at configurable time
- Speaks summary or saves to diary

**2. Weather Extension**
- Fetches weather for configured location
- Proactively mentions weather context ("It's cold outside today")
- Schedule: every 3 hours

**3. System Health Extension**
- Monitors CPU, RAM, disk, network
- Alerts Seven if resources are low
- Schedule: every 5 minutes

**4. Learning Journal Extension**
- Tracks what Seven learned today (new KG nodes, facts, user preferences)
- Summarizes learning at end of day
- Schedule: daily

**5. Conversation Analytics Extension**
- Track average response time, topics discussed, emotional patterns
- Build user engagement metrics
- Schedule: after each conversation (via on_message)

**6. Auto-Backup Extension**
- Backs up Seven's data files (DB, KG, emotions, identity)
- Schedule: daily
- Keeps last 7 backups

**7. News/RSS Extension**
- Reads configurable RSS feeds
- Summarizes headlines via Ollama
- Can discuss current events knowledgeably

**8. Motivation Extension**
- Generates encouraging messages based on Seven's emotional state
- Activates when energy is low or mood is negative
- Schedule: triggered by homeostasis

### New Abilities (require code changes):

**1. Windows Toast Notifications**
- Seven can send desktop notifications for reminders, alerts, proactive thoughts
- Uses `win10toast` or `plyer` library

**2. Browser Tab Awareness**
- Know what the user is browsing (via accessibility API or browser extension)
- Offer contextual help

**3. PDF/Report Generation**
- Seven can create formatted reports from her data
- Uses `reportlab` or `fpdf`

**4. Voice Memo Recording**
- Record audio clips to files
- Already has microphone access

**5. Image/Screenshot OCR**
- Extract text from images/screenshots
- Already has OpenCV; add `pytesseract`

**6. Multi-Language Translation**
- Translate text between languages via Ollama
- Already has the LLM — just needs prompt engineering

**7. Clipboard History**
- Track last N clipboard entries (not just current)
- Already monitors clipboard — extend to keep history

**8. App/Window Awareness**
- Detect active window and running applications
- Offer context-sensitive help ("I see you're in VS Code...")
- Uses `pygetwindow` or Win32 API

---

## SECTION 6: SUMMARY & PRIORITY

### Must Fix (security/correctness):
1. **BUG-1:** Self-scripting safety scan bypass — HIGH
2. **BUG-4:** Extension notify_message not called — MODERATE
3. **BUG-2:** vector_memory_v2 not used — MODERATE

### Should Fix (quality):
4. **BUG-6:** Wire edit_file/read_file to voice
5. **BUG-7:** Dream System web UI display
6. **DEAD-1 through DEAD-6:** Clean dead code
7. **IMP-4:** Self-scripting → Extension bridge

### Nice to Have (features):
8. Pre-built extensions (6-8 of them)
9. Windows toast notifications
10. Script debugging loop
11. Performance monitor wiring

---

*End of audit. All findings verified against source code.*
