# Seven grounded project catalog — 2026-07-29

## Why this change exists

The Peanut conversation database proved that Seven claimed she was organizing
project files without possessing a project catalog. Her only autonomous goal was
`Organize Project Files`; its active plan repeatedly requested nonexistent
`ls`, `find`, and `mkdir` tool names. The configured workspace was empty, the
database had no project records, and the linked goal was already blocked while
its plan continued to run.

This was a logic and grounding failure, separate from Ollama response latency.

## Implemented contract

- SQLite schema version 6 adds durable `projects` records. Portable memory
  exports include them.
- `list_projects` combines durable records with bounded discovery under the
  workspace, Seven source root, and explicitly configured project roots.
- `register_project` accepts only a readable directory containing a supported
  project marker inside a configured root. The model cannot register an
  invented name or inaccessible path.
- Explicit project-inventory questions run the audited catalog directly.
  Unrelated questions such as “what changed in this project?” remain ordinary
  conversation.
- Direct text-protocol calls to `ls`, `list_files`, `list_tools`, and
  `describe_tool` now resolve through the same dispatcher contract and are
  audited.
- Listing projects/tools is observational evidence and cannot advance a plan or
  create a skill candidate.
- Plans linked to blocked, failed, done, or missing goals no longer run.
- Free-will goal invention receives the real project catalog and is instructed
  not to assume unlisted projects or files exist.

## Verification

- Focused project, dispatcher, memory, and real-agent tests: passed.
- Full repository test suite: passed, with the two pre-existing skips.
- `python -m seven --status`: passed locally with schema/tool initialization.
- Local exact request `List all my projects please`: returned the actual Seven
  repository and explicitly stated that no additional owner projects were
  synced.
- The required live Peanut release, database backup/migration, catalog seed,
  service restart, exact authenticated request, audit record, and rollback
  evidence are recorded below after deployment.

## Live Peanut evidence

- Live immutable release: `/opt/seven-projects-20260729-8b69868`
  (`/opt/seven` resolves to it).
- Git commits:
  - `b45e039` implements the grounded catalog and plan/tool corrections.
  - `8b69868` makes discovery skip protected or stale directories instead of
    aborting the entire catalog.
- Release archive:
  `seven-project-catalog-8b69868.tar.gz`, 31,383,984 bytes,
  SHA-256
  `09610bf69affd8fe791a435b4c14bc776fbec0b7f44c2229fbcd0af4b4d81c27`.
- Live `seven/tools/projects.py` SHA-256:
  `4a2392f7dc4e31dd3fac103f78c410d45a1f50763490e81113b53ae4b66edf5a`.
- Database schema is 6 and `PRAGMA integrity_check` returned `ok`.
- The catalog has ten verified Peanut project paths:
  `/opt/irc-admin`, `/opt/irc-chat/backend`, `/opt/jvr-auctionhouse`,
  `/opt/line-strike`, `/opt/line-strike/server`,
  `/opt/line-strike-beta`, `/opt/line-strike-beta/server`, `/opt/seven`,
  `/opt/tv-room`, and `/opt/video-den`.
- Exact authenticated request: `list all my projects please`.
  The reply listed all ten paths. Audit record 79 is
  `list_projects`, `ok=1`, with `registered_count=10`,
  `discovered_count=10`, and `count=10`.
- The preceding live attempt exposed a protected-directory failure at
  `/opt/irc-admin/public/.git`; that failure remains preserved as audit record
  78 (`ok=0`) and directly motivated commit `8b69868`.
- The stale plan remains stored as historical evidence, but its goal is
  `blocked`; the active-plan query now returns no runnable plans.
- `seven-core`, `seven-web`, and `seven-ollama` were all `active`; core and web
  restart counts were zero. Loopback core/web health and public
  `https://jvrsoftware.co.za/seven/health` all returned HTTP 200.
- Post-test hashes:
  - `/etc/seven/seven-core.env`:
    `e762d9d5dd591fa42759466d9a00b4101de60a63692dde5f9d0dda98d72e5a5b`
  - `/var/lib/seven/seven.db`:
    `ccd8377c3a406405c2ae94eb08c68379fa5041ae966e8b6b92fd23636f56c6d0`

## Rollback evidence

Two exact before-state pairs were preserved:

- Initial deployment:
  - `/etc/seven/seven-core.env.before-projects-20260729T162439Z.bak`
    SHA-256
    `a1bdacc2a137ce9b82c9d1cf763cc2f263d8e5f093f168a468233fa69bdbd619`
  - `/var/lib/seven/seven.db.before-projects-20260729T162439Z.bak`
    SHA-256
    `6a2f0a22d72d11d96f44b0e26f0b8f01a5ed3061392702b867143a4cbe003bae`
- Protected-directory correction:
  - `/etc/seven/seven-core.env.before-unreadable-fix-20260729T163401Z.bak`
    SHA-256
    `e762d9d5dd591fa42759466d9a00b4101de60a63692dde5f9d0dda98d72e5a5b`
  - `/var/lib/seven/seven.db.before-unreadable-fix-20260729T163401Z.bak`
    SHA-256
    `caf54f60c00bdb42cef13fb74b4d1f09659ede31bf9bdabaf621dd82d2ad0f5d`

## Scope still not represented

This catalog describes projects actually visible on Peanut. It does not yet
claim to include Windows-only repositories, GitHub repositories not checked
out on Peanut, or informal folders without a supported project marker.
Ollama latency was intentionally left unchanged for this logical repair.
