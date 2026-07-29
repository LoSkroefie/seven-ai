"""Grounded project catalog and bounded filesystem discovery."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional

from seven import config

PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "pom.xml",
)


def _roots() -> list[Path]:
    values = [config.WORKSPACE_DIR, config.BASE_DIR, *config.PROJECT_ROOTS]
    roots: list[Path] = []
    seen: set[str] = set()
    for value in values:
        try:
            resolved = Path(value).expanduser().resolve(strict=False)
        except OSError:
            continue
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            roots.append(resolved)
    return roots


def _marker_names(path: Path) -> list[str]:
    return [name for name in PROJECT_MARKERS if (path / name).exists()]


def _project_name(path: Path) -> str:
    pyproject = path / "pyproject.toml"
    if pyproject.is_file():
        try:
            import tomllib

            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            value = str((data.get("project") or {}).get("name") or "").strip()
            if value:
                return value
        except (OSError, UnicodeError, ValueError):
            pass
    package_json = path / "package.json"
    if package_json.is_file():
        try:
            value = str(
                (json.loads(package_json.read_text(encoding="utf-8")) or {}).get("name")
                or ""
            ).strip()
            if value:
                return value
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            pass
    return path.name or str(path)


def discover_projects(
    roots: Optional[Iterable[Path]] = None,
    max_projects: int = 100,
) -> list[dict[str, Any]]:
    """Inspect each allowed root and its immediate children only."""
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in list(roots) if roots is not None else _roots():
        try:
            root = Path(root).expanduser().resolve(strict=False)
        except OSError:
            continue
        if not root.is_dir():
            continue
        candidates = [root]
        try:
            candidates.extend(
                item
                for item in sorted(root.iterdir(), key=lambda p: p.name.casefold())
                if item.is_dir() and not item.is_symlink()
            )
        except OSError:
            pass
        for candidate in candidates:
            markers = _marker_names(candidate)
            if not markers:
                continue
            try:
                resolved = candidate.resolve(strict=False)
                modified_at = candidate.stat().st_mtime
            except OSError:
                continue
            key = os.path.normcase(str(resolved))
            if key in seen:
                continue
            seen.add(key)
            discovered.append(
                {
                    "name": _project_name(candidate),
                    "path": str(resolved),
                    "description": "",
                    "status": "active",
                    "source": "filesystem",
                    "markers": markers,
                    "modified_at": modified_at,
                }
            )
            if len(discovered) >= max(1, min(int(max_projects), 500)):
                return discovered
    return discovered


def _validated_project_path(path: str) -> Path:
    value = str(path or "").strip()
    if not value:
        raise ValueError("project path is required")
    candidate = Path(value).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"project path is not readable: {candidate}") from exc
    if not resolved.is_dir():
        raise ValueError(f"project path is not a directory: {resolved}")
    if not _marker_names(resolved):
        raise ValueError(f"no supported project marker found in: {resolved}")
    allowed = _roots()
    if not any(resolved == root or root in resolved.parents for root in allowed):
        raise ValueError(
            "project path is outside Seven's configured project roots"
        )
    return resolved


def list_projects(
    memory,
    refresh: bool = True,
    include_archived: bool = False,
    max_projects: int = 100,
) -> str:
    registered = memory.list_projects(include_archived=bool(include_archived))
    projects: list[dict[str, Any]] = [
        {
            "id": row["id"],
            "name": row["name"],
            "path": row.get("path") or "",
            "description": row.get("description") or "",
            "status": row.get("status") or "active",
            "source": row.get("source") or "user",
        }
        for row in registered
    ]
    discovered = (
        discover_projects(max_projects=max_projects)
        if bool(refresh)
        else []
    )
    known_paths = {
        os.path.normcase(str(Path(item["path"]).resolve(strict=False)))
        for item in projects
        if item.get("path")
    }
    for item in discovered:
        path_key = os.path.normcase(str(Path(item["path"]).resolve(strict=False)))
        if path_key not in known_paths:
            projects.append(item)
            known_paths.add(path_key)
    projects = projects[: max(1, min(int(max_projects), 500))]
    return json.dumps(
        {
            "ok": True,
            "workspace": str(config.WORKSPACE_DIR.resolve(strict=False)),
            "roots": [str(path) for path in _roots()],
            "registered_count": len(registered),
            "discovered_count": len(discovered),
            "count": len(projects),
            "projects": projects,
        },
        ensure_ascii=False,
    )


def register(reg, memory=None):
    from seven.tools.registry import Tool

    def catalog(
        refresh: bool = True,
        include_archived: bool = False,
        max_projects: int = 100,
    ) -> str:
        if memory is None:
            return "ERROR: memory not ready"
        return list_projects(
            memory,
            refresh=refresh,
            include_archived=include_archived,
            max_projects=max_projects,
        )

    def remember(path: str, status: str = "active") -> str:
        if memory is None:
            return "ERROR: memory not ready"
        try:
            resolved = _validated_project_path(path)
            name = _project_name(resolved)
            project_id = memory.register_project(
                name=name,
                path=str(resolved),
                description="",
                status=status,
                source="filesystem_verified",
            )
        except ValueError as exc:
            return f"ERROR: {exc}"
        return f"OK project #{project_id}: {name}"

    reg.register(Tool(
        name="list_projects",
        description=(
            "List registered projects plus projects actually visible in configured "
            "project roots. Use this for 'list my projects'; never invent projects."
        ),
        parameters={
            "type": "object",
            "properties": {
                "refresh": {"type": "boolean"},
                "include_archived": {"type": "boolean"},
                "max_projects": {"type": "integer"},
            },
        },
        handler=catalog,
    ))
    reg.register(Tool(
        name="register_project",
        description=(
            "Register a real project directory after validating that it exists, "
            "contains a project marker, and is inside a configured project root."
        ),
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["active", "paused", "archived"],
                },
            },
            "required": ["path"],
        },
        handler=remember,
    ))
