"""
Thin embodiment bus for robots, future mobile, wearables.
Serial protocol is simple line-based: CMD [ARG]
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from seven import config

logger = logging.getLogger("seven.embodiment")

try:
    import serial
    import serial.tools.list_ports
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False


class EmbodimentBus:
    """Hardware-agnostic action bus. Safe when nothing is plugged in."""

    def __init__(self, port: Optional[str] = None, baud: int = None):
        self.port = port or config.ROBOTICS_PORT or ""
        self.baud = baud or config.ROBOTICS_BAUD
        self.conn = None
        self.connected = False
        self.lock = threading.Lock()
        self.last_action: Optional[str] = None
        self.last_error: Optional[str] = None
        self.action_log: List[Dict[str, Any]] = []

    def list_ports(self) -> List[Dict[str, str]]:
        if not SERIAL_OK:
            return []
        return [
            {"device": p.device, "description": p.description or ""}
            for p in serial.tools.list_ports.comports()
        ]

    def connect(self, port: Optional[str] = None) -> bool:
        if not SERIAL_OK:
            self.last_error = "pyserial not installed"
            return False
        if port:
            self.port = port
        if not self.port:
            ports = self.list_ports()
            if not ports:
                self.last_error = "no serial ports found"
                return False
            self.port = ports[0]["device"]
        try:
            self.conn = serial.Serial(self.port, self.baud, timeout=2)
            self.connected = True
            self.last_error = None
            logger.info("Embodiment connected %s @ %s", self.port, self.baud)
            return True
        except Exception as e:
            self.last_error = str(e)
            self.connected = False
            return False

    def disconnect(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        self.conn = None
        self.connected = False

    def execute_named(self, action: str, params: Optional[Dict] = None) -> bool:
        params = params or {}
        cmd_map = {
            "led_on": "LED_ON",
            "led_off": "LED_OFF",
            "led_blink": f"LED_BLINK {params.get('times', 3)}",
            "scan": "SCAN",
            "celebrate": "CELEBRATE",
            "alert": "ALERT",
            "idle_breathe": "IDLE_BREATHE",
            "servo_move": f"SERVO {params.get('angle', 90)}",
            "motor_forward": f"MOTOR_FWD {params.get('speed', 100)}",
            "motor_stop": "MOTOR_STOP",
            "buzzer_beep": "BUZZER",
        }
        line = cmd_map.get(action.lower()) or action.upper()
        self.last_action = line
        entry = {"action": action, "line": line, "ts": datetime.now().isoformat(), "ok": False}
        if not self.connected:
            # Soft queue — logged, not fatal. Ready for when body exists.
            entry["queued"] = True
            self.action_log.append(entry)
            logger.info("Embodiment queued (not connected): %s", line)
            return True
        try:
            with self.lock:
                self.conn.write((line + "\n").encode("utf-8"))
            entry["ok"] = True
            self.action_log.append(entry)
            return True
        except Exception as e:
            self.last_error = str(e)
            self.action_log.append(entry)
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "serial_lib": SERIAL_OK,
            "connected": self.connected,
            "port": self.port or None,
            "baud": self.baud,
            "ports": self.list_ports(),
            "last_action": self.last_action,
            "last_error": self.last_error,
            "queued_or_sent": len(self.action_log),
        }
