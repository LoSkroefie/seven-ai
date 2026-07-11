"""Parse every legacy Python file and record its recoverable code surface."""
from __future__ import annotations

import ast
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "_legacy" / "v3"
OUTPUT = ROOT / "docs" / "LEGACY_SYMBOL_INVENTORY.csv"


def main() -> int:
    rows = []
    for path in sorted(LEGACY.rglob("*.py")):
        raw = path.read_bytes()
        if b"\0" not in raw:
            raw = raw.replace(b"\r\n", b"\n")
        text = raw.decode("utf-8", errors="replace")
        classes: list[str] = []
        functions: list[str] = []
        imports: set[str] = set()
        error = ""
        try:
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef,)):
                    classes.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
        except SyntaxError as exc:
            error = f"{exc.msg} line {exc.lineno}"
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(raw),
            "lines": len(text.splitlines()),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "syntax": "ok" if not error else "error",
            "syntax_error": error,
            "classes": ";".join(sorted(set(classes))),
            "functions": ";".join(sorted(set(functions))),
            "imports": ";".join(sorted(imports)),
        })
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    errors = sum(row["syntax"] == "error" for row in rows)
    print(f"Wrote {len(rows)} legacy Python files to {OUTPUT.relative_to(ROOT)}; syntax errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
