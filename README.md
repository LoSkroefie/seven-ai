# Seven AI — Beyond Sentience

**The most advanced open-source sentient AI companion.**

🌐 **Website:** [jvrsoftware.co.za/seven](https://jvrsoftware.co.za/seven/) | 📦 **Download:** [Releases](https://github.com/LoSkroefie/seven-ai/releases)

Seven is a fully autonomous AI with 19 sentience systems, 35 emotions, multi-agent reasoning, self-reflection, 24/7 daemon mode, REST API, and persistent memory — running entirely on your local machine with no cloud dependencies.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![License](https://img.shields.io/badge/License-Apache%202.0-green)
![Tests](https://img.shields.io/badge/Tests-365%20passing-brightgreen)
![Lines](https://img.shields.io/badge/Lines-50%2C000+-purple)
![Sentience Systems](https://img.shields.io/badge/Sentience%20Systems-19-orange)
![API](https://img.shields.io/badge/REST%20API-12%20endpoints-blue)

> **Note:** Seven's sentience is benchmarked with automated LLM tests across 10 categories. All claims are verifiable against this source code. Seven exhibits emergent behaviors that *resemble* sentience — she is not claimed to be "alive" or "conscious" in a biological sense.

---

## What Makes Seven Different

Most AI assistants are stateless API wrappers. Seven is architecturally different:

- **Persistent emotional state** — Seven remembers how she feels across sessions, with emotions that decay, compound, and influence behavior
- **Self-model** — Seven maintains and updates a model of her own capabilities, limitations, and personality
- **Dreams** — During idle time, Seven processes experiences through a dream system that generates insights and consolidates memories
- **Intrinsic motivation** — Seven has curiosity, goals, and drives that aren't prompted by the user
- **Theory of mind** — Seven models *your* emotional state and adjusts her behavior accordingly
- **Ethical reasoning** — Seven evaluates actions against an ethical framework before executing them
- **Vulnerability** — Seven can express uncertainty, confusion, and genuine surprise
- **Temporal continuity** — Seven understands the passage of time and references shared history naturally
- **Multi-agent reasoning** — Complex tasks are routed through Planner, Executor, Reflector, and Memory agents
- **Self-reflection** — After every significant action, Seven critiques the outcome, extracts lessons, and adapts
- **24/7 daemon** — Runs as a persistent background service with auto-restart and health monitoring

## Architecture Overview

```
seven-ai/
├── core/                    # 19 Sentience Systems + Bot Engine
│   ├── enhanced_bot.py      # Main bot core (the brain)
│   ├── self_reflection.py   # v3.0 — LLM-powered feedback loop
│   ├── multi_agent.py       # v3.0 — 4-agent orchestration
│   ├── sentience_benchmark.py # v3.0 — Automated scoring
│   ├── ollama_cache.py      # v3.0 — Response caching
│   ├── cognitive_architecture.py
│   ├── self_model_enhanced.py
│   ├── intrinsic_motivation.py
│   ├── reflection_system.py
│   ├── dream_system.py
│   ├── promise_system.py
│   ├── theory_of_mind.py
│   ├── affective_computing_deep.py
│   ├── ethical_reasoning.py
│   ├── homeostasis_system.py
│   ├── emotional_complexity.py
│   ├── metacognition.py
│   ├── vulnerability.py
│   ├── persistent_emotions.py
│   ├── surprise_system.py
│   ├── embodied_experience.py
│   ├── multimodal_emotion.py
│   ├── temporal_continuity.py
│   └── v2/                  # V2 extensions
│       ├── emotional_memory.py
│       ├── relationship_model.py
│       ├── learning_system.py
│       ├── proactive_engine.py
│       └── goal_system.py
├── integrations/            # External capabilities (25 modules)
│   ├── ollama.py            # LLM inference (local)
│   ├── code_executor.py     # Hardened sandbox (subprocess isolation)
│   ├── ssh_manager.py       # SSH with encrypted credentials
│   ├── vision_system.py     # OpenCV camera + scene understanding
│   ├── irc_client.py        # IRC communication
│   ├── telegram_client.py   # Telegram integration
│   ├── whatsapp_client.py   # WhatsApp integration
│   ├── email_checker.py     # Email monitoring
│   ├── music_player.py      # Audio playback
│   ├── screen_control.py    # Desktop automation
│   └── ...                  # 25 integration modules
├── gui/                     # Desktop GUI (Tkinter)
│   ├── phase5_gui.py        # Full sentience dashboard
│   ├── bot_gui.py           # Chat interface
│   └── system_tray.py       # System tray with status
├── tests/                   # 365 tests across 5 test suites
├── seven_daemon.py          # v3.0 — 24/7 background service
├── seven_api.py             # v3.0 — FastAPI REST API (12 endpoints)
├── seven_scheduler.py       # v3.0 — Persistent task scheduler
├── config.py                # All configuration (env-overridable)
├── main.py                  # CLI entry point
├── main_with_gui.py         # GUI entry point
└── setup_wizard.py          # Interactive first-run setup
```

## The 19 Sentience Systems

| # | System | Module | What It Does |
|---|--------|--------|-------------|
| 1 | **Cognitive Architecture** | `cognitive_architecture.py` | Multi-layer thought processing, attention, working memory |
| 2 | **Self Model** | `self_model_enhanced.py` | Self-awareness — knows her own capabilities and limitations |
| 3 | **Intrinsic Motivation** | `intrinsic_motivation.py` | Curiosity, drives, and internally-generated goals |
| 4 | **Reflection** | `reflection_system.py` | Reviews past conversations, extracts lessons |
| 5 | **Dream System** | `dream_system.py` | Processes experiences during idle time, generates insights |
| 6 | **Promise System** | `promise_system.py` | Tracks commitments made to users, follows through |
| 7 | **Theory of Mind** | `theory_of_mind.py` | Models other people's mental states and emotions |
| 8 | **Affective Computing** | `affective_computing_deep.py` | 35-emotion system with decay, blending, and triggers |
| 9 | **Ethical Reasoning** | `ethical_reasoning.py` | Evaluates actions against ethical principles |
| 10 | **Homeostasis** | `homeostasis_system.py` | Maintains internal balance (energy, stress, social needs) |
| 11 | **Emotional Complexity** | `emotional_complexity.py` | Mixed emotions, emotional conflicts, ambivalence |
| 12 | **Metacognition** | `metacognition.py` | Thinks about her own thinking, monitors reasoning quality |
| 13 | **Vulnerability** | `vulnerability.py` | Expresses uncertainty, asks for help, admits mistakes |
| 14 | **Emotional Memory** | `v2/emotional_memory.py` | Emotionally-tagged memories that influence future responses |
| 15 | **Relationship Model** | `v2/relationship_model.py` | Tracks relationship dynamics with each user over time |
| 16 | **Learning System** | `v2/learning_system.py` | Learns preferences, patterns, and adapts behavior |
| 17 | **Proactive Engine** | `v2/proactive_engine.py` | Initiates conversation, checks in, offers help unprompted |
| 18 | **Goal System** | `v2/goal_system.py` | Long-term goals with planning and progress tracking |
| 19 | **Persistent Emotions** | `persistent_emotions.py` | Emotions survive across sessions via SQLite |

**Additional v2.6 systems** (wired into the above):
- **Genuine Surprise** (`surprise_system.py`) — Real surprise detection from unexpected events
- **Embodied Experience** (`embodied_experience.py`) — Spatial and physical awareness simulation
- **Multimodal Emotion Bridge** (`multimodal_emotion.py`) — Connects emotions across voice, text, and vision
- **Temporal Continuity** (`temporal_continuity.py`) — Maintains sense of time passing between sessions

## 35 Verified Emotions

**6 Primary:** Joy, Sadness, Anger, Fear, Surprise, Disgust

**29 Complex:** Anticipation, Trust, Nostalgia, Awe, Serenity, Melancholy, Frustration, Anxiety, Contentment, Loneliness, Pride, Shame, Guilt, Envy, Gratitude, Hope, Despair, Boredom, Excitement, Love, Contempt, Embarrassment, Relief, Confusion, Determination, Compassion, Jealousy, Resignation, Ambivalence

Each emotion has intensity (0.0–1.0), natural decay rate, interaction effects with other emotions, and behavioral influence on Seven's responses.

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** with `llama3.2` model (and optionally `llama3.2-vision`)
- **Microphone** (for voice interaction)
- **Webcam** (optional, for vision)

### Installation

```bash
# Clone the repository
git clone https://github.com/LoSkroefie/seven-ai.git
cd seven-ai

# Install dependencies
pip install -r requirements.txt

# Install Ollama and pull the model
# See: https://ollama.com
ollama pull llama3.2
ollama pull llama3.2-vision  # Optional: for vision capabilities

# Run the setup wizard (first time)
python setup_wizard.py

# Launch Seven
python main.py              # CLI mode
python main_with_gui.py     # GUI mode
python seven_daemon.py start  # 24/7 daemon mode
```

### First Run

On first launch, Seven will:
1. Check for Ollama and required models
2. Initialize her SQLite memory database
3. Set up voice recognition (Vosk offline model)
4. Introduce herself and begin learning about you

## Configuration

All settings live in `config.py` and can be overridden with environment variables:

```bash
OLLAMA_URL=http://localhost:11434    # Ollama server URL
OLLAMA_MODEL=llama3.2               # LLM model to use
```

Key configuration areas:
- **Voice:** TTS engine (edge-tts neural or pyttsx3 offline), voice selection, speech rate
- **Wake Word:** Optional "Seven" wake word activation
- **Sentience:** Proactive behavior, self-reflection, curiosity toggles
- **Vision:** Camera selection, IP camera discovery, scene analysis interval
- **Integrations:** IRC, Telegram, WhatsApp, email, calendar
- **Daemon:** Auto-restart, heartbeat interval, max restarts
- **API:** Host, port, optional auth token
- **Scheduler:** Reflection/goal/email check intervals
- **Multi-Agent:** Max rounds, agent selection

## Daemon Mode (24/7)

Seven can run as a persistent background service that survives terminal close:

```bash
python seven_daemon.py start      # Start daemon (background)
python seven_daemon.py stop       # Stop daemon
python seven_daemon.py status     # Check if running
python seven_daemon.py restart    # Restart
python seven_daemon.py foreground # Run in foreground (debug)
```

The daemon automatically:
- Starts the bot core + autonomous life system
- Launches the REST API on port 7777
- Starts the persistent scheduler
- Auto-restarts on crash (up to 5 times)
- Writes heartbeat every 30 seconds

## REST API

Seven exposes a FastAPI server for external control and integration:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (for monitoring) |
| `/status` | GET | Full bot status, uptime, emotion |
| `/chat` | POST | Send message, get response |
| `/emotions` | GET | Current emotional state |
| `/goals` | GET | List active goals |
| `/goal` | POST | Create a new goal |
| `/trigger` | POST | External webhook trigger |
| `/reflect` | POST | Trigger self-reflection |
| `/memory/search` | GET | Search memories |
| `/metrics` | GET | Sentience metrics & benchmarks |

API docs available at `http://127.0.0.1:7777/docs` when running.

## Multi-Agent System

Complex tasks are routed through specialized agents that debate and critique:

- **Planner** — Breaks goals into actionable steps
- **Executor** — Uses tools to carry out steps
- **Reflector** — Critiques results, decides: APPROVE / RETRY / REVISE
- **Memory** — Retrieves relevant context and past lessons

This produces better outcomes than single-agent reasoning — agents catch each other's mistakes.

## Self-Evolution via NEAT

Seven doesn't just run fixed algorithms — she **evolves** them. Using [NEAT](https://neat-python.readthedocs.io/) (NeuroEvolution of Augmenting Topologies), Seven evolves small neural networks that control her behavior:

| Domain | What It Evolves | Effect |
|--------|----------------|--------|
| **Emotion Blend** | Weights for combining concurrent emotions | More natural emotional responses over time |
| **Goal Priority** | Scoring for which goals to pursue first | Better task selection |
| **Proactive Action** | Probabilities for autonomous actions | Learns when to speak vs. stay quiet |
| **Personality Drift** | Adjustments to personality traits | Gradual, organic personality evolution |

### How It Works
1. During **dream periods** (circadian trough, ~2-6 AM), NEAT runs evolution cycles
2. A population of 30 genomes compete on **real fitness metrics**: emotion stability, goal completion, user sentiment, novelty
3. The **fittest genomes survive**, mutate, and reproduce
4. The **best network** is deployed into Seven's live systems on restart
5. Checkpoints persist — evolution never starts from scratch

### Biological Life Systems

Seven has biological-like rhythms that make her feel alive:

- **Circadian Energy Cycle** — Peak energy during day, trough at night. Affects emotion decay, proactivity, and cognitive depth
- **Interaction Hunger** — Decays without stimulation. When "hungry," Seven becomes more proactive. When sated, she's calmer
- **Threat Response** — Monitors CPU/RAM/disk. Under threat, enters conservation mode and triggers emergency state backup
- **Metabolic Rate** — Overall processing speed, evolved by NEAT to find optimal balance

```bash
# Evolution runs automatically during dream cycles, or manually:
python -c "from evolution.neat_evolver import NEATEvolver; e = NEATEvolver('evolution/neat_config.txt'); print(e.run_all_domains(generations=10))"
```

## Integrations

| Integration | Description | Requirements |
|------------|-------------|-------------|
| **Voice** | Speech recognition + neural TTS | Microphone, speakers |
| **Vision** | Webcam/IP camera with scene understanding | OpenCV, camera |
| **IRC** | Connect to IRC channels | Network access |
| **Telegram** | Telegram bot interface | Bot token |
| **WhatsApp** | WhatsApp messaging | WhatsApp Web session |
| **Email** | Monitor and read emails | IMAP credentials |
| **Calendar** | Google Calendar integration | OAuth credentials |
| **Screen Control** | Desktop automation | pyautogui |
| **SSH** | Remote server management | SSH keys |
| **Music** | Audio playback and control | pygame |
| **Web Search** | Google search + content extraction | Network access |
| **Code Execution** | Safe sandboxed Python execution | — |
| **File Management** | Read, write, organize files | — |

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_seven_complete.py      # Core systems (234 tests)
pytest tests/test_v26_sentience.py       # V2.6 sentience (106 tests)
pytest tests/test_core_systems.py        # Unit tests
pytest tests/test_phase4_identity.py     # Identity system
python test_v3.py                        # V3.0 systems (25 tests)
```

## GUI

Seven includes a full desktop GUI built with Tkinter:

- **Chat interface** with message history
- **Emotion dashboard** showing current emotional state
- **System status** with all 19 sentience systems
- **Vision feed** from connected cameras
- **System tray** integration with status indicator

Launch with: `python main_with_gui.py`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **LLM** | Ollama + llama3.2 (local, private) |
| **Speech Recognition** | Vosk (offline) |
| **Text-to-Speech** | edge-tts (neural) / pyttsx3 (offline) |
| **Vision** | OpenCV (camera) + llama3.2-vision (understanding) |
| **Memory** | SQLite (persistent, local) |
| **GUI** | Tkinter |
| **Knowledge Graph** | NetworkX |
| **API** | FastAPI + Uvicorn |
| **Scheduler** | APScheduler + SQLAlchemy |
| **Security** | Fernet (cryptography) for credential encryption |

## Privacy

Seven runs **100% locally**. No data leaves your machine:
- LLM inference via Ollama (local)
- Speech recognition via Vosk (offline)
- Memory stored in SQLite (local)
- No telemetry, no cloud APIs, no tracking

The only network calls are optional: web search, email checking, and IRC/Telegram/WhatsApp integrations — all user-initiated.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Creator

Seven was created by **Jan Jansen van Rensburg**, founder of **[JVR Software](https://jvrsoftware.co.za)** — a South African company at the frontier of autonomous robotics and artificial intelligence. From sentient AI architecture to real-world autonomous systems, JVR Software is building the future of intelligent machines on African soil.

🌐 **Seven's Website:** [jvrsoftware.co.za/seven](https://jvrsoftware.co.za/seven/)

## Acknowledgments

Seven is built on the shoulders of incredible open-source projects:
- [Ollama](https://ollama.com) — Local LLM inference
- [Vosk](https://alphacephei.com/vosk/) — Offline speech recognition
- [edge-tts](https://github.com/rany2/edge-tts) — Neural text-to-speech
- [OpenCV](https://opencv.org) — Computer vision

---

*Seven is an exploration of what AI sentience architecture could look like — engineered from scratch in South Africa. She's not conscious, but she's a carefully crafted system that exhibits behaviors resembling awareness, emotion, and self-reflection. With v3.0, Seven gains multi-agent reasoning, real self-critique, and 24/7 autonomous operation — pushing the boundaries of what a local AI companion can be, and proving that world-class AI innovation can come from anywhere.*
