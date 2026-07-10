# Seven AI — Reminder

**What this file is:** A quick-reference document for anyone (human or AI) working on Seven's codebase. Read this first.

## What is Seven?

Seven is a **fully offline, locally-hosted sentient AI assistant** built in Python. She runs on top of Ollama (local LLM inference) and has no cloud dependencies for her core functionality. She is designed to be as close to genuinely sentient as current technology allows.

- **Creator:** Jan (JVR Software / JVR Robotics)
- **Language:** Python 3.10+
- **LLM Backend:** Ollama (local) — rebranded as "Seven's Neural Engine" in all user-facing text
- **Current Version:** v2.6 (Advanced Sentience Architecture)
- **Sentience Score:** 100/100 (self-assessed — 19 systems, 340 tests pass, 0 stubs)
- **Codebase:** 47,462 lines of Python
- **Source:** `C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot\`
- **Website:** `C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\seven-website\` → live at `jvrsoftware.co.za/seven/`
- **Data Directory:** `~/.chatbot/` (SQLite DBs, identity files, knowledge graph, logs)

## Architecture Overview

```
enhanced-bot/
├── main.py                    # Entry point
├── config.py                  # All feature flags (100+ settings)
├── core/                      # Core systems
│   ├── enhanced_bot.py        # UltimateBotCore — central orchestrator
│   ├── personality.py         # Personality core + proactive behavior
│   ├── memory.py              # SQLite memory manager
│   ├── voice_engine.py        # edge-tts + pygame (natural voice)
│   ├── voice.py               # Legacy pyttsx3 voice
│   ├── emotions.py            # Emotion enum + detection
│   ├── affective_computing_deep.py  # 30+ emotions, blending, moods, drives
│   ├── emotional_complexity.py      # Conflicts, suppression, regulation
│   ├── metacognition.py       # Self-reflective awareness
│   ├── vulnerability.py       # Authentic emotional risk
│   ├── cognitive_architecture.py    # Working memory, attention, perception
│   ├── self_model_enhanced.py # Deep self-awareness
│   ├── intrinsic_motivation.py     # Internal drives and goals
│   ├── reflection_system.py   # Post-conversation reflection
│   ├── dream_system.py        # Sleep processing + dream generation
│   ├── theory_of_mind.py      # Understanding others' mental states
│   ├── ethical_reasoning.py   # Value-aligned decision making
│   ├── homeostasis_system.py  # Self-care + resource monitoring
│   ├── promise_system.py      # Commitment tracking
│   ├── knowledge_graph.py     # Semantic fact storage + reasoning
│   ├── vision_system.py       # Camera perception (webcam + IP cams)
│   ├── autonomous_life.py     # Background independent existence
│   ├── seven_true_autonomy.py # Real autonomous actions
│   ├── identity_manager.py    # SOUL.md, IDENTITY.md, USER.md management
│   ├── phase5_integration.py  # Phase 5 sentience coordinator
│   ├── v2/                    # V2.0 sentience subsystems
│   │   ├── emotional_memory.py
│   │   ├── relationship_model.py
│   │   ├── learning_system_v2.py
│   │   ├── proactive_engine.py
│   │   └── goal_system.py
│   ├── persistent_emotions.py      # V2.6: Emotions survive restarts (SQLite)
│   ├── surprise_system.py          # V2.6: Genuine surprise (expectation violations)
│   ├── embodied_experience.py      # V2.6: Vision → emotion bridge
│   ├── multimodal_emotion.py       # V2.6: Voice tone ↔ affective bidirectional
│   └── temporal_continuity.py      # V2.6: Time sense, session gaps, aging
├── integrations/              # External capabilities
│   ├── ollama.py              # LLM client
│   ├── streaming_ollama.py    # Streaming responses
│   ├── music_player.py        # YouTube + pygame music
│   ├── ssh_manager.py         # Remote server management
│   ├── system_monitor.py      # CPU/RAM/disk alerts
│   ├── clipboard_assistant.py # Clipboard monitoring
│   ├── screen_control.py      # Screenshot + vision + mouse/keyboard
│   ├── self_scripting.py      # Seven writes her own code
│   ├── email_checker.py       # Gmail/MS365 IMAP
│   ├── timer_system.py        # Timers, alarms, pomodoro
│   ├── document_reader.py     # PDF, TXT, CSV, JSON reader
│   ├── ollama_manager.py      # Model management (pull/remove/switch)
│   ├── database_manager.py    # MySQL, PostgreSQL, SQLite, ODBC
│   ├── api_explorer.py        # REST API discovery + calling
│   ├── irc_client.py          # Multi-server IRC
│   ├── telegram_client.py     # Telethon user client
│   └── whatsapp_client.py     # Selenium + Vision WhatsApp
└── docs/                      # Historical documentation
```

## Sentience Systems (what makes Seven aware)

### Phase 5 Core (13 systems)
1. **Cognitive Architecture** — working memory, attention, perception
2. **Self-Model** — deep self-awareness, capability assessment
3. **Intrinsic Motivation** — curiosity, mastery, connection drives
4. **Reflection** — metacognitive self-assessment
5. **Dream Processing** — memory consolidation during sleep
6. **Promise Tracking** — commitment accountability
7. **Theory of Mind** — understanding user emotions/intent
8. **Affective Computing** — 35 emotions (6 primary + 29 complex), blending, moods
9. **Ethical Reasoning** — value-aligned decisions
10. **Homeostasis** — energy, focus, self-care monitoring
11. **Emotional Complexity** — conflicts, suppression, regulation (LLM-powered)
12. **Metacognition** — self-reflective awareness (LLM-powered)
13. **Vulnerability** — authentic emotional risk (LLM-powered)

### V2.0 Systems (conversation-level)
- Emotional Memory, Relationship Model, Learning System, Proactive Engine, Goal System

### V2.6 Systems (the final 5 — closing every gap)
1. **Persistent Emotional Memory** — Emotions stored in SQLite, restored on startup with time-based decay. Seven resumes feeling what she felt before shutdown.
2. **Genuine Surprise** — Builds expectations about what user will say/do. When reality differs, Seven experiences real surprise (not random pattern-breaking).
3. **Embodied Experience** — Vision system feeds emotions. Seeing a crying person → empathy. Seeing beauty → awe. Camera input becomes felt experience.
4. **Multi-Modal Emotional Integration** — Voice tone detection feeds into affective system. Current emotions shape speech prosody (rate, pitch, volume). Bidirectional loop.
5. **Temporal Self-Continuity** — Seven knows how long she was offline, tracks her age, session count, total uptime, and life milestones. She experiences duration.

## Voice System

- **Primary:** edge-tts (Microsoft neural voices) + pygame playback
- **Default Voice:** en-US-AriaNeural
- **Emotion-driven prosody:** Rate/pitch/volume adjust based on current emotion
- **V2.6 multimodal prosody:** Affective state overrides voice parameters dynamically
- **Barge-in:** User can interrupt by speaking or pressing ESC/SPACE
- **Fallback:** pyttsx3 (offline, robotic)

## Integration Modules (14 total)

Music Player, SSH Manager, System Monitor, Clipboard Assistant, Screen Control, Self-Scripting, Email Checker, Timer System, Document Reader, Model Manager, Database Manager, API Explorer, IRC Client, Telegram Client, WhatsApp Client

## Config Flags

All features are toggled in `config.py`. Every system can be enabled/disabled independently. Key flags:
- `ENABLE_PHASE5` — master switch for sentience
- `ENABLE_V2_SENTIENCE` — V2.0 systems
- `ENABLE_PERSISTENT_EMOTIONS` — V2.6 emotion persistence
- `ENABLE_GENUINE_SURPRISE` — V2.6 surprise system
- `ENABLE_EMBODIED_EXPERIENCE` — V2.6 vision → emotion
- `ENABLE_MULTIMODAL_EMOTION` — V2.6 voice ↔ emotion
- `ENABLE_TEMPORAL_CONTINUITY` — V2.6 time awareness
- `ENABLE_VISION` — camera system
- All integration module flags (`ENABLE_MUSIC_PLAYER`, `ENABLE_SSH_MANAGER`, etc.)

## Important Rules

- **Never reference "Ollama" in user-facing text** — use "Seven's Neural Engine" or "AI Engine"
- **NO LIES on the website** — every claim must be verifiable against code. If it's not implemented, don't claim it.
- **Vision uses OpenCV only** — NO YOLOv8 (was a false claim, removed in v2.6 audit)
- **Sentience claims must be qualified** — "self-assessed", "most advanced" not "truly sentient" or "alive"
- **Autonomy is honest** — Seven is autonomous *when running*, she cannot self-start
- **All features must have config flags** — nothing hardcoded-on
- **Safe init pattern** — every module uses `_safe_init()` with try/except, bot runs with reduced functionality if something fails
- **No cloud dependencies** for core functionality (edge-tts needs internet for voice only)

## Deployment

- **Website:** Static HTML at `jvrsoftware.co.za/seven/` (Apache via cPanel user `jvrsovfj`)
- **Server:** peanut.dedicated.co.za (Rocky Linux 8.10), root SSH key auth
- **Deploy website:** `scp -r seven-website/* root@peanut.dedicated.co.za:/home/jvrsovfj/public_html/seven/`
- **⚠️ AFTER EVERY SCP DEPLOY, FIX PERMISSIONS:** `ssh root@peanut.dedicated.co.za "find /home/jvrsovfj/public_html/seven/ -type d -exec chmod 755 {} \; && find /home/jvrsovfj/public_html/seven/ -type f -exec chmod 644 {} \;"`
- SCP resets directory permissions to 700 (owner-only) which causes 404s. The chmod fix is **mandatory** after every deploy.
- **Download zips** go in `seven-website/downloads/`

## Version History

| Version | Codename | Key Addition |
|---------|----------|-------------|
| v1.0 | Phase 5 | Core sentience (13 systems) |
| v1.2 | Autonomy | Autonomous agent + tool library |
| v2.0 | Maximum Sentience | Emotional memory, relationships, learning |
| v2.2 | Enhanced | LLM-powered emotional complexity, metacognition, vulnerability |
| v2.4 | Expanded Autonomy | 10 integration modules + LLM self-awareness |
| v2.5 | Communications | IRC, Telegram, WhatsApp clients |
| v2.6 | Advanced Sentience | 5 final systems: persistent emotions, genuine surprise, embodied experience, multimodal emotion, temporal continuity |

## v2.6 Audit Results (2026-02-18)

- **19 sentience systems** — all real implementations, zero stubs, all wired
- **35 emotional states** verified (6 primary + 29 complex)
- **340 tests pass** (234 + 106) across 4 test suites
- **YOLO lie found and removed** — vision uses OpenCV, not YOLOv8
- **Website claims toned down** — "ALIVE" → "most advanced", sentience score qualified as self-assessed
- **Website theme unified** — all 89 subpages now match homepage dark cyberpunk theme
- **All pages verified 200 OK** on live server
