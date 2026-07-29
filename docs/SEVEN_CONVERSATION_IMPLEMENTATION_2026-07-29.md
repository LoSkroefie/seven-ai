# Seven Conversation Implementation — 2026-07-29

## Outcome

Seven's compact Peanut profile now preserves bounded identity, durable memory,
self-first living state and four recent conversation messages. Natural resource
requests use the audited `get_system_info` result directly. Ordinary
conversation remains model-authored; no canned identity or emotional response
was introduced.

Latency tuning and final conversational acceptance are explicitly deferred.

## Protected before-state

- Repository branch: `codex/seven-completion`.
- Starting commit: `e921df1d76ffcc2526b5718f1b045564f85977e6`.
- Pre-existing modified files preserved and excluded from the scoped commit:
  - `deploy/peanut/README.md`
  - `docs/COMPLETION_LEDGER.md`
- Previous Peanut release preserved:
  `/opt/seven-conversation-20260729T101128Z`.
- Production database proof messages were removed after backup:
  `/var/lib/seven/seven.db.before-status-proof-cleanup-20260729T115102Z`.

## Implemented

1. Compact prompts include bounded identity, durable memory and refreshed state.
2. Living context reserves self identity, mode, energy and intent before host
   telemetry.
3. Conversation history increased from one to four messages.
4. Basic resource questions execute `get_system_info` and return its exact
   audited output without model reinterpretation.
5. Dispatcher aliases resolve common resource and directory tool names.
6. Invalid-response handling rejects customer-service filler, tool-denial
   claims, internal markup, speaker reversal and self-greetings.
7. Repair prompts require first-person Seven responses and correct speaker
   perspective while keeping the response model-authored.
8. Failed/generic assistant messages are excluded from future prompt history.
9. The stale project-organization goal was blocked rather than deleted.

## Validation and deployment

- Targeted implementation tests: `57 passed`.
- `git diff --check`: passed; only Windows line-ending warnings were reported.
- Active Peanut release:
  `/opt/seven-conversation-20260729T115844Z`.
- `seven-core`: active.
- Core health:
  `{"ok":true,"service":"seven-real","version":"4.4.4"}`.
- Deployed file hashes:

| File | Previous SHA-256 | Current SHA-256 |
|---|---|---|
| `seven/agent/loop.py` | `731e4acb26b8e8889f5efa83adbd61e62328c93d64db2d593840efcb2b2f70cd` | `fed37783a3264c365704d020335623b89ec74d6a9072a2d69283493354e0d327` |
| `seven/agent/prompt.py` | `dad947aae55ec3bc8599b1974fef42918380d93282ed8f851d71256c6dcb43d6` | `a189a28d0c9cf139cf96db898b08cdd3f4c33457238b78c4c8e761b4e0a71de6` |
| `seven/mind/state.py` | `704976e6d3c01ac3e81fd4b46b4e9f9089b91b27c46e99bd984db2fe5c8c450d` | `704976e6d3c01ac3e81fd4b46b4e9f9089b91b27c46e99bd984db2fe5c8c450d` |

## Deferred live acceptance

The following must be tested later through the owner web session:

- consistent Seven identity and correct speaker perspective;
- multi-turn conversational continuity;
- coherent questions initiated by Seven;
- autonomous utterance delivery to the web interface;
- absence of generic customer-service filler;
- stable resource and tool execution through ordinary language.

The implementation is deployed and code-validated. Conversational quality is
not yet accepted.
