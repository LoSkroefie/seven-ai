# Seven on Peanut: operator runbook

This runbook covers the production boundaries around the Seven services on
Peanut. It does not grant the language model root access and does not describe
subjective consciousness.

## Services

The supported service set is:

- `seven-ollama.service`: dedicated loopback Ollama runtime.
- `seven-core.service`: Seven's authenticated loopback API and continuously
  running heartbeat.
- `seven-web.service`: low-authority public owner gateway.
- `seven-backup.timer`: operator-owned daily verified state backup.

`seven-core` and `seven-web` must never expose their loopback ports directly.
Apache publishes only the owner gateway at `/seven/`.

## Install the backup timer

Install the committed unit files as root, then enable the timer:

```text
install -m 0644 deploy/peanut/systemd/seven-backup.service /etc/systemd/system/
install -m 0644 deploy/peanut/systemd/seven-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now seven-backup.timer
systemctl start seven-backup.service
systemctl status seven-backup.service seven-backup.timer
journalctl -u seven-backup.service --no-pager -n 100
```

The backup service runs as the unprivileged `seven` account, reuses the
production environment file, writes only under `/var/lib/seven`, and calls the
same verified backup implementation as `python -m seven --backup`. A successful
command creates an archive, hashes every included file, verifies ZIP integrity,
and verifies the manifest before reporting `ok`.

The timer is persistent: a missed daily run is executed after the host returns.
The randomized delay prevents all maintenance from starting at exactly
midnight.

## Recovery

Do not automate restore. A human operator must:

1. Stop `seven-core.service`.
2. Run
   `sudo -u seven env SEVEN_DATA_DIR=/var/lib/seven /opt/seven/venv/bin/python -m seven --verify-backup PATH`.
3. Preserve the current state with a separate forensic copy if corruption is
   suspected.
4. Run
   `sudo -u seven env SEVEN_DATA_DIR=/var/lib/seven /opt/seven/venv/bin/python -m seven --restore-backup PATH`.
5. Start `seven-core.service`.
6. Prove loopback health, public gateway health, SQLite integrity, a real owner
   message/reply, and service restart counts.

Restore protects Seven's owned state. It cannot undo shell commands, remote
changes, deleted host files, or other external side effects.

## Releases and self-update

Seven may inspect, benchmark and stage candidates, but the language model does
not own production activation. Production release activation remains an
operator action:

1. Back up and verify state.
2. Stage an immutable release directory.
3. Record source commit and file hashes.
4. Run the complete local/installed test gates.
5. Switch `/opt/seven` atomically.
6. Restart the affected service set.
7. Prove local and public health plus a real owner exchange.
8. Restore the previous symlink and restart if any gate fails.

This boundary is deliberate. An unrestricted self-modifying updater cannot also
guarantee rollback, source authenticity, data preservation and service
recovery.

## Model changes

Text and vision models are separate production roles. A candidate is promoted
only after fixed-corpus quality checks, cold/warm latency, memory/cgroup and swap
measurements, restart persistence, and rollback proof. An installed model is
not automatically a production model.
