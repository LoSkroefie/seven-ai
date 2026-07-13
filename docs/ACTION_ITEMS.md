# Conversation action candidates

Seven can notice explicit commitments in user messages and keep them as reviewable action candidates. This is a local deterministic parser, not a second LLM call. It recognizes deliberately narrow wording such as `todo: submit invoice`, `remind me to call Sam`, `I need to renew the licence`, and `we have to book the venue`.

Candidates are not silently treated as completed work and do not become tasks until accepted. Seven exposes:

- `list_action_items` for pending, accepted, or dismissed candidates;
- `accept_action_item`, which transactionally creates a task and records its ID;
- `dismiss_action_item`, which records the rejection without creating a task.

Exact normalized duplicates are ignored across restarts. Candidates and their source message IDs live in the same SQLite database as messages and tasks and are included in portable memory exports and verified backups.

## Privacy and control

The default `SEVEN_ACTION_CAPTURE=suggest` performs only local pattern matching. Set `SEVEN_ACTION_CAPTURE=off` before starting Seven to disable automatic capture. Existing candidates remain until the user resolves them or removes their local Seven data; disabling capture does not secretly delete history.

The parser intentionally misses vague or implied intentions rather than inventing obligations. The LLM can still call `add_task` when the user explicitly asks Seven to create one. No due date is guessed from conversational prose.

## Legacy disposition

The v3 action digest read a removed `ConversationMemory` format and stored notification fingerprints in `~/.chatbot/action_items_seen.json`. It could drift from current tasks and its toast call did not prove delivery. Seven now uses the current database and native reminder/notification lifecycle. Automatic proactive candidate announcements are not claimed; accepted tasks use the supported reminder flow when a real due time is set.
