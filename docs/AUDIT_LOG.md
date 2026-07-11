# Tool Audit Log

Every tool call through `ToolRegistry` is recorded in Seven's SQLite `audit` table with the tool, arguments, result preview, outcome and timestamp.

Before persistence, Seven recursively redacts values under credential-shaped keys such as passwords, tokens, API keys, authorization headers, cookies and private keys. It also redacts common credential patterns embedded in textual output.

Redaction deliberately occurs only in the persisted audit copy. The real tool receives its original arguments and Seven receives the real tool result during the active turn.

## Limitations

Pattern-based redaction cannot identify every possible secret. Users should avoid printing secrets through shell commands or asking Seven to place credentials in ordinary files. Integrations should retrieve credentials only when needed and avoid returning them in tool results.

Existing audit rows created before this feature are not rewritten automatically. Back them up, inspect them and purge the historical audit table if it may contain credentials.
