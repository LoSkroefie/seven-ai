# External Coding Agents

Seven can delegate repository work to installed local CLIs through `coding_agent_status`, `run_opencode`, `run_claude_cli`, `run_codex_cli` and `run_aider`.

## Verified command contracts

- OpenCode: `opencode run --agent plan|build <prompt>`
- Claude Code: `claude --print [--dangerously-skip-permissions] <prompt>`
- Codex: `codex exec --skip-git-repo-check [--dangerously-bypass-approvals-and-sandbox] <prompt>`
- Aider: `aider --yes-always --message <prompt>`

`SEVEN_CODING_AGENT_UNRESTRICTED=1` is the L4 default and selects the documented unrestricted flags for Claude and Codex. Set it to `0` to retain their own approval/sandbox defaults. `SEVEN_OPENCODE_BUILD=0` disables OpenCode's build agent.

Windows `.ps1`, `.cmd` and `.bat` command shims are launched through their actual host shells. Every agent runs through Seven's tracked process runner, so timeouts terminate descendants and return exit code, partial output and affected process IDs.

## Live baseline (2026-07-11)

- OpenCode 1.17.7 installed
- Codex CLI 0.140.0 installed
- Claude Code 2.1.118 installed
- Aider not installed

No live mutation prompt was issued during this audit. Command/version discovery was live; non-interactive argument contracts and process lifecycle are automated. Each agent still requires its own legitimate authentication/provider configuration.
