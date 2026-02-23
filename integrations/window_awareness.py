"""
Window / App Awareness — Seven AI

Detect active window and running applications on Windows.
Offers context-sensitive help based on what the user is doing.
"""

import logging
import platform
from typing import Optional, Dict, List

logger = logging.getLogger("WindowAwareness")

IS_WINDOWS = platform.system() == "Windows"

# Try to import Windows-specific modules
if IS_WINDOWS:
    try:
        import ctypes
        from ctypes import wintypes
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class WindowAwarenessManager:
    """Detect active window and running applications"""

    def __init__(self):
        self.available = IS_WINDOWS and (HAS_WIN32 or HAS_PSUTIL)
        self._last_window = ""
        self._window_history = []

        if self.available:
            logger.info("[OK] Window awareness ready")
        else:
            logger.info("[INFO] Window awareness unavailable (Windows + ctypes/psutil required)")

    def get_active_window(self) -> Optional[Dict]:
        """Get the currently active window title and process"""
        if not IS_WINDOWS or not HAS_WIN32:
            return None

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()

            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

            # Get process ID
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # Get process name
            process_name = ""
            if HAS_PSUTIL:
                try:
                    proc = psutil.Process(pid.value)
                    process_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            result = {
                "title": title,
                "process": process_name,
                "pid": pid.value,
                "hwnd": hwnd,
            }

            # Track history
            if title != self._last_window:
                self._last_window = title
                self._window_history.append(result)
                if len(self._window_history) > 50:
                    self._window_history = self._window_history[-50:]

            return result

        except Exception as e:
            logger.debug(f"Active window detection failed: {e}")
            return None

    def get_running_apps(self) -> List[Dict]:
        """Get list of running GUI applications"""
        if not HAS_PSUTIL:
            return []

        apps = []
        seen = set()

        try:
            for proc in psutil.process_iter(['name', 'pid', 'status']):
                try:
                    name = proc.info['name']
                    if name and name not in seen and proc.info['status'] == 'running':
                        # Filter out system processes
                        if not name.startswith('svchost') and not name.startswith('System'):
                            apps.append({
                                'name': name,
                                'pid': proc.info['pid'],
                            })
                            seen.add(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.debug(f"Running apps detection failed: {e}")

        return sorted(apps, key=lambda x: x['name'].lower())

    def get_context_hint(self) -> Optional[str]:
        """Get a context hint based on the active window"""
        window = self.get_active_window()
        if not window or not window['title']:
            return None

        title = window['title'].lower()
        process = window['process'].lower() if window['process'] else ""

        # IDE / Code editors
        if any(x in process for x in ['code', 'devenv', 'pycharm', 'idea', 'sublime', 'notepad++']):
            return "coding"
        if any(x in title for x in ['visual studio', 'vs code', 'pycharm', 'intellij']):
            return "coding"

        # Browsers
        if any(x in process for x in ['chrome', 'firefox', 'msedge', 'opera', 'brave']):
            if any(x in title for x in ['youtube', 'netflix', 'twitch', 'disney']):
                return "watching_video"
            if any(x in title for x in ['github', 'stackoverflow', 'docs.']):
                return "researching"
            if any(x in title for x in ['gmail', 'outlook', 'mail']):
                return "email"
            return "browsing"

        # Communication
        if any(x in process for x in ['teams', 'slack', 'discord', 'telegram', 'whatsapp']):
            return "chatting"

        # Office
        if any(x in process for x in ['winword', 'excel', 'powerpnt', 'onenote']):
            return "office_work"

        # Gaming
        if any(x in title for x in ['steam', 'epic games', 'game']):
            return "gaming"

        # Terminal
        if any(x in process for x in ['windowsterminal', 'cmd', 'powershell', 'conhost']):
            return "terminal"

        # File manager
        if 'explorer' in process:
            return "file_management"

        return None

    def get_window_history(self, limit: int = 10) -> List[Dict]:
        """Get recent window switches"""
        return self._window_history[-limit:]

    def is_app_running(self, app_name: str) -> bool:
        """Check if a specific app is running"""
        if not HAS_PSUTIL:
            return False
        try:
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    return True
        except Exception:
            pass
        return False
