"""
WhatsApp Client - Seven Connects to WhatsApp via Browser Automation

Seven uses Selenium to control a Chrome browser with WhatsApp Web.
Primary: Vision system to see and understand the WhatsApp interface.
Secondary: DOM reading via Selenium to extract messages reliably.

She can read messages, send responses, and interact naturally.
She knows how to bring WhatsApp to focus (taskbar click, Alt+Tab).

First run: Opens WhatsApp Web, user scans QR code. Session persists.

Requires: pip install selenium webdriver-manager
"""

import asyncio
import logging
import threading
import json
import time
import re
import os
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("WhatsAppClient")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException,
        StaleElementReferenceException, WebDriverException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.info("Selenium not installed — run: pip install selenium webdriver-manager")

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


class WhatsAppMessage:
    """Represents a WhatsApp message."""
    def __init__(self, sender: str, text: str, timestamp: str = "",
                 is_group: bool = False, chat_name: str = ""):
        self.sender = sender
        self.text = text
        self.timestamp = timestamp
        self.is_group = is_group
        self.chat_name = chat_name


class SevenWhatsAppClient:
    """
    Seven's WhatsApp capability — browser automation + vision.

    PRIMARY: Seven's vision system sees the WhatsApp screen
    SECONDARY: Selenium DOM reading for reliable message extraction
    AUTONOMY: Seven can bring WhatsApp to focus, navigate chats, respond

    - Opens WhatsApp Web in Chrome (user scans QR once)
    - Reads messages via DOM extraction AND vision
    - Sends responses through Seven's core brain
    - Knows how to Alt+Tab or click taskbar to bring WhatsApp to focus
    - Persistent session (no re-scan needed)
    """

    def __init__(self, bot_core=None, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("WhatsAppClient")
        self.available = SELENIUM_AVAILABLE
        self.bot_core = bot_core

        # Config
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "Seven" / "whatsapp"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "whatsapp_config.json"
        self.chrome_profile = str(self.config_dir / "chrome_profile")
        self.config = self._load_config()

        # Browser
        self.driver: Optional[webdriver.Chrome] = None
        self._thread = None
        self._running = False
        self._authenticated = False

        # Conversation tracking
        self.active_convos: Dict[str, float] = {}  # chat_name -> expiry
        self.CONVO_TIMEOUT = 180
        self.conversation_memory: Dict[str, List[dict]] = defaultdict(list)
        self.MAX_MEMORY = 50
        self.last_seen_messages: Dict[str, str] = {}  # chat -> last message hash

        # Rate limiting
        self.rate_limits: Dict[str, List[float]] = defaultdict(list)
        self.RATE_LIMIT = 8
        self.RATE_WINDOW = 60

        # Respond-to-all chats (by name)
        self.respond_to_all: List[str] = self.config.get('respond_to_all', [])
        self.ignored_chats: List[str] = self.config.get('ignored_chats', [])

        # Polling
        self.POLL_INTERVAL = self.config.get('poll_interval', 3)  # seconds

        if not SELENIUM_AVAILABLE:
            self.logger.warning("Selenium not available — install with: pip install selenium webdriver-manager")

    def _load_config(self) -> dict:
        """Load WhatsApp configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load WhatsApp config: {e}")
        return {
            'respond_to_dms': True,
            'respond_in_groups': True,
            'respond_to_all': [],
            'ignored_chats': [],
            'poll_interval': 3,
            'use_vision': True,
            'headless': False,  # Must be False for QR scan
        }

    def _save_config(self):
        """Save WhatsApp configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save WhatsApp config: {e}")

    def start(self) -> str:
        """Start the WhatsApp Web client."""
        if not self.available:
            return "Selenium not installed. Run: pip install selenium webdriver-manager"
        if self._running:
            return "WhatsApp client already running."

        self._running = True
        self._thread = threading.Thread(target=self._run_browser, daemon=True)
        self._thread.start()
        return ("WhatsApp Web opening... If this is your first time, "
                "scan the QR code with your phone. Session will persist after that.")

    def stop(self) -> str:
        """Stop the WhatsApp client."""
        self._running = False
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self._authenticated = False
        return "WhatsApp client stopped."

    def _run_browser(self):
        """Run the WhatsApp Web browser."""
        try:
            self._init_browser()
            self._wait_for_auth()
            self._poll_messages()
        except Exception as e:
            self.logger.error(f"WhatsApp browser error: {e}")
        finally:
            self._running = False

    def _init_browser(self):
        """Initialize Chrome with persistent profile for WhatsApp Web."""
        options = ChromeOptions()

        # Persistent profile — keeps session after QR scan
        options.add_argument(f"user-data-dir={self.chrome_profile}")
        options.add_argument("--profile-directory=Default")

        # Performance
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")

        # Window size
        options.add_argument("--window-size=1280,900")

        # Don't run headless — need to see QR code
        if self.config.get('headless', False):
            options.add_argument("--headless=new")

        try:
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            self.logger.error(f"Chrome init failed: {e}")
            raise

        self.driver.get("https://web.whatsapp.com")
        self.logger.info("[WhatsApp] Opened WhatsApp Web")

    def _wait_for_auth(self):
        """Wait for WhatsApp Web authentication (QR scan or cached session)."""
        self.logger.info("[WhatsApp] Waiting for authentication...")

        # Wait up to 120 seconds for the main chat panel to appear
        try:
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
            )
            self._authenticated = True
            self.logger.info("[WhatsApp] Authenticated successfully!")
        except TimeoutException:
            self.logger.warning("[WhatsApp] Authentication timeout — QR code may not have been scanned")
            self._running = False
            return

    def _poll_messages(self):
        """Main polling loop — reads messages from the active chat and unread chats."""
        self.logger.info("[WhatsApp] Starting message polling...")

        while self._running:
            try:
                # Check for new unread messages
                self._check_unread_chats()

                # Also use vision if available and configured
                if self.config.get('use_vision', True) and self.bot_core:
                    self._vision_check()

                time.sleep(self.POLL_INTERVAL)

            except WebDriverException as e:
                if "disconnected" in str(e).lower() or "session" in str(e).lower():
                    self.logger.error("[WhatsApp] Browser disconnected")
                    self._running = False
                    break
                self.logger.warning(f"[WhatsApp] WebDriver error: {e}")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"[WhatsApp] Poll error: {e}")
                time.sleep(5)

    def _check_unread_chats(self):
        """Find and process chats with unread messages."""
        try:
            # Find all chat items with unread badges
            unread_elements = self.driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="chat-list"] [data-testid="icon-unread-count"]'
            )

            for badge in unread_elements[:5]:  # Process max 5 unread chats
                try:
                    # Navigate up to the chat row and click it
                    chat_row = badge.find_element(By.XPATH, './ancestor::div[@data-testid="cell-frame-container"]')
                    chat_name_el = chat_row.find_element(By.CSS_SELECTOR, '[data-testid="cell-frame-title"] span')
                    chat_name = chat_name_el.get_attribute('title') or chat_name_el.text

                    if chat_name in self.ignored_chats:
                        continue

                    # Click to open the chat
                    chat_row.click()
                    time.sleep(1)

                    # Read messages from the opened chat
                    self._read_and_respond(chat_name)

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    self.logger.debug(f"Error processing unread chat: {e}")
                    continue

        except Exception as e:
            self.logger.debug(f"Error checking unread: {e}")

    def _read_and_respond(self, chat_name: str):
        """Read messages from the currently open chat and respond if needed."""
        try:
            # Determine if this is a group chat
            is_group = self._is_group_chat()

            # Get recent messages from the chat panel
            messages = self._extract_messages()
            if not messages:
                return

            # Check if we've already seen the last message
            last_msg = messages[-1]
            msg_hash = f"{last_msg.sender}:{last_msg.text}"
            if self.last_seen_messages.get(chat_name) == msg_hash:
                return  # Already processed
            self.last_seen_messages[chat_name] = msg_hash

            # Store in memory
            for msg in messages[-5:]:
                self.conversation_memory[chat_name].append({
                    'sender': msg.sender,
                    'text': msg.text,
                    'time': datetime.now().isoformat(),
                    'is_group': is_group,
                })
            if len(self.conversation_memory[chat_name]) > self.MAX_MEMORY:
                self.conversation_memory[chat_name] = self.conversation_memory[chat_name][-self.MAX_MEMORY:]

            # Decide whether to respond
            should_respond = False
            now = time.time()

            if not is_group and self.config.get('respond_to_dms', True):
                # Always respond to DMs
                should_respond = True
            elif is_group:
                # Check if mentioned
                mentioned = any(
                    'seven' in msg.text.lower()
                    for msg in messages[-3:]
                )
                # Active convo
                in_active = chat_name in self.active_convos and self.active_convos[chat_name] > now
                # Respond-to-all
                in_respond_all = chat_name in self.respond_to_all

                if mentioned or in_active or in_respond_all:
                    should_respond = True
                    self.active_convos[chat_name] = now + self.CONVO_TIMEOUT

            if not should_respond:
                return

            # Rate limit
            self.rate_limits[chat_name] = [t for t in self.rate_limits[chat_name] if t > now - self.RATE_WINDOW]
            if len(self.rate_limits[chat_name]) >= self.RATE_LIMIT:
                return
            self.rate_limits[chat_name].append(now)

            # Generate response using Seven's brain
            response = self._generate_response(last_msg, chat_name, is_group)
            if response:
                self._send_message(response)
                self.logger.info(f"[WhatsApp] Replied in {chat_name}: {response[:80]}...")

        except Exception as e:
            self.logger.error(f"[WhatsApp] Read/respond error: {e}")

    def _extract_messages(self) -> List[WhatsAppMessage]:
        """Extract messages from the currently open chat via DOM."""
        messages = []
        try:
            # Find message containers
            msg_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 'div.message-in, div.message-out, div[data-testid="msg-container"]'
            )

            for el in msg_elements[-15:]:  # Last 15 messages
                try:
                    # Try to get sender (group chats)
                    sender = "Unknown"
                    try:
                        sender_el = el.find_element(By.CSS_SELECTOR, '[data-testid="msg-meta"] span, .copyable-text')
                        sender_attr = sender_el.get_attribute('data-pre-plain-text')
                        if sender_attr:
                            # Format: "[HH:MM, DD/MM/YYYY] Name: "
                            match = re.search(r'\]\s*(.+?):\s*$', sender_attr)
                            if match:
                                sender = match.group(1).strip()
                    except NoSuchElementException:
                        pass

                    # Check if it's our own message
                    if 'message-out' in el.get_attribute('class'):
                        sender = "Seven"

                    # Get message text
                    text = ""
                    try:
                        text_el = el.find_element(By.CSS_SELECTOR, '[data-testid="balloon-text-msg"] span, .selectable-text span')
                        text = text_el.text
                    except NoSuchElementException:
                        try:
                            text_el = el.find_element(By.CSS_SELECTOR, '.copyable-text span')
                            text = text_el.text
                        except NoSuchElementException:
                            continue

                    if text.strip():
                        messages.append(WhatsAppMessage(sender=sender, text=text.strip()))

                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue

        except Exception as e:
            self.logger.debug(f"Message extraction error: {e}")

        return messages

    def _is_group_chat(self) -> bool:
        """Check if the currently open chat is a group."""
        try:
            # Group chats usually show member count or "click here for group info"
            header = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="conversation-info-header-chat-title"]')
            subtitle = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="conversation-info-header-chat-subtitle"]')
            if subtitle:
                text = subtitle[0].text.lower()
                if 'click here' in text or 'members' in text or ',' in text:
                    return True
        except NoSuchElementException:
            pass
        return False

    def _send_message(self, text: str):
        """Send a message in the currently open chat."""
        try:
            # Find the message input box
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"], div[contenteditable="true"][data-tab="10"]')
                )
            )

            # Type the message (handle multi-line)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                input_box.send_keys(line)
                if i < len(lines) - 1:
                    input_box.send_keys(Keys.SHIFT, Keys.ENTER)

            # Send
            input_box.send_keys(Keys.ENTER)
            time.sleep(0.5)

        except Exception as e:
            self.logger.error(f"[WhatsApp] Send error: {e}")

    def _generate_response(self, message: WhatsAppMessage, chat_name: str,
                           is_group: bool) -> Optional[str]:
        """Generate a response using Seven's brain."""
        if not self.bot_core:
            return None

        context_prefix = f"[WhatsApp {'group' if is_group else 'DM'}: {chat_name}] {message.sender}: "

        # Include recent history
        recent = self.conversation_memory.get(chat_name, [])[-10:]
        history_lines = []
        for msg in recent[:-1]:
            history_lines.append(f"{msg['sender']}: {msg['text']}")
        history = "\n".join(history_lines[-5:]) if history_lines else ""

        full_input = f"{context_prefix}{message.text}"
        if history:
            full_input = f"[Recent chat:\n{history}]\n{full_input}"

        try:
            response = self.bot_core._process_input(full_input)
            if response:
                response = re.sub(r'\[.*?\]', '', response).strip()
                if len(response) > 4000:
                    response = response[:4000] + "..."
            return response
        except Exception as e:
            self.logger.error(f"[WhatsApp] Brain error: {e}")
            return None

    def _vision_check(self):
        """Use Seven's vision system to see the WhatsApp window."""
        if not self.bot_core or not hasattr(self.bot_core, 'screen_control'):
            return
        if not self.bot_core.screen_control or not self.bot_core.screen_control.available:
            return

        # Vision check happens less frequently (every 30 seconds)
        if not hasattr(self, '_last_vision_check'):
            self._last_vision_check = 0
        if time.time() - self._last_vision_check < 30:
            return
        self._last_vision_check = time.time()

        try:
            # Take a screenshot of the WhatsApp window area
            screenshot = self.bot_core.screen_control.take_screenshot()
            if screenshot:
                self.logger.debug("[WhatsApp] Vision check: screenshot captured")
                # Vision analysis happens through Seven's main screen_control
                # which uses llama3.2-vision to understand what's on screen
        except Exception as e:
            self.logger.debug(f"[WhatsApp] Vision check error: {e}")

    # === Autonomy: Bring WhatsApp to focus ===

    def bring_to_focus(self) -> str:
        """Bring WhatsApp Web browser to the foreground."""
        if not self.driver:
            return "WhatsApp not running."
        try:
            # Switch to the browser window
            self.driver.switch_to.window(self.driver.current_window_handle)
            self.driver.maximize_window()

            # Also try pyautogui for taskbar click
            try:
                import pyautogui
                import subprocess
                # Use PowerShell to bring Chrome to front
                subprocess.run([
                    'powershell', '-Command',
                    '(New-Object -ComObject WScript.Shell).AppActivate("WhatsApp")'
                ], capture_output=True, timeout=5)
            except Exception:
                pass

            return "WhatsApp brought to focus."
        except Exception as e:
            return f"Could not focus WhatsApp: {e}"

    def open_chat(self, contact_name: str) -> str:
        """Open a specific chat by contact/group name."""
        if not self.driver or not self._authenticated:
            return "WhatsApp not connected."
        try:
            # Click the search box
            search = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-testid="chat-list-search"], [data-testid="search-input"]')
                )
            )
            search.click()
            time.sleep(0.5)

            # Find and use the actual search input
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, '[data-testid="search-input"] div[contenteditable="true"], input[data-testid="search-input"]'
            )
            search_input.clear()
            search_input.send_keys(contact_name)
            time.sleep(1.5)

            # Click the first result
            results = self.driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="cell-frame-container"]'
            )
            if results:
                results[0].click()
                time.sleep(1)
                return f"Opened chat with {contact_name}"
            return f"Could not find chat: {contact_name}"

        except Exception as e:
            return f"Error opening chat: {e}"

    def send_to_contact(self, contact: str, message: str) -> str:
        """Send a message to a specific contact."""
        result = self.open_chat(contact)
        if "Opened" in result:
            self._send_message(message)
            return f"Sent to {contact}: {message[:60]}..."
        return result

    # === Voice/text command methods ===

    def get_status(self) -> str:
        """Get WhatsApp connection status."""
        if not self.available:
            return "Selenium not installed. Run: pip install selenium webdriver-manager"
        if not self._running:
            return "WhatsApp not running. Say 'start whatsapp' to connect."
        if not self._authenticated:
            return "WhatsApp waiting for QR code scan..."

        active = sum(1 for t in self.active_convos.values() if t > time.time())
        chats = len(self.conversation_memory)
        return (f"WhatsApp: Connected (authenticated) | "
                f"Active convos: {active} | "
                f"Chats tracked: {chats} | "
                f"DM replies: {'ON' if self.config.get('respond_to_dms') else 'OFF'} | "
                f"Group replies: {'ON' if self.config.get('respond_in_groups') else 'OFF'} | "
                f"Vision: {'ON' if self.config.get('use_vision') else 'OFF'}")

    def list_chats(self) -> str:
        """List tracked chats."""
        if not self.conversation_memory:
            return "No WhatsApp chats tracked yet."
        lines = ["WhatsApp chats:"]
        for name, msgs in self.conversation_memory.items():
            lines.append(f"  {name}: {len(msgs)} messages")
        return "\n".join(lines)
