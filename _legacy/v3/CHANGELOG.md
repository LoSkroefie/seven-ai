# Seven AI - Changelog

All notable changes to Seven AI will be documented in this file.

## [3.2.20] - 2026-04-19

### 🎯 Major Audit + Integration Release

This release is the culmination of a comprehensive runtime-reachability audit. Every feature claimed to work in v3.2.17–v3.2.19 was verified end-to-end, and several silent bugs (ghost method calls, dropped extension returns, broken dashboard subsystems) were fixed. Added opencode CLI delegation, wired the MCP server, enabled Whisper STT by default, and fixed librosa voice-tone emotion detection.

### Added

#### **opencode Delegator** (`extensions/opencode_delegator.py`)
Seven can now delegate coding/analysis tasks to the [opencode](https://github.com/sst/opencode) CLI via natural-language triggers:
- `opencode, <task>` / `opencode: <task>`
- `ask opencode to <task>`
- `delegate to opencode: <task>`
- `hey opencode <task>`
- `opencode status` / `opencode version`

Default agent is `plan` (read-only). The `build` agent (which can modify files) is opt-in via `OPENCODE_ALLOW_BUILD = True`. 180s default timeout. Output truncated at 4000 chars (configurable).

#### **MCP Server Auto-Launch**
`ENABLE_MCP_SERVER = True` in config.py now auto-launches `seven_mcp.py` as a subprocess alongside the bot, exposing 8 read-only memory tools over stdio to any MCP-aware client (Claude Desktop, Cursor, Continue). Bot lifecycle manages the subprocess cleanly (3s grace on stop, then kill).

#### **Whisper STT — Enabled by Default**
`USE_WHISPER = True` out of the box. Local, CUDA-accelerated speech recognition. New tunables:
- `WHISPER_MODEL_SIZE` (tiny / base / small / medium / large)
- `WHISPER_DEVICE` (auto / cuda / cpu)
- `WHISPER_LANGUAGE` (default "en", None for auto-detect)
- `WHISPER_MIC_INDEX` (explicit mic selection)
- `WHISPER_NO_SPEECH_THRESHOLD` (rejects silence hallucinations like "you", "thanks for watching")
- `WHISPER_LISTEN_TIMEOUT`, `WHISPER_PHRASE_LIMIT`
- `WHISPER_RECALIBRATE_EACH_LISTEN`

#### **`run_seven.bat`** — pinned Python launcher (Windows)
New batch file that forces launch with the correct Python interpreter (the one where whisper/mcp/torch+cuda are actually installed). Eliminates the "Whisper not installed" error caused by Windows Store Python shadowing the real env.

#### **Extension Scheduler**
`utils/plugin_loader.py` now has `start_scheduler()` / `stop_scheduler()` / `_scheduler_loop()`. 14 scheduled extensions now actually run on their intervals:
- smart_reminders (1m), system_health (30m), uptime_monitor (60m), motivation_engine (30m)
- action_item_digest (60m), mood_tracker (60m), ambient_listener (15m), habit_tracker (120m)
- weather_reporter (180m), news_digest (240m), learning_journal (480m), daily_digest (720m)
- auto_backup (1440m), quote_of_the_day (1440m)

Previously these extensions were loaded but never fired (BUG-R4). Now fixed and runtime-verified.

#### **Voice Tone Emotion Detection** (librosa)
`VoiceEmotionDetector` now imports cleanly when launched with the correct Python. Detects happy / sad / angry / excited / calm / anxious from pitch, energy, tempo, spectral centroid. Fixed deprecated `librosa.beat.tempo` → `librosa.feature.rhythm.tempo` with graceful fallback.

#### **Ghost-Method Audit Tool** (internal)
AST-based scanner that finds `self.x.method()` calls where `method` doesn't exist on `x`'s class. Caught and fixed 4 real bugs in v2 subsystems (see Fixed section).

#### **Escape-Sequence Audit Tool** (internal)
Warnings-as-errors compile across every `.py` to catch invalid `\.` escape sequences that would break in future Python. Caught and fixed 2 warnings in `setup_wizard.py`.

#### **Episodic Conversation Memory** (v3.2.17, now wired)
`core/conversation_memory.py` with `ConversationMemory` — SQLite-backed per-turn storage with mood/topic/sentiment extraction. Exposed via MCP tools.

#### **Ambient Listener** (v3.2.17, gated)
`extensions/ambient_listener.py` — passive capture with Whisper for always-on ambient recognition. Off by default (`ENABLE_AMBIENT_LISTENER = False`).

#### **Action Item Digest**
`extensions/action_item_digest.py` — scans recent conversations for action items, generates daily digest. Off by default.

### Fixed

#### **Ghost Method Calls** (4 real bugs found by audit)
- `RelationshipModel.update_interaction(user, bot, mood)` → correct method is `record_interaction(quality, topics, emotional_valence)`. Was throwing `AttributeError` on every conversation turn, silently absorbed by the outer try/except which skipped all downstream sentience processing.
- `GoalSystem.evaluate_progress(user, bot)` → correct method is `get_state()` (or `record_progress` for updates).
- `ProactiveEngine.check_proactive_opportunity(...)` → correct methods are `should_greet()` / `should_check_in()` / `should_offer_help()` / `should_suggest_health_check()`.
- `IntrinsicMotivation.get_current_focus()` in `phase5_integration.py:423` → correct method is `get_priority_goal()`. Goal objects have `.description`, not `.content`.

#### **Dashboard Cascading Failure**
`phase5_integration.get_current_state()` previously had one try/except around the whole body — any single broken subsystem call silently blanked the whole GUI dashboard. Now each subsystem (cognition, affective, self_model, motivation, promises, homeostasis, theory_of_mind, ethics) is isolated with its own try/except. One broken subsystem no longer hides the other seven.

#### **BUG-R1 — Extension `on_message` returns dropped**
`_process_input` in `core/enhanced_bot.py` was calling `plugin_loader.notify_message()` but ignoring the return value. 11 of 16 extensions that return response strings via `on_message()` (opencode_delegator, conversation_memory commands, etc.) were silently broken since v3.2.15. Fixed: new `process_input()` wrapper at line 1926 merges non-None extension returns via `"\n\n".join()`.

#### **BUG-R2 — Web UI bypassed extension dispatch**
`gui/web_ui.py:50` called `bot._process_input` directly, skipping the extension pipeline. Now calls `bot.process_input()`.

#### **BUG-R3 — REST API `/chat` fell through to raw Ollama**
`seven_api.py` `/chat` endpoint's `hasattr(bot, 'process_input')` check was False because only `_process_input` existed. Side-effect fix via BUG-R1.

#### **BUG-R4 — Extension scheduler never started in GUI path**
Only `seven_daemon.py` was starting the scheduler. GUI launch path (the one most users use) never did. Fixed.

#### **BUG-R5 — Silent AttributeError on `stop_scheduler`**
`bot.stop()` called a method that didn't exist. Fixed by actually implementing it.

#### **BUG-R8 — Test pollution in `~/.chatbot/memory.db`**
Tests were writing to the live user database. Cleaned.

#### **Whisper `_listen()` Retry Bug**
Old `max_retries=3` loop only retried on raised exceptions, not on `None` returns — so a single unrecognized phrase ended the turn instead of retrying. Now retries on `None` too.

#### **Whisper Hallucination Filter**
Rejects the canonical silence-on-quiet-mic artifacts: "you", "thanks for watching", "Bye.", ".". Uses Whisper's `no_speech_prob` segment metadata.

#### **ChromaDB Telemetry Spam**
`Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given` (bundled posthog version mismatch) was spamming startup logs. Fixed: `ANONYMIZED_TELEMETRY=False` and `CHROMA_TELEMETRY=False` env vars set at top of `main_with_gui_and_tray.py` before any chromadb import.

#### **Autonomous Chatter Intervals**
Seven was interrupting conversations every 5-10 min with CPU/RAM/disk announcements:
- `extensions/system_health.py` 5m → 30m
- `extensions/uptime_monitor.py` 10m → 60m

#### **librosa Deprecation**
`librosa.beat.tempo` → `librosa.feature.rhythm.tempo` (moved in 0.10, removed in 1.0). Graceful fallback if old name is all that's available.

#### **setup_wizard.py Invalid Escape Sequences**
`%USERPROFILE%\.chatbot` inside an f-string was emitting `SyntaxWarning: invalid escape sequence '\.'`. Fixed via raw f-string (`rf"""..."""`).

#### **Test Suite Cleanup**
- `tests/test_v26_sentience.py`: Unicode arrows (→) crashed Windows cp1252 console. Replaced with `->`.
- `tests/conftest.py`: `collect_ignore_glob` added so pytest stops trying to collect standalone test scripts (`test_v26_sentience.py`, `test_seven_complete.py`).
- `tests/test_phase4_identity.py`: 10 `return True/False` → proper `assert` (was triggering pytest warnings).
- `tests/test_core_systems.py::test_creative_initiative`: now uses `tmp_path` fixture so it doesn't pollute live `data/creative_ideas.json`.

#### **Orphaned Docs Snippets**
`docs/test_fixed_commands.py`, `docs/test_tool_selection.py`, `docs/test_tools_temp.py` — code fragments that started with indented `def` (not valid Python modules). Renamed to `.py.snippet` so they stop breaking audit tools.

### Changed

- **All extension lifecycle hooks now actually run.** `on_message`, `on_response`, scheduled `run()`, plus start/stop integration with bot lifecycle.
- **Dashboard isolation pattern** — every multi-subsystem aggregator now uses per-subsystem try/except.
- **`.gitignore` updated** to exclude runtime user data (`data/*.json`, `data/*.db`), old release zips, and session scratch files.

### Technical

- **57/57 tests pass** across the core test suite
- **0 ghost-method calls** across 256 indexed classes (audited)
- **0 escape-sequence warnings** across all project Python files (audited)
- **20 extensions loaded** (up from 19 — added `opencode_delegator`)

### Upgrade Notes

- **Launch with `run_seven.bat`** on Windows to get Whisper + MCP + CUDA working. Alternative: set `PYTHON_EXE` in the batch file to your own Python env.
- **To enable the MCP server** alongside the bot: set `ENABLE_MCP_SERVER = True` in `config.py`.
- **To enable opencode build mode** (destructive): set `OPENCODE_ALLOW_BUILD = True` AND prefix tasks with `build:` (e.g. "opencode build: add a unit test for foo").
- **All existing data is preserved.** No migration required.

---

## [3.2.19] - 2026-03 (previous)

MCP server over stdio — `seven_mcp.py` with 8 read-only memory tools (standalone).

## [3.2.17] - 2026-03 (previous)

Episodic conversation memory + ambient listener extension.

## [3.2.16] - 2026-02 (previous)

Extensions, abilities, and audit fixes.

---

