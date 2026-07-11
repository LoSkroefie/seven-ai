# Packaging and Installation

Seven is packaged from `pyproject.toml` as `seven-ai`. Runtime and package metadata share version `4.3.0`; prerelease/completion status is communicated through project status rather than inventing a runtime-only version suffix.

## Build and verify a wheel

```text
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/verify_wheel.py dist/seven_ai-4.3.0-py3-none-any.whl
```

The verifier requires Seven's console entry point, metadata and all identity files. This gate exists because the baseline wheel silently omitted `SOUL.md`, `IDENTITY.md`, `USER.md` and `TOOLS.md`, leaving installed copies without their authored identity.

## Dependency groups

- Core: agent, Ollama HTTP, system state, desktop/screen and camera foundations
- `voice`: TTS, audio playback, recognition, Whisper and microphone support
- `tray`: system tray UI
- `robotics`: serial hardware
- `browser`: Playwright browser automation
- `dev`: test runner
- `all`: every group above

Clean-environment installation and uninstall validation remain required before release. `requirements-real.txt` is retained during reconciliation but is not the long-term package authority; `pyproject.toml` is authoritative.
