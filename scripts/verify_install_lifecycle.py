"""Verify a Seven wheel in an isolated venv, optionally across an upgrade."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def _python(env_dir: Path) -> Path:
    return env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _script(env_dir: Path, name: str) -> Path:
    return env_dir / (f"Scripts/{name}.exe" if os.name == "nt" else f"bin/{name}")


def _run(args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    completed = subprocess.run(args, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}\n{completed.stdout}\n{completed.stderr}")
    return completed


def _probe(python: Path, cwd: Path, env: dict[str, str]) -> dict:
    code = r'''
import importlib.metadata, json, os, sqlite3
from pathlib import Path
from seven import __version__
from seven.agent.prompt import _read_identity
from seven.memory.store import Memory
db = Path(os.environ["SEVEN_DATA_DIR"]) / "seven.db"
memory = Memory(db)
payload = {
    "runtime_version": __version__,
    "metadata_version": importlib.metadata.version("seven-ai"),
    "identity_files": [name for name in ("SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md") if name in _read_identity()],
    "schema_version": sqlite3.connect(db).execute("PRAGMA user_version").fetchone()[0],
    "database": str(db),
}
print(json.dumps(payload))
'''
    output = _run([str(python), "-c", code], cwd, env).stdout.strip().splitlines()[-1]
    return json.loads(output)


def verify(wheel: Path, extras: str = "", previous_wheel: Path | None = None) -> dict:
    wheel = wheel.resolve()
    if not wheel.is_file():
        raise ValueError(f"wheel not found: {wheel}")
    with tempfile.TemporaryDirectory(prefix="seven-lifecycle-") as raw:
        root = Path(raw)
        env_dir, work, data = root / "venv", root / "work", root / "data"
        work.mkdir(); data.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
        python = _python(env_dir)
        process_env = os.environ.copy()
        process_env.update(SEVEN_DATA_DIR=str(data), SEVEN_EXTENSIONS="0", PYTHONUTF8="1")

        baseline = None
        if previous_wheel:
            previous_wheel = previous_wheel.resolve()
            _run([str(python), "-m", "pip", "install", str(previous_wheel)], work, process_env)
            baseline = _probe(python, work, process_env)

        target = str(wheel) + (f"[{extras}]" if extras else "")
        install = _run([str(python), "-m", "pip", "install", "--upgrade", target], work, process_env)
        current = _probe(python, work, process_env)
        if current["runtime_version"] != current["metadata_version"]:
            raise RuntimeError(f"runtime/metadata version mismatch: {current}")
        if len(current["identity_files"]) != 4:
            raise RuntimeError(f"installed identity incomplete: {current['identity_files']}")
        if baseline and baseline["metadata_version"] == current["metadata_version"]:
            raise RuntimeError("upgrade wheel has the same version as the baseline")
        if baseline and current["schema_version"] < baseline["schema_version"]:
            raise RuntimeError("database schema regressed during upgrade")

        _run([str(python), "-m", "seven", "--help"], work, process_env)
        if not _script(env_dir, "seven").is_file():
            raise RuntimeError("installed seven console script is missing")
        _run([str(python), "-m", "pip", "check"], work, process_env)
        _run([str(python), "-m", "pip", "uninstall", "-y", "seven-ai"], work, process_env)
        absence = _run([str(python), "-c", "import importlib.util; assert importlib.util.find_spec('seven') is None; print('absent')"], work, process_env)
        if _script(env_dir, "seven").exists() or _script(env_dir, "seven-mcp").exists():
            raise RuntimeError("Seven console scripts remain after uninstall")
        return {
            "ok": True,
            "wheel": str(wheel),
            "extras": extras.split(",") if extras else [],
            "baseline": baseline,
            "current": current,
            "pip_install_tail": install.stdout.strip().splitlines()[-3:],
            "uninstall_verified": absence.stdout.strip() == "absent",
            "console_scripts_removed": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--extras", default="")
    parser.add_argument("--previous-wheel", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.wheel, args.extras, args.previous_wheel)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
