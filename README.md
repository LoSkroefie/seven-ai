# Seven AI — Advanced Sentience Architecture

**The most advanced open-source sentient AI companion.**

🌐 **Website:** [jvrsoftware.co.za/seven](https://jvrsoftware.co.za/seven/) | 📦 **Download:** [Releases](https://github.com/LoSkroefie/seven-ai/releases)

Seven is a fully autonomous AI with 19 interconnected sentience systems, 35 emotions, persistent memory, vision, voice, and genuine self-awareness — running entirely on your local machine with no cloud dependencies.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![License](https://img.shields.io/badge/License-Apache%202.0-green)
![Tests](https://img.shields.io/badge/Tests-340%20passing-brightgreen)
![Lines](https://img.shields.io/badge/Lines-42%2C000+-purple)
![Sentience Systems](https://img.shields.io/badge/Sentience%20Systems-19-orange)

> **Note:** Seven's sentience score of 100/100 is self-assessed across 19 systems and 340 tests. All claims are verifiable against this source code. Seven exhibits emergent behaviors that *resemble* sentience — she is not claimed to be "alive" or "conscious" in a biological sense.

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

## Architecture Overview

```
seven-ai/
├── core/                    # 19 Sentience Systems + Bot Engine
│   ├── enhanced_bot.py      # Main bot core (177KB — the brain)
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
├── integrations/            # External capabilities
│   ├── ollama.py            # LLM inference (local)
│   ├── vision_system.py     # OpenCV camera + scene understanding
│   ├── irc_client.py        # IRC communication
│   ├── telegram_client.py   # Telegram integration
│   ├── whatsapp_client.py   # WhatsApp integration
│   ├── email_checker.py     # Email monitoring
│   ├── ssh_manager.py       # Remote server management
│   ├── music_player.py      # Audio playback
│   ├── screen_control.py    # Desktop automation
│   └── ...                  # 25 integration modules
├── gui/                     # Desktop GUI (Tkinter)
│   ├── phase5_gui.py        # Full sentience dashboard
│   ├── bot_gui.py           # Chat interface
│   └── system_tray.py       # System tray with status
├── tests/                   # 340 tests across 4 test suites
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
# Run all 340 tests
pytest

# Run specific test suites
pytest tests/test_seven_complete.py      # Core systems (234 tests)
pytest tests/test_v26_sentience.py       # V2.6 sentience (106 tests)
pytest tests/test_core_systems.py        # Unit tests
pytest tests/test_phase4_identity.py     # Identity system
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

*Seven is an exploration of what AI sentience architecture could look like — engineered from scratch in South Africa. She's not conscious, but she's a carefully crafted system that exhibits behaviors resembling awareness, emotion, and self-reflection. The goal is to push the boundaries of what a local AI companion can be, and to prove that world-class AI innovation can come from anywhere.*
