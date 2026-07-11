# Seven Real — Roadmap

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Phase 0 — Foundation `[x]`

- [x] Clone repo, audit v3 lies vs code  
- [x] User constraints locked (L4, local-first, form factors)  
- [x] Package `seven/` agent loop + Brain + Memory  
- [x] L4 tool suite (39 tools)  
- [x] CLI entry `python -m seven`  
- [x] Smoke tests + live Ollama tool calls  
- [x] Handoff docs  

---

## Phase 1 — Harden core `[x]`

- [x] Tool-arg sanitization across all tools (empty strings, wrong types) — `seven/tools/sanitize.py` + registry  
- [x] Shrink or tier tool schemas for small local models (core vs full) — `SEVEN_TOOL_TIER`, `/tools core|full`  
- [x] Better error when Ollama is mid-swap (surface `ollama ps` hint in /status)  
- [x] Conversation compaction when history grows — `Memory.compact_history`  
- [x] One integration test that mocks Brain tool_calls → registry  
- [x] Fix any Windows shell quoting issues for complex commands — PowerShell hint, UTF-8, fence strip  

**Next default → Phase 2 (Desktop UX) or Phase 3 (Voice) per user.**

---

## Phase 2 — Desktop UX `[x]`

- [x] System tray (pystray optional; hide on close) — `seven/ui/chat_gui.py`  
- [x] Minimal GUI chat that only calls `Seven.handle()`  
- [x] Optional REST API on 127.0.0.1 — stdlib `seven/ui/api_server.py`  
- [x] Desktop shortcut script → `create_seven_shortcut.ps1` + `run_seven_gui.bat`  
- [x] CLI flags: `--gui` `--api` `--api-only`  

**Next default → Phase 3 Voice**

---

## Phase 3 — Voice `[x]`

- [x] Document exact Windows install — `docs/VOICE.md`  
- [x] Default-off voice; `--voice` / `--gui --voice` / `run_seven_voice.bat`  
- [x] edge-tts + pygame TTS with pyttsx3 fallback; markdown strip  
- [x] Push-to-talk only (CLI empty/`/listen`, GUI Mic) — no ambient spam  
- [x] Whisper lazy-load + Google STT fallback + hallucination filter  

**Next default → Phase 4 Vision**

---

## Phase 4 — Vision & presence `[x]`

- [x] `see_screen` / `analyze_image` VRAM-aware (downscale, short keep_alive) + `docs/VISION.md`  
- [x] Webcam: `list_cameras`, `capture_webcam`, `see_webcam` (warmup + CAP_DSHOW)  
- [x] Presence: `check_presence` via OpenCV Haar (OpenSeeFace landmarks deferred)  
- [ ] Optional OpenSeeFace landmarks / live-ascii avatar (backlog)

---

## Phase 5 — Continuous autonomy `[x]`

- [x] Goals that schedule real multi-step tool work — `AutonomyEngine.run_goal_step`  
- [x] Heartbeat writes `autonomy` notes; progress only after real tools  
- [x] `/audit` pretty activity log (`format_audit`)  
- [x] Work session: `/work` `/workstep` `/workstatus` `/stopwork`  
- [x] Docs: `docs/AUTONOMY.md`

---

## Phase 6a — Always-on living core `[x]`

- [x] World model + self model + `living_state.json`  
- [x] Daemon (`--daemon` / stop / status) + API  
- [x] Heartbeat: sense → act → reflect  
- [x] Windows autostart script `install_autostart.ps1`  
- [x] Docs: `docs/ALIVE.md`  

## Phase 6 — Embodiment & mobile `[ ]`

- [ ] Arduino sketch + protocol doc matching `embodiment/bus.py`  
- [ ] Wearable/phone push channel (design first: WebSocket or MQTT)  
- [ ] omi-like ambient capture pattern (opt-in, privacy clear)

---

## Phase 7 — Repo hygiene & ship `[~]`

- [x] Move legacy tree → `_legacy/v3/`  
- [x] Root README → Seven Real only  
- [x] Align package metadata to the 4.3 series
- [~] Exhaustively classify current and legacy files — see `docs/COMPLETION_LEDGER.md`
- [~] Reconcile every product claim with implementation and evidence
- [ ] Clean install, upgrade, uninstall, recovery, hardware and soak gates
- [ ] Push completion branch and open an evidence-backed draft PR
- [ ] Tag a release only after every release gate passes

---

## Backlog (unordered)

- Multi-provider auto-fallback: ollama → openai if local dead  
- Vector memory (Chroma) only if local embeddings stay light  
- MCP server exposing Seven tools (legitimate)  
- Port only *working* legacy integrations (calendar, email) one-by-one with tests  
- Uncensored local model profile for freer tool use  

---

## Explicitly rejected

- Rebuilding 19 fake sentience modules with random phrases  
- “Sentience score 100/100” marketing  
- Unauthorized free Claude/Codex API abuse  
- Re-enabling 5-minute “how are you / system health” chatter  

---

## Current recommendation

**Current state:** the living core, tools and user interfaces are implemented, but the project remains Beta. Completion work is recovering legacy value, closing lifecycle gaps and producing release-grade evidence. See `docs/COMPLETION_LEDGER.md`.
