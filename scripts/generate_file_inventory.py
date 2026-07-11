"""Generate the tracked-file completion inventory deterministically."""
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "FILE_INVENTORY.csv"


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return sorted(p.decode("utf-8") for p in result.stdout.split(b"\0") if p)


def classify(path: str) -> tuple[str, str, str]:
    parts = Path(path).parts
    top = parts[0]
    if top == "seven":
        return "production", "keep-audit", "Supported runtime; verify implementation and tests"
    if top == "tests":
        return "current-tests", "keep-expand", "Current evidence; expand coverage and split suites"
    if top == "docs":
        return "current-docs", "keep-reconcile", "Documentation must match current behavior"
    if top == "scripts":
        return "release-tools", "keep-audit", "Developer/release automation requires validation"
    if top == ".github":
        return "ci", "keep-audit", "CI/release automation requires validation"
    if top != "_legacy":
        return "root-surface", "keep-consolidate", "Public launch/package/project surface"

    rel = "/".join(parts[2:]) if len(parts) > 2 else path
    area = parts[2] if len(parts) > 2 else "legacy-root"
    name = Path(path).name.lower()
    if area in {"core", "integrations", "extensions", "learning", "evolution", "gui", "utils"}:
        return f"legacy-{area}", "review-port", "Inspect for real behavior worth porting to seven/"
    if area in {"data", "test_data"}:
        return f"legacy-{area}", "review-migrate", "Inspect for user data, fixtures, secrets and migration needs"
    if area in {"tests_old"}:
        return "legacy-tests", "keep-reference", "Evidence/reference; map coverage before archive or port"
    if area in {"docs_old"} or name.endswith(".md") or "audit" in name:
        return "legacy-documentation", "review-archive", "Reconcile claims; preserve only useful history/evidence"
    if name.endswith((".bat", ".ps1", ".vbs", ".sh")) or name.startswith(("install", "uninstall", "launch", "create_")):
        return "legacy-lifecycle", "review-port", "Inspect setup/start/update/uninstall behavior for recovery"
    return "legacy-root", "review-port", f"Inspect legacy root artifact ({rel})"


def main() -> int:
    rows = []
    for relative in tracked_files():
        absolute = ROOT / relative
        data = absolute.read_bytes()
        area, disposition, reason = classify(relative)
        rows.append({
            "path": relative.replace("\\", "/"),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "area": area,
            "initial_disposition": disposition,
            "reason": reason,
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} tracked paths to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
