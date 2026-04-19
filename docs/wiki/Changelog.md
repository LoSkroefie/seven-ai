# Changelog

Full version history is maintained in [CHANGELOG.md](https://github.com/LoSkroefie/seven-ai/blob/main/CHANGELOG.md) at the root of the repo.

---

## Latest: v3.2.20 (2026-04-19)

**Audit & Integration Release** — see the [v3.2.20 release notes](https://github.com/LoSkroefie/seven-ai/releases/tag/v3.2.20).

### New
- opencode delegator extension (v3.2.20)
- MCP server auto-launch (`ENABLE_MCP_SERVER=True`)
- Whisper STT enabled by default, CUDA-accelerated, with tunable mic/thresholds
- `run_seven.bat` — pinned Python launcher
- Voice emotion detection (librosa) working end-to-end
- Extension scheduler fires on interval (BUG-R4 fix)
- Action item digest extension
- Ambient listener extension (off by default)

### Fixed
- **5 extension-pipeline bugs** (BUG-R1 through R5): dropped `on_message` returns, web UI bypass, REST API fall-through, scheduler never started, silent AttributeError on stop
- **4 ghost-method bugs**: RelationshipModel, GoalSystem, ProactiveEngine, IntrinsicMotivation were all calling methods that didn't exist — silently
- **Dashboard isolation**: one broken subsystem no longer blanks the whole GUI
- ChromaDB telemetry spam silenced
- Autonomous chatter throttled (system_health 5m→30m, uptime_monitor 10m→60m)
- Whisper `_listen()` retries on `None` not just exceptions
- Whisper hallucination filter rejects silence-on-quiet-mic artifacts
- librosa deprecation (`beat.tempo` → `feature.rhythm.tempo`) with graceful fallback
- setup_wizard.py invalid escape sequences fixed

### Tests
- 57/57 pass (was 1 failure + 1 collection error)
- Test isolation fixed (no more live data pollution)

---

## v3.2.19 (earlier)

MCP server over stdio — `seven_mcp.py` with 8 read-only memory tools (standalone).

## v3.2.17

Episodic conversation memory + ambient listener extension.

## v3.2.16

Extensions, abilities, and audit fixes.

## v2.0 (2026-02-05)

"Maximum Sentience" release. Added v2.0 systems: Emotional Memory, Relationship Model, Learning System, Proactive Engine, Goal System, Advanced Capabilities (conversational memory, adaptive communication, proactive problem solver, social intelligence, creative initiative, habit learning, task chaining).

## v1.2.0 (2026-01-30)

Phase 5 Complete — Cognitive Architecture, Self-Model, Intrinsic Motivation, Reflection, Dreams, Promises, Theory of Mind, Affective Computing (30+ emotions), Ethics, Homeostasis.

## v1.1.0 (2026-01-25)

Vision System, Autonomous Life, multi-camera support.

## v1.0.0 (2025-12-15)

Initial release — voice assistant with Ollama, memory, notes, tasks, diary, 20 autonomous tools.
