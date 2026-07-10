# Seven system documentation pack

**Purpose:** Everything we need to remember, fix, enhance, and not lose when context dies.

| Doc | Contents |
|---|---|
| [TRUTH_AUDIT.md](TRUTH_AUDIT.md) | Honest what works / broken / risky (dated) |
| [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) | What Seven should have vs implemented |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the living package is structured |
| [FLOWS.md](FLOWS.md) | Runtime flows (talk, quiet, daemon, tools) |
| [BUGS_AND_FIXES.md](BUGS_AND_FIXES.md) | Known bugs, fixed issues, watch list |
| [ENHANCEMENTS.md](ENHANCEMENTS.md) | Next enhancements priority list |
| [LEGACY_AND_STALE.md](LEGACY_AND_STALE.md) | Abandoned code under `_legacy/v3` |
| [RUNBOOK.md](RUNBOOK.md) | How to run / test / recover |
| [MEMORY_MODEL.md](MEMORY_MODEL.md) | Short-term vs long-term memory design |
| [CHANGELOG_SESSION.md](CHANGELOG_SESSION.md) | Session history of rebuild |
| [NIGHT_BUILD.md](NIGHT_BUILD.md) | 4.2.0 mind features landed overnight |
| [MODEL_AND_VOICE.md](MODEL_AND_VOICE.md) | qwen2.5:7b + AvaNeural + barge-in + Playwright |

**Active product root:** `seven/`  
**Entry:** `run_seven.bat` (talk) · `run_seven_quiet.bat` (night) · `run_seven_daemon.bat` (always-on)  
**User data:** `%USERPROFILE%\.seven\`
