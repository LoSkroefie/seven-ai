# Native Extensions

Seven loads user-owned Python extensions from `SEVEN_EXTENSIONS_DIR` (default `~/.seven/extensions`) when `SEVEN_EXTENSIONS=1`.

An extension is a `.py` file defining:

```python
from seven.tools.registry import Tool

def register(registry):
    registry.register(Tool(
        name="my_tool",
        description="What the tool really does.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: "real result",
    ))
```

`extension_status` reports every discovered file, state, tools and load error. `extension_reload` removes tools owned by the prior load, unloads modules and imports current files again. Partial registrations are rolled back on failure. Extensions cannot replace an existing core or other extension tool.

## Trust model

Extensions execute natively as the logged-in user and are not sandboxed. Seven does not claim an AST import scan makes arbitrary Python safe. Install only code you trust. Extension tool calls still pass through the normal registry audit.

## Legacy recovery boundary

This restores a real hot-reloadable tool-extension contract without reviving `_legacy/v3/utils/plugin_loader.py` or automatically claiming its many extensions work. Legacy extensions using `on_message`, background schedules or old bot attributes must be ported individually with modern data, lifecycle and tests.
