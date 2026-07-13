"""Desktop notification tools."""
from seven.runtime.notifications import notification_status_text, notify_desktop


def register(reg):
    from seven.tools.registry import Tool
    reg.register(Tool(
        name="notification_status",
        description="Report the native desktop notification backend and availability.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: notification_status_text(),
    ))
    reg.register(Tool(
        name="notify_desktop",
        description="Submit a native desktop notification. Success means submitted, not proven viewed.",
        parameters={
            "type": "object",
            "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
            "required": ["title", "body"],
        },
        handler=notify_desktop,
    ))
