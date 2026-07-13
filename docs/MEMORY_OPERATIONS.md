# Memory Integrity and Export

Seven's current SQLite schema is explicitly versioned with `PRAGMA user_version=4`. Version 2 added transactional conversation action candidates; version 3 added migration provenance plus action-source fields; version 4 adds immutable skill revisions and bounded run records. Migrations are idempotent and the release lifecycle proves an upgrade from the recorded pre-completion schema.

## Integrity and statistics

```text
python -m seven --memory-check
```

This runs SQLite integrity and foreign-key checks and reports schema version, file size and record counts by table.

## Portable export

```text
python -m seven --export-memory seven-memory.json
```

The UTF-8 JSON export includes format/version metadata, Seven/schema versions, timestamp, source database SHA-256 and ordered records for conversation, facts, goals, tasks, action candidates, notes, beliefs, working memory, skills, plans, embeddings, digests and preferences.

Tool audit history is excluded by default because older rows may contain sensitive values. To include the current redacted audit table deliberately:

```text
python -m seven --export-memory-with-audit seven-memory-with-audit.json
```

Export refuses to run when integrity checks fail. JSON export is for inspection, migration and interoperability; disaster recovery uses the verified ZIP backup described in `BACKUP_AND_RECOVERY.md`.

## Import v3 conversation memory

The supported importer accepts only the legacy SQLite schema containing `conversations` and `utterances`. It opens the source read-only, runs integrity and column checks, hashes it, maps user/Seven utterances to current roles, preserves timestamps and provenance metadata, stores summaries as searchable `legacy-conversation` facts, and imports extracted actions as pending review candidates with source references.

Dry-run is the default and operates against a temporary migrated copy of current memory, so it neither creates nor upgrades the real target:

```text
seven --migrate-legacy-memory C:\path\to\conversation_memory.db
seven --apply-legacy-memory C:\path\to\conversation_memory.db
```

Apply creates and verifies a backup before changing an existing target. Exact message timestamps/content/roles, summary provenance keys, action fingerprints, and the source SHA-256 provide deduplication. A completed source hash is recorded in `legacy_imports`, making repeated apply a visible no-op. Malformed action JSON is counted and skipped; the source database is never modified. This does not claim automatic migration of every unrelated v3 JSON/SQLite subsystem.

## Explicit retention

Retention is never automatic. Preview records eligible counts without changing or schema-migrating the real database:

```text
seven --memory-retention 90
seven --apply-memory-retention 90
```

Default ephemeral scopes are `messages,audit,working_memory,digests,message_embeddings,completed_tasks,dismissed_actions`. Select a subset with `--retention-scope`, for example:

```text
seven --memory-retention 30 --retention-scope audit,message_embeddings
```

Apply refuses missing/corrupt databases, creates a verified pre-change backup before schema migration/deletion, then deletes all selected rows older than the UTC cutoff in one immediate transaction. Long-term facts, notes, goals, open tasks, accepted/pending actions, skills, plans, preferences and non-message embeddings are deliberately outside the default purge surface.

## Corruption recovery drill

`--memory-check` visibly fails on a corrupt database. Restore still preserves the damaged pre-restore bytes: if SQLite online backup cannot open them, Seven creates a verified `forensic-raw-1` ZIP with hashes and a consistency warning, then restores the previously verified good archive. A test corrupts real SQLite bytes, verifies detection, validates the forensic archive, restores, and reads the original fact.
