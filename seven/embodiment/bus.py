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
        self.last_result: Optional[Dict[str, Any]] = None

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

    def _command(self, action: str, params: Dict[str, Any]) -> str:
        action = (action or "").strip().lower()
        if action == "led_on": return "LED_ON"
        if action == "led_off": return "LED_OFF"
        if action == "led_blink": return f"LED_BLINK {max(1, min(100, int(params.get('times', 3))))}"
        if action == "scan": return "SCAN"
        if action == "celebrate": return "CELEBRATE"
        if action == "alert": return "ALERT"
        if action == "idle_breathe": return "IDLE_BREATHE"
        if action == "servo_move": return f"SERVO {max(0, min(180, int(params.get('angle', 90))))}"
        if action == "motor_forward": return f"MOTOR_FWD {max(0, min(255, int(params.get('speed', 100))))}"
        if action == "motor_stop": return "MOTOR_STOP"
        if action == "buzzer_beep": return "BUZZER"
        raise ValueError(f"unknown robot action: {action}")

    def execute_named(self, action: str, params: Optional[Dict] = None) -> bool:
        params = params or {}
        try:
            line = self._command(action, params)
        except (TypeError, ValueError) as exc:
            self.last_error = str(exc)
            self.last_result = {"ok": False, "state": "rejected", "action": action, "error": str(exc)}
            self.action_log.append(self.last_result.copy())
            return False
        self.last_action = line
        entry = {"action": action, "line": line, "ts": datetime.now().isoformat(), "ok": False, "state": "not_sent"}
        if not self.connected:
            entry["error"] = "robot is not connected"
            self.action_log.append(entry)
            self.last_result = entry
            self.last_error = entry["error"]
            logger.warning("Embodiment action not sent: %s", line)
            return False
        try:
            with self.lock:
                self.conn.write((line + "\n").encode("utf-8"))
                if hasattr(self.conn, "flush"):
                    self.conn.flush()
                response = self.conn.readline().decode("utf-8", errors="replace").strip() if hasattr(self.conn, "readline") else ""
            entry["state"] = "acknowledged" if response.startswith("ACK") else "sent_unacknowledged"
            entry["response"] = response or None
            entry["ok"] = response.startswith("ACK")
            self.action_log.append(entry)
            self.last_result = entry
            self.last_error = None if entry["ok"] else "command sent but no ACK received"
            return entry["ok"]
        except Exception as e:
            self.last_error = str(e)
            entry["state"] = "send_failed"
            entry["error"] = str(e)
            self.action_log.append(entry)
            self.last_result = entry
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
            "actions_attempted": len(self.action_log),
            "last_result": self.last_result,
        }
