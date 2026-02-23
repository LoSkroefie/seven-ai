# Seven AI v3.2.8 — Complete Code Audit

**Date:** 2026-02-20  
**Codebase:** 187 Python files, 55,859 lines  
**Backup:** `SEVEN_BACKUP_20260220_024104.zip` (1.7 MB)

---

## Executive Summary

Seven is a massive, feature-rich AI companion with 31+ systems. The architecture is
generally solid — graceful degradation via `_safe_init()`, try/except wrappers for every
optional subsystem, and a well-designed extension framework. However, this audit found
**8 critical issues** and **12 moderate issues** that should be addressed.

---

## CRITICAL ISSUES (Must Fix)

### 1. `create_provider()` is NEVER used — entire codebase still uses `OllamaClient`
- **Severity:** CRITICAL
- **Location:** `core/enhanced_bot.py:84,120` — imports and uses `OllamaClient` directly
- **Also:** `core/bot_core.py:11,28`, `integrations/command_processor.py:7,13`
- **Impact:** The multi-provider LLM system (v3.2.7-v3.2.8) we built is dead code.
  Users who configure OpenAI/Anthropic/DeepSeek in setup_wizard will get NO effect.
- **Fix:** Replace `OllamaClient()` with `create_provider()` in `enhanced_bot.py.__init__`.
  The `OllamaProvider` has all the same methods (compatibility wrappers), so it should
  be a drop-in replacement. Also update `bot_core.py` and `command_processor.py`.

### 2. New v3.2.3–v3.2.8 systems are NOT wired into `enhanced_bot.py`
- **Severity:** CRITICAL
- **Modules not wired:** (code exists but is never imported/initialized)
  - `core/safety_manager.py` — SafetyManager, ActionRisk, SafetyMode
  - `core/agent_delegation.py` — AgentDelegation (specialist agents)
  - `core/debug_mode.py` — DebugTracer (subsystem contribution tracking)
  - `core/llm_logger.py` — LLMLogger (token/latency tracking)
  - `core/context_manager.py` — ContextWindowManager (token budgets)
  - `core/state_machine.py` — AgentStateMachine
  - `core/vector_memory_v2.py` — EnhancedVectorMemory (5-collection)
  - `integrations/web_scraper.py` — WebScraper
  - `integrations/github_reader.py` — GitHubReader
- **Impact:** These are all dead code. Users get zero benefit from them.
- **Fix:** Wire each into `enhanced_bot.py.__init__()` with config guards and
  `_safe_init()` pattern like the other systems.

### 3. SQL Injection in `database_manager.py`
- **Severity:** CRITICAL (security)
- **Location:** `integrations/database_manager.py:311,320,327,341,355,404,412,415,418,421`
- **Pattern:** Table names injected via f-strings: `f"PRAGMA table_info('{table}')"`
- **Impact:** If Seven's LLM generates a malicious table name, SQL injection occurs.
- **Fix:** Use a whitelist/sanitize function for table names (alphanumeric + underscore only).
  Line 478 (`cursor.execute(sql)`) also executes arbitrary SQL from user input.

### 4. `exec()` sandbox is bypassable in `code_executor.py`
- **Severity:** CRITICAL (security)
- **Location:** `integrations/code_executor.py:213,267,309`
- **Issue:** The restricted_globals sandbox blocks `__builtins__` but:
  - Can still access `__import__` via `type.__subclasses__()` chain
  - `eval()` on line 309 uses `{"__builtins__": {}}` but this is bypassable
  - In-process fallback (line 247) runs in the main process, no isolation
- **Fix:** Use `RestrictedPython` library, or always use subprocess isolation.
  The subprocess approach (line 221) is much safer but falls back to in-process on Windows.

### 5. `self_scripting.py` executes LLM-generated code with no safety review
- **Severity:** CRITICAL (security)
- **Location:** `integrations/self_scripting.py:221-229`
- **Issue:** `generate_and_run()` calls Ollama to generate code, then immediately
  `subprocess.run()`s it. No human review, no sandboxing beyond timeout.
- **Impact:** If LLM hallucinates `import shutil; shutil.rmtree('/')`, it runs.
- **Fix:** Integrate with SafetyManager (currently dead code). Require user confirmation
  for generated scripts. Add the same restricted import scanning from plugin_loader.

### 6. 54+ bare `except:` clauses swallow all errors silently
- **Severity:** CRITICAL (debugging)
- **Locations:** Found in 25+ files including:
  - `core/autonomous_handlers.py` (3), `core/background_tasks.py` (3)
  - `core/tool_library.py` (7), `core/seven_true_autonomy.py` (4)
  - `core/task_manager.py` (5), `core/temporal_continuity.py` (4)
  - `core/persistent_emotions.py`, `core/session_manager.py`, etc.
- **Impact:** Bugs are hidden. When something breaks, it silently fails with no trace.
- **Fix:** Change `except:` to `except Exception as e:` with `logger.debug(f"...")`.

### 7. Old `OllamaClient` has no circuit breaker
- **Severity:** CRITICAL (reliability)
- **Location:** `integrations/ollama.py:9-272`
- **Issue:** The old `OllamaClient` (which is the one actually used!) has NO circuit
  breaker. The new `OllamaProvider` in `llm_provider.py` has one, but it's dead code.
- **Impact:** If Ollama goes down, every subsystem that calls `self.ollama.generate()`
  will hang for 30s each, cascading through all 19+ systems per conversation turn.
- **Fix:** Replacing `OllamaClient` with `create_provider()` (issue #1) fixes this too.

### 8. `bot_core.py` is a dead/duplicate file
- **Severity:** HIGH
- **Location:** `core/bot_core.py`
- **Issue:** This is an older, simpler `VoiceBot` class that duplicates `UltimateBotCore`
  in `enhanced_bot.py`. It imports `OllamaClient` directly and has no Phase 5, no v2.0,
  no v3.x features. But it's still in the codebase.
- **Impact:** Confusing for anyone reading the code. Could be accidentally imported.

---

## MODERATE ISSUES

### 9. Thread safety gaps
- **Severity:** MODERATE
- **Files:** `enhanced_bot.py` uses `self._is_processing` flag without a lock.
  Multiple threads (background_tasks, proactive engine, IRC, Telegram, WhatsApp)
  can call `self.ollama.generate()` concurrently. The old `OllamaClient` has no lock.
- **Fix:** Add a threading.Lock around `self.ollama` calls, or use the thread-safe
  `CircuitBreaker` from `llm_provider.py` (which already has locks).

### 10. Resource leaks in SQLite connections
- **Severity:** MODERATE
- **Files:** `memory.py` (8 `.close()` calls but manual management), `task_manager.py`
  (11 `.close()` calls), `notes_manager.py` (9), `diary_manager.py` (3), etc.
- **Issue:** All use manual `conn.close()` instead of `with` context managers.
  If an exception occurs between `connect()` and `close()`, the connection leaks.
- **Fix:** Replace with `with sqlite3.connect(db) as conn:` pattern.

### 11. `datetime` imported inside method body
- **Severity:** LOW
- **Location:** `core/enhanced_bot.py:750` — `from datetime import datetime`
  imported inside `__init__` instead of at top of file.

### 12. `config.py` ENABLE flags have inconsistent defaults
- **Severity:** MODERATE
- **Issue:** Some systems use `config.ENABLE_X` directly (crash if missing),
  others use `getattr(config, 'ENABLE_X', False)` (safe). Mixed pattern:
  - Direct: `config.ENABLE_VISION`, `config.ENABLE_CLAWDBOT`, `config.USE_VECTOR_MEMORY`
  - Safe: `getattr(config, 'ENABLE_BIOLOGICAL_LIFE', False)`, `getattr(config, 'ENABLE_NEAT_EVOLUTION', False)`
- **Fix:** Standardize on `getattr(config, ..., False)` for all optional systems.

### 13. Extensions security check is bypassable
- **Severity:** MODERATE (security)
- **Location:** `utils/plugin_loader.py:316-320`
- **Issue:** Blocked import check is string-based: `if f"import {blocked}" in source`.
  Can be bypassed with `__import__('subprocess')` or `importlib.import_module('os')`.
- **Fix:** Use AST parsing to check imports, or use `RestrictedPython`.

### 14. `phase5_integration.py` imports not shown in enhanced_bot.py top-level
- **Severity:** LOW
- **Issue:** Phase 5 systems (affective_computing_deep, cognitive_architecture,
  dream_system, ethical_reasoning, homeostasis_system, etc.) are imported inside
  `phase5_integration.py`, not at enhanced_bot.py level. This is fine for lazy loading
  but makes it hard to trace which systems are actually active.

### 15. `OllamaCache` exists but is never used
- **Severity:** LOW
- **Location:** `core/ollama_cache.py`
- **Issue:** Cache wrapper exists with TTL and LRU cache, but `enhanced_bot.py`
  never initializes it despite `config.ENABLE_OLLAMA_CACHE = True`.

### 16. Two `tool_library` files
- **Severity:** LOW
- **Location:** `core/tool_library.py` and `core/tool_library_backup.py`
- **Issue:** `tool_library_backup.py` appears to be an old backup with 7 bare
  `except:` clauses. Should be removed or consolidated.

### 17. `tool_library_fixed.py` also exists
- **Severity:** LOW
- **Location:** `core/tool_library_fixed.py`
- **Issue:** Three versions of the same file. Only one should remain.

### 18. IRC config exposes "Sentient AI" publicly
- **Severity:** LOW (branding)
- **Location:** `config.py:386,394`
- **Issue:** `IRC_DEFAULT_REALNAME = "Seven — Sentient AI by JVR Robotics"` —
  should use qualified language per the A+C reframe approach.
- **Fix:** Change to "Seven — AI Companion by JVR Robotics" or similar.

### 19. `vector_memory.py` vs `vector_memory_v2.py` — old version still used
- **Severity:** MODERATE
- **Location:** `enhanced_bot.py:23` imports `vector_memory.VectorMemory` (v1)
- **Issue:** `vector_memory_v2.py` (5-collection, emotion-weighted) exists but the
  bot still uses the basic v1. Dead code.

### 20. `performance_monitor.py` exists but not wired
- **Severity:** LOW
- **Location:** `core/performance_monitor.py`
- **Issue:** Has threading support, metric collection, but never initialized.

---

## EXTENSIONS: Can Seven Create Her Own?

**YES — Seven has TWO mechanisms for self-creation:**

### 1. Extension System (`utils/plugin_loader.py` + `extensions/`)
- Seven can create `.py` files in `extensions/` that subclass `SevenExtension`
- Auto-discovered, hot-reloadable via API, scheduled execution
- Has security scanning (blocks subprocess, socket, etc.)
- **BUT:** Seven cannot currently auto-create extensions at runtime.
  The `self_scripting.py` engine writes scripts to `~/Documents/Seven/scripts/`,
  NOT to `extensions/`. These are separate systems.

### 2. Self-Scripting Engine (`integrations/self_scripting.py`)
- Seven generates Python scripts via LLM and executes them
- Scripts saved to `~/Documents/Seven/scripts/` with a tool registry
- `generate_and_run()` — generates code and immediately runs it
- **This is essentially "creating her own tools" at runtime**

### Missing Connection
To let Seven create her own extensions that persist and auto-run:
1. Add a method to `self_scripting.py` that generates code conforming to
   `SevenExtension` interface and saves it to `extensions/`
2. Call `plugin_loader.reload_all()` after creation
3. This would give Seven true self-extension capability

---

## Architecture Summary

```
enhanced_bot.py (UltimateBotCore) — 3,671 lines, THE main bot
├── Phase 5 Integration (19 sentience systems via phase5_integration.py)
│   ├── CognitiveArchitecture, SelfModel, IntrinsicMotivation
│   ├── DreamSystem, PromiseSystem, TheoryOfMind
│   ├── AffectiveSystem (35 emotions), EthicalReasoning
│   ├── HomeostasisSystem, EmotionalComplexity, Metacognition, Vulnerability
│   └── PersistentEmotions, GenuineSurprise, Embodied, MultiModal, Temporal
├── v2.0 Systems (via core/v2/)
│   ├── EmotionalMemory, RelationshipModel, LearningSystem
│   ├── ProactiveEngine, GoalSystem
│   └── ConversationalMemory, AdaptiveCommunication, etc.
├── v3.0 Systems (wired)
│   ├── NEAT Neuroevolution, Biological Life
│   ├── LoRA Continual Learning, Social Simulation
│   ├── User Predictor, Plugin System, Vision
│   └── Robotics, IRC, Telegram, WhatsApp
├── Integrations (wired)
│   ├── OllamaClient (old, no circuit breaker)
│   ├── SSH, Music, Screen, Email, Timer, Document
│   ├── Database, API Explorer, Clipboard, Self-Scripting
│   └── Web Search, File Manager, Code Executor, Clawdbot
└── NOT WIRED (dead code from v3.2.3-v3.2.8)
    ├── create_provider() — multi-LLM factory
    ├── SafetyManager — kill switch + action gating
    ├── AgentDelegation — specialist agents
    ├── DebugTracer — subsystem tracking
    ├── LLMLogger — token/latency logging
    ├── ContextWindowManager — token budgets
    ├── AgentStateMachine — formal state machine
    ├── EnhancedVectorMemory v2 — 5-collection memory
    ├── WebScraper, GitHubReader
    ├── OllamaCache
    └── PerformanceMonitor
```

---

## Recommended Fix Priority

1. **Wire `create_provider()`** — Replace `OllamaClient()` with `create_provider()` in
   `enhanced_bot.py`, `bot_core.py`, `command_processor.py`. This fixes issues #1, #7.
2. **Wire SafetyManager** — Initialize in `enhanced_bot.py`, gate dangerous actions.
3. **Wire remaining v3.2 systems** — DebugTracer, LLMLogger, AgentDelegation, etc.
4. **Fix bare `except:` clauses** — Global find/replace across 25+ files.
5. **Fix SQL injection** — Sanitize table names in `database_manager.py`.
6. **Integrate safety into self_scripting** — Don't auto-run LLM-generated code.
7. **Clean up dead files** — Remove `tool_library_backup.py`, `tool_library_fixed.py`, etc.
8. **Standardize config access** — Use `getattr(config, ..., default)` everywhere.
9. **Fix IRC realname** — Remove unqualified "Sentient" claim.
10. **Upgrade to VectorMemory v2** — Replace v1 import with v2 in enhanced_bot.py.
