# Installation, upgrade, and uninstall

`pyproject.toml` is Seven's only dependency authority. `uv.lock` is the committed universal resolution for reproducible development and source deployments. The small `requirements-real.txt` file is a temporary compatibility redirect to the project extras; it no longer duplicates versions.

## Supported Python

Seven supports CPython 3.11, 3.12, and 3.13. Use a virtual environment so Seven and its optional AI/audio dependencies do not alter unrelated Python applications.

### Reproducible source install with uv

```text
git clone https://github.com/LoSkroefie/seven-ai.git
cd seven-ai
uv sync --locked --extra voice --extra tray
uv run seven --help
```

`uv lock --check` proves that `uv.lock` still matches `pyproject.toml`. Do not hand-edit the lock; use the documented dependency update process in `DEVELOPMENT_AND_RELEASE_PROCESS.md`.

### Standard pip source install

```text
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[voice,tray]"
seven --help
```

Core-only automation or server installs use `python -m pip install .`. Other extras are `music`, `documents`, `mcp`, `robotics`, `browser`, `tray`, `voice`, and `dev`. The `all` extra requests every declared group and may require platform audio/compiler packages; it is not used as a substitute for the tested matrix.

Playwright's Python package does not install browser engines. After selecting browser automation, run `python -m playwright install` for the engines appropriate to that host.

## Upgrade

Back up Seven's data first:

```text
seven --backup
git pull --ff-only
uv sync --locked --extra voice --extra tray
```

For pip, reactivate the same virtual environment and run `python -m pip install --upgrade -e ".[voice,tray]"`. Seven performs idempotent SQLite migrations when memory opens. Never downgrade a live database without restoring a backup created by the target version.

The automated lifecycle verifier installs an older wheel, creates its real data, upgrades to the candidate wheel, verifies runtime/metadata version agreement, identity assets and non-regressing schema, executes the installed CLI, runs `pip check`, uninstalls, and proves `seven` is no longer importable.

## Uninstall

First remove user-login startup while Seven is still installed:

```text
seven --remove-startup
python -m pip uninstall seven-ai
```

Package uninstall deliberately preserves `SEVEN_DATA_DIR` (normally `~/.seven`) because it contains user memory, backups, extensions, logs, and identity state. After making and verifying a backup, the user may remove that directory manually. Seven never deletes user memory merely because a Python package was uninstalled.

An editable source checkout, Ollama models, Playwright browser engines, OpenSSH keys, coding-agent CLIs, and system packages are independently owned and are not removed by `pip uninstall seven-ai`.

## Release lifecycle command

```text
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/verify_wheel.py dist/seven_ai-4.4.0-py3-none-any.whl
python scripts/verify_install_lifecycle.py dist/seven_ai-4.4.0-py3-none-any.whl
```

Use `--extras mcp,documents,music,robotics,tray,browser` for the clean optional-integration matrix and `--previous-wheel PATH` for a real upgrade/migration drill.
