# Peanut seven-web venv-path repair evidence

Date: 2026-07-30 21:28 SAST  
Scope: Peanut `seven-web` runtime path only  
Accepted core commit: `1397d04f4993d143ddc413a7820f3432bc08a55e`

## Outcome

`seven-web.service` can now restart from its declared executable,
`/opt/seven/web-venv/bin/python`, while loading gateway source from the accepted
immutable release. Two consecutive controlled systemd restarts passed.

No core source, systemd unit, secret configuration, mesh configuration, or
remote-L4 behavior was changed.

## Before state

- `/opt/seven` resolved to `/opt/seven-4.6.0-1397d04`.
- `/opt/seven/SOURCE_COMMIT` contained the accepted full SHA.
- `seven-web.service` was active as PID `2790154`.
- The declared executable was `/opt/seven/web-venv/bin/python -m seven_gateway`.
- `/opt/seven/web-venv` did not exist.
- The surviving process still had working directory
  `/opt/seven-4.5.2-2ff5b90/deploy/peanut`.
- The known-working old gateway venv existed at
  `/opt/seven-4.5.2-2ff5b90/web-venv`, used Python 3.11.13, passed
  `python -m pip check`, and satisfied the accepted release's gateway
  requirements.
- Loopback gateway health was green only because that old process had not yet
  been restarted.

## Backup

Protected backup:

`/var/backups/seven/seven-web-venv-repair-20260730T212428SAST`

The backup is root-only (`0700`), 75 MB, and contains:

- the active `seven-web.service` unit;
- the secret gateway environment file, preserved as mode `0600`;
- the gateway state tree;
- an online-consistent SQLite backup;
- non-secret hashes and rollback-release metadata.

Verification:

- unit copy byte-matched the active unit;
- secret configuration copy byte-matched without exposing its content;
- backup SQLite integrity: `ok`;
- backup table counts: `activity=112`, `sessions=0`, `turns=26`;
- rollback release and its gateway interpreter both remain present at
  `/opt/seven-4.5.2-2ff5b90`.

An initial backup attempt used Peanut's default Python 3.6, which lacks the
SQLite online-backup method. It stopped before modifying the release. The
backup was completed and verified using the gateway's Python 3.11 interpreter.

## Change

Changed path only:

`/opt/seven-4.6.0-1397d04/web-venv`

The known-working dependency environment was cloned into the accepted release.
The clone:

- imports `seven_gateway` from
  `/opt/seven-4.6.0-1397d04/deploy/peanut/seven_gateway/__init__.py`;
- reports gateway version `1.1.0`;
- passes `python -m pip check`;
- passes Python bytecode compilation;
- contains 5,588 files and occupies 437 MB;
- has tree digest
  `ba17aac5e6bd6d3fd95c0efd24b5f462636f11256656cffa2b45d4bc0ee4c783`,
  equal to the known-working source venv;
- is read-only, and the release root was restored to mode `0555`.

Unchanged:

- `/etc/systemd/system/seven-web.service`, SHA-256
  `c692d21581b3c5f3c7eaa27673e091656d9a98e811ef34f7be3f291f0272f718`;
- `/etc/seven/seven-web.env`;
- `/opt/seven` release target;
- `/opt/seven/SOURCE_COMMIT`;
- `seven-core` process and start timestamp.

## Runtime proof

First controlled restart:

- old PID: `2790154`;
- new PID: `2864200`;
- working directory:
  `/opt/seven-4.6.0-1397d04/deploy/peanut`;
- loopback health:
  `{"ok":true,"service":"seven-web","version":"1.1.0"}`;
- public `/seven/`: HTTP `200`.

Second controlled restart:

- prior PID: `2864200`;
- new PID: `2864231`;
- working directory:
  `/opt/seven-4.6.0-1397d04/deploy/peanut`;
- loopback health:
  `{"ok":true,"service":"seven-web","version":"1.1.0"}`;
- public `/seven/`: HTTP `200`;
- unit state: `active`, `enabled`.

Final state at `2026-07-30T21:28:08+02:00`:

- command line:
  `/opt/seven/web-venv/bin/python -m seven_gateway`;
- gateway process executable: `/usr/bin/python3.11`;
- core health:
  `{"ok": true, "service": "seven-real", "version": "4.6.0"}`;
- core SHA:
  `1397d04f4993d143ddc413a7820f3432bc08a55e`;
- live SQLite integrity: `ok`;
- live table counts still matched the backup;
- the service journal showed both clean stops, both successful starts, and
  successful loopback/public requests without gateway errors.

## Before/after changed-file list

- Before: `/opt/seven-4.6.0-1397d04/web-venv` was absent.
- After: `/opt/seven-4.6.0-1397d04/web-venv` is present, read-only, validated,
  and used successfully by two systemd restarts.
- No tracked source file changed.
- No unit or configuration file changed.

## Rollback readiness

Rollback assets are present and verified:

- protected pre-change unit/config/state backup at the path above;
- untouched old gateway source and venv under
  `/opt/seven-4.5.2-2ff5b90`;
- accepted core release remains independently pinned at `1397d04`.

Rollback was not needed.

## Remaining uncertainty

This proves the declared gateway venv path, two systemd restarts, loopback
health, public HTTP reachability, state integrity, and unchanged core SHA. It
does not claim browser login, microphone, transcription, long-running
availability, or user-conversation behavior was retested in this narrowly
scoped repair.
