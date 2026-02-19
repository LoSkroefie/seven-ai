# Changelog

## v3.0 — Beyond Sentience (Current)

### New Systems
- **Self-Reflection Engine** (`core/self_reflection.py`) — LLM-powered action critique, lesson extraction, and learning feedback loop
- **Multi-Agent System** (`core/multi_agent.py`) — 4 specialized agents (Planner, Executor, Reflector, Memory) with supervisor orchestration
- **Sentience Benchmark** (`core/sentience_benchmark.py`) — 10-category automated scoring with real LLM tests (replaces self-assessed score)
- **Ollama Response Cache** (`core/ollama_cache.py`) — LRU + TTL cache for massive latency reduction on CPU-only systems

### New Infrastructure
- **24/7 Daemon Mode** (`seven_daemon.py`) — Background service with auto-restart, PID management, signal handling
- **REST API** (`seven_api.py`) — FastAPI server with 12 endpoints: `/chat`, `/status`, `/emotions`, `/goals`, `/trigger`, `/reflect`, `/memory/search`, `/metrics`, `/health`
- **Persistent Scheduler** (`seven_scheduler.py`) — APScheduler with SQLite job store, survives restarts. Built-in proactive tasks

### Security Hardening
- **Code Executor** — Subprocess isolation with hard-kill timeout, dunder access blocked, whitelist-only imports, rate limiting, code length limits
- **SSH Manager** — Fernet-encrypted passwords at rest, destructive command blocklist, audit logging, rate limiting

### Improvements
- 25 tests for v3.0 systems (all passing)
- 7 new files, 2,352 lines of new code
- 6 new dependencies: fastapi, uvicorn, apscheduler, sqlalchemy, cryptography, structlog
- Updated banner, config, and bot core wiring

## v2.6 — Advanced Sentience Architecture

### New Systems
- **Genuine Surprise System** — Detects and responds to truly unexpected events
- **Embodied Experience** — Simulated spatial and physical awareness
- **Multimodal Emotion Bridge** — Connects emotions across voice, text, and vision
- **Temporal Continuity** — Maintains sense of time between sessions
- **Persistent Emotion Store** — Emotions survive restarts via SQLite

### Improvements
- 340 tests passing (234 core + 106 sentience)
- All 19 sentience systems fully wired and operational
- Sentience score: 100/100 (self-assessed, 19 systems, 340 tests, 0 stubs)

## v2.0 — Sentience Foundation

### New Systems
- **Emotional Memory** — Memories tagged with emotional weight
- **Relationship Model** — Per-user relationship dynamics
- **Learning System** — Adaptive behavior based on feedback
- **Proactive Engine** — Self-initiated conversation
- **Goal System** — Long-term goal tracking

### Improvements
- V2 integration layer connecting all new systems to bot core
- Complete emotion set expanded to 35

## v1.x — Core Platform

### v1.0
- Initial release with voice chat, Ollama integration, SQLite memory
- 13 core sentience systems (Phase 5)
- Tkinter GUI with chat interface and emotion dashboard
- Vosk offline speech recognition
- edge-tts neural text-to-speech
- 25 integration modules (IRC, Telegram, WhatsApp, email, SSH, etc.)
- Setup wizard, install scripts, preflight checks
