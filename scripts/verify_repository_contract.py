"""Verify source/release boundaries that ordinary unit tests cannot prove."""
from __future__ import annotations

import ast
import csv
import re
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TOP_LEVEL = {"_legacy", "core", "evolution", "extensions", "gui", "integrations", "learning", "utils"}
LINK = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def production_legacy_imports() -> list[str]:
    failures: list[str] = []
    for path in sorted((ROOT / "seven").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".", 1)[0] in FORBIDDEN_TOP_LEVEL:
                    failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: {name}")
    return failures


def unresolved_inventory() -> list[str]:
    with (ROOT / "docs" / "FILE_INVENTORY.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    failures = []
    for row in rows:
        disposition = row.get("disposition", "")
        if not disposition or disposition.startswith("review-"):
            failures.append(f"{row.get('path')}: {disposition or '<missing>'}")
    return failures


def broken_local_links() -> list[str]:
    failures = []
    for path in sorted([ROOT / "README.md", ROOT / "SEVEN_REAL.md", *(ROOT / "docs").rglob("*.md")]):
        text = path.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            resolved = (path.parent / urllib.parse.unquote(target)).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing {target}")
    return failures


def main() -> int:
    failures = [
        *(f"legacy import: {item}" for item in production_legacy_imports()),
        *(f"unresolved inventory: {item}" for item in unresolved_inventory()),
        *(f"broken documentation link: {item}" for item in broken_local_links()),
    ]
    if failures:
        print("Repository contract failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK repository contract: no legacy runtime imports and no unresolved inventory dispositions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
