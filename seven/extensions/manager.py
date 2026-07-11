"""Native, accountable extension discovery and tool lifecycle."""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

logger = logging.getLogger("seven.extensions")


@dataclass
class ExtensionRecord:
    name: str
    path: str
    state: str
    tools: list[str] = field(default_factory=list)
    error: str = ""
    module_name: str = ""


class ExtensionManager:
    def __init__(self, registry, directory: Path):
        self.registry = registry
        self.directory = Path(directory).expanduser().resolve()
        self.records: dict[str, ExtensionRecord] = {}
        self._owned_tools: set[str] = set()

    def discover(self) -> list[Path]:
        self.directory.mkdir(parents=True, exist_ok=True)
        return sorted(
            path for path in self.directory.glob("*.py")
            if path.name != "__init__.py" and not path.name.startswith(".")
        )

    def _module_name(self, path: Path) -> str:
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]
        return f"seven_user_extension_{digest}"

    def _unload_owned_tools(self):
        for name in sorted(self._owned_tools):
            self.registry.unregister(name)
        self._owned_tools.clear()
        for record in self.records.values():
            if record.module_name:
                sys.modules.pop(record.module_name, None)

    def load_all(self) -> list[dict[str, Any]]:
        self._unload_owned_tools()
        self.records = {}
        for path in self.discover():
            self._load(path)
        return self.status()

    def _load(self, path: Path):
        name = path.stem
        module_name = self._module_name(path)
        record = ExtensionRecord(name=name, path=str(path), state="loading", module_name=module_name)
        before = set(self.registry.all_names())
        try:
            module = ModuleType(module_name)
            module.__file__ = str(path)
            module.__package__ = ""
            sys.modules[module_name] = module
            source = path.read_text(encoding="utf-8")
            exec(compile(source, str(path), "exec"), module.__dict__)
            register = getattr(module, "register", None)
            if not callable(register):
                raise TypeError("extension must define register(registry)")
            register(self.registry)
            after = set(self.registry.all_names())
            tools = sorted(after - before)
            if not tools:
                raise ValueError("extension registered no tools")
            record.state = "loaded"
            record.tools = tools
            self._owned_tools.update(tools)
        except Exception as exc:
            after = set(self.registry.all_names())
            for tool in after - before:
                self.registry.unregister(tool)
            sys.modules.pop(module_name, None)
            record.state = "failed"
            record.error = f"{type(exc).__name__}: {exc}"
            logger.exception("Extension failed: %s", path)
        self.records[name] = record

    def status(self) -> list[dict[str, Any]]:
        return [
            {"name": r.name, "path": r.path, "state": r.state, "tools": r.tools, "error": r.error}
            for r in sorted(self.records.values(), key=lambda item: item.name)
        ]

    def status_text(self) -> str:
        return json.dumps({"directory": str(self.directory), "extensions": self.status()}, indent=2)

    def reload_text(self) -> str:
        return json.dumps({"directory": str(self.directory), "extensions": self.load_all()}, indent=2)

    def register_management_tools(self):
        from seven.tools.registry import Tool
        self.registry.register(Tool(
            name="extension_status",
            description="List native Seven extensions, registered tools and visible failures.",
            parameters={"type": "object", "properties": {}},
            handler=lambda: self.status_text(),
        ))
        self.registry.register(Tool(
            name="extension_reload",
            description="Reload all native Seven extensions from the configured extensions directory.",
            parameters={"type": "object", "properties": {}},
            handler=lambda: self.reload_text(),
        ))
