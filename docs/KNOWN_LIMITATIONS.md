# Known limitations — Seven 4.6.0

Seven is high-authority local agent software, not a sandbox, security boundary,
sentient being, or guarantee of correct model decisions. Audit records cannot
reverse effects. Seven is not proven conscious or sentient, and the project is
not complete.

## Runtime, authority and privacy

- Ollama is external and must run for the default experience; model downloads/licenses are not bundled. Small models can produce malformed calls or poor decisions.
- Full-tier tools can execute commands, alter files, operate input devices, use camera/microphone/SSH, move robots and invoke external coding agents.
- Loopback API tokens authenticate local HTTP calls but do not isolate Seven from the logged-in account or same-user malware.
- Continuous ambient microphone/camera capture is intentionally absent. Talk/vision actions are explicit.
- Secrets inside arbitrary command text cannot be classified perfectly. Skill validation rejects credential-shaped argument keys but is not a data-loss-prevention system.

## Platform and hardware

- CI covers Windows and Ubuntu lifecycles; macOS paths are unit-tested without a hosted install/hardware matrix.
- Physical audio, camera, multi-monitor, GPU and robot results depend on named devices/drivers. Emulator and silent-backend tests are not physical proof.
- Robot motor firmware returns `MOTOR_DRIVER_NOT_CONFIGURED` until the owner configures real pins/driver.
- Notification backend acceptance does not prove a person saw it. Playwright requires a separate browser-engine installation; control of an existing signed-in Chrome session is not claimed.
- Long-duration recovery across sleep, GPU-driver resets and Ollama updates is not proven for every host.
- The Windows install wrapper has a no-write dry-run and the wheel has an
  isolated lifecycle proof. A real second-machine Windows run remains owner
  acceptance.
- The Unix wrapper was not executed on this Windows host because its WSL disk
  attachment was unavailable. It remains subject to a real Unix-shell run.

## Current production and evaluation boundaries

- Local and Peanut deployments are pinned to core SHA
  `1397d04f4993d143ddc413a7820f3432bc08a55e`. Documentation-only branch commits
  may be newer without changing production.
- Peanut uses a constrained host profile. Local and Peanut model/schema
  overrides must not be mistaken for source defaults.
- Mesh is authenticated data/presence/relay messaging only. It does not merge
  memory or identity, and it never grants remote L4 tool execution.
- The Peanut gateway venv path and two service restarts are proven. Browser
  login, microphone, transcription, and owner-conversation behavior were not
  retested by that narrowly scoped repair.
- The owner-browser smoke test after the 1397d04 deploy remains optional and
  unproven in the deployment evidence.
- C-drive cleanup is deferred. `docs/orchestration/11_CLEANUP_AND_GIT_PRESERVE.md`
  is an order document, not evidence that cleanup occurred.
- Continual LoRA/foundation-model training and v3 emotion/sentience theater are
  unsupported. Historical sources remain quarantined and import-inert.

Subjective sentience cannot be established by a test suite. Seven does not
train or create a foundation model from ordinary conversations, and the
production updater remains operator-supervised so source authenticity, state
backup and rollback stay independently verifiable.

## Data

Backups protect Seven's SQLite state, not host/remote side effects. Skill rollback changes the future recipe and cannot undo prior actions. Semantic indexing does not guarantee perfect recall.
