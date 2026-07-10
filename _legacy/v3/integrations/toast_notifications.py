"""
Windows Toast Notifications — Seven AI

Send desktop notifications for reminders, alerts, proactive thoughts.
Uses win10toast-persist or plyer as fallback.
"""

import logging
import threading
from typing import Optional

logger = logging.getLogger("ToastNotifications")

# Try multiple notification backends
BACKEND = None

try:
    from win10toast import ToastNotifier
    BACKEND = "win10toast"
except ImportError:
    pass

if not BACKEND:
    try:
        from plyer import notification as plyer_notification
        BACKEND = "plyer"
    except ImportError:
        pass


class ToastNotificationManager:
    """Send Windows desktop toast notifications"""

    def __init__(self):
        self.available = BACKEND is not None
        self._toaster = None

        if BACKEND == "win10toast":
            try:
                self._toaster = ToastNotifier()
            except Exception as e:
                logger.warning(f"win10toast init failed: {e}")
                self.available = False

        if self.available:
            logger.info(f"[OK] Toast notifications ready (backend: {BACKEND})")
        else:
            logger.info("[INFO] Toast notifications unavailable — install win10toast or plyer")

    def notify(self, title: str, message: str, duration: int = 5,
               icon_path: Optional[str] = None, threaded: bool = True):
        """
        Send a desktop notification.

        Args:
            title: Notification title
            message: Notification body text
            duration: How long to show (seconds)
            icon_path: Optional .ico file path
            threaded: Run in background thread (non-blocking)
        """
        if not self.available:
            logger.debug(f"Toast unavailable — would show: {title}: {message}")
            return False

        if threaded:
            t = threading.Thread(
                target=self._send, args=(title, message, duration, icon_path),
                daemon=True
            )
            t.start()
            return True
        else:
            return self._send(title, message, duration, icon_path)

    def _send(self, title: str, message: str, duration: int,
              icon_path: Optional[str]) -> bool:
        try:
            if BACKEND == "win10toast" and self._toaster:
                self._toaster.show_toast(
                    title, message,
                    icon_path=icon_path,
                    duration=duration,
                    threaded=False
                )
                return True

            elif BACKEND == "plyer":
                plyer_notification.notify(
                    title=title,
                    message=message,
                    timeout=duration,
                    app_name="Seven AI"
                )
                return True

        except Exception as e:
            logger.warning(f"Toast notification failed: {e}")
        return False

    def notify_reminder(self, reminder_text: str):
        """Convenience: send a reminder notification"""
        self.notify("Seven AI — Reminder", reminder_text, duration=10)

    def notify_alert(self, alert_text: str):
        """Convenience: send an alert notification"""
        self.notify("Seven AI — Alert", alert_text, duration=8)

    def notify_thought(self, thought: str):
        """Convenience: share a proactive thought"""
        self.notify("Seven AI", thought, duration=5)
