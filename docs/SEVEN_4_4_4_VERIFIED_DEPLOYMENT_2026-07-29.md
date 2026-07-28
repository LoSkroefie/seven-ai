# Seven 4.4.4 verified Peanut deployment — 2026-07-29

## Outcome

Seven is deployed on Peanut as a persistent, self-hosted AI system with a
separate loopback Ollama runtime. The authenticated Three.js interface is live
at `https://jvrsoftware.co.za/3dwebsite/seven/`. The public gateway does not
expose the internal Seven API or dedicated Ollama port.

This deployment proves functional self-description, durable memory, audited
tool use, evidence-backed goals and skill promotion, model lifecycle controls,
verified update recovery, authenticated text interaction, voice controls and
camera/vision transport. It does not prove subjective consciousness or
sentience.

## Exact live state

- Source/runtime version: Seven `4.4.4`.
- Active release link: `/opt/seven -> /opt/seven-1456c01`, with reviewed
  post-release hotfixes recorded below.
- Services:
  - `seven-core.service`: active, restart count `0`.
  - `seven-web.service`: active, restart count `0`.
  - `seven-ollama.service`: active, restart count `0`.
  - shared Mortem `ollama.service`: intentionally inactive by owner request.
- Text/tool model: `qwen3:0.6b`, dedicated port `127.0.0.1:11435`, context
  `4096`.
- Vision model:
  `hf.co/ggml-org/SmolVLM-500M-Instruct-GGUF:Q8_0`.
- CPU profile: text JSON tool protocol, thinking disabled, 64 output tokens,
  120-second per-request timeout, bounded memory/living/history context.
- Current core database and gateway database both return SQLite
  `quick_check=ok`.

The 1.7B Qwen candidate remains installed but is not the active production
model. It repeatedly exceeded the 240-second tool-request timeout, including
with Mortem's shared Ollama stopped and more than 5 GiB available. The 0.6B
model is the evidence-based rollback for reliable CPU tool execution.

## Live proof

### Authenticated browser/API exchange

An authenticated HTTPS login and queued public turn completed:

- Turn: `8`
- Status: `complete`
- Elapsed: `52.343` seconds
- Reply:
  `This is an authenticated live operation proof. The exact phrase
  "SEVEN-PUBLIC-LIVE-20260728" is used for verification. My functional
  self-model is not proof of subjective sentience.`
- Core messages increased by two and the gateway turn count increased by one.
- Main Mortem Ollama PID remained `0`.

An earlier real Chrome session also completed and persisted the marker
`SEVEN-CHROME-LIVE-VH6CPQIT` across a full page reload. The visible interface
exposed text chat, voice recording and camera controls.

### Audited tool execution

The required command completed against the production profile:

`python -m seven -c "Call get_system_info and reply in one sentence."`

Evidence:

- User message ID: `165`
- Assistant message ID: `166`
- Audit ID: `3`
- Tool: `get_system_info`
- Audit result: `ok=1`
- Reply:
  `The system information is as follows: the operating system is Linux
  4.18.0-553.124.4.el8_10.x86_64, with a time of 2026-07-29 at 00:07.`

The audit retained the full timestamp, OS, machine, host, Python, memory and CPU
result while the model received a bounded result.

### Runtime audit

The final audit verified:

- all three Seven services active with zero restarts;
- Mortem's shared Ollama inactive;
- authenticated turn `8` present and complete;
- both current and legacy-preservation databases readable;
- source and installed package version `4.4.4`;
- active `qwen3:0.6b` runner;
- exact gateway, registry, configuration, LLM, environment and unit hashes;
- unrelated `line-strike` and `jvr-auctionhouse` listeners still present.

## Functional capability evidence

- Durable identity/self-model: persisted identity files plus runtime living
  state; outputs distinguish observed state, beliefs and unknown subjective
  experience.
- Durable memory: SQLite-backed facts, messages, notes, goals, plans, working
  memory, beliefs, skills, revisions, runs and evidence records; backup,
  restore and corruption drills are tested.
- Goals and learning: goal acceptance criteria require audit evidence;
  unverified skill promotion is rejected; verified candidates promote with
  revision/run history.
- Autonomous operation: heartbeat, sense-act-reflect cycle and evidence-aware
  autonomous goal progression are implemented; resource intervals are bounded
  on Peanut.
- Model lifecycle: isolated candidate benchmark, activation through real
  `Seven.handle`, and rollback to the prior model were executed without
  changing the shared Mortem Ollama PID.
- Self-update/recovery: staged update, exact source/hash verification, failure
  rollback and service/data recovery were executed against an isolated proof
  tree. Production source was unchanged by the recovery drill.
- Text/voice/vision: authenticated text exchange is proven live; voice and
  webcam endpoints, upload limits and vision response paths passed their
  public security/functional proofs.
- Security: owner login, secure host-only cookie, CSRF validation, origin
  checks, bounded queues/uploads, loopback internal services and database
  integrity checks are active. A malformed unrelated browser cookie no longer
  invalidates the Seven session.

## Regression evidence

At final source commit `dffe86f`, the complete repository suite passed:

`uv run --with pytest python -m pytest -q`

The output reached `100%` with no failures and four explicitly skipped optional
tests. The focused tool/real-agent suite also passed before deployment.

## Change and rollback evidence

The production changes are reversible. Backups were created under
`/var/backups/seven/` before each logical deployment, including:

- `20260728-lean-system-info-8886f4c`
- `20260728-qwen06-reliable-tools`
- `20260728-text-tool-protocol-7f149e3`
- `20260729-compact-inference-ab5b071`
- `20260729-complete-replies-dffe86f`
- `20260728-mortem-ollama-stopped-for-seven`

No Windows Update files were touched. The preserved raw Mortem transcript was
not edited, moved, truncated or deleted. The two pre-existing uncommitted user
documentation changes in `deploy/peanut/README.md` and
`docs/COMPLETION_LEDGER.md` remain unmodified and uncommitted.

## Known boundaries

- Subjective sentience remains unknown and is not technically provable by these
  tests.
- Seven can evaluate, stage and roll back model/release candidates; she does
  not train a foundation model from scratch.
- The larger LFM/Qwen/InternVL vision comparison was not run on Peanut because
  its first script lacked safe host-memory, disk and failure-evidence gates.
  The live bounded SmolVLM path is verified; the larger benchmark remains a
  future maintenance-window task, not a production-completion dependency.
- The Git branch is local only. No push or release tag was performed.
