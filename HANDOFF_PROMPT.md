# Handoff prompt

The old paste contained obsolete 4.4.0, 39-tool and core-tier claims.

Use the canonical single-session prompt instead:

[docs/CONTINUATION_PROMPT.md](docs/CONTINUATION_PROMPT.md)

If the repository is not available, start with this minimal recovery block:

```text
Read docs/CONTINUATION_PROMPT.md and
docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md before acting.

Seven production core is 4.6.0 at
1397d04f4993d143ddc413a7820f3432bc08a55e locally and on Peanut.
The branch may contain newer documentation-only commits.

Do not claim sentience or completeness. Do not rewrite Seven. Do not grant
remote L4 over mesh. Do not commit secrets, venvs, databases or private
backups. Do not deploy or clean disks without explicit owner authorization.

Grok is police. Report Done / Evidence / Unproven / Next 3.
```
