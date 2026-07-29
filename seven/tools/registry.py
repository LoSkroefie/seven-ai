"""
Tool registry — OpenAI/Ollama function-calling schemas + executors.
L4: tools run for real. Every call is audited via Memory.
Supports tiers: lean (small shared hosts), core (desktop co-pilot), and full.
"""
from __future__ import annotations

import json
import logging
import re
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from seven.memory.store import Memory
from seven.tools.sanitize import sanitize_arguments

logger = logging.getLogger("seven.tools")

_EXIT_CODE = re.compile(r"(?:^|\s)exit_code=(-?\d+)(?:\s|$)")


def result_is_success(result: Any) -> bool:
    """Classify a tool result conservatively for audit and autonomy."""
    text = "" if result is None else str(result)
    stripped = text.lstrip()
    if stripped.startswith("ERROR"):
        return False
    match = _EXIT_CODE.search(text)
    if match and int(match.group(1)) != 0:
        return False
    if "timed out after" in text.lower():
        return False
    if stripped.startswith(("{", "[")):
        try:
            payload = json.loads(stripped)
            if isinstance(payload, dict) and payload.get("ok") is False:
                return False
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return True

# Tools always exposed in "core" tier — enough for desktop co-pilot on small LLMs
CORE_TOOL_NAMES: Set[str] = {
    "run_shell",
    "read_file",
    "write_file",
    "list_dir",
    "list_projects",
    "search_files",
    "run_python",
    "get_system_info",
    "web_search",
    "web_fetch",
    "browser_get",
    "open_url",
    "list_windows",
    "active_window",
    "screenshot",
    "screen_size",
    "mouse_click",
    "mouse_move",
    "type_text",
    "hotkey",
    "remember_fact",
    "search_memory",
    "semantic_search",
    "index_memory",
    "form_belief",
    "list_beliefs",
    "wm_push",
    "wm_show",
    "save_skill",
    "list_skills",
    "run_skill",
    "create_plan",
    "plan_from_goal",
    "advance_plan",
    "write_digest",
    "set_preference",
    "add_task",
    "list_tasks",
    "complete_task",
    "add_note",
    "list_notes",
    "add_goal",
    "list_goals",
    "update_goal",
    "submit_goal_evidence",
    "list_goal_evidence",
    "get_clipboard",
    "set_clipboard",
    "list_cameras",
    "capture_webcam",
    "analyze_image",
    "see_screen",
    "see_webcam",
    "check_presence",
}

# Minimal cognitive tool surface for small CPU-hosted models. Every registered
# tool remains directly executable and the owner can switch to core/full.
LEAN_TOOL_NAMES: Set[str] = {
    "get_system_info",
    "list_projects",
    "remember_fact",
    "search_memory",
    "semantic_search",
    "form_belief",
    "list_beliefs",
    "save_skill",
    "list_skills",
    "run_skill",
    "add_goal",
    "list_goals",
    "update_goal",
    "submit_goal_evidence",
    "list_goal_evidence",
    "create_plan",
    "advance_plan",
}

# Extended sets (still in full tier)
FULL_ONLY_HINT = (
    "delete_path", "move_path", "mouse_click", "mouse_move", "type_text", "hotkey",
    "capture_webcam", "analyze_image", "see_screen",
    "add_goal", "update_goal", "list_goals",
    "coding_agent_status", "run_opencode", "run_claude_cli", "run_codex_cli", "run_aider",
    "robot_status", "robot_connect", "robot_action",
)


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., str]
    enabled: bool = True
    tier: str = "full"  # "core" | "full" — core tools also set tier=core at register time
    tags: List[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self, memory: Optional[Memory] = None, tier: str = "full"):
        self.memory = memory
        self.tier = (tier or "full").lower()
        self._tools: Dict[str, Tool] = {}

    def set_tier(self, tier: str):
        self.tier = (tier or "full").lower()

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        # Auto-tag core membership
        if tool.name in CORE_TOOL_NAMES:
            tool.tier = "core"
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        return self._tools.pop(name, None) is not None

    def _is_active(self, tool: Tool) -> bool:
        if not tool.enabled:
            return False
        if self.tier == "full":
            return True
        if self.tier == "lean":
            return tool.name in LEAN_TOOL_NAMES
        if self.tier == "core":
            return tool.tier == "core" or tool.name in CORE_TOOL_NAMES
        return True

    def schemas(self) -> List[Dict[str, Any]]:
        out = []
        for t in self._tools.values():
            if not self._is_active(t):
                continue
            out.append(self._schema(t))
        return out

    @staticmethod
    def _schema(tool: Tool) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    def all_schemas(self) -> List[Dict[str, Any]]:
        """Schemas for every enabled tool, independent of presentation tier."""
        return [
            self._schema(tool)
            for tool in self._tools.values()
            if tool.enabled
        ]

    def schema_for(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an enabled tool schema even when its tier is not displayed."""
        tool = self._tools.get(str(name))
        if tool is None or not tool.enabled:
            return None
        return self._schema(tool)

    def names(self) -> List[str]:
        return sorted(n for n, t in self._tools.items() if self._is_active(t))

    def all_names(self) -> List[str]:
        return sorted(self._tools.keys())

    def execute(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a tool by name.
        Tiers control schema exposure, not authority. A deliberately disabled tool,
        however, must never execute through the registry.
        """
        arguments = arguments if isinstance(arguments, dict) else {}
        tool = self._tools.get(name)
        if not tool:
            result = f"ERROR: unknown tool '{name}'. Use list_tools to discover tools."
            if self.memory:
                self.memory.audit(name, arguments, result, ok=False)
            return result
        if not tool.enabled:
            result = f"ERROR: tool '{name}' is disabled"
            if self.memory:
                self.memory.audit(name, arguments, result, ok=False)
            return result

        params = tool.parameters or {}
        props = params.get("properties") or {}
        required = params.get("required") or []
        kwargs = sanitize_arguments(arguments, properties=props, required=required)

        try:
            result = tool.handler(**kwargs)
            if result is None:
                result = ""
            result = str(result)
            if len(result) > 50000:
                result = result[:50000] + "\n...[truncated]"
            if self.memory:
                self.memory.audit(name, kwargs, result, ok=result_is_success(result))
            return result
        except TypeError:
            # Retry with looser kwargs (drop unknowns already done; try original cleaned)
            try:
                loose = {k: v for k, v in arguments.items() if not _is_blank_loose(v)}
                loose = sanitize_arguments(loose, properties=props, required=required)
                result = str(tool.handler(**loose))
                if self.memory:
                    self.memory.audit(name, loose, result, ok=result_is_success(result))
                return result
            except Exception as e2:
                result = f"ERROR executing {name}: {e2}\n{traceback.format_exc()[-800:]}"
                if self.memory:
                    self.memory.audit(name, arguments, result, ok=False)
                return result
        except Exception as e:
            result = f"ERROR executing {name}: {e}\n{traceback.format_exc()[-800:]}"
            logger.exception("Tool %s failed", name)
            if self.memory:
                self.memory.audit(name, arguments, result, ok=False)
            return result


def _is_blank_loose(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() in ("", "null", "None", "undefined"):
        return True
    return False


def build_default_registry(
    memory: Memory,
    brain=None,
    tier: Optional[str] = None,
    agent=None,
) -> ToolRegistry:
    """Wire all real tools; expose schemas per tier."""
    from seven import config
    from seven.tools import (
        shell, files, screen, web, vision, code_run,
        system_info, notes_tasks, projects, clipboard, coding_agent, robotics_bus,
        desktop_windows, browser, mind_tools, ollama_manager, notifications, action_items, documents, music, ssh, github_reader,
    )

    use_tier = (tier or getattr(config, "TOOL_TIER", "full") or "full").lower()
    reg = ToolRegistry(memory=memory, tier=use_tier)

    shell.register(reg)
    files.register(reg)
    screen.register(reg)
    web.register(reg)
    vision.register(reg, brain=brain)
    code_run.register(reg)
    system_info.register(reg)
    notes_tasks.register(reg, memory=memory)
    projects.register(reg, memory=memory)
    clipboard.register(reg)
    coding_agent.register(reg)
    robotics_bus.register(reg)
    desktop_windows.register(reg)
    browser.register(reg)
    mind_tools.register(reg, memory=memory, agent=agent)
    ollama_manager.register(reg, brain=brain)
    notifications.register(reg)
    action_items.register(reg, memory=memory)
    documents.register(reg)
    music.register(reg)
    ssh.register(reg)
    github_reader.register(reg)

    if getattr(config, "ENABLE_EXTENSIONS", True):
        from seven.extensions.manager import ExtensionManager
        manager = ExtensionManager(reg, config.EXTENSIONS_DIR)
        manager.load_all()
        manager.register_management_tools()
        reg.extension_manager = manager

    logger.info("Tool registry tier=%s active=%s total=%s", use_tier, len(reg.names()), len(reg.all_names()))
    return reg
