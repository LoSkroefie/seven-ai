"""
Screen Capture — Seven AI

Take screenshots of the desktop. Can optionally describe
what's on screen using Ollama vision or text analysis.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("ScreenCapture")

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ScreenCaptureManager:
    """Take and save screenshots"""

    def __init__(self, output_dir: Optional[str] = None):
        self.available = HAS_MSS or HAS_PIL
        self.output_dir = Path(output_dir) if output_dir else (
            Path.home() / "Documents" / "Seven" / "screenshots"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_capture = None

        if self.available:
            logger.info(f"[OK] Screen capture ready (mss={HAS_MSS}, PIL={HAS_PIL})")
        else:
            logger.info("[INFO] Screen capture unavailable — install mss or Pillow")

    def capture(self, monitor: int = 0, save: bool = True) -> Optional[Dict]:
        """
        Take a screenshot.

        Args:
            monitor: Monitor index (0 = all monitors, 1 = primary, etc.)
            save: Whether to save to disk

        Returns:
            Dict with 'path', 'width', 'height', 'timestamp'
        """
        if HAS_MSS:
            return self._capture_mss(monitor, save)
        elif HAS_PIL:
            return self._capture_pil(save)
        return None

    def _capture_mss(self, monitor: int, save: bool) -> Optional[Dict]:
        """Capture using mss (fast, multi-monitor)"""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                if monitor >= len(monitors):
                    monitor = 0

                shot = sct.grab(monitors[monitor])

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result = {
                    'width': shot.width,
                    'height': shot.height,
                    'timestamp': timestamp,
                    'monitor': monitor,
                }

                if save:
                    filepath = self.output_dir / f"screenshot_{timestamp}.png"
                    mss.tools.to_png(shot.rgb, shot.size, output=str(filepath))
                    result['path'] = str(filepath)
                    result['size_kb'] = round(filepath.stat().st_size / 1024, 1)
                    self.last_capture = result

                return result

        except Exception as e:
            logger.error(f"mss capture failed: {e}")
            return None

    def _capture_pil(self, save: bool) -> Optional[Dict]:
        """Capture using PIL/Pillow (fallback)"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result = {
                'width': img.width,
                'height': img.height,
                'timestamp': timestamp,
                'monitor': 0,
            }

            if save:
                filepath = self.output_dir / f"screenshot_{timestamp}.png"
                img.save(str(filepath))
                result['path'] = str(filepath)
                result['size_kb'] = round(filepath.stat().st_size / 1024, 1)
                self.last_capture = result

            return result

        except Exception as e:
            logger.error(f"PIL capture failed: {e}")
            return None

    def get_last_capture(self) -> Optional[Dict]:
        """Get info about the last screenshot"""
        return self.last_capture
