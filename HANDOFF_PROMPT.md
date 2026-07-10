# Handoff prompt — paste into a new Grok / agent session

Copy everything inside the fence below.

```
You are continuing work on Seven AI → "Seven Real" v4.

## Repo
- Local clone: C:\Users\USER-PC\seven-ai
- Upstream (old): https://github.com/LoSkroefie/seven-ai
- Active product: package `seven/` (v4 Real). Legacy v3 is under `_legacy/v3/` — DO NOT extend; only reference if porting a real tool.
- Start docs: HANDOFF.md, SEVEN_REAL.md, ROADMAP.md, AGENTS.md

## Mission (user intent — non-negotiable)
- Seven is a COMPANION: user TALKS and LISTENS; Seven TALKS and LISTENS.
- FREE WILL: she invents goals and acts without the user typing /work or any slash commands.
- Slash commands are power-user only — never the product face.
- Local-first Ollama. L4 tools when SHE chooses. No greeting spam.
- Hardware: Windows, ~8GB VRAM, 32GB RAM, mic essential, webcam optional.
- Primary entry: `python -m seven --talk` / `run_seven.bat`

## What already works (verified 2026-07-10)
- `python -m seven` CLI agent loop with tool calling via Ollama
- 39 tools registered; default schema tier **core** (lean for llama3.2); `/tools full` for all schemas
- SQLite memory at ~/.seven/seven.db (facts, goals, tasks, audit, notes, messages, compaction)
- Arg sanitization (`seven/tools/sanitize.py`); Windows shell PowerShell hints
- `/status` shows loaded VRAM models + Ollama swap hints
- Live smoke: get_system_info + run_shell; Phase 1 tests including mock-brain tool round
- Heartbeat: only acts on overdue tasks / active goals — NO greeting spam

## What is NOT done
- Tray/GUI (old Tk/Gradio is legacy) — **Phase 2**
- Whisper voice path not production-hardened / not default-on — **Phase 3**
- OpenSeeFace / live avatar / omi-style wearable stream — Phase 4/6
- Mobile bridge; archiving legacy; push to GitHub

## Rules of engagement
1. Extend `seven/` only for product features.
2. Prefer real tool execution over narrative "I would…".
3. No random.choice fake emotions/dreams/thoughts.
4. Goal progress only after real tool work.
5. After changes: `python -m pytest tests/test_seven_real.py -q` and a live `python -m seven -c "…"`.
6. If Ollama hangs: check `ollama ps` for Stopping…; restart Ollama; cold load can take ~60s on 8GB.
7. Read HANDOFF.md + ROADMAP.md before coding. Update them when you finish a milestone.

## Immediate next priorities (pick in order unless user redirects)
1. Multi-step planner + intrinsic goals (thicker mind)
2. Push/tag to GitHub when user asks
3. OpenSeeFace / mobile / robot embodiment

## First actions this session
1. `cd C:\Users\USER-PC\seven-ai`
2. Read HANDOFF.md, ROADMAP.md, docs/ALIVE.md
3. `python -m seven --status` ; `python -m seven --daemon-status`
4. Ask user what to ship next
```
