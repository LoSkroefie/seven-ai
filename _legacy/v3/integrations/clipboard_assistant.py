"""
Clipboard Assistant - Seven Watches Your Clipboard

Monitors clipboard changes and offers contextual help:
- Copy a URL → Seven summarizes it
- Copy code → Seven explains it
- Copy an error → Seven diagnoses it
- Copy text → Seven can translate, summarize, or act on it

Requires: pyperclip
"""

import logging
import threading
import time
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger("ClipboardAssistant")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    logger.warning("pyperclip not installed — clipboard monitoring unavailable")


class ClipboardAssistant:
    """
    Seven's clipboard awareness.
    
    - Monitors clipboard for changes in background
    - Detects content type (URL, code, error, text)
    - Offers contextual actions via Ollama
    - Can set clipboard content
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("ClipboardAssistant")
        self.available = PYPERCLIP_AVAILABLE
        
        # State
        self._last_content = ""
        self._monitoring = False
        self._thread = None
        self._poll_interval = 2  # Check every 2 seconds
        
        # History
        self.clipboard_history = []
        self._max_history = 50
        
        # Callback for when clipboard changes
        self._on_change_callback: Optional[Callable] = None
        
        if self.available:
            try:
                self._last_content = pyperclip.paste() or ""
            except Exception:
                self._last_content = ""
            self.logger.info("[OK] Clipboard assistant ready")
    
    def start_monitoring(self):
        """Start monitoring clipboard in background"""
        if self._monitoring or not self.available:
            return
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ClipboardMonitor")
        self._thread.start()
        self.logger.info("Clipboard monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=3)
    
    def _monitor_loop(self):
        """Background clipboard monitoring"""
        while self._monitoring:
            try:
                current = pyperclip.paste()
                if current and current != self._last_content:
                    self._last_content = current
                    self._on_clipboard_change(current)
            except Exception as e:
                self.logger.debug(f"Clipboard read error: {e}")
            
            time.sleep(self._poll_interval)
    
    def _on_clipboard_change(self, content: str):
        """Handle clipboard content change"""
        content_type = self.detect_content_type(content)
        
        # Log to history
        self.clipboard_history.append({
            'content': content[:500],
            'type': content_type,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.clipboard_history) > self._max_history:
            self.clipboard_history = self.clipboard_history[-self._max_history:]
        
        self.logger.debug(f"Clipboard changed: {content_type} ({len(content)} chars)")
        
        # Only proactively help with certain types
        if content_type == 'error' and len(content) > 20:
            self._offer_help(content, content_type)
    
    def _offer_help(self, content: str, content_type: str):
        """Proactively offer help based on clipboard content"""
        if not self.bot or not hasattr(self.bot, 'autonomous_life') or not self.bot.autonomous_life:
            return
        
        if content_type == 'error':
            self.bot.autonomous_life.queue_message(
                f"I noticed you copied an error. Want me to help diagnose it?",
                priority="low"
            )
    
    # ============ CONTENT DETECTION ============
    
    def detect_content_type(self, content: str) -> str:
        """Detect what kind of content is on the clipboard"""
        content = content.strip()
        
        # URL
        if content.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # File path
        if content.startswith(('C:\\', 'D:\\', '/', '~/')):
            return 'filepath'
        
        # Error/stack trace
        error_indicators = ['error', 'exception', 'traceback', 'failed', 'stack trace',
                          'at line', 'syntaxerror', 'typeerror', 'valueerror', 'keyerror',
                          'nullreferenceexception', 'segmentation fault']
        if any(ind in content.lower() for ind in error_indicators):
            return 'error'
        
        # Code detection
        code_indicators = ['def ', 'class ', 'import ', 'function ', 'const ', 'var ',
                          'public ', 'private ', 'static ', 'void ', '#include',
                          'using System', 'namespace ', 'Dim ', 'Sub ', 'Function ']
        if any(ind in content for ind in code_indicators):
            return 'code'
        
        # JSON
        if (content.startswith('{') and content.endswith('}')) or \
           (content.startswith('[') and content.endswith(']')):
            return 'json'
        
        # Email
        if '@' in content and '.' in content and len(content) < 100:
            return 'email'
        
        # Number/math
        if content.replace('.', '').replace(',', '').replace('-', '').isdigit():
            return 'number'
        
        return 'text'
    
    # ============ ACTIONS ============
    
    def get_clipboard(self) -> str:
        """Get current clipboard content"""
        if not self.available:
            return "Clipboard not available"
        try:
            return pyperclip.paste() or "(empty clipboard)"
        except Exception:
            return "(couldn't read clipboard)"
    
    def set_clipboard(self, content: str) -> str:
        """Set clipboard content"""
        if not self.available:
            return "Clipboard not available"
        try:
            pyperclip.copy(content)
            return f"Copied to clipboard ({len(content)} chars)"
        except Exception as e:
            return f"Failed to set clipboard: {e}"
    
    def analyze_clipboard(self) -> str:
        """Analyze current clipboard content and return description"""
        content = self.get_clipboard()
        if content.startswith("("):
            return content
        
        content_type = self.detect_content_type(content)
        preview = content[:200] + "..." if len(content) > 200 else content
        
        return f"Clipboard ({content_type}, {len(content)} chars):\n{preview}"
    
    def process_clipboard_with_ollama(self, action: str = "explain") -> Optional[str]:
        """Process clipboard content through Ollama"""
        if not self.bot or not hasattr(self.bot, 'ollama') or not self.bot.ollama:
            return None
        
        content = self.get_clipboard()
        if content.startswith("("):
            return content
        
        content_type = self.detect_content_type(content)
        
        prompts = {
            'explain': f"Explain this {content_type} concisely:\n\n{content[:2000]}",
            'summarize': f"Summarize this in 2-3 sentences:\n\n{content[:3000]}",
            'fix': f"Find and fix any issues in this {content_type}:\n\n{content[:2000]}",
            'translate': f"Translate this to English (or from English to the detected language):\n\n{content[:2000]}",
        }
        
        prompt = prompts.get(action, prompts['explain'])
        
        try:
            result = self.bot.ollama.generate(prompt, temperature=0.3, max_tokens=300)
            return result
        except Exception as e:
            return f"Couldn't process clipboard: {e}"
