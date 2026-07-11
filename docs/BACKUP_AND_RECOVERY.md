# Backup and Recovery

Seven stores runtime data under `SEVEN_DATA_DIR` (default `~/.seven`). Backups contain an online-consistent SQLite copy plus other runtime state, a manifest, byte sizes and SHA-256 hashes.

## Create

```text
python -m seven --backup
```

Archives are written under `SEVEN_DATA_DIR/backups`. Seven retains the latest seven. The backup is verified immediately; a failed archive is deleted rather than reported as successful.

## Verify

```text
python -m seven --verify-backup /path/to/seven-backup-TIMESTAMP.zip
```

Verification checks ZIP integrity, safe member names, manifest membership, sizes and SHA-256 hashes.

## Restore

Stop all Seven GUI, talk, CLI and daemon processes, then run:

```text
python -m seven --daemon-stop
python -m seven --restore-backup /path/to/seven-backup-TIMESTAMP.zip
```

Restore refuses to run when the recorded daemon is active. It verifies the archive and creates a pre-restore safety backup before copying files into the data directory.

The safety archive is stored beside the data directory under `seven-pre-restore-backups`. If a non-daemon Seven process is still running, close it before restore; those processes do not currently publish a shared runtime lock.

## Provenance

This replaces `_legacy/v3/extensions/auto_backup.py`. The legacy extension zipped live files, silently skipped files over 50 MB and had no integrity manifest or restore path. The modern implementation uses SQLite's backup API and verifies every archived file.
