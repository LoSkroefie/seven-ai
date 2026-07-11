"""Fail unless a built Seven wheel contains required runtime assets/metadata."""
from __future__ import annotations

import argparse
import email
import zipfile
from pathlib import Path


REQUIRED_SUFFIXES = {
    "seven/identity/SOUL.md",
    "seven/identity/IDENTITY.md",
    "seven/identity/USER.md",
    "seven/identity/TOOLS.md",
    "seven/__main__.py",
}


def verify(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as wheel:
        names = set(wheel.namelist())
        missing = sorted(REQUIRED_SUFFIXES - names)
        errors.extend(f"missing wheel asset: {item}" for item in missing)
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        entry_names = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(metadata_names) != 1:
            errors.append("wheel must contain exactly one METADATA file")
        else:
            metadata = email.message_from_bytes(wheel.read(metadata_names[0]))
            if metadata.get("Name") != "seven-ai":
                errors.append(f"unexpected package name: {metadata.get('Name')}")
            if metadata.get("Version") != "4.3.0":
                errors.append(f"unexpected package version: {metadata.get('Version')}")
        if len(entry_names) != 1 or "seven = seven.__main__:main" not in wheel.read(entry_names[0]).decode("utf-8"):
            errors.append("seven console entry point missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    errors = verify(args.wheel)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK wheel verified: {args.wheel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
