# Known limitations — Seven 4.4.0

Seven is high-authority local agent software, not a sandbox, security boundary, sentient being, or guarantee of correct model decisions. Audit records cannot reverse effects.

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

## Excluded from 4.4

Email, calendar, chat-network clients, PDF authoring, online music acquisition, ambient surveillance, continual LoRA training and v3 emotion/sentience theater are unsupported. Their sources remain quarantined and import-inert.

Subjective sentience cannot be established by a test suite. Seven does not
train or create a foundation model from ordinary conversations, and the
production updater remains operator-supervised so source authenticity, state
backup and rollback stay independently verifiable.

## Data

Backups protect Seven's SQLite state, not host/remote side effects. Skill rollback changes the future recipe and cannot undo prior actions. Semantic indexing does not guarantee perfect recall.
