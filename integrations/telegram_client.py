"""
Telegram Client - Seven Connects to Telegram as a User

Seven uses Telethon (user client, NOT BotFather) to connect to Telegram
as a real user account. This gives her full access to all chats, groups,
channels, and features without bot restrictions.

She can read messages, send responses, join groups, send media,
and interact naturally — just like a human Telegram user.

Requires: pip install telethon
First run requires phone number + verification code (one-time).
"""

import asyncio
import logging
import threading
import json
import time
import re
from pathlib import Path
from typing import Optional, Dict, List, Callable
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("TelegramClient")

try:
    from telethon import TelegramClient as TelethonClient
    from telethon import events
    from telethon.tl.types import User, Chat, Channel
    from telethon.errors import SessionPasswordNeededError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.info("Telethon not installed — run: pip install telethon")


class SevenTelegramClient:
    """
    Seven's Telegram capability — user client, not a bot.

    - Connects as a real Telegram user (Telethon)
    - Reads and responds to private messages
    - Participates in group chats when mentioned or in active convos
    - Sends media, stickers, voice messages
    - Full access to all Telegram features (no bot restrictions)
    - Routes all messages through Seven's core _process_input
    """

    def __init__(self, bot_core=None, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("TelegramClient")
        self.available = TELETHON_AVAILABLE
        self.bot_core = bot_core

        # Config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "Seven" / "telegram"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "telegram_config.json"
        self.session_file = str(self.config_dir / "seven_telegram")
        self.config = self._load_config()

        # State
        self.client: Optional[TelethonClient] = None
        self._loop = None
        self._thread = None
        self._running = False

        # Conversation tracking
        self.active_convos: Dict[int, float] = {}  # chat_id -> expiry
        self.CONVO_TIMEOUT = 180  # 3 minutes
        self.conversation_memory: Dict[int, List[dict]] = defaultdict(list)
        self.MAX_MEMORY = 50

        # Rate limiting
        self.rate_limits: Dict[int, List[float]] = defaultdict(list)
        self.RATE_LIMIT = 10  # messages per window
        self.RATE_WINDOW = 60  # seconds

        # Respond-to-all chats (by chat_id or title pattern)
        self.respond_to_all: List = self.config.get('respond_to_all', [])

        # Ignored chats
        self.ignored_chats: List = self.config.get('ignored_chats', [])

        if not TELETHON_AVAILABLE:
            self.logger.warning("Telethon not available — install with: pip install telethon")

    def _load_config(self) -> dict:
        """Load Telegram configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load Telegram config: {e}")
        return {
            'api_id': None,
            'api_hash': None,
            'phone': None,
            'respond_to_dms': True,
            'respond_in_groups': True,
            'respond_to_all': [],
            'ignored_chats': [],
            'auto_read': True,
            'typing_indicator': True,
        }

    def _save_config(self):
        """Save Telegram configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save Telegram config: {e}")

    def configure(self, api_id: int, api_hash: str, phone: str = None) -> str:
        """Configure Telegram API credentials. Get these from https://my.telegram.org"""
        self.config['api_id'] = api_id
        self.config['api_hash'] = api_hash
        if phone:
            self.config['phone'] = phone
        self._save_config()
        return f"Telegram configured! API ID: {api_id}. Run 'start telegram' to connect."

    def _is_configured(self) -> bool:
        """Check if API credentials are set."""
        return bool(self.config.get('api_id') and self.config.get('api_hash'))

    def start(self) -> str:
        """Start the Telegram client in a background thread."""
        if not self.available:
            return "Telethon not installed. Run: pip install telethon"
        if not self._is_configured():
            return ("Telegram not configured. I need API credentials.\n"
                    "1. Go to https://my.telegram.org\n"
                    "2. Log in and create an app\n"
                    "3. Tell me: 'configure telegram [api_id] [api_hash] [phone]'")
        if self._running:
            return "Telegram client already running."

        self._running = True
        self._thread = threading.Thread(target=self._run_client, daemon=True)
        self._thread.start()
        return "Telegram client starting... I'll connect to your account now."

    def stop(self) -> str:
        """Stop the Telegram client."""
        self._running = False
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self._loop)
        return "Telegram client stopped."

    async def _disconnect(self):
        """Disconnect the Telethon client."""
        if self.client:
            await self.client.disconnect()

    def _run_client(self):
        """Run the Telegram client in its own event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._client_main())
        except Exception as e:
            self.logger.error(f"Telegram client error: {e}")
        finally:
            self._running = False
            self._loop.close()

    async def _client_main(self):
        """Main Telegram client logic."""
        api_id = self.config['api_id']
        api_hash = self.config['api_hash']
        phone = self.config.get('phone')

        self.client = TelethonClient(self.session_file, api_id, api_hash)

        await self.client.start(phone=phone)
        me = await self.client.get_me()
        self.logger.info(f"[Telegram] Connected as: {me.first_name} (@{me.username})")

        # Register message handler
        @self.client.on(events.NewMessage)
        async def handle_message(event):
            await self._handle_incoming(event)

        self.logger.info("[Telegram] Listening for messages...")

        # Keep running
        while self._running:
            await asyncio.sleep(1)

        await self.client.disconnect()

    async def _handle_incoming(self, event):
        """Handle an incoming Telegram message."""
        try:
            # Don't process our own messages
            if event.out:
                return

            # Get sender info
            sender = await event.get_sender()
            if not sender:
                return
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'Unknown')
            sender_id = sender.id

            # Get chat info
            chat = await event.get_chat()
            chat_id = event.chat_id
            chat_title = getattr(chat, 'title', None) or sender_name
            is_private = event.is_private
            is_group = event.is_group or event.is_channel

            message_text = event.text or ''
            if not message_text.strip():
                return  # Skip empty / media-only for now

            # Check if ignored
            if chat_id in self.ignored_chats:
                return

            # Store in conversation memory
            self.conversation_memory[chat_id].append({
                'sender': sender_name,
                'sender_id': sender_id,
                'text': message_text,
                'time': datetime.now().isoformat(),
                'is_private': is_private,
            })
            if len(self.conversation_memory[chat_id]) > self.MAX_MEMORY:
                self.conversation_memory[chat_id] = self.conversation_memory[chat_id][-self.MAX_MEMORY:]

            # Decide whether to respond
            should_respond = False
            now = time.time()

            if is_private and self.config.get('respond_to_dms', True):
                should_respond = True
            elif is_group:
                # Check if mentioned
                me = await self.client.get_me()
                my_name = (me.first_name or '').lower()
                my_username = (me.username or '').lower()
                mentioned = (my_name and my_name in message_text.lower()) or \
                            (my_username and f"@{my_username}" in message_text.lower()) or \
                            'seven' in message_text.lower()

                # Check active conversation
                in_active_convo = chat_id in self.active_convos and self.active_convos[chat_id] > now

                # Check respond-to-all
                in_respond_all = chat_id in self.respond_to_all

                if mentioned or in_active_convo or in_respond_all:
                    should_respond = True
                    self.active_convos[chat_id] = now + self.CONVO_TIMEOUT

            if not should_respond:
                return

            # Rate limit check
            self.rate_limits[chat_id] = [t for t in self.rate_limits[chat_id] if t > now - self.RATE_WINDOW]
            if len(self.rate_limits[chat_id]) >= self.RATE_LIMIT:
                return
            self.rate_limits[chat_id].append(now)

            # Mark as read
            if self.config.get('auto_read', True):
                await event.mark_read()

            # Show typing
            if self.config.get('typing_indicator', True):
                async with self.client.action(chat_id, 'typing'):
                    response = await self._generate_response(
                        sender_name, message_text, chat_title, is_private, chat_id
                    )
            else:
                response = await self._generate_response(
                    sender_name, message_text, chat_title, is_private, chat_id
                )

            if response:
                # Split long messages (Telegram limit is 4096)
                if len(response) > 4096:
                    for i in range(0, len(response), 4096):
                        await event.reply(response[i:i+4096])
                        await asyncio.sleep(0.5)
                else:
                    await event.reply(response)

                self.logger.info(f"[Telegram] Replied in {chat_title}: {response[:80]}...")

        except Exception as e:
            self.logger.error(f"[Telegram] Error handling message: {e}")

    async def _generate_response(self, sender: str, message: str, chat: str,
                                  is_private: bool, chat_id: int) -> Optional[str]:
        """Generate a response using Seven's brain."""
        if not self.bot_core:
            return None

        # Build context
        context_prefix = f"[Telegram {'DM' if is_private else 'group'}: {chat}] {sender}: "

        # Include recent conversation history
        recent = self.conversation_memory.get(chat_id, [])[-10:]
        history_lines = []
        for msg in recent[:-1]:  # Exclude current message
            history_lines.append(f"{msg['sender']}: {msg['text']}")
        history = "\n".join(history_lines[-5:]) if history_lines else ""

        full_input = f"{context_prefix}{message}"
        if history:
            full_input = f"[Recent chat:\n{history}]\n{full_input}"

        # Route through Seven's brain
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self.bot_core._process_input, full_input
            )
            if response:
                # Clean for Telegram (remove voice markup etc)
                response = re.sub(r'\[.*?\]', '', response).strip()
                if len(response) > 4000:
                    response = response[:4000] + "..."
            return response
        except Exception as e:
            self.logger.error(f"[Telegram] Brain error: {e}")
            return None

    # === Voice/Text command methods (called from _handle_telegram_request) ===

    def send_message(self, target: str, message: str) -> str:
        """Send a message to a user or group by username/title."""
        if not self._running or not self.client:
            return "Telegram not connected."

        async def _send():
            try:
                entity = await self.client.get_entity(target)
                await self.client.send_message(entity, message)
                return f"Sent to {target}: {message[:60]}..."
            except Exception as e:
                return f"Failed to send to {target}: {e}"

        future = asyncio.run_coroutine_threadsafe(_send(), self._loop)
        return future.result(timeout=15)

    def get_status(self) -> str:
        """Get Telegram connection status."""
        if not self.available:
            return "Telethon not installed. Run: pip install telethon"
        if not self._is_configured():
            return "Telegram not configured. Need API ID + hash from https://my.telegram.org"
        if not self._running:
            return "Telegram client not running. Say 'start telegram' to connect."

        active = sum(1 for t in self.active_convos.values() if t > time.time())
        chats = len(self.conversation_memory)
        return (f"Telegram: Connected | "
                f"Active convos: {active} | "
                f"Chats seen: {chats} | "
                f"DM replies: {'ON' if self.config.get('respond_to_dms') else 'OFF'} | "
                f"Group replies: {'ON' if self.config.get('respond_in_groups') else 'OFF'}")

    def list_chats(self) -> str:
        """List recent chats."""
        if not self._running or not self.client:
            return "Telegram not connected."

        async def _list():
            dialogs = await self.client.get_dialogs(limit=20)
            lines = ["Recent Telegram chats:"]
            for d in dialogs:
                chat_type = "DM" if d.is_user else ("Group" if d.is_group else "Channel")
                unread = f" ({d.unread_count} unread)" if d.unread_count else ""
                lines.append(f"  [{chat_type}] {d.name}{unread}")
            return "\n".join(lines)

        future = asyncio.run_coroutine_threadsafe(_list(), self._loop)
        return future.result(timeout=15)

    def get_unread(self) -> str:
        """Get unread messages."""
        if not self._running or not self.client:
            return "Telegram not connected."

        async def _unread():
            dialogs = await self.client.get_dialogs(limit=50)
            unread_chats = [d for d in dialogs if d.unread_count > 0]
            if not unread_chats:
                return "No unread Telegram messages."
            lines = [f"Unread Telegram messages ({sum(d.unread_count for d in unread_chats)} total):"]
            for d in unread_chats[:15]:
                lines.append(f"  {d.name}: {d.unread_count} unread")
            return "\n".join(lines)

        future = asyncio.run_coroutine_threadsafe(_unread(), self._loop)
        return future.result(timeout=15)

    def set_respond_dms(self, enabled: bool) -> str:
        """Toggle responding to DMs."""
        self.config['respond_to_dms'] = enabled
        self._save_config()
        return f"Telegram DM responses: {'ON' if enabled else 'OFF'}"

    def set_respond_groups(self, enabled: bool) -> str:
        """Toggle responding in groups."""
        self.config['respond_in_groups'] = enabled
        self._save_config()
        return f"Telegram group responses: {'ON' if enabled else 'OFF'}"
