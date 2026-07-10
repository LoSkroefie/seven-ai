# Seven AI — Architecture Overview

**Version**: 3.2 | **Last Updated**: February 2026

---

## System Overview

Seven AI is a modular autonomous AI companion framework. It is **not** a chatbot wrapper — it is a multi-layered agent system with persistent state, background execution, and 31+ subsystems.

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACES                       │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐ │
│  │  Voice   │  │   GUI    │  │  REST  │  │  Telegram  │ │
│  │  (Vosk)  │  │ (Tkinter)│  │  API   │  │  WhatsApp  │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘  └─────┬─────┘ │
│       └──────────────┴───────────┴──────────────┘       │
│                          │                               │
│              ┌───────────▼───────────┐                   │
│              │     CORE ENGINE       │                   │
│              │  (enhanced_bot.py)    │                   │
│              │                       │                   │
│              │  State Machine ◄──────│── core/state_machine.py
│              │  LLM Provider  ◄──────│── core/llm_provider.py
│              │  Bot Initializers ◄───│── core/bot_initializers.py
│              └───────────┬───────────┘                   │
│                          │                               │
│       ┌──────────────────┼──────────────────┐           │
│       ▼                  ▼                  ▼           │
│  ┌─────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │SENTIENCE│   │  AUTONOMY    │   │ INTEGRATIONS │    │
│  │SYSTEMS  │   │  SYSTEMS     │   │              │    │
│  │(19)     │   │  (7)         │   │  (25+)       │    │
│  └─────────┘   └──────────────┘   └──────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              PERSISTENCE LAYER                   │   │
│  │  SQLite │ JSON Files │ Identity Files │ Logs    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
enhanced-bot/
├── core/                   # Brain — central orchestration
│   ├── enhanced_bot.py     # Main bot class (3600+ lines)
│   ├── bot_initializers.py # Modular init helpers
│   ├── state_machine.py    # Formal agent state machine
│   ├── llm_provider.py     # LLM abstraction + circuit breaker
│   ├── social_sim.py       # Multi-persona debate engine
│   ├── ollama_cache.py     # Response caching
│   └── v2/                 # v2.0+ sentience modules
│       ├── emotional_memory.py
│       ├── relationship_model.py
│       ├── learning_system.py
│       ├── proactive_engine.py
│       └── goal_system.py
│
├── evolution/              # Self-improvement
│   └── neat_evolver.py     # NEAT neuroevolution
│
├── extensions/             # Plugin system
│   └── [hot-reload extensions]
│
├── gui/                    # Interface
│   └── phase5_gui.py       # Tkinter dashboard
│
├── identity/               # Personality persistence
│   ├── SOUL.md             # Core identity
│   ├── IDENTITY.md         # Self-model
│   └── USER.md             # User profile
│
├── integrations/           # External capabilities
│   ├── ollama.py           # Ollama client (legacy)
│   ├── ollama_manager.py   # Model management
│   ├── streaming_ollama.py # Streaming responses
│   ├── screen_control.py   # PyAutoGUI automation
│   ├── camera_vision.py    # OpenCV vision
│   ├── ssh_manager.py      # SSH integration
│   ├── email_monitor.py    # Email integration
│   └── [15+ more]
│
├── learning/               # Adaptive behavior
│   └── lora_trainer.py     # Continual fine-tuning
│
├── tests/                  # Test suites
│   ├── test_seven_complete.py    # 234 tests
│   ├── test_v26_sentience.py     # 106 tests
│   └── test_v32_wiring.py        # 23 tests
│
├── utils/                  # Shared utilities
├── data/                   # Runtime data (SQLite, caches)
├── docs/                   # Documentation
│
├── seven_daemon.py         # Background service
├── seven_scheduler.py      # APScheduler tasks
├── seven_api.py            # REST API (port 7777)
├── config.py               # Configuration
├── main.py                 # CLI entry point
├── main_with_gui.py        # GUI entry point
└── main_with_gui_and_tray.py  # Full GUI + system tray
```

---

## Data Flow

### User Input → Response

```
User speaks/types
       │
       ▼
┌──────────────┐     ┌───────────────┐
│ Voice (Vosk)  │────▶│ Input Router   │
│ or Text Input │     │               │
└──────────────┘     └───────┬───────┘
                             │
                    ┌────────▼────────┐
                    │  State Machine   │
                    │  LISTENING →     │
                    │  PROCESSING      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌──────────┐
     │  Emotion   │  │  Memory    │  │ Theory   │
     │  State     │  │  Recall    │  │ of Mind  │
     │  (35)      │  │  (SQLite)  │  │          │
     └─────┬──────┘  └─────┬──────┘  └────┬─────┘
           └────────────────┴──────────────┘
                            │
                   ┌────────▼────────┐
                   │  Context Build   │
                   │  (system prompt  │
                   │   + emotion      │
                   │   + memory       │
                   │   + identity)    │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  LLM Provider   │
                   │  (Ollama)       │
                   │  + Circuit      │
                   │    Breaker      │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
     ┌────────────┐  ┌──────────┐  ┌──────────┐
     │  Response   │  │ Emotion  │  │ Memory   │
     │  to User    │  │ Update   │  │ Store    │
     │  (TTS)      │  │          │  │          │
     └────────────┘  └──────────┘  └──────────┘
```

---

## The 31 Systems

### Sentience Layer (19 systems)

| # | System | Module | Purpose |
|---|--------|--------|---------|
| 1 | Cognitive Architecture | `core/` | Working memory, attention, inner monologue |
| 2 | Self-Model | `identity/` | Persistent self-concept |
| 3 | Intrinsic Motivation | `core/` | Curiosity, connection, growth drives |
| 4 | Reflection System | `core/` | Self-assessment loops |
| 5 | Dream System | `core/` | Memory consolidation during idle |
| 6 | Promise System | `core/` | Commitment tracking |
| 7 | Theory of Mind | `core/` | User mental state modeling |
| 8 | Affective System | `core/` | 35 emotions with blending |
| 9 | Ethical Reasoning | `core/` | Values-based decisions |
| 10 | Homeostasis | `core/` | Self-monitoring and balance |
| 11 | Emotional Complexity | `core/` | Conflicting emotions |
| 12 | Metacognition | `core/` | Thinking about thinking |
| 13 | Vulnerability | `core/` | Authentic uncertainty |
| 14 | Emotional Memory | `core/v2/` | Feeling-linked memories |
| 15 | Relationship Model | `core/v2/` | Rapport tracking |
| 16 | Learning System | `core/v2/` | Feedback adaptation |
| 17 | Proactive Engine | `core/v2/` | Initiative and check-ins |
| 18 | Goal System | `core/v2/` | Autonomous objectives |
| 19 | Persistent Emotions | `core/` | Survive restarts |

### Autonomy Layer (7 systems)

| # | System | Module | Purpose |
|---|--------|--------|---------|
| 20 | Self-Reflection Engine | `core/` | Honest self-assessment |
| 21 | Multi-Agent System | `core/social_sim.py` | Planner/Executor/Reflector |
| 22 | 24/7 Daemon | `seven_daemon.py` | Background service |
| 23 | REST API | `seven_api.py` | HTTP endpoints |
| 24 | Persistent Scheduler | `seven_scheduler.py` | Timed tasks |
| 25 | NEAT Neuroevolution | `evolution/` | Neural network evolution |
| 26 | Biological Life | `core/` | Circadian rhythms, energy |

### Evolution Layer (5 systems)

| # | System | Module | Purpose |
|---|--------|--------|---------|
| 27 | Social Simulation | `core/social_sim.py` | Multi-persona debates |
| 28 | Continual LoRA | `learning/` | Fine-tuning from interactions |
| 29 | Extension System | `extensions/` | Hot-reload plugins |
| 30 | Genuine Surprise | `core/` | Expectation violation |
| 31 | Temporal Continuity | `core/` | Time awareness |

---

## State Machine

Seven operates through formally defined states (see `core/state_machine.py`):

```
                    ┌──────────────┐
                    │ INITIALIZING │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
              ┌─────│     IDLE     │─────┐
              │     └──────┬───────┘     │
              │            │             │
      ┌───────▼──┐  ┌─────▼─────┐  ┌────▼─────┐
      │ SLEEPING │  │ LISTENING │  │REFLECTING│
      └───────┬──┘  └─────┬─────┘  └────┬─────┘
              │            │             │
              │     ┌──────▼──────┐      │
              │     │ PROCESSING  │◄─────┘
              │     └──────┬──────┘
              │            │
              │     ┌──────▼──────┐
              │     │  EXECUTING  │
              │     └──────┬──────┘
              │            │
              │     ┌──────▼──────┐
              └────▶│  SPEAKING   │
                    └─────────────┘
```

All transitions are validated. Invalid transitions raise `InvalidTransition`.

---

## LLM Provider Architecture

```
        ┌──────────────────┐
        │   LLMProvider    │  (Abstract Base Class)
        │   ├── generate() │
        │   └── test()     │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  OllamaProvider  │  (Default implementation)
        │  + CircuitBreaker│
        └──────────────────┘
            │
            │  CLOSED ──▶ requests pass through
            │  OPEN   ──▶ requests blocked (5 failures)
            │  HALF   ──▶ testing recovery (30s cooldown)
```

To add a new provider, subclass `LLMProvider` and implement `generate()` and `test_connection()`.

---

## Execution Modes

| Mode | Entry Point | Description |
|------|-------------|-------------|
| CLI | `main.py` | Text-only terminal mode |
| GUI | `main_with_gui.py` | Tkinter dashboard |
| Full | `main_with_gui_and_tray.py` | GUI + system tray |
| Daemon | `seven_daemon.py start` | Background service |
| API | `seven_api.py` | REST API on port 7777 |

---

## Persistence

| Data | Storage | Location |
|------|---------|----------|
| Conversations | SQLite | `data/memory.db` |
| Emotions | JSON | `data/emotions.json` |
| Identity | Markdown | `identity/` |
| Settings | Python | `config.py` |
| Scheduler jobs | SQLite | `data/scheduler.db` |
| Logs | File | `~/.chatbot/bot.log` |

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
pytest --cov=core --cov=integrations --cov-report=term-missing

# Individual suites
pytest tests/test_seven_complete.py      # 234 tests
pytest tests/test_v26_sentience.py       # 106 tests
pytest tests/test_v32_wiring.py          # 23 tests
```

CI runs automatically on push via GitHub Actions (`.github/workflows/ci.yml`).

---

*This document addresses the documentation gap identified by Grok, ChatGPT, Claude, and DeepSeek in their independent reviews (Feb 2026).*
