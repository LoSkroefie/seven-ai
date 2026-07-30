# Seven Peanut deployment evidence

- Target: Peanut `/opt/seven`
- Deployed SHA: `1397d04f4993d143ddc413a7820f3432bc08a55e`
- Active release: `/opt/seven-4.6.0-1397d04`
- Deployment time: 2026-07-30 SAST
- Secrets, tokens, passwords, environment values, credential contents, and secret-file hashes are omitted.

## Backup before switch

- Archive: `/var/lib/seven/backups/seven-backup-20260730T190251932721Z.zip`
- SHA-256: `bce8477f4f4ba44b84696246a3bee14e8a8c3dcb5589af2d723ba9d3137dc935`
- Backup result: `ok=true`, 23 files
- Independent `--verify-backup` result: `ok=true`, zero errors

## Immutable release

- Local and remote Git archive SHA-256 matched:
  `716e397717a3433851349e006e8738b02f1925fae07670a9c63a4e4f4e5b9955`
- Embedded `SOURCE_COMMIT`: exact deployed SHA
- The first inactive staging test stopped because the production venv did not contain pytest.
- Pytest was added only to the inactive new venv; production remained on the prior healthy release.
- Retried finish-wave pytest: 7 passed
- Repository contract verifier: passed
- Future due-date check: false
- Atomic `/opt/seven` symlink switch completed only after those gates passed.

Installed file hashes:

- `freewill.py`: `5e93266bf7c91b01dce4b383f8d4554e504fa1d8708f8081d5eeefa4f49681ad`
- `planner.py`: `d8ca1299311b24bd7b4b3327a056522f4589b258818089ea609e36b806ce4dd5`
- `autonomy.py`: `cd64bf2bbaabcc2fc5eedc7fb710130f1488697381083b1209d6dba358bb9789`

## Runtime proof

- `seven-core`: active
- `seven-web`: active
- `seven-ollama`: active
- `httpd`: active
- Core loopback health: `ok=true`, version `4.6.0`
- Gateway loopback health: `ok=true`, version `1.1.0`
- Public `/seven/` HTTP result: 200
- Audited `get_system_info`: audit id 87, `ok=1`, result included OS information.
- Deliberate missing-file `read_file`: audit id 88, `ok=0`, returned an error.
- `seven-core` restart proof: main PID changed.
- After restart:
  - `tool:read_file` failure belief present: true
  - belief states failure: true
  - failure belief appears in generated memory context: true
- `seven.db` integrity: ok
- `seven_mesh.db` integrity: ok

## Rollback

- Previous release preserved: `/opt/seven-4.6.0-ca671b4`
- Rollback symlink: `/opt/seven-rollback-before-1397d04`
- Rollback target verification: `/opt/seven-4.6.0-ca671b4`
- Atomic rollback command path was prepared before the switch and would restore the prior symlink followed by a `seven-core` restart.

## Scope

No new features, model changes, gateway changes, Ollama changes, mesh authority changes, remote L4 capability, or sentience claims were made.
