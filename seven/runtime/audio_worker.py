"""Private pygame playback worker controlled through small local JSON files."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


def _write(path: Path, payload: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temp, path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--file", required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--state", required=True)
    args = parser.parse_args(argv)
    control, state = Path(args.control), Path(args.state)
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(args.file)
        pygame.mixer.music.play()
        _write(state, {"state": "playing", "pid": os.getpid()})
        last_command = None
        while True:
            if control.exists():
                try:
                    payload = json.loads(control.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    payload = {}
                command_id = payload.get("id")
                if command_id and command_id != last_command:
                    last_command = command_id
                    command = payload.get("command")
                    if command == "pause":
                        pygame.mixer.music.pause()
                        _write(state, {"state": "paused", "pid": os.getpid()})
                    elif command == "resume":
                        pygame.mixer.music.unpause()
                        _write(state, {"state": "playing", "pid": os.getpid()})
                    elif command == "stop":
                        pygame.mixer.music.stop()
                        _write(state, {"state": "stopped", "pid": os.getpid()})
                        return 0
            if not pygame.mixer.music.get_busy():
                current = json.loads(state.read_text(encoding="utf-8"))
                if current.get("state") != "paused":
                    _write(state, {"state": "finished", "pid": os.getpid()})
                    return 0
            time.sleep(0.1)
    except Exception as exc:
        _write(state, {"state": "error", "pid": os.getpid(), "error": str(exc)[:500]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
