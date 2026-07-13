# Packaging and Installation

Seven is packaged from `pyproject.toml` as `seven-ai`. Runtime and package metadata share version `4.4.0`; prerelease/completion status is communicated through project status rather than inventing a runtime-only version suffix.

## Build and verify a wheel

```text
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/verify_wheel.py dist/seven_ai-4.4.0-py3-none-any.whl
```

The verifier requires Seven's console entry point, metadata and all identity files. This gate exists because the baseline wheel silently omitted `SOUL.md`, `IDENTITY.md`, `USER.md` and `TOOLS.md`, leaving installed copies without their authored identity.

## Dependency groups

- Core: agent, Ollama HTTP, system state, desktop/screen and camera foundations
- `voice`: TTS, audio playback, recognition, Whisper and microphone support
- `music`: owned local playback worker without the microphone/TTS stack
- `documents`: PDF extraction (`pypdf`); Office extraction is built in
- `mcp`: local stdio Model Context Protocol server
- `tray`: system tray UI
- `robotics`: serial hardware
- `browser`: Playwright browser automation
- `dev`: test runner
- `all`: every group above

`uv.lock` records a universal resolution of all declared extras and is checked for drift in CI. `requirements-real.txt` is retained only as a compatibility redirect to the project; it contains no duplicate dependency declarations.

`verify_install_lifecycle.py` creates a disposable virtual environment and proves installed version/metadata identity, packaged identity assets, SQLite initialization/migration, CLI help, `pip check`, uninstall, and import absence. CI runs core lifecycle on Windows and the bounded MCP/document/music/robotics/tray/browser extras matrix on Ubuntu. See `INSTALLATION.md` for commands and data-retention semantics.
