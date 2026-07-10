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
- Build a WORKING local autonomous agent named Seven, not a personality simulation.
- User paid for a product that only said hello / repeated dumb questions. That is the bug class to never reintroduce.
- Local-first (Ollama). Optional legitimate cloud (OpenAI / Anthropic / OpenAI-compat with USER keys). No stolen "free Claude" endpoints.
- Autonomy L4: shell, files, screen, network, code — no confirmation nags. Audit log yes.
- Form factors over time: voice companion + desktop co-pilot + wearable/mobile-ready + robot-ready bus. Phase, don't vaporware.
- Hardware: Windows, NVIDIA ~8GB VRAM (5050-class), 32GB RAM, Ollama, mic, webcam optional, no robot yet.
- Models user has: llama3.2, llama3.2-vision, neural-chat, artifish/llama3.2-uncensored, custom botha/mortem.
- Honest: do NOT claim biological sentience. Deliver continuous agency + real tools + memory.

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
