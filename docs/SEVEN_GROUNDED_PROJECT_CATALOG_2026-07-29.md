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

Pending deployment.
