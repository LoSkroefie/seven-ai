# Durable Reminders

Seven uses the existing SQLite `tasks` table as the durable reminder source. A task with an ISO-8601 `due_at` survives process and machine restarts.

Examples of accepted values:

```text
2026-07-12T08:30:00+02:00
2026-07-12T06:30:00Z
```

Naive timestamps without an offset are interpreted in the machine's local timezone. Invalid timestamps remain visible tasks but are not fired.

The heartbeat checks open, undelivered due tasks before autonomous goal work. Delivery occurs only when a real user-facing output callback is attached, such as talk mode. Seven marks the reminder delivered only after that callback returns successfully. When only the silent daemon is running, the due reminder remains pending for the next interactive session.

This deliberately replaces `_legacy/v3/extensions/smart_reminders.py`, whose reminders existed only in memory and disappeared on restart, and avoids the old scheduler's placeholder built-in jobs that called optional/nonexistent subsystems.

## Current limitation

Native background desktop notifications are not yet a supported output channel. Until that is implemented and tested, silent daemon mode retains reminders rather than falsely marking them delivered.
