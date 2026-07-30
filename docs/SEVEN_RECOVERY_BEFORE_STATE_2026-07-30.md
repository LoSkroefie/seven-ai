# Seven recovery before-state — 2026-07-30

This is the edit gate for the recovery of Seven's lost personality, affect,
relationship, reflection, autonomy, and desktop-companion behavior.  It records
the state before this recovery changes production code.

## Safety boundary

- No local or Peanut model was loaded, unloaded, benchmarked, pulled, or run for
  this audit.
- Existing Mortem Ollama state was observed only.
- The legacy Seven trees and raw backups listed below are read-only evidence.
- Production changes belong under `seven/`; `_legacy/v3/` remains reference
  material.
- Two pre-existing user changes are preserved and excluded from this change:
  `deploy/peanut/README.md`
  (`1F627C5CAEA675469BBA31BBC7549C583415FC3BF3E5EE1B8C4CE5CF233A4929`)
  and `docs/COMPLETION_LEDGER.md`
  (`85D87D51456FF1DE921C7EEB8457DB68AA979C546B926CFDF8F4FF0A25137643`).
- No credential values are recorded in this document.

## Current repository

- Repository:
  `C:\Users\USER-PC\Documents\Codex\2026-07-20\mortem-continues\seven-ai`
- Branch: `codex/seven-completion`
- Before commit: `2a1e36adc883e0fea689470f8b027e30365f349f`
- Remote branch matched the before commit.
- Hidden/dot content was included in the inventory.  The complete tree contained
  24,594 files, of which 654 were Git-tracked; most untracked hidden content was
  the local virtual environment and caches.

## Historical evidence found

The search covered the active repository, Downloads, Documents, the organized
desktop archive, the old `voice-chat/python-chat-bot` family, pre-enhancement
snapshots, distribution copies, output copies, and `D:\SevenLocal`.

Representative roots:

- `D:\DOWNLOADS\Seven-AI-v2.0-Complete`
- `D:\DOWNLOADS\Seven-AI-v3.2.9 (1)`
- `D:\DOWNLOADS\Seven-AI-v3.2.13`
- `D:\Desktop Organized 2026-07-14\Other Projects\seven-ai`
- `D:\Desktop Organized 2026-07-14\Other Projects\Seven-Backup-2026-02-19`
- `D:\Desktop Organized 2026-07-14\Other Projects\backups_2026-02-20_0010\seven-ai-backup`
- `D:\Desktop Organized 2026-07-14\User Folder Projects\Other Projects\source\Code\SEVEN-BACKUP-2026-02-08-011955-PRE-ENHANCEMENTS`
- `D:\Desktop Organized 2026-07-14\User Folder Projects\Other Projects\source\Code\SEVEN-BACKUP-20260208-013254-PRE-COMPLETE-ENHANCEMENT`
- `D:\Desktop Organized 2026-07-14\User Folder Projects\Other Projects\source\Code\SEVEN-COMPLETE-BACKUP-20260207-PRE-UPGRADES`
- `D:\Desktop Organized 2026-07-14\User Folder Projects\Other Projects\source\Code\voice-chat\python-chat-bot`
- `C:\Users\USER-PC\Documents\Seven`

The important result is not the number of copies but the small number of unique
lineages.  The common v3.2.13 lineage is stable across many backups:

| Capability evidence | Representative SHA-256 | What is worth recovering |
|---|---|---|
| `persistent_emotions.py` | `8EDD87E806CBD91A1E07A5288C0605C86785BDD8A7BF4A6F033B16C38A95DD93` | Durable affect, decay, timeline, baselines |
| `relationship_model.py` | `9CFCB005776B7E378FBE73B54666DC6471549DF849D58C6C35E7422B0476C817` | Trust, rapport, interaction history, shared experiences |
| `emotional_memory.py` | `098559BAF9524E0269C8FCDCEFB88E6D79525159B79235E50E7486C67DD4D3BA` | User mood and evidence-backed triggers |
| `self_reflection.py` | `E3118AF05964DF6410F2A7D2E34F5DF35B145D5E175D3D07FF77C4E2451C6FD6` | Outcome-based lessons and effectiveness |
| `reflection_system.py` | `91DCB4F70B50D3322CCAB823817BB99A21B2A1583183536DC30D9220993BBA28` | Post-turn reflection and actionable insights |
| `autonomous_life.py` | `DA1361E5EFF476649D0435B5C4C29882E7CAB6C0F969AD609F4DBB3762C7793C` | Health, goals, promises, presence, away activity |
| `seven_true_autonomy.py` | `AB2280B6A207DF861F9E4F4DBBB966764A6487C113B0B70045DE717A94DFB77C` | Research and self-directed work patterns |
| `dream_system.py` | `4EE0B0265E1671F9CCA390BE0ADCFCAF77765B0D0CD1E31ECC8AC9F30DC703DC` | Memory consolidation and pattern discovery |

The old implementations also contain random phrase selection, unproved
"sentience" claims, simulated progress, and template dreams.  Those parts are
not recovery candidates.  The modern replacement must be deterministic,
evidence-backed, persisted in Seven's SQLite memory, and honest about not
proving subjective consciousness.

The floating-companion design was recovered from
`MemoryForgeUltimateDashboard\ResourcePetWindow.cs`, SHA-256
`E9916C3BB55F22FB7D8DA9A4AC75B9BF56625195E6C948345130E9EC20BA1F86`.
Useful behavior is: transparent always-on-top window, drag positioning,
breathing/hover/sway motion, live status, state-dependent poses, scaling, and a
hide menu.  Seven's implementation will use live Seven state rather than random
pose selection.

## Live Windows state

- Local install: `D:\SevenLocal`.
- Local API health returned Seven Real `4.4.4` on loopback port 18765.
- A quiet Seven process and a separate API-only Seven process were both active.
  They can concurrently write the same state and must be consolidated.
- Ollama was active on port 11434 with a Mortem model already loaded.  It was
  left untouched.
- Startup launched `python -m seven --quiet` with a full tool tier.
- The startup configuration selected a 7B text model and a small on-demand
  vision model.  No model inference was run during this audit.

## Live Peanut state

- `/opt/seven` resolved to `/opt/seven-voice-20260729-ac532c0`.
- `seven-core`, `seven-web`, and Seven's dedicated loopback Ollama service were
  active.
- Dedicated Ollama: `127.0.0.1:11435`, CPU-only, one model and one parallel
  request maximum.
- Configured text model: `qwen3:0.6b`; configured context: 1536 tokens;
  configured Seven timeout: 75 seconds.
- Repeated real requests were truncated from about 2,070 prompt tokens to 1,536
  and failed after exactly 75 seconds.  This directly explains the incoherent
  or absent web replies; latency alone is not the only defect.
- A separate legacy `seven-ai.service` was still running
  `/opt/seven-ai/backend/seven_server.py` on public port 7777 and targeted the
  wrong Ollama port/model.  It is not the modern runtime.
- `seven-backup.service` was failed because a root-owned proof database file
  under `/var/lib/seven` could not be read by the Seven service account.
- The model inventory and loaded-process endpoint were read only.  No inference
  or model lifecycle action was taken.

## Exact code manifest before recovery

| Path | Bytes | SHA-256 |
|---|---:|---|
| `seven/memory/store.py` | 59549 | `7D7BC0D7CD39F5181ADBC015D834CAABA2858B1688829AF797A5F74CEC7B3C63` |
| `seven/mind/state.py` | 5910 | `704976E6D3C01AC3E81FD4B46B4E9F9089B91B27C46E99BD984DB2FE5C8C450D` |
| `seven/mind/self_model.py` | 3616 | `537530A925A490981ED18C1A1EBF9A36345BE0A0EAACAC36FAB53CAE3F5B614F` |
| `seven/mind/freewill.py` | 14800 | `63A96FB8DCFFCF7B1FB94FB52FF7EEBBB55726668F244CE90A9FDE125FB24E0C` |
| `seven/agent/loop.py` | 40553 | `958246A73215C8B4C5C1E7FDFFB67A9DF3F6062F275B32897E8B6B049AEFE43F` |
| `seven/agent/prompt.py` | 5106 | `11CA92C6735726763FA820B3D05C6B29752A692134AEF7BCE9391E19E9CEED8E` |
| `seven/tools/mind_tools.py` | 15588 | `54E1D89533CBF73384A39356C952E8C7AA109AB27E0DD647D29A956EE5F0FF7D` |
| `seven/tools/registry.py` | 10865 | `31D70053E3E6352F0F425B1ACD62CB2370FD853FA41408FC87F38B8F0A93E584` |
| `seven/ui/api_server.py` | 17415 | `E0318CFBBEA1D8BB40F0E89DAE6989FDBE416B9A06A3027B91DD1087C2899C04` |
| `seven/ui/desktop.py` | 1181 | `2500D16CAF20901C42655B194E21C7661743E75C7D966408B71C6311762443E8` |
| `seven/ui/talk.py` | 8548 | `D147A3B2B65951839A1059620B9693C2E17797849A04D20B80C42A196F0B2FCE` |
| `seven/runtime/startup.py` | 4745 | `7B2D79650D3A35CA1F33899DE082AC95E48A445EC6F5C5F93BCFFB45BA31A92E` |
| `seven/runtime/backup.py` | 8766 | `D6AE7A36E6F12778DEF56C779227C11A41DD4231F327732057356F5ED87C158D` |
| `seven/__main__.py` | 16695 | `B12FEBDA1F29574A0BC2B98A2DA75B1AAE3B8D1C36EC53B1CCB20E079B84FC50` |
| `seven/config.py` | 11852 | `DD32ED1EFEE1A28ECD1546A81CADF9AD53CFECFEB4ACD669E8ADC62B8A531890` |
| `seven/identity/IDENTITY.md` | 236 | `BFB11F6D9964A47DBD072CE46BB12EB3E7DC9C967FBDE4FBC6845DC6D28446DF` |
| `seven/identity/SOUL.md` | 388 | `954CBA1C5B52500CE393ABA12FB3E6A6294884B8F65166EB5CADBD55F6DEC47C` |
| `seven/identity/USER.md` | 281 | `67ABB16BD550DB5D886968F835A88CB8D78AA24C932CF81FB3C40334F4C28EBD` |
| `seven/identity/TOOLS.md` | 734 | `A592F3FB20C38A9A638068FFFE183CF032BE7A28E669BFD99275163062D17B7E` |
| `tests/test_seven_real.py` | 30196 | `BEDD6D457F2C931DD87A9AE9BD1E4D4653B1B17C03D1EAF48322CC266FE8D4D6` |
| `tests/test_startup.py` | 2728 | `341506FE104DB81E0C0EEFA3C355067255C1C3D85FA3BBF205DC76F5B36B4675` |
| `tests/test_api_lifecycle.py` | 9457 | `5291C4606EA3F113330426EF8043E186D5FAF79C941787647AFCE2A3741E108C` |
| `tests/test_backup.py` | 2349 | `4FC6A3B433A541D67A5D1BBF2294E6CF3251A985B2DB62417C905045E2E9A340` |

## Recovery decisions

1. Restore durable affect, relationship memory, reflection, and needs/drives as
   modern deterministic state, not legacy random speech.
2. Use real message/tool outcomes as appraisal evidence.
3. Put durable cognitive state in Seven's existing SQLite memory and expose a
   bounded summary to the prompt and API.
4. Tie the desktop companion's image, motion, and status to live affect,
   activity, resource, and brain states.
5. Keep one local Seven owner process; do not let the pet become a second brain.
6. Fix Peanut's timeout/prompt mismatch and failed backup only after code and
   mocked tests pass.  Do not infer production success from compilation.
