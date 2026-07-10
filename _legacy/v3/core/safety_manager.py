"""
Seven AI — Autonomous Action Safety Manager

Kill switch, action gating, and audit logging for autonomous behavior.
Addresses DeepSeek's critique: autonomous actions need safety controls.

Features:
- Global kill switch (hotkey or API call)
- Action classification (safe/moderate/dangerous)
- User confirmation for dangerous actions
- Full audit log of all autonomous actions
- Rate limiting to prevent runaway loops

Usage:
    from core.safety_manager import SafetyManager, ActionRisk

    safety = SafetyManager()
    if safety.can_execute("delete_file", ActionRisk.DANGEROUS):
        # Will require confirmation in interactive mode
        # Will be blocked in safe mode
        do_dangerous_thing()
"""

import logging
import threading
import time
from enum import Enum, auto
from typing import Optional, Callable, Dict, List
from datetime import datetime, timedelta


class ActionRisk(Enum):
    """Risk classification for autonomous actions"""
    SAFE = auto()       # Reading, observing, internal processing
    MODERATE = auto()   # Writing files, sending messages, web requests
    DANGEROUS = auto()  # System commands, mouse/keyboard, file deletion
    CRITICAL = auto()   # Self-modification, installing packages, admin ops


class SafetyMode(Enum):
    """Operating safety modes"""
    AUTONOMOUS = auto()    # All actions allowed (expert users)
    SUPERVISED = auto()    # Dangerous+ requires confirmation (default)
    SAFE = auto()          # Only SAFE actions allowed
    LOCKED = auto()        # Kill switch active — nothing executes


# Default risk classification for known action types
ACTION_RISK_MAP: Dict[str, ActionRisk] = {
    # SAFE
    "read_file": ActionRisk.SAFE,
    "list_directory": ActionRisk.SAFE,
    "web_search": ActionRisk.SAFE,
    "memory_recall": ActionRisk.SAFE,
    "emotion_update": ActionRisk.SAFE,
    "reflection": ActionRisk.SAFE,
    "dream_cycle": ActionRisk.SAFE,
    "social_sim": ActionRisk.SAFE,
    "speak": ActionRisk.SAFE,
    # MODERATE
    "write_file": ActionRisk.MODERATE,
    "send_message": ActionRisk.MODERATE,
    "send_email": ActionRisk.MODERATE,
    "create_note": ActionRisk.MODERATE,
    "set_reminder": ActionRisk.MODERATE,
    "web_request": ActionRisk.MODERATE,
    "take_screenshot": ActionRisk.MODERATE,
    # DANGEROUS
    "delete_file": ActionRisk.DANGEROUS,
    "mouse_click": ActionRisk.DANGEROUS,
    "keyboard_type": ActionRisk.DANGEROUS,
    "screen_control": ActionRisk.DANGEROUS,
    "execute_command": ActionRisk.DANGEROUS,
    "ssh_command": ActionRisk.DANGEROUS,
    "move_file": ActionRisk.DANGEROUS,
    # CRITICAL
    "install_package": ActionRisk.CRITICAL,
    "modify_config": ActionRisk.CRITICAL,
    "self_modify_code": ActionRisk.CRITICAL,
    "admin_command": ActionRisk.CRITICAL,
    "shutdown_system": ActionRisk.CRITICAL,
}


class SafetyManager:
    """
    Thread-safe safety manager for Seven AI autonomous actions.
    """

    def __init__(self, mode: SafetyMode = SafetyMode.SUPERVISED,
                 logger: Optional[logging.Logger] = None,
                 confirmation_callback: Optional[Callable] = None):
        self._lock = threading.Lock()
        self._mode = mode
        self._killed = False
        self._kill_time: Optional[datetime] = None
        self._audit_log: List[dict] = []
        self._max_audit = 500
        self._action_counts: Dict[str, int] = {}
        self._rate_window_start = datetime.now()
        self._rate_limit = 60  # max actions per minute
        self._action_count_window = 0
        self.logger = logger or logging.getLogger("SafetyManager")
        self._confirmation_callback = confirmation_callback

    @property
    def mode(self) -> SafetyMode:
        return self._mode

    @property
    def is_killed(self) -> bool:
        return self._killed

    def kill(self, reason: str = "manual"):
        """Emergency kill switch — immediately blocks all autonomous actions"""
        with self._lock:
            self._killed = True
            self._kill_time = datetime.now()
            self._mode = SafetyMode.LOCKED
            self.logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
            self._audit("KILL_SWITCH", "system", ActionRisk.CRITICAL,
                        blocked=False, reason=reason)

    def unkill(self, reason: str = "manual"):
        """Deactivate kill switch and return to supervised mode"""
        with self._lock:
            self._killed = False
            self._kill_time = None
            self._mode = SafetyMode.SUPERVISED
            self.logger.warning(f"Kill switch deactivated: {reason}")
            self._audit("UNKILL", "system", ActionRisk.CRITICAL,
                        blocked=False, reason=reason)

    def set_mode(self, mode: SafetyMode):
        """Change safety mode"""
        with self._lock:
            old = self._mode
            self._mode = mode
            if mode != SafetyMode.LOCKED:
                self._killed = False
            self.logger.info(f"Safety mode: {old.name} -> {mode.name}")

    def classify_action(self, action_type: str) -> ActionRisk:
        """Get risk level for an action type"""
        return ACTION_RISK_MAP.get(action_type, ActionRisk.MODERATE)

    def can_execute(self, action_type: str,
                    risk: Optional[ActionRisk] = None,
                    details: str = "") -> bool:
        """
        Check if an action is allowed under current safety mode.

        Args:
            action_type: Type of action (e.g. "mouse_click", "read_file")
            risk: Override risk classification (auto-detected if None)
            details: Description for audit log

        Returns:
            True if action is allowed, False if blocked
        """
        if risk is None:
            risk = self.classify_action(action_type)

        with self._lock:
            # Kill switch blocks everything
            if self._killed:
                self._audit(action_type, details, risk, blocked=True,
                            reason="Kill switch active")
                return False

            # Rate limiting
            now = datetime.now()
            if (now - self._rate_window_start) > timedelta(minutes=1):
                self._rate_window_start = now
                self._action_count_window = 0

            self._action_count_window += 1
            if self._action_count_window > self._rate_limit:
                self._audit(action_type, details, risk, blocked=True,
                            reason=f"Rate limit exceeded ({self._rate_limit}/min)")
                self.logger.warning(f"Rate limit hit: {self._action_count_window} actions/min")
                return False

            # Mode-based gating
            allowed = False
            reason = ""

            if self._mode == SafetyMode.LOCKED:
                reason = "Safety mode: LOCKED"
                allowed = False

            elif self._mode == SafetyMode.SAFE:
                allowed = risk == ActionRisk.SAFE
                if not allowed:
                    reason = f"Safe mode blocks {risk.name} actions"

            elif self._mode == SafetyMode.SUPERVISED:
                if risk in (ActionRisk.SAFE, ActionRisk.MODERATE):
                    allowed = True
                elif risk in (ActionRisk.DANGEROUS, ActionRisk.CRITICAL):
                    # Ask for confirmation if callback available
                    if self._confirmation_callback:
                        try:
                            allowed = self._confirmation_callback(
                                action_type, risk.name, details
                            )
                            reason = "User confirmed" if allowed else "User denied"
                        except Exception as e:
                            self.logger.error(f"Confirmation callback error: {e}")
                            allowed = False
                            reason = f"Confirmation error: {e}"
                    else:
                        # No callback = suggest but don't execute
                        allowed = False
                        reason = "No confirmation callback — action suggested only"

            elif self._mode == SafetyMode.AUTONOMOUS:
                allowed = True

            # Track and audit
            self._action_counts[action_type] = self._action_counts.get(action_type, 0) + 1
            self._audit(action_type, details, risk, blocked=not allowed, reason=reason)

            if not allowed:
                self.logger.info(f"BLOCKED: {action_type} ({risk.name}) — {reason}")

            return allowed

    def get_status(self) -> dict:
        """Get safety manager status"""
        return {
            'mode': self._mode.name,
            'killed': self._killed,
            'kill_time': self._kill_time.isoformat() if self._kill_time else None,
            'actions_this_minute': self._action_count_window,
            'rate_limit': self._rate_limit,
            'total_actions': sum(self._action_counts.values()),
            'action_breakdown': dict(self._action_counts),
            'recent_audit': self._audit_log[-10:],
        }

    def get_audit_log(self, limit: int = 50) -> List[dict]:
        """Get recent audit entries"""
        return self._audit_log[-limit:]

    def _audit(self, action_type: str, details: str, risk: ActionRisk,
               blocked: bool, reason: str = ""):
        """Record action in audit log"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type,
            'risk': risk.name,
            'blocked': blocked,
            'reason': reason,
            'details': details[:200],  # truncate long details
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > self._max_audit:
            self._audit_log = self._audit_log[-self._max_audit:]
