# Seven AI — Wiki Home

Welcome to the Seven AI wiki. Seven is an **offline-first, standalone AI companion** built on local Ollama, with a rich behavioral simulation stack (35 emotions, relationship tracking, memory, dreams, ethics, promises) and 20 extensions.

**Current version**: `v3.2.20` — [latest release](https://github.com/LoSkroefie/seven-ai/releases/tag/v3.2.20)

---

## 📚 Wiki Pages

### Getting Started
- **[Installation](Installation)** — Windows / Linux / macOS setup
- **[First Launch](First-Launch)** — what to expect on day one
- **[Troubleshooting](Troubleshooting)** — common issues and fixes

### Configuration
- **[Configuration Reference](Configuration-Reference)** — every `config.py` knob explained
- **[Voice & Whisper STT](Voice-and-Whisper-STT)** — speech recognition setup
- **[TTS Voices](TTS-Voices)** — edge-tts neural voices

### Features
- **[Sentience Architecture](Sentience-Architecture)** — the 19 behavioral systems
- **[Extensions](Extensions)** — 20 loaded plugins, triggers, scheduling
- **[opencode Delegator](opencode-Delegator)** — coding task delegation
- **[MCP Server](MCP-Server)** — exposing Seven's memory to external AI tools
- **[Voice Emotion Detection](Voice-Emotion-Detection)** — librosa-based tone analysis
- **[REST API](REST-API)** — 15 endpoints on port 7777
- **[Daemon Mode](Daemon-Mode)** — 24/7 background service

### Development
- **[Architecture Overview](Architecture-Overview)** — how Seven is wired
- **[Writing Extensions](Writing-Extensions)** — plugin authoring guide
- **[Testing](Testing)** — running the 57-test suite
- **[Audit Reports](Audit-Reports)** — v3.2.18 / v3.2.19 / v3.2.20 audit results

### Reference
- **[Changelog](Changelog)** — version history
- **[Known Limitations](Known-Limitations)** — what Seven can't do

---

## 🎯 Quick Links

- **Repo**: https://github.com/LoSkroefie/seven-ai
- **Latest release**: https://github.com/LoSkroefie/seven-ai/releases/latest
- **Issue tracker**: https://github.com/LoSkroefie/seven-ai/issues
- **Website**: https://jvrsoftware.co.za/seven/

---

## 🆕 What's New in v3.2.20

- **opencode delegator** — "opencode, explain this" hands a task to the opencode CLI
- **MCP server auto-launch** — exposes Seven's memory to Claude Desktop / Cursor
- **Whisper STT enabled by default** — local, CUDA-accelerated speech recognition
- **`run_seven.bat`** — pinned Python launcher so whisper/mcp/torch actually resolve
- **4 ghost-method bugs fixed** (RelationshipModel, GoalSystem, ProactiveEngine, IntrinsicMotivation)
- **Dashboard isolation** — one broken subsystem no longer blanks the GUI
- **Extension scheduler actually runs** — 14 scheduled extensions now fire on interval
- **57/57 tests pass** — 0 ghost-method bugs, 0 escape-sequence warnings

Full notes: [Changelog](Changelog) · [v3.2.20 release](https://github.com/LoSkroefie/seven-ai/releases/tag/v3.2.20)
