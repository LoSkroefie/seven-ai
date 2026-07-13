# Seven 4.4.0 release checklist

Automated release blockers are separate from unavailable device/provider evidence. Missing hardware evidence remains a limitation; it must never be recorded as a pass.

## Blocking software gates

- [ ] Clean worktree and identified candidate commit.
- [ ] Tests pass on Windows and Ubuntu Python 3.11–3.13; compile and lock gates pass.
- [ ] Inventories regenerate without diff; 216 archived Python files parse.
- [ ] Repository contract has zero legacy imports and unresolved dispositions.
- [ ] Wheel content/version/assets verification passes.
- [ ] Isolated install, `pip check`, CLI, schema, API health and uninstall pass on Windows/Ubuntu.
- [ ] Real 4.3.x-to-4.4.0 upgrade drill passes.
- [ ] API/daemon socket/subprocess lifecycles pass.
- [ ] Documentation links/tool count match the installed package.
- [ ] Dependency provenance matches the lock; unknown declarations are recorded limitations.
- [ ] No tracked build/cache/runtime/token/credential artifacts or secret-scan findings.
- [ ] PR review/checks green and release commit intentionally merged.

## Manual evidence matrix

- [ ] Windows login startup: one owned process and real greeting.
- [ ] Target Linux login startup: one owned process and real greeting.
- [ ] Named microphone/speaker, webcam and multi-monitor flows.
- [ ] Named robot handshake/actions/emergency stop.
- [ ] Supported Ollama text/vision live session.
- [ ] Real MCP client initialize/list/call/shutdown.
- [ ] Authorized OpenSSH command/upload/download target.
- [ ] 24-hour daemon/autonomy/model soak with bounded resources/logs and restart recovery.

Unchecked manual items block claims for that scenario, not the tested core package; list them in `KNOWN_LIMITATIONS.md`.

## Commands

```powershell
python -m pytest -q
python -m compileall -q seven scripts
python scripts/generate_file_inventory.py
python scripts/generate_legacy_symbol_inventory.py
python scripts/verify_repository_contract.py
uv lock --check
python -m pip wheel . --no-deps -w dist
python scripts/verify_wheel.py dist/seven_ai-4.4.0-py3-none-any.whl
python scripts/verify_install_lifecycle.py dist/seven_ai-4.4.0-py3-none-any.whl
git diff --check
```

Record commit, CI URLs, wheel SHA-256, platform/Python and model/device/provider identities in `RELEASE_EVIDENCE.md`. Never tick a box from intention.
