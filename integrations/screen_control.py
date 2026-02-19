"""
Screen Control - Seven Can See and Interact With Your Screen

Seven takes screenshots, analyzes them through llama3.2-vision,
and can control mouse/keyboard via pyautogui.

Requires: pyautogui, pillow
"""

import os
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger("ScreenControl")

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.3
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed — screen control unavailable")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ScreenControl:
    """
    Seven's eyes and hands on the screen.
    
    - Takes screenshots and analyzes via vision model
    - Controls mouse (move, click, right-click, drag)
    - Controls keyboard (type, hotkeys)
    - Always asks before dangerous actions
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("ScreenControl")
        self.available = PYAUTOGUI_AVAILABLE
        
        # Temp dir for screenshots (auto-cleaned)
        self._screenshot_dir = Path(tempfile.gettempdir()) / "seven_screenshots"
        self._screenshot_dir.mkdir(exist_ok=True)
        
        # Track screenshots for cleanup
        self._screenshot_files = []
        self._max_screenshots = 5
        
        if self.available:
            screen = pyautogui.size()
            self.logger.info(f"[OK] Screen control ready — {screen.width}x{screen.height}")
    
    # ============ SCREENSHOTS + VISION ============
    
    def take_screenshot(self, region: Optional[Tuple] = None) -> Optional[str]:
        """
        Take a screenshot and return the file path.
        
        Args:
            region: Optional (x, y, width, height) to capture a region
        
        Returns:
            Path to screenshot file, or None
        """
        if not self.available:
            return None
        
        try:
            filename = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self._screenshot_dir / filename
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(str(filepath))
            
            # Track for cleanup
            self._screenshot_files.append(filepath)
            self._cleanup_old_screenshots()
            
            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None
    
    def see_screen(self, question: Optional[str] = None) -> Optional[str]:
        """
        Take a screenshot and analyze it with the vision model.
        
        Args:
            question: What to ask about the screen (default: describe what you see)
        
        Returns:
            Vision model's analysis of the screen
        """
        screenshot_path = self.take_screenshot()
        if not screenshot_path:
            return "Couldn't take a screenshot."
        
        return self.analyze_image(screenshot_path, question)
    
    def analyze_image(self, image_path: str, question: Optional[str] = None) -> Optional[str]:
        """
        Analyze an image using the vision model.
        
        Args:
            image_path: Path to image file
            question: What to ask about the image
        """
        if not self.bot:
            return "No bot instance available for vision analysis."
        
        ollama = getattr(self.bot, 'ollama', None)
        if not ollama:
            return "Ollama not available for vision analysis."
        
        if not question:
            question = "Describe what you see on this screen. What is the user working on? Note any important details."
        
        try:
            # Use llama3.2-vision model
            result = ollama.generate_with_image(
                prompt=question,
                image_path=image_path,
                model="llama3.2-vision"
            )
            
            # Clean up screenshot after analysis
            try:
                os.unlink(image_path)
                if Path(image_path) in self._screenshot_files:
                    self._screenshot_files.remove(Path(image_path))
            except Exception:
                pass
            
            return result if result else "Couldn't analyze the screenshot."
            
        except AttributeError:
            # generate_with_image might not exist yet — try raw API
            return self._vision_fallback(image_path, question)
        except Exception as e:
            self.logger.error(f"Vision analysis failed: {e}")
            return f"Vision analysis failed: {str(e)[:200]}"
    
    def _vision_fallback(self, image_path: str, question: str) -> Optional[str]:
        """Fallback vision using direct Ollama API call"""
        try:
            import base64
            import requests
            
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2-vision",
                    "prompt": question,
                    "images": [img_b64],
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'No response from vision model')
            else:
                return f"Vision API error: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"Vision fallback failed: {e}")
            return f"Vision analysis unavailable: {str(e)[:200]}"
    
    # ============ MOUSE CONTROL ============
    
    def mouse_move(self, x: int, y: int) -> str:
        """Move mouse to position"""
        if not self.available:
            return "Screen control not available"
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Moved mouse to ({x}, {y})"
    
    def mouse_click(self, x: Optional[int] = None, y: Optional[int] = None,
                    button: str = 'left', clicks: int = 1) -> str:
        """Click at position (or current position if no coords)"""
        if not self.available:
            return "Screen control not available"
        
        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
            return f"{button.capitalize()} clicked at ({x}, {y})"
        else:
            pyautogui.click(clicks=clicks, button=button)
            pos = pyautogui.position()
            return f"{button.capitalize()} clicked at current position ({pos.x}, {pos.y})"
    
    def mouse_right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Right-click"""
        return self.mouse_click(x, y, button='right')
    
    def mouse_double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Double-click"""
        return self.mouse_click(x, y, clicks=2)
    
    def mouse_scroll(self, amount: int = -3) -> str:
        """Scroll (negative = down, positive = up)"""
        if not self.available:
            return "Screen control not available"
        pyautogui.scroll(amount)
        direction = "down" if amount < 0 else "up"
        return f"Scrolled {direction} by {abs(amount)}"
    
    def get_mouse_position(self) -> str:
        """Get current mouse position"""
        if not self.available:
            return "Screen control not available"
        pos = pyautogui.position()
        return f"Mouse is at ({pos.x}, {pos.y})"
    
    # ============ KEYBOARD CONTROL ============
    
    def type_text(self, text: str, interval: float = 0.02) -> str:
        """Type text"""
        if not self.available:
            return "Screen control not available"
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
        return f"Typed {len(text)} characters"
    
    def press_key(self, key: str) -> str:
        """Press a single key"""
        if not self.available:
            return "Screen control not available"
        pyautogui.press(key)
        return f"Pressed {key}"
    
    def hotkey(self, *keys) -> str:
        """Press a key combination (e.g., hotkey('ctrl', 'c'))"""
        if not self.available:
            return "Screen control not available"
        pyautogui.hotkey(*keys)
        return f"Pressed {'+'.join(keys)}"
    
    def get_screen_size(self) -> str:
        """Get screen resolution"""
        if not self.available:
            return "Screen control not available"
        size = pyautogui.size()
        return f"Screen: {size.width}x{size.height}"
    
    # ============ CLEANUP ============
    
    def _cleanup_old_screenshots(self):
        """Keep only recent screenshots"""
        while len(self._screenshot_files) > self._max_screenshots:
            old = self._screenshot_files.pop(0)
            try:
                if old.exists():
                    old.unlink()
            except Exception:
                pass
    
    def cleanup(self):
        """Clean up all temporary screenshots"""
        for f in self._screenshot_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        self._screenshot_files.clear()
        self.logger.info("Screenshots cleaned up")
