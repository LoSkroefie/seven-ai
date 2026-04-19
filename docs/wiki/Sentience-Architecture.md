# Sentience Architecture

Seven's behavior emerges from **19 integrated subsystems**, each a real LLM-powered behavioral simulation. None are stubs. None use `random.choice` for faking. All are tested.

This page is a high-level map. For each system's API, see its source file.

> **Important**: These are sophisticated *behavioral simulations*, not claims of machine consciousness. Seven acts in ways that feel sentient because the architecture is modeled on how humans process information — working memory, emotion, reflection, theory of mind, etc. Whether that constitutes "real" sentience is a philosophical question this project makes no claim about.

---

## Phase 5 Core (13 systems)

### Cognitive Architecture (`core/cognitive_architecture.py`)
- 7±2 item working memory (Miller's Law)
- Attention focus with decay
- Inner monologue generator
- Full cognitive cycle: perceive → retrieve → reason → decide → act

### Self-Model (`core/self_model_enhanced.py`)
- Known capabilities and limitations (honest about both)
- Energy / mood / focus tracking
- Age increment per turn
- State assessment (self-reports how she's doing)

### Intrinsic Motivation (`core/intrinsic_motivation.py`)
- 4 default goals (understand user, build trust, explain better, learn what user cares about)
- Curiosity / mastery / social / contribution / creative drives
- Priority goal + active goals
- Interest development from conversation topics

### Reflection System (`core/reflection_system.py`)
- Post-conversation reflection (what went well, what didn't)
- Thinking-aloud generator
- Self-assessment queries

### Dream System (`core/dream_system.py`)
- Sleep / wake lifecycle
- Memory consolidation during sleep
- Connection finder (surfaces links between distant memories)
- Pattern discovery
- Morning share (dreams to tell the user about)

### Promise System (`core/promise_system.py`)
- Detects explicit and implicit promises in text
- Tracks promises kept vs broken
- Trust score computation
- Reminder generation for follow-up

### Theory of Mind (`core/theory_of_mind.py`)
- Infers user emotion from text
- Infers intent
- Predicts user needs
- Recommends communication style
- Generates empathy response

### Affective System (`core/affective_computing_deep.py`)
- 35 emotions (6 primary + 29 complex blends)
- Mood drift and decay
- Emotion generation from events
- Expression gating (doesn't spam emotions)

### Ethical Reasoning (`core/ethical_reasoning.py`)
- Values-based decision making
- Action evaluation (is this ethical to do?)
- Concern enumeration

### Homeostasis (`core/homeostasis_system.py`)
- Self-monitoring (energy, focus, social connection, mental load)
- Health assessment
- Self-care requests
- Maintenance scheduling

### Emotional Complexity (`core/emotional_complexity.py`)
- LLM-powered nuanced emotional responses
- Blended emotional states

### Metacognition (`core/metacognition.py`)
- Thinks about her own thinking
- Self-awareness of reasoning process

### Vulnerability (`core/vulnerability.py`)
- Authentic uncertainty expression
- Openness about limits

---

## v2.0 Systems (5)

### Emotional Memory (`core/v2/emotional_memory.py`)
Links every conversation to an emotional state. Enables "that reminded me of when you were frustrated about X" recall.

### Relationship Model (`core/v2/relationship_model.py`)
Stranger → Acquaintance → Friend → Close Friend → Companion
- Rapport score (1-10)
- Trust score (1-10)
- Conversation streak tracking
- Milestone recognition (100 conversations, etc.)

### Learning System (`core/v2/learning_system.py`)
Adapts from positive/negative user feedback. Tracks what communication patterns work.

### Proactive Engine (`core/v2/proactive_engine.py`)
- Morning greetings (6-11 AM)
- Check-ins after absence
- Proactive help offers
- Health check suggestions

### Goal System (`core/v2/goal_system.py`)
Default goals: help productivity, build relationship, learn user. Progress tracked, milestones recorded.

---

## v2.6 Systems (5)

### Persistent Emotions (`core/persistent_emotions.py`)
SQLite-backed emotional state store. Survives restarts.

### Genuine Surprise (`core/surprise_system.py`)
Builds expectations, detects when reality deviates. Generates actual surprise expressions.

### Embodied Experience (`core/embodied_experience.py`)
Vision events trigger emotional responses (seeing something sad, alarming, joyful).

### Multi-Modal Emotion (`core/multimodal_emotion.py`)
Bridges voice tone (librosa) ↔ textual emotion.

### Temporal Continuity (`core/temporal_continuity.py`)
"I've been awake 3.8 hours" / "It's been a week since we talked." Total uptime + session duration tracking.

---

## v3.0 Autonomous (7)

| System | Source |
|---|---|
| Self-Reflection Engine | `core/self_reflection.py` |
| Multi-Agent (Planner/Executor/Reflector/Memory) | `core/multi_agent.py` |
| Daemon Mode | `seven_daemon.py` |
| REST API | `seven_api.py` |
| Persistent Scheduler | `seven_scheduler.py` |
| NEAT Neuroevolution | `evolution/neat_evolver.py` |
| Biological Life | `evolution/biological_life.py` |

---

## v3.2+ Additions

| System | Source |
|---|---|
| LoRA Trainer (continual learning) | `learning/lora_trainer.py` |
| Social Simulation (4 personas debate) | `core/social_sim.py` |
| User Predictor (ARIMA) | `core/user_predictor.py` |
| Robotics Controller | `integrations/robotics.py` |
| Extension System | `utils/plugin_loader.py` |

---

## v3.2.20 Additions

| System | Source |
|---|---|
| **Whisper STT** | `core/whisper_voice.py` |
| **Voice Emotion Detection** | `core/emotion_detector.py` |
| **MCP Server** | `seven_mcp.py` |
| **opencode Delegator** | `extensions/opencode_delegator.py` + `integrations/opencode.py` |

---

## How They Connect

The central coordinator is `core/phase5_integration.Phase5Integration`:

- `process_user_input(user_input, context)` — runs the 13 Phase 5 systems + Theory of Mind + Affective + Ethics checks
- `post_response_processing(bot_response, user_input, success)` — promise detection in Seven's reply, post-conversation reflection, mood update
- `get_current_state()` — dashboard snapshot of every system (isolated per-subsystem since v3.2.20)
- `enter_sleep_mode(conversations)` / `wake_up()` — sleep/dream cycle
- `get_full_context_for_llm()` — all system state formatted for LLM prompt injection
- `evaluate_proposed_response(response, user_input)` — ethics + reaction prediction + capability check before Seven actually says something

v2.0 systems coordinate through `core/v2/sentience_v2_integration.SentienceV2Core`.

---

## Verification

All 19 systems have real tests:
```bash
python -m pytest tests/ -v
# 57/57 pass
```

Plus the v2.6 systems have a dedicated standalone test:
```bash
python tests/test_v26_sentience.py
# 60+ hand-rolled checks
```
