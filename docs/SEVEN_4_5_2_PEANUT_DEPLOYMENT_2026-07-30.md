# Seven 4.5.2 Peanut deployment — 2026-07-30

## Outcome

Seven 4.5.2 is active on Peanut. The core and web services restarted cleanly,
the dedicated Ollama service was not restarted, loopback and public health
passed, a non-model direct conversation proved the new audit-grounded response,
and the post-deployment logs contain no core or gateway error pattern.

## Before state

- Active release: `/opt/seven-4.5.0-4791bac`.
- Core version and health: `4.5.0`, HTTP 200 on `127.0.0.1:18765`.
- Gateway version and health: `1.1.0`, HTTP 200 on `127.0.0.1:18788`.
- `seven-core`, `seven-web`, and `seven-ollama` were active with zero restarts.
- The database passed `PRAGMA integrity_check`.
- Before the deployment proof turn, the database contained 101 messages and
  83 tool-audit records.
- Host resources: 7.5 GiB RAM, 3.4 GiB available, 8 GiB swap with 2.4 GiB in
  use, and 1.5 TiB free on the root filesystem.

## Immutable inputs

- Implementation commit:
  `2ff5b907b98e68a982f65873d87eee2876003bad`.
- Exact Git archive:
  `seven-4.5.2-2ff5b90-deploy.tar.gz`.
- Git archive SHA-256:
  `c814b40f4029cdf3210e2d54d5607298ad981f4d45af390e287bb5140a4a6b09`.
- Wheel:
  `seven_ai-4.5.2-py3-none-any.whl`.
- Wheel SHA-256:
  `5897ed15acb7bc22d578a8511fdef6f8ad6910c271b4b33abc4ff4cda096ad25`.
- Local automated validation before deployment: 10 focused tests and all 219
  tests passed.

The two pre-existing uncommitted user documentation changes in
`deploy/peanut/README.md` and `docs/COMPLETION_LEDGER.md` were not included in
the archive, altered, staged, or overwritten.

## Backup and rollback

- Verified pre-deployment backup:
  `/var/lib/seven/backups/seven-backup-20260730T135758819019Z.zip`.
- Pre-deployment backup SHA-256:
  `c6b0f8737326ef3940af52cb08aa22d47960dfb773d79813454137d719d5e7e6`.
- The backup verifier returned `ok: true` with no errors.
- Rollback release retained at `/opt/seven-4.5.0-4791bac`.

## Staging and activation

- Staged immutable release: `/opt/seven-4.5.2-2ff5b90`.
- The uploaded archive and wheel matched the expected SHA-256 values.
- The copied environment passed `pip check`.
- Python compilation passed for the core and gateway packages.
- Staged package import returned Seven `4.5.2`.
- The gateway imported from the staged release.
- `/opt/seven` was switched atomically to the staged release.
- Only `seven-core` and `seven-web` were restarted. `seven-ollama` retained its
  original PID and activation time.

## Runtime proof

- Active release: `/opt/seven-4.5.2-2ff5b90`.
- Core health:
  `{"ok": true, "service": "seven-real", "version": "4.5.2"}`.
- Gateway health:
  `{"ok":true,"service":"seven-web","version":"1.1.0"}`.
- Public `https://jvrsoftware.co.za/seven/health`: HTTP 200.
- Public `https://jvrsoftware.co.za/seven/`: HTTP 200, 4,699 bytes.
- Core, gateway, and dedicated Ollama services are active with zero restarts.
- The direct authenticated core turn `did black work?` returned HTTP 200 and:
  `No. I checked my audit log: Black was never executed, so I cannot claim
  that it formatted or checked anything.`
- The turn used a deterministic audit route and did not invoke model inference.

The proof turn triggered the existing bounded history compaction. This was not
data loss: all 74 imported `legacy_history` messages remain, 12 recent live
turns remain, and the older eligible live turns are represented by
low-confidence `session.compact` facts. Database integrity remained `ok`.

## Post-deployment backup and logs

- Verified post-deployment backup:
  `/var/lib/seven/backups/seven-backup-20260730T140627330855Z.zip`.
- Post-deployment backup SHA-256:
  `36929f070a021f6917f99f1e26c5dabaab232993d6207cb00c53090249d82347`.
- Backup manifest version: Seven `4.5.2`.
- Backup verifier returned `ok: true` with no errors.
- The post-deployment core/gateway journal contains no match for error,
  exception, traceback, failed, timeout, or HTTP 5xx.

## Log findings and remaining boundaries

- Before deployment, core and gateway had no crash loop or restart failure.
- The old core emitted repeated identical freewill status lines. Seven 4.5.2
  suppresses repeated grounded freewill utterances; automated tests pass, but
  the 30-minute heartbeat interval means runtime repetition needs observation
  over time.
- Ollama logs periodically warn that its optional model-recommendations cache
  cannot be written under `/usr/share/ollama/.ollama/cache` because the service
  filesystem is read-only. Inference and tag/process endpoints remain healthy.
  This nonessential warning was not changed because fixing it would require an
  Ollama service configuration change and restart, which was outside this
  deployment and could disturb model state.
- A public authenticated owner-login/chat flow and a general model-backed reply
  were not exercised in this deployment. Public health/home and authenticated
  loopback direct conversation were proven.
