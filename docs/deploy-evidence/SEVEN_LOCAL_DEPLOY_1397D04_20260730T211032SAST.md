# Seven Local deployment evidence

- Target: `D:\SevenLocal`
- Deployed SHA: `1397d04f4993d143ddc413a7820f3432bc08a55e`
- Accepted remote branch: `codex/seven-completion`
- The local `finish-wave-review` checkout HEAD and accepted remote branch both
  matched the deployed SHA before staging and again after deployment.
- Deployment time: 2026-07-30 SAST
- Secrets, tokens, passwords, credential contents, and secret-file hashes are omitted.

## Backup before switch

- Archive: `D:\SevenLocal\data\backups\seven-backup-20260730T184333492537Z.zip`
- SHA-256: `8E14D26C0EB26F1523AD4CF9261D8E8E0B3A5DED4734D7870B110595FF200397`
- Backup result: `ok=true`, 76 files
- Independent `--verify-backup` result: `ok=true`, zero errors

## Immutable release

- Release: `D:\SevenLocal\releases\seven-4.6.0-1397d04`
- Git archive: `D:\SevenLocal\releases\seven-4.6.0-1397d04-source.zip`
- Git archive SHA-256: `716E397717A3433851349E006E8738B02F1925FAE07670A9C63A4E4F4E5B9955`
- Embedded `SOURCE_COMMIT`: exact deployed SHA
- Staged finish-wave pytest: 7 passed
- Repository contract verifier: passed
- Active junction: `D:\SevenLocal\venv` -> new release venv

Installed file hashes:

- `freewill.py`: `5E93266BF7C91B01DCE4B383F8D4554E504FA1D8708F8081D5EEEFA4F49681AD`
- `planner.py`: `D8CA1299311B24BD7B4B3327A056522F4589B258818089EA609E36B806CE4DD5`
- `autonomy.py`: `CD64BF2BBAABCC2FC5EEDC7FB710130F1488697381083B1209D6DBA358BB9789`

## Runtime proof

- API health before switch: `ok=true`
- API health after switch and restart: `ok=true`, service `seven-real`, version `4.6.0`
- Status: Ollama reachable; configured text and vision models present; 125 tools registered.
- Audited `get_system_info`: audit id 40, `ok=1`, result included OS information.
- Deliberate missing-file `read_file`: audit id 41, `ok=0`, returned an error.
- After another API restart:
  - `tool:read_file` failure belief present: true
  - belief states failure: true
  - failure belief appears in generated memory context: true
- Finish-wave due-date check:
  - future timestamp forced: false
  - past timestamp forced: true

## Rollback

- Previous release preserved: `D:\SevenLocal\releases\seven-4.6.0-ca671b4`
- Rollback junction: `D:\SevenLocal\rollback\venv-active-link-before-1397d04-20260730T2046`
- A second rollback link to the same prior venv also exists.
- Rollback requires stopping the local API, moving the active junction aside, restoring the prior junction target, and restarting the API.

## Scope

No new features, model changes, mesh authority changes, avatar work, email work, or sentience claims were made.
