"""Robotics tools backed by Seven's acknowledged serial embodiment bus."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from seven import config

logger = logging.getLogger("seven.robotics")

_controller = None


def _get_controller():
    global _controller
    if _controller is not None:
        return _controller
    try:
        from seven.embodiment.bus import EmbodimentBus
        _controller = EmbodimentBus()
        return _controller
    except Exception as exc:
        logger.debug("embodiment bus init: %s", exc)
        return None


def robot_status() -> str:
    c = _get_controller()
    if c is None:
        return json.dumps({
            "available": False,
            "message": "No robotics backend loaded. Serial bus ready when hardware connected.",
            "enable_flag": config.ENABLE_ROBOTICS,
            "port": config.ROBOTICS_PORT or "(auto)",
        })
    if hasattr(c, "get_status"):
        return json.dumps(c.get_status(), default=str)
    return json.dumps({"available": True, "controller": type(c).__name__})


def robot_connect(port: str = "") -> str:
    c = _get_controller()
    if c is None:
        return "ERROR: no robotics backend"
    port = port or config.ROBOTICS_PORT
    if hasattr(c, "connect"):
        ok = c.connect() if not port else c.connect(port) if _accepts_port(c.connect) else c.connect()
        return "OK connected" if ok else "ERROR: connect failed"
    return "ERROR: controller has no connect()"


def robot_disconnect() -> str:
    c = _get_controller()
    if c is None or not hasattr(c, "disconnect"):
        return "ERROR: no disconnect-capable robotics backend"
    c.disconnect()
    return "OK disconnected"


def robot_list_ports() -> str:
    c = _get_controller()
    if c is None or not hasattr(c, "list_ports"):
        return "ERROR: no serial port discovery backend"
    return json.dumps(c.list_ports(), default=str)


def _accepts_port(fn) -> bool:
    import inspect
    try:
        return "port" in inspect.signature(fn).parameters
    except Exception:
        return False


def robot_action(action: str, params_json: str = "{}") -> str:
    c = _get_controller()
    if c is None:
        return "ERROR: no robotics backend; action was not sent: " + action
    try:
        params = json.loads(params_json) if params_json else {}
    except json.JSONDecodeError:
        params = {"raw": params_json}
    if hasattr(c, "execute_named"):
        ok = c.execute_named(action, params)
        result = getattr(c, "last_result", None)
        if result:
            return json.dumps(result, default=str)
        return f"ACK action={action}" if ok else f"ERROR action={action}"
    return "ERROR: controller cannot execute actions"


def register(reg):
    from seven.tools.registry import Tool

    reg.register(Tool(
        name="robot_status",
        description="Check robotics/embodiment bus status (serial robot, future mobile/wearable).",
        parameters={"type": "object", "properties": {}},
        handler=lambda: robot_status(),
    ))
    reg.register(Tool(
        name="robot_connect",
        description="Connect to robot hardware on a serial port.",
        parameters={
            "type": "object",
            "properties": {"port": {"type": "string"}},
        },
        handler=robot_connect,
    ))
    reg.register(Tool(
        name="robot_disconnect",
        description="Disconnect the active serial robot.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: robot_disconnect(),
    ))
    reg.register(Tool(
        name="robot_list_ports",
        description="List serial ports available for robot connection.",
        parameters={"type": "object", "properties": {}},
        handler=lambda: robot_list_ports(),
    ))
    reg.register(Tool(
        name="robot_action",
        description="Execute a robot action: led_on, led_off, led_blink, scan, celebrate, alert, idle_breathe, servo_move, motor_forward, motor_stop, buzzer_beep.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "params_json": {"type": "string", "description": "JSON object of params"},
            },
            "required": ["action"],
        },
        handler=robot_action,
    ))
