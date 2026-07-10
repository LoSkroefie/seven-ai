"""Filesystem tools — read/write/list/search."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


def read_file(path: str, max_bytes: int = 200_000) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: not found: {p}"
    if p.is_dir():
        return f"ERROR: is a directory: {p}"
    data = p.read_bytes()
    truncated = False
    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    out = f"path={p.resolve()}\nsize={p.stat().st_size}\n\n{text}"
    if truncated:
        out += "\n...[truncated]"
    return out


def write_file(path: str, content: str, mode: str = "overwrite") -> str:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append" and p.exists():
        with p.open("a", encoding="utf-8") as f:
            f.write(content)
    else:
        p.write_text(content, encoding="utf-8")
    return f"OK wrote {len(content)} chars to {p.resolve()}"


def list_dir(path: str = ".", max_entries: int = 200) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: not found: {p}"
    if not p.is_dir():
        return f"ERROR: not a directory: {p}"
    entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = [f"{p.resolve()} ({len(entries)} entries)"]
    for i, e in enumerate(entries[:max_entries]):
        kind = "DIR " if e.is_dir() else "FILE"
        try:
            size = e.stat().st_size if e.is_file() else 0
        except OSError:
            size = -1
        lines.append(f"  {kind} {e.name}" + (f"  ({size} B)" if e.is_file() else ""))
    if len(entries) > max_entries:
        lines.append(f"  ... +{len(entries) - max_entries} more")
    return "\n".join(lines)


def search_files(root: str, pattern: str, max_hits: int = 50) -> str:
    """Glob search under root."""
    root_p = Path(root).expanduser()
    if not root_p.exists():
        return f"ERROR: not found: {root_p}"
    hits = list(root_p.rglob(pattern))[:max_hits]
    if not hits:
        return f"No matches for '{pattern}' under {root_p}"
    return "\n".join(str(h) for h in hits)


def delete_path(path: str, recursive: bool = False) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: not found: {p}"
    if p.is_dir():
        if recursive:
            shutil.rmtree(p)
            return f"OK deleted directory tree {p}"
        try:
            p.rmdir()
            return f"OK deleted empty directory {p}"
        except OSError as e:
            return f"ERROR: {e} (use recursive=true for non-empty dirs)"
    p.unlink()
    return f"OK deleted file {p}"


def move_path(src: str, dst: str) -> str:
    s, d = Path(src).expanduser(), Path(dst).expanduser()
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d))
    return f"OK moved {s} -> {d}"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="read_file",
        description="Read a text file from disk.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_bytes": {"type": "integer"},
            },
            "required": ["path"],
        },
        handler=read_file,
    ))
    reg.register(Tool(
        name="write_file",
        description="Write or append text to a file. Creates parent dirs.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "description": "overwrite|append", "enum": ["overwrite", "append"]},
            },
            "required": ["path", "content"],
        },
        handler=write_file,
    ))
    reg.register(Tool(
        name="list_dir",
        description="List directory contents.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_entries": {"type": "integer"},
            },
        },
        handler=list_dir,
    ))
    reg.register(Tool(
        name="search_files",
        description="Glob search for files under a root path (e.g. pattern='*.py').",
        parameters={
            "type": "object",
            "properties": {
                "root": {"type": "string"},
                "pattern": {"type": "string"},
                "max_hits": {"type": "integer"},
            },
            "required": ["root", "pattern"],
        },
        handler=search_files,
    ))
    reg.register(Tool(
        name="delete_path",
        description="Delete a file or directory.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "recursive": {"type": "boolean"},
            },
            "required": ["path"],
        },
        handler=delete_path,
    ))
    reg.register(Tool(
        name="move_path",
        description="Move/rename a file or directory.",
        parameters={
            "type": "object",
            "properties": {
                "src": {"type": "string"},
                "dst": {"type": "string"},
            },
            "required": ["src", "dst"],
        },
        handler=move_path,
    ))
