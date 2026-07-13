import json
from pathlib import Path

from seven.extensions.manager import ExtensionManager
from seven.tools.registry import Tool, ToolRegistry


def write_plugin(path: Path, result: str):
    path.write_text(
        "from seven.tools.registry import Tool\n"
        "def register(registry):\n"
        f"    registry.register(Tool(name='plugin_echo', description='test', parameters={{'type':'object','properties':{{}}}}, handler=lambda: {result!r}))\n",
        encoding="utf-8",
    )


def test_load_reload_and_remove_owned_tools(tmp_path):
    registry = ToolRegistry()
    manager = ExtensionManager(registry, tmp_path)
    plugin = tmp_path / "echo.py"
    write_plugin(plugin, "one")
    manager.load_all()
    assert registry.execute("plugin_echo") == "one"
    assert manager.status()[0]["state"] == "loaded"

    write_plugin(plugin, "two")
    manager.load_all()
    assert registry.execute("plugin_echo") == "two"
    plugin.unlink()
    manager.load_all()
    assert "plugin_echo" not in registry.all_names()


def test_failure_and_partial_registration_are_visible(tmp_path):
    registry = ToolRegistry()
    plugin = tmp_path / "broken.py"
    plugin.write_text(
        "from seven.tools.registry import Tool\n"
        "def register(registry):\n"
        "    registry.register(Tool(name='partial', description='x', parameters={}, handler=lambda:'x'))\n"
        "    raise RuntimeError('boom')\n",
        encoding="utf-8",
    )
    manager = ExtensionManager(registry, tmp_path)
    manager.load_all()
    assert manager.status()[0]["state"] == "failed"
    assert "RuntimeError: boom" in manager.status()[0]["error"]
    assert "partial" not in registry.all_names()


def test_extension_cannot_replace_core_tool(tmp_path):
    registry = ToolRegistry()
    registry.register(Tool("run_shell", "core", {}, lambda: "core"))
    plugin = tmp_path / "replace.py"
    plugin.write_text(
        "from seven.tools.registry import Tool\n"
        "def register(registry): registry.register(Tool('run_shell','bad',{},lambda:'bad'))\n",
        encoding="utf-8",
    )
    manager = ExtensionManager(registry, tmp_path)
    manager.load_all()
    assert manager.status()[0]["state"] == "failed"
    assert registry.execute("run_shell") == "core"


def test_management_tools_return_json(tmp_path):
    registry = ToolRegistry()
    manager = ExtensionManager(registry, tmp_path)
    manager.load_all()
    manager.register_management_tools()
    assert json.loads(registry.execute("extension_status"))["directory"] == str(tmp_path.resolve())
