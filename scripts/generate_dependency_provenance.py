"""Snapshot locked-package provenance and publisher-declared license metadata."""
from __future__ import annotations
import csv, json, tomllib, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "DEPENDENCY_PROVENANCE.csv"

def _metadata(item: tuple[str, str, str]) -> dict[str, str]:
    name, version, source = item
    row = {"name": name, "version": version, "source": source, "declared_license": "UNKNOWN", "project_url": ""}
    if name == "seven-ai" and source == "editable":
        row.update({"declared_license": "Apache-2.0", "project_url": "https://github.com/LoSkroefie/seven-ai"})
        return row
    if source != "registry": return row
    url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/{urllib.parse.quote(version)}/json"
    try:
        with urllib.request.urlopen(url, timeout=20) as response: info = json.load(response)["info"]
    except (OSError, KeyError, ValueError, urllib.error.URLError): return row
    expression = (info.get("license_expression") or "").strip()
    legacy = (info.get("license") or "").strip().replace("\r", " ").replace("\n", " ")
    classifiers = [v.removeprefix("License :: ").strip() for v in info.get("classifiers") or [] if v.startswith("License :: ")]
    row["declared_license"] = expression or legacy[:200] or " | ".join(classifiers) or "UNKNOWN"
    urls = info.get("project_urls") or {}
    row["project_url"] = urls.get("Source") or urls.get("Repository") or urls.get("Homepage") or info.get("home_page") or ""
    return row

def main() -> int:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = [(p["name"], p["version"], next(iter((p.get("source") or {"unknown": ""}).keys()))) for p in lock["package"]]
    with ThreadPoolExecutor(max_workers=16) as pool:
        rows = sorted(pool.map(_metadata, packages), key=lambda row: (row["name"].lower(), row["version"]))
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "version", "source", "declared_license", "project_url"], lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} locked packages to {OUTPUT.relative_to(ROOT)}; unknown license declarations={sum(r['declared_license'] == 'UNKNOWN' for r in rows)}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
