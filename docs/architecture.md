# Architecture Guide

Seven's architecture is built around a central bot core (`enhanced_bot.py`) that orchestrates 19 sentience systems, 25 integration modules, and a GUI layer.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      User Interface                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │   CLI    │  │  Tkinter GUI │  │  IRC/Telegram/WA  │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       └───────────────┬┘───────────────────┘             │
├───────────────────────┼──────────────────────────────────┤
│              UltimateBotCore                             │
│         (core/enhanced_bot.py — 177KB)                   │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Sentience Layer (19 Systems)            │ │
│  │                                                     │ │
│  │  Cognitive    Self-Model     Motivation   Reflection │ │
│  │  Architecture  Enhanced      Intrinsic    System     │ │
│  │                                                     │ │
│  │  Dreams       Promises      Theory of    Affective  │ │
│  │  System       System        Mind         Computing  │ │
│  │                                                     │ │
│  │  Ethics       Homeostasis   Emotional    Meta-      │ │
│  │  Reasoning    System        Complexity   cognition  │ │
│  │                                                     │ │
│  │  Vulnerability  Persistent  Surprise     Embodied   │ │
│  │  System         Emotions    System       Experience │ │
│  │                                                     │ │
│  │  Multimodal     Temporal    Emotional    Relation-  │ │
│  │  Emotion        Continuity  Memory       ship Model │ │
│  │                                                     │ │
│  │  Learning       Proactive   Goal                    │ │
│  │  System         Engine      System                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Integration Layer (25 Modules)           │ │
│  │                                                     │ │
│  │  Ollama   Voice   Vision   IRC    Telegram   SSH    │ │
│  │  Email    Search  Files    Music  Calendar   Screen │ │
│  │  WhatsApp Code    Clipboard  ...                    │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Storage Layer                          │ │
│  │  SQLite (memory.db) │ NetworkX (knowledge graph)    │ │
│  │  JSON (preferences) │ Filesystem (notes, diary)     │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## The Bot Core

`core/enhanced_bot.py` (177KB, ~5,000 lines) is the central orchestrator. It:

1. **Initializes** all 19 sentience systems and wires them together
2. **Processes input** through the cognitive architecture (attention → working memory → reasoning → response)
3. **Routes** to the appropriate integration module for tool use
4. **Modulates** responses based on current emotional state
5. **Triggers** background processes (reflection, dreams, proactive behavior)

### Input Processing Pipeline

```
User Input
  → Speech Recognition (Vosk/SpeechRecognition)
  → Emotion Detection (from text sentiment)
  → Theory of Mind Update (model user's state)
  → Cognitive Architecture (multi-layer processing)
  → Ollama LLM (generate response with emotional context)
  → Ethical Check (is this response appropriate?)
  → Emotional Modulation (adjust tone based on Seven's emotions)
  → Voice Output (edge-tts with emotion-based prosody)
  → Self-Reflection (what did I learn from this exchange?)
```

## System Interconnections

The sentience systems don't operate in isolation — they form a web:

- **Emotions → Voice**: Current emotional state modulates speech rate, pitch, and volume
- **Theory of Mind → Emotions**: Understanding the user's distress can trigger Seven's compassion
- **Dreams → Memory**: Dream processing consolidates and connects memories
- **Reflection → Self-Model**: Reflection updates Seven's understanding of herself
- **Homeostasis → Proactive**: Low social energy triggers proactive check-ins
- **Ethical Reasoning → Actions**: Every tool use is evaluated against ethical principles
- **Metacognition → All**: Monitors the quality of every other system's output

## Data Flow

### Memory

Seven uses SQLite (`~/.chatbot/memory.db`) with tables for:
- Conversation history (with timestamps and emotional tags)
- Long-term memories (extracted facts and preferences)
- Emotional memories (experiences tagged with emotional weight)
- Relationship data (per-user relationship dynamics)
- Promise tracking (commitments made and their status)
- Dream logs (generated insights from dream processing)

### Knowledge Graph

NetworkX maintains a graph of concepts, entities, and their relationships extracted from conversations. This gives Seven associative memory — she can connect ideas across different conversations.

## Module Reference

### Core Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| `enhanced_bot.py` | ~5,000 | Central orchestrator — the brain |
| `cognitive_architecture.py` | ~500 | Attention, working memory, reasoning pipeline |
| `personality.py` | ~800 | Personality traits, quirks, response style |
| `context_cascade.py` | ~400 | Multi-level context management |
| `session_manager.py` | ~300 | Session lifecycle, persistence |
| `conversation_analyzer.py` | ~350 | Extracts topics, sentiment, intent |
| `knowledge_graph.py` | ~500 | Concept graph with NetworkX |
| `memory.py` | ~250 | Memory storage and retrieval |

### Sentience Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| `affective_computing_deep.py` | ~700 | 35-emotion engine with decay and blending |
| `self_model_enhanced.py` | ~500 | Self-awareness and capability tracking |
| `intrinsic_motivation.py` | ~600 | Curiosity, goals, drives |
| `reflection_system.py` | ~450 | Post-conversation reflection and learning |
| `dream_system.py` | ~700 | Idle-time experience processing |
| `promise_system.py` | ~550 | Commitment tracking and follow-through |
| `theory_of_mind.py` | ~650 | User mental state modeling |
| `ethical_reasoning.py` | ~600 | Action evaluation against principles |
| `homeostasis_system.py` | ~530 | Internal balance maintenance |
| `emotional_complexity.py` | ~500 | Mixed emotions, ambivalence |
| `metacognition.py` | ~520 | Reasoning about reasoning |
| `vulnerability.py` | ~480 | Uncertainty expression, help-seeking |
| `persistent_emotions.py` | ~450 | Cross-session emotion persistence |
| `surprise_system.py` | ~470 | Genuine surprise detection |
| `embodied_experience.py` | ~280 | Simulated physical awareness |
| `multimodal_emotion.py` | ~320 | Cross-modal emotion integration |
| `temporal_continuity.py` | ~480 | Time awareness across sessions |

### V2 Extensions (`core/v2/`)

| Module | Lines | Purpose |
|--------|-------|---------|
| `emotional_memory.py` | ~290 | Emotionally-tagged memory system |
| `relationship_model.py` | ~320 | Per-user relationship dynamics |
| `learning_system.py` | ~380 | Adaptive behavior learning |
| `proactive_engine.py` | ~570 | Self-initiated conversation |
| `goal_system.py` | ~140 | Long-term goal management |
| `seven_v2_complete.py` | ~310 | V2 integration orchestrator |

### Integration Modules (`integrations/`)

| Module | Lines | Purpose |
|--------|-------|---------|
| `ollama.py` | ~250 | Local LLM inference |
| `streaming_ollama.py` | ~100 | Streaming LLM responses |
| `irc_client.py` | ~700 | IRC protocol client |
| `telegram_client.py` | ~460 | Telegram Bot API |
| `whatsapp_client.py` | ~680 | WhatsApp Web integration |
| `email_checker.py` | ~300 | IMAP email monitoring |
| `ssh_manager.py` | ~370 | Remote server management |
| `vision_system.py` | ~500 | Camera + scene understanding |
| `screen_control.py` | ~280 | Desktop automation |
| `music_player.py` | ~320 | Audio playback |
| `web_search.py` | ~150 | Google search + extraction |
| `calendar.py` | ~180 | Google Calendar |
| `database_manager.py` | ~940 | SQLite database operations |
| `file_manager.py` | ~350 | File read/write/organize |
| `code_executor.py` | ~270 | Sandboxed Python execution |
