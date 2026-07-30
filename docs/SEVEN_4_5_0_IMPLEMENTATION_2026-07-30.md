# Seven 4.5.0 implementation and validation — 2026-07-30

## Outcome

Seven 4.5.0 restores the useful continuity mechanisms found in older builds and
adds a lightweight Windows desktop body without loading an image or language
model merely to animate it.

## Logical change set 1 — persistent mind

Added:

- SQLite schema v7 tables for affect state/events, owner relationships and
  reflections;
- deterministic affect appraisal and time decay;
- persistent relationship depth, trust, rapport, user mood and shared
  experiences;
- post-turn evidence-backed reflection;
- prompt, living-state, slash-command, tool and API wiring;
- grounded replies for greeting, identity, location, functional state,
  capabilities and invitations to ask a question;
- identity documents that tell Seven who Jan is and define the resource/model
  boundary.

The direct grounded routes do not call an LLM and therefore remain available
when a local model is slow or offline.

## Logical change set 2 — floating desktop Seven

Added:

- an eight-pose, identity-consistent transparent sprite sheet;
- an always-on-top draggable Windows companion;
- state-driven pose selection for idle, welcome, thinking, determination,
  concern, speaking, listening and amusement;
- subtle low-frequency breathing/bobbing;
- live CPU/RAM, activity and affect display;
- right-click mind status and chat;
- double-click chat using the same Seven object, memory, heartbeat and API;
- `python -m seven --avatar --api`;
- Windows quiet-startup convergence onto one avatar/API process.

There is no background image generator and no second Seven brain process.

## Logical change set 3 — constrained-host reliability

Added:

- `SEVEN_BACKGROUND_LLM=0` mode: heartbeat/free-will remains active but does not
  spend server inference on autonomous goal invention/work/speech;
- daily digest summarization and queued-plan execution also respect that
  boundary, closing the two remaining background inference paths;
- deterministic proactive speech from current affect and intent in that mode;
- Peanut example context increased from 1536 to 2048, response budget from 64
  to 160 and timeout from 75 to 180 seconds;
- model failures no longer advise loading a hard-coded `llama3.2` model;
- `/mind` API route;
- tool count updated to 120.

## Resource boundary

During this implementation:

- no local or Peanut model was loaded, unloaded, pulled, switched, benchmarked
  or asked to generate a response;
- the already loaded Mortem model on Windows was left untouched;
- the dedicated Peanut Ollama service was inspected through metadata only.

## Automated and Windows validation

- the complete automated suite passed: `214 passed`;
- the 4.5.0 wheel passed package-content verification;
- an isolated 4.4.4 -> 4.5.0 install/upgrade/uninstall lifecycle passed;
- that lifecycle proved runtime and package version `4.5.0`, all four identity
  files, SQLite schema migration 5 -> 7, API health, console-script removal
  after uninstall and dependency consistency;
- the wheel was installed into `D:\SevenLocal` without changing dependencies,
  data, workspace, browser profile, mail credential store or Ollama;
- Windows now runs one logical `python -m seven --avatar --api` runtime on
  `127.0.0.1:18765`; the old port 7777 listener is absent;
- live `/health` returned Seven `4.5.0`;
- authenticated `/mind` returned persistent affect and owner relationship
  state;
- authenticated direct conversation returned:
  `Hi, Jan. I’m here on Terminal2. I’m calm and ready to continue with you.`;
- a second direct state turn returned calm/curious state with persisted
  relationship interaction count `2`;
- the desktop avatar was visually verified on the Windows desktop using the
  same live Seven process.

No model inference was used for those conversation proofs.

A successful build or grounded direct reply is not treated as proof that
Peanut model conversation quality is good; that still requires an explicitly
permitted model-backed live chat test.

## Peanut deployment proof

The immutable release was deployed from Git commit
`4791bac706336da9227808fc729c7e1b8018cf89`.

- active release: `/opt/seven-4.5.0-4791bac`;
- source archive SHA-256:
  `b6ac73982a3422b0e4e6f96af6cc745cae5c5cfe1b75b624eae905b43b74e1a8`;
- wheel SHA-256:
  `cae3eda173ab1aca34b030ce6a375f09a075a197a7def8deacefa985fed5deba`;
- previous release remains at `/opt/seven-voice-20260729-ac532c0`;
- previous core environment remains at
  `/etc/seven/seven-core.env.before-4.5.0-4791bac`;
- `seven-core`, `seven-web` and dedicated `seven-ollama` services are active;
- public `https://jvrsoftware.co.za/seven/health` returned the healthy web
  gateway and `/seven/` returned HTTP 200 with the 4.5.0 page;
- stale unauthenticated `seven-ai.service` was disabled after modern direct
  reply proof; its files were preserved and public port 7777 is closed.

The live core environment now has:

- owner name `Jan`;
- background LLM work disabled;
- tool tier `lean`, dispatcher schema mode and all 120 tools registered;
- response timeout 180 seconds;
- maximum response budget 160 tokens;
- context budget 2048 tokens.

Authenticated non-model smoke proof:

- `/health` returned `4.5.0`;
- `/mind` returned persistent affect and relationship state;
- `hi` returned
  `Hi, Jan. I’m here on peanut.dedicated.co.za. I’m calm and ready to continue with you.`;
- `list my current projects` returned the real catalog, including IRC admin and
  chat, JVR Auction World, Line Strike, Seven, SubmitJoy TV Room and Video Den;
- the owner relationship persisted four verification interactions;
- the dedicated Ollama model list, digest, context and zero-VRAM state were
  identical before and after both direct turns.

## Backup and state proof

The failed daily backup was traced to one preserved database snapshot that was
root-owned. Only that file's ownership and mode were corrected; its SHA-256
remained
`53b2582857779a9880650f004719b948cf8dda7fa4e93ec04762ef883b1fca38`.

After deployment:

- SQLite integrity: `ok`;
- schema version: `7`;
- message rows: `89`;
- project rows: `10`;
- relationship rows: `1`;
- reflection rows: `1`;
- verified backup:
  `/var/lib/seven/backups/seven-backup-20260730T012049673798Z.zip`;
- backup SHA-256:
  `f870959ca853975c4f5f7dac33e5e1a90e4becacb64e91adcac5f237d96d01d5`.

## Remaining proof boundary

The deterministic identity, mind, project, API, package, service, backup and
avatar paths are proven. General model-backed conversation, vision, speech
quality, long-running autonomy and a 24-hour soak were deliberately not
exercised in this pass because doing so would have invoked or disturbed model
resources. They remain test items, not claimed successes.
