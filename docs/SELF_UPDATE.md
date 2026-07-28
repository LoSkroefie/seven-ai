# External self-update supervisor

Seven does not replace its own running process. Updates are performed by the
operator-owned `scripts/seven_update_supervisor.py` process, which is not
registered as an LLM tool.

## Transaction model

1. Clone the requested source/ref into an isolated staging directory.
2. Resolve and record the exact commit.
3. Run every configured test command.
4. Run a candidate import/health command.
5. For `apply`, move the verified candidate into the immutable `releases/`
   directory and save the prior `current.json` pointer under `backups/`.
6. Atomically replace `current.json`, restart the service, and check live
   service health.
7. If restart or live health fails, atomically restore the old pointer, restart
   the old release, and verify rollback health.

Failed candidates remain inactive. Successful old releases remain on disk for
rollback. Transaction reports contain command arguments, return codes, timeout
state, and SHA-256 hashes of stdout/stderr without copying arbitrary command
output into the audit file.

## Modes

- `plan`: calculates paths and steps; performs no filesystem or command work.
- `dry-run`: isolated checkout, tests, and candidate health only; no pointer or
  service changes.
- `apply`: requires explicit restart and service-health commands.

Example dry run:

```powershell
python scripts/seven_update_supervisor.py dry-run `
  --root C:\SevenSupervisor `
  --source C:\src\seven-ai `
  --ref main `
  --release-id candidate-20260728
```

Example application with Windows service commands:

```powershell
python scripts/seven_update_supervisor.py apply `
  --root C:\SevenSupervisor `
  --source C:\src\seven-ai `
  --ref main `
  --release-id seven-4.5.0 `
  --restart-command "powershell -NoProfile -File C:\ops\restart-seven.ps1 {release}" `
  --service-health-command "powershell -NoProfile -File C:\ops\health-seven.ps1"
```

Use equivalent fixed-argument `systemctl` wrappers on Linux. Commands are
executed without a shell. The service launcher should call
`resolve_active_release()` or read the validated `current.json` pointer before
starting Seven.

## Safety boundaries

- The supervisor directory must be writable only by the deployment operator.
- Source/ref and commands are operator configuration, never model-generated
  tool arguments.
- The web gateway and Seven's LLM tool registry must not expose this CLI.
- Production `apply` must use a health command that proves the new service
  answers through its real local endpoint, not only that Python imports.
- Keep the previous release until a post-deployment soak has passed.
