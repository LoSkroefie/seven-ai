# Finish Seven as a living companion (not just an agent)

**Date:** 2026-07-31  
**Police:** Grok — based on code + owner logs (not vibes)  
**Deployed SHA now:** `1397d04` (tools/memory honest)  
**Product gap:** She decides `speak` but **`uttered=False`** — mouth/ear path broken or unwired in the process that is running.

---

## 1. Direct answers

### Does she have a voice?
**Code: yes (optional).** `seven/voice/io.py` — edge-tts / pyttsx3.  
**Product: only if** `python -m seven --talk` (or GUI with Speak) **and** TTS deps work.  
**API-only / avatar+api / quiet** paths often **never attach TTS** to free will.

### Does she listen?
**Code: partial.** `listen_once()` = timed mic capture (timeout ~12s), **not** always-on ambient listening.  
**Product:** talk loop calls listen in a loop when mic works — still **turn-based**, not continuous open mic with VAD.  
Docs even say: *“Push-to-talk / talk mode — not ambient spam.”*

### Why your log is broken
```
Freewill: speak — I have something to say
alive_cycle ... decision=speak uttered=False
```

In `loop._autonomous_tick`:
1. `decide()` → **speak**
2. `execute()` → `_speak_thought()` must return text  
3. If text is empty/`None` → **`uttered=False`**  
4. Even if text exists, **`on_utter` must be set** or she only logs *“would say”* (no speaker)

**`uttered=False` means step 2 failed** (no text), not only missing speakers.

Common causes in **current** code:
| Cause | Where |
|---|---|
| LLM `generate` fails / empty / &lt;3 chars | `freewill._speak_thought` when `BACKGROUND_LLM=1` |
| Grounded template **suppressed as duplicate** | `BACKGROUND_LLM=0` path returns `None` after repeat |
| **`last_speak_ts` set even when utter fails** | burns speak slot, loops empty speak decisions later |
| Process is **API / daemon without talk** | no `on_utter` → even good text never hits speakers |
| **`Start-Seven-Quiet.cmd`** sets `SEVEN_BACKGROUND_LLM=0` and runs **`--avatar --api`** | not full talk/listen companion |

So: **she is not “alive in the room.”** She is an **agent heartbeat** choosing speak with **no successful utterance pipeline** in that process.

### Text works → voice/listen must work
**Correct product rule.** Today: text path (`handle`) is solid; **voice is a side mode**, not the same pipeline. That is the main architectural hold-up.

---

## 2. What is holding her back from speak / listen / grow

| Blocker | Effect |
|---|---|
| **No always-on companion process** with mic+TTS+`on_utter` | Free will speech is silent |
| **Listen is timeout bursts**, not continuous | Misses speech; feels deaf |
| **Speak decision without guaranteed utter** | Logs show life; room hears silence |
| **Growth = random goals/tools**, not preference/outcome learning loop productized | “Does random stuff” |
| **Learning weak** | Beliefs from tools exist; not strong “who I am / what owner wants / what I learned today” shaping speech |
| **Launcher split** | Talk vs API vs avatar — product identity unclear |
| **VRAM/model cold load** | Speak generate fails → uttered=False |
| **Permission-to-speak / barge-in** | Not first-class UX (barge-in flag exists partially; not full social protocol) |

---

## 3. Definition of “published alive companion” (acceptance)

Must all pass on owner Windows (`D:\SevenLocal`) before “published”:

### A. One primary product process
- Single recommended launcher: **Talk companion** (mic + TTS + free will + optional API)  
- Startup installs that mode by default  

### B. Listen
- Continuous listen loop while idle (VAD or rolling `listen_once` with short timeout)  
- Wake/respond when user speech transcribed (optional wake word later)  
- Text keyboard always works as fallback in same process  

### C. Speak
- Every freewill `decision=speak` that succeeds must either:  
  - play TTS **or**  
  - print + log **why** speech failed (engine/model) — never silent `uttered=False` without reason  
- Unsolicited speech: rate-limited; optional **ask permission** mode (`SEVEN_SPEAK_PERMISSION=1`)  
- Replies to user always TTS when voice mode on  

### D. Grow (not random thrash)
- Daily/idle learning: consolidate facts about owner + self from conversations  
- Free will invent goals **from gaps/preferences**, not only “tidy workspace” fallback  
- After work: one spoken reflection that cites what changed  
- Suppress invent spam when no user benefit  

### E. Honest logs
- `alive_cycle` includes `utter_reason=` when `uttered=False`  
- Metrics: speaks heard by TTS ok rate  

---

## 4. TODO list (ordered for Codex)

### P0 — Stop the silent “speak” lie (ship blocker)

| ID | Task | Files |
|---|---|---|
| **V0** | When `decision=speak` and utter is None: log **why** (llm_fail, empty, duplicate, no_callback) | `freewill.py`, `loop.py` |
| **V1** | Do **not** advance `last_speak_ts` until a real utterance string is produced (or intentional suppress) | `freewill.py` |
| **V2** | Fallback chain for speak: LLM → grounded non-duplicate template → static “I’m still here.” never pure silence on speak decision | `freewill.py` |
| **V3** | Daemon/API/avatar: **wire default utterance channel** — at least Windows notification + log file `utterances.log`; if `SEVEN_VOICE=1`, TTS via shared VoiceIO singleton | `daemon.py`, `avatar.py`, `loop.py` |
| **V4** | Fix launchers: `Start-Seven.cmd` = full talk; quiet must not pretend companion without voice policy documented; don’t set BACKGROUND_LLM=0 without grounded fallback that still utters | `D:\SevenLocal\*.cmd` + repo scripts |

### P1 — Real listen / talk product loop

| ID | Task | Files |
|---|---|---|
| **L1** | **Always-on listen mode** in `run_talk`: continuous loop with short timeouts; process speech; while TTS speaking, pause listen or barge-in | `talk.py`, `voice/io.py` |
| **L2** | Shared `CompanionRuntime` owning: agent, VoiceIO, on_utter, listen thread, heartbeat | new `seven/runtime/companion.py` |
| **L3** | Permission-to-speak: config `SEVEN_UNSOLICITED=ask|free|off` — ask once via TTS/notif before monologue bursts | freewill + companion |
| **L4** | Prove with test or script: mock STT/TTS; freewill speak → callback invoked | tests |
| **L5** | Install path: `--install-startup` defaults to talk with voice | `startup.py` |

### P2 — Growth / learning (so she isn’t random agent)

| ID | Task | Files |
|---|---|---|
| **G1** | After each user conversation turn: extract 0–2 durable preferences/facts (existing prefs + facts) | `preferences.py`, loop |
| **G2** | Freewill invent: prompt **must** use owner prefs + open goals + recent failures; ban pure random tidy | `freewill.py` |
| **G3** | “What I learned” episodic note daily; speak one sentence from it when idle speak fires | episodic + freewill |
| **G4** | Cap autonomous shell/download intensity; prefer learn/reflect/speak over thrash | freewill + autonomy |
| **G5** | Relationship/trust signal: ask before long monologues or invasive tools (L4 stays but social layer asks) | freewill / loop |

### P3 — Publish polish

| ID | Task |
|---|---|
| **P1** | Single “Seven is ready” checklist in README: install voice deps, mic privacy, run Start-Seven, hear greeting |
| **P2** | Smoke script: TTS speak test, STT optional, freewill utter callback unit test |
| **P3** | Deploy talk-capable local profile to D:\SevenLocal after P0–P1 green; Peanut web stays browser (voice local-first) |
| **P4** | CONTINUATION + HANDOFF updated: companion not agent-only |

---

## 5. Out of scope for this finish (do not distract)

- Sentience claims  
- Mesh remote L4  
- Full C: cleanup (separate)  
- Avatar lipstick without ear/mouth  
- New email/calendar as substitute for voice life  

---

## 6. Codex master prompt (paste)

```
You are finishing Seven as a LIVING COMPANION for publish — not another agent feature dump.

READ FIRST:
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\00_RESUME_AFTER_POWER_FAILURE.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\13_FINISH_COMPANION_ALIVE.md
seven/mind/freewill.py (_speak_thought)
seven/agent/loop.py (_autonomous_tick alive_cycle)
seven/ui/talk.py
seven/voice/io.py
D:\SevenLocal\Start-Seven.cmd
D:\SevenLocal\Start-Seven-Quiet.cmd

OWNER SYMPTOM (must fix):
Logs show: Freewill decision=speak but uttered=False repeatedly.
Text agent works. Companion must SPEAK and LISTEN. Growth not random thrash.

CURRENT TRUTH:
- Deployed core 1397d04 is fine for tools/memory honesty.
- Voice code exists but product wiring is broken / incomplete.
- listen_once is NOT continuous ambient listen yet.
- on_utter only set in talk/GUI — API/daemon/avatar free will is mute.

IMPLEMENT IN ORDER — ship vertical slices with tests:

WAVE A — P0 silent speak (do this first, one PR/commit)
1) V0–V2: speak decision never silent without logged reason; fix last_speak_ts; fallback utterance chain.
2) V3: any long-running process (daemon/api with freewill) gets an utterance sink (TTS if SEVEN_VOICE=1 else notification + utterances.log).
3) V4: fix Windows launchers so primary Start-Seven is real --talk with voice; document quiet/api.
4) Test: freewill speak path returns non-empty or explicit suppress reason; callback invoked in unit test.
5) Prove on machine: run talk or instrumented tick; log shows uttered=True OR utter_reason=...

WAVE B — P1 listen always
6) CompanionRuntime + continuous listen loop + barge-in policy
7) User speech → handle → TTS reply in same process
8) Optional SEVEN_UNSOLICITED=ask|free|off

WAVE C — P2 growth
9) G1–G5 learning/speak from memory; invent goals from prefs not noise

WAVE D — publish
10) Smoke script + README ready path + deploy local talk profile

RULES:
- Branch codex/seven-completion from current tip
- No sentience claims, no remote L4 mesh, no full rewrite
- L4 tools stay; add social "ask to speak / ask before heavy thrash" where specified
- Report every wave: Done / Evidence / Still broken / Next 3
- Do NOT claim "complete human" — claim "usable living companion" only when acceptance A–E in 13_ are evidenced

START WAVE A IMMEDIATELY. First reply = code, not essay.
```

---

## 7. Short whip

```
13_FINISH_COMPANION_ALIVE.md Wave A only.
Fix decision=speak uttered=False. Wire on_utter. Fallback speech. Log utter_reason.
Tests + local proof. No avatar fluff. Go.
```

---

## 8. Grok stance (not losing the plot)

She should be **more than an agent**: a **presence** that hears, speaks, and changes from experience.  
We already made the **agent honest**. What’s left is the **body in the room** (ear/mouth) and **growth** (learn → change).  

Your log is the smoking gun. Wave A is non-negotiable before any “published alive” claim.
