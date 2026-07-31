# Unified product: one Seven — talk + avatar + mind

**Owner decision (2026-07-31):** The console/`--talk` companion is the **core**. The desktop avatar is **not** optional chrome — it must run **in the same process** as listen/speak/think. Two agents is wrong.

**GPT diagnosis: ACCEPTED (REAL).**
Current `Start-Seven.cmd` → only `--talk`. `--avatar` is a separate mutually exclusive branch. No avatar process while talk runs.

---

## Product truth

| Must be true | Must not |
|---|---|
| One `Seven` agent instance | Two processes each with own Memory/heartbeat fighting |
| Continuous listen + TTS (CompanionRuntime) | Avatar without ears/mouth |
| Avatar poses follow live state (listening/speaking/thinking/idle) | Fake “listening” pose with no STT |
| Optional console for debug logs | Console as the only face of the product |
| Single launcher starts the full companion | “Start avatar separately” as normal UX |

**Published default:** one window (avatar) + voice life + free will + shared agent.
Console may still open for logs, but **product identity is the avatar + voice**, not a black CMD alone.

---

## Architecture (required shape)

```
Start-Seven.cmd
    → python -m seven --companion   (or --talk becomes this)
         │
         ├─ Seven() agent (one)
         ├─ CompanionRuntime (mic, TTS, freewill queue, handle)
         ├─ SevenAvatar UI (same process, same agent)
         │     poses from living state / is_speaking / listen cycle
         │     optional chat panel = same handle_user_text path
         └─ optional --api on same agent (not second Seven)
```

**Do not:** start `run_talk()` and `run_avatar()` as two processes.
**Do:** extract shared runtime; avatar is a view; talk loop is the controller (or one `CompanionApp` owns both).

---

## Implementation todos (Codex order)

### P0 — One process, one agent

| ID | Task |
|---|---|
| **U1** | Add `seven/runtime/companion_app.py` (or extend `companion.py`) that owns: agent, VoiceIO, CompanionRuntime, heartbeat, optional API thread, and Avatar UI mainloop |
| **U2** | Wire `run_avatar` to use **CompanionRuntime** for speech I/O (not a mute freewill with no mic) |
| **U3** | Change CLI: `--companion` (preferred) or make `--talk` launch unified app when GUI available; keep `--talk-console` / `SEVEN_CONSOLE_ONLY=1` for headless debug |
| **U4** | Remove mutual exclusion as product default: `--avatar` alone should still get listen/speak if voice enabled, not orphan pet |
| **U5** | `Start-Seven.cmd` → unified companion (avatar + talk). Document Quiet/API variants |
| **U6** | Tests: companion_app constructs one agent; freewill on_utter is companion callback; pose transitions when speaking/listening flags set (mock voice) |

### P1 — Avatar driven by real life

| ID | Task |
|---|---|
| **U7** | Pose binding: `listening` while listen cycle; `speaking` while TTS; `thinking` while handle(); idle otherwise |
| **U8** | Chat panel uses `runtime.handle_user_text` only (same path as STT) |
| **U9** | Tray/menu: Quit, Mute unsolicited, Open log folder — no second agent |

### P2 — Publish

| ID | Task |
|---|---|
| **U10** | Deploy exact SHA to D:\SevenLocal; Start-Seven shows avatar + listens |
| **U11** | Evidence: process cmdline, screenshot optional, log Listening + pose updates |
| **U12** | README: primary UX is unified companion, not console-only |

---

## Paste to Codex

```
Grok + owner product decision (non-negotiable):

Seven's published face is ONE process: desktop avatar + continuous listen/speak + single agent mind.
Console-only --talk is debug/fallback, not the product.
Starting --avatar and --talk as two processes is FORBIDDEN as normal UX (two Sevens).

GPT is correct: wire avatar into the same talk/CompanionRuntime.

Read:
- docs/orchestration/14_UNIFIED_AVATAR_TALK.md (create if only in audit path; implement anyway)
- seven/ui/avatar.py
- seven/ui/talk.py
- seven/runtime/companion.py
- seven/__main__.py (avatar vs talk branches)
- D:\SevenLocal\Start-Seven.cmd

Implement U1–U6 at minimum (P0):
1) Unified companion app: one Seven(), CompanionRuntime, Avatar UI, heartbeat together
2) Start-Seven.cmd launches that unified mode
3) --talk-console or env for console-only if needed
4) Avatar poses follow listening/speaking/thinking from real runtime flags
5) Tests for single-agent wiring
6) Commit+push on codex/seven-completion; deploy D:\SevenLocal; prove one process shows avatar AND Listening logs

Base from current tip (56235ae or later).
No second agent. No Peanut unless asked. No sentience claims.
Report: Done / Evidence / Still broken / Next 3
GO.
```

---

## Short whip

```
One Seven: avatar+talk+CompanionRuntime same process. Fix Start-Seven. No dual agents. Deploy and prove. Go.
```
