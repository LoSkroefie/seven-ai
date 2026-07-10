# Seven Real — Project Handoff

**Last updated:** 2026-07-10  
**Status:** v4.0.6-alive; daemon + world/self model; legacy in `_legacy/v3/`; **push only if user asks**  
**Owner intent:** Fully working local agent (L4), not simulation theater

---

## 1. Quick start (next human or agent)

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -r requirements-real.txt
python -m seven --status
python -m seven -c "Call get_system_info and summarize OS and RAM in one sentence."
python -m pytest tests/test_seven_real.py -q
python -m seven
```

Launcher: `run_seven_real.bat`  
Paste-ready session prompt: **[HANDOFF_PROMPT.md](HANDOFF_PROMPT.md)**  
Conventions: **[AGENTS.md](AGENTS.md)**  
Priorities: **[ROADMAP.md](ROADMAP.md)**  
User-facing real docs: **[SEVEN_REAL.md](SEVEN_REAL.md)**

---

## 2. What this project is

| Layer | Path | Role |
|---|---|---|
| **Seven Real v4** | `seven/` | **Active product** — agent loop + tools + memory |
| **Legacy v3.2.20** | `_legacy/v3/` | Archived simulation codebase; reference only |
| **User data (v4)** | `%USERPROFILE%\.seven\` | DB, logs, workspace |
| **User data (v3)** | `%USERPROFILE%\.chatbot\` | Old bot data — do not mix blindly |

Upstream: https://github.com/LoSkroefie/seven-ai  
Local clone: `C:\Users\USER-PC\seven-ai`  
Git: v4 files are still **untracked** (`?? seven/`, `SEVEN_REAL.md`, etc.) on `main`.

---

## 3. Architecture (v4)

```
User / CLI / (future tray)
        │
        ▼
 seven.agent.loop.Seven.handle(text)
        │
        ├─► seven.brain.Brain.chat(messages, tools)   # Ollama / OpenAI / Anthropic / compat
        │         │
        │         └─ tool_calls ──► seven.tools.ToolRegistry.execute
        │                                  │
        │                                  └─ shell, files, screen, web, vision, …
        │
        └─► seven.memory.Memory  # SQLite audit + history + facts/goals/tasks
```

### Key modules

| Module | File | Notes |
|---|---|---|
| Entry | `seven/__main__.py` | `python -m seven` |
| Config | `seven/config.py` | Env overrides; L4 defaults |
| Agent | `seven/agent/loop.py` | Tool rounds, slash cmds, heartbeat |
| Prompt | `seven/agent/prompt.py` | System prompt + identity files |
| Brain | `seven/brain/llm.py` | Native tools + JSON text-tool fallback |
| Memory | `seven/memory/store.py` | `~/.seven/seven.db` |
| Tools | `seven/tools/*.py` | Real host actions |
| Embodiment | `seven/embodiment/bus.py` | Serial robot bus; queues if offline |
| Voice | `seven/voice/io.py` | Optional TTS/STT |
| CLI | `seven/ui/cli.py` | Interactive REPL |
| Identity | `seven/identity/*.md` | Fresh Seven Real persona |

### Tools registered (39)

`run_shell`, `read_file`, `write_file`, `list_dir`, `search_files`, `delete_path`, `move_path`,  
`screenshot`, `screen_size`, `mouse_click`, `mouse_move`, `type_text`, `hotkey`,  
`web_search`, `web_fetch`,  
`capture_webcam`, `analyze_image`, `see_screen`,  
`run_python`, `get_system_info`,  
`remember_fact`, `search_memory`, `add_task`, `list_tasks`, `complete_task`,  
`add_goal`, `update_goal`, `list_goals`, `add_note`, `list_notes`,  
`get_clipboard`, `set_clipboard`,  
`coding_agent_status`, `run_opencode`, `run_claude_cli`, `run_codex_cli`,  
`robot_status`, `robot_connect`, `robot_action`

---

## 4. User decisions (locked)

From 2026-07-09 session:

1. **Hardware:** NVIDIA ~8GB VRAM, 32GB RAM, Ollama, mic, webcam optional, robot later, mobile/wearables hoped for  
2. **LLM:** Local first; legitimate multi-provider support  
3. **Models:** llama3.2 + llama3.2-vision (also has uncensored / custom models)  
4. **Autonomy:** **L4 unrestricted** — no lift-restrictions UX; audit only  
5. **Scope:** All form factors phased (voice, desktop, wearable, robot-ready)  
6. **Problem to fix:** Product never delivered beyond hello / looped questions  
7. **Integrations:** Legitimate opencode / Claude Code / Codex CLIs OK  
8. **Memory:** Fresh Seven Real OK (`~/.seven`), not required to migrate `.chatbot`  
9. **Workflow:** Rewrite the **clone**; user spent money and wants it working  

**Do not re-open:** “should we restrict L4?” — user said no. Keep audit.  
**Do not claim:** true consciousness / “100/100 sentience score.”

---

## 5. Verified tests (2026-07-10)

| Check | Result |
|---|---|
| `pytest tests/test_seven_real.py` | 6 passed (pre-harden); Phase 1 expanded suite |
| `python -m seven --status` | Ollama OK, 39 tools, llama3.2 + vision present |
| Live `get_system_info` | Windows 11, ~34GB RAM reported |
| Live `run_shell` echo | `Seven-Real-Works` |
| Empty optional tool args (`cwd=""`, `timeout=""`) | Handled in `shell.py` + `sanitize.py` |
| Phase 1 | Tool tiers, compaction, mock brain integration, Ollama ps hints |
| Phase 2 | GUI/API imports; 15 pytest passed; `--gui` / `--api-only` flags |
| Phase 3 | 18 pytest; TTS speak True (edge); STT whisper lazy+google; PTT CLI/GUI |
| Phase 4 | 21 pytest; webcam 1280x720 capture; presence OpenCV; screen 1920x1080 save |
| Phase 5 | 25 pytest; progress only after tools; work session commands |

---

## 6. Known pitfalls

### Ollama stuck / timeouts
- Symptom: `/api/tags` works, `/api/chat` hangs 120–300s  
- Often `ollama ps` shows a model **Stopping…** (VRAM swap on 8GB)  
- Fix: restart Ollama app/process; wait for cold load (~30–60s for llama3.2)  
- Brain already: 300s timeout, `keep_alive=30m`, fallback to loaded model on timeout  

### Small models + many tools
- llama3.2 may ignore tools or emit weak plans  
- Fallback: text JSON tool protocol in `brain/llm.py`  
- If flaky: reduce schemas, stronger system prompt, or better model (uncensored / larger / cloud)  

### Vision VRAM
- `llama3.2-vision` ≈ 7.8GB — fights with text model on 8GB  
- Use vision tools only when needed; expect swap latency  

### Legacy confusion
- README.md at root still markets v3.2.20 “51 systems”  
- `main_with_gui_and_tray.py` is **not** Seven Real  
- Always run `python -m seven`  

### Windows Python
- Prefer real Python 3.11+; Store Python breaks Whisper/torch  
- `run_seven_real.bat` supports `PYTHON_EXE` override  

---

## 7. Inspiration repos (user-supplied)

| Repo | Use for Seven |
|---|---|
| emilianavt/OpenSeeFace | Face/landmarks → presence (not done) |
| Arcelyth/live-ascii | Avatar / Live2D terminal (optional) |
| BasedHardware/omi | Continuous wearable-style capture patterns (not done) |
| benjojo/dnsfs | Low priority novelty |
| free-claude-code | **Legitimate multi-agent UX only** — no unauthorized free APIs |

---

## 8. File map (v4 touch points)

```
seven-ai/
  HANDOFF.md              ← this file
  HANDOFF_PROMPT.md       ← paste into new session
  AGENTS.md               ← coding rules for agents
  ROADMAP.md              ← ordered work
  SEVEN_REAL.md           ← user-facing real docs
  requirements-real.txt
  run_seven_real.bat
  tests/test_seven_real.py
  seven/
    __main__.py
    config.py
    agent/loop.py
    agent/prompt.py
    brain/llm.py
    memory/store.py
    tools/…
    embodiment/bus.py
    voice/io.py
    ui/cli.py
    identity/
  core/ …                 ← LEGACY (do not grow)
```

---

## 9. Session log (brief)

| When | What |
|---|---|
| 2026-07-09 | Cloned repo; audited v3 lies (random.choice, fake goals, dep drift) |
| 2026-07-09 | User locked L4, local-first, all form factors, rewrite clone |
| 2026-07-09–10 | Built `seven/` Real agent; tests green; live tool calls OK after Ollama restart |
| 2026-07-10 | Handoff pack written |
| 2026-07-10 | Phase 1 harden: sanitize, core/full tiers, compaction, status hints, more tests |
| 2026-07-10 | Phase 2 desktop: tk GUI, optional pystray, stdlib REST API, shortcut script |
| 2026-07-10 | Phase 3 voice: PTT, edge-tts, whisper lazy + google fallback, docs/VOICE.md |
| 2026-07-10 | Phase 4 vision: VRAM-aware analyze/see_screen/webcam, OpenCV presence, docs/VISION.md |
| 2026-07-10 | Phase 5 autonomy: work sessions, goal steps, audit pretty, progress only after tools |
| 2026-07-10 | Phase 7: legacy → `_legacy/v3/`, root README, pyproject 4.0.5, local commit |
| 2026-07-10 | 4.0.6 alive: LivingState, daemon, sense→act→reflect, autostart script |

---

## 10. When finishing a work session

Update:

1. **ROADMAP.md** — check off items, add blockers  
2. **HANDOFF.md** §5 / §9 — new verified tests + session log line  
3. **HANDOFF_PROMPT.md** — only if mission or next priorities change  
4. Optionally commit (ask user before push)

Suggested commit message when user wants git:

```
feat: Seven Real v4 local agent loop with L4 tools

Replace simulation theater with tool-calling agent (Ollama-first).
```
