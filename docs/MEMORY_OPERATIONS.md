# Memory Integrity and Export

Seven's current SQLite schema is explicitly versioned with `PRAGMA user_version=2`. Version 2 adds transactional conversation action candidates and their links to source messages and accepted tasks.

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
