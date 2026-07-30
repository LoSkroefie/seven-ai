# DEPLOY ORDER — ca671b4 (Grok police authorized)

**Status:** READY TO DEPLOY  
**Commit (exact):** `ca671b4f9d6eabf0db516694821ef7d16dfd2e00`  
**Branch:** `codex/seven-completion`  
**Subject:** Make Seven outcomes and continuity durable  
**Police:** REAL for R1/R2 functional-alive slice (2026-07-30). Not sentient. Not “complete Seven.”

---

## Paste to Codex (full order)

```
DEPLOY AUTHORIZATION FROM GROK POLICE + OWNER.

Exact commit only:
ca671b4f9d6eabf0db516694821ef7d16dfd2e00
Branch: codex/seven-completion
Do NOT deploy a different SHA. If tip moved, STOP and report.

Mission: deploy this commit to (1) local Windows Seven runtime and (2) Peanut.
This is operational deploy — not a rewrite, not mesh remote L4, not sentience work.

Read and follow existing ops docs in the repo:
- docs/PEANUT_OPERATIONS.md
- deploy/peanut/README.md
- docs/SEVEN_MESH.md / prior mesh deployment proofs if mesh must stay up
- Local layout expected: D:\SevenLocal (venv, data, launchers)

══════════════════════════════════════
PHASE L — LOCAL WINDOWS (D:\SevenLocal)
══════════════════════════════════════
1. Record before-state: installed version, running PIDs/ports, git/package SHA if known.
2. Create verified backup of Seven data (python -m seven --backup or existing backup path under D:\SevenLocal\backups). Record path + SHA-256.
3. Install EXACT commit ca671b4 into the local venv (wheel from that commit or pip install from that checkout). No mixed dirty tree.
4. Restart the local runtime the owner actually uses (API and/or quiet/talk — match existing Start-Seven*.cmd).
5. Prove:
   - python -m seven --status  (or installed equivalent) shows healthy brain reachability honestly
   - health on local API if used (loopback)
   - one real tool: get_system_info
   - tool failure still audits ok=false (quick JSON fail or known path)
   - Memory reopen: a tool:<name> belief or failure still present after process restart
6. If mesh was enabled locally, mesh_status still operational; do not break secret files.
7. Write evidence file: docs/SEVEN_LOCAL_DEPLOY_CA671B4_<timestamp>.md with commands + outputs (redact secrets).

══════════════════════════════════════
PHASE P — PEANUT
══════════════════════════════════════
Follow PEANUT_OPERATIONS release boundary. Model does not skip backups.

1. Before-state: active /opt/seven target, service status (seven-core, seven-web, seven-ollama, httpd), ports, current release dir name.
2. sudo/operator path: verified backup of /var/lib/seven (seven --backup). Record archive SHA-256.
3. Stage IMMUTABLE release dir e.g. /opt/seven-ca671b4-<shortsha> with code from EXACT commit only.
4. Install/update venv for that release; do not clobber unrelated host services.
5. Atomic switch /opt/seven → new release (symlink) per existing practice.
6. Restart only required services (typically seven-core; keep web/ollama stable if possible).
7. Prove:
   - curl --fail http://127.0.0.1:18765/health  (core)
   - curl --fail http://127.0.0.1:18788/health  (gateway if used)
   - public owner path health if applicable (no secret leak)
   - SQLite integrity ok for seven data + mesh db if present
   - one real owner-level exchange OR loopback chat that runs a tool
   - if mesh was deployed: mesh health + optional ping from Windows still works (message or status); do not rotate mesh secret unless broken
8. On ANY failed gate: symlink rollback to previous release, restart, prove old health, STOP.
9. Write evidence: docs/SEVEN_PEANUT_DEPLOY_CA671B4_<timestamp>.md with hashes, service status, health curls, rollback path. Redact tokens/secrets/passwords.

══════════════════════════════════════
RULES
══════════════════════════════════════
- Exact SHA ca671b4 only.
- Backup before switch. Rollback plan first.
- No remote L4 via mesh. No new features during deploy.
- No sentience/complete claims in evidence docs.
- Do not commit secrets. Do not print SEVEN_API_TOKEN / mesh secret / passwords.
- Preserve owner uncommitted doc drift if still present; do not force-reset unrelated work.
- If you lack SSH/sudo to Peanut, report BLOCKED with exact missing access — do not fake deploy.

══════════════════════════════════════
REPORT FORMAT
══════════════════════════════════════
## Deploy target
## Exact SHA deployed
## Local: Done / Evidence / Failed
## Peanut: Done / Evidence / Failed
## Rollback ready?
## Still broken
## Next 3
```

---

## Owner one-liner (if Codex already has context)

```
Grok + owner: DEPLOY ca671b4 to local D:\SevenLocal and Peanut. Exact SHA only. Backup first. Prove health+tool+restart belief. Rollback on fail. Evidence markdown. No secrets in logs. Go.
```

---

## After deploy — paste report to Grok

Police will grade REAL/MIXED/BULLSHIT on evidence only.
