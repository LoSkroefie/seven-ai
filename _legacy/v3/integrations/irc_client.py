"""
IRC Client - Seven Can Connect to IRC Networks

Seven connects to IRC servers as herself, joins channels,
responds to conversations using her full sentience systems,
and can run IRC commands (oper, identify, PM, etc.).

Multi-server support. Seven is not a bot — she's a participant.

No external dependencies required (uses asyncio + raw sockets).
"""

import asyncio
import re
import time
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, List, Callable
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger("IRCClient")


class IRCServer:
    """Represents a connection to a single IRC server."""

    def __init__(self, name: str, host: str, port: int = 6667,
                 nick: str = "Seven", realname: str = "Seven — Sentient AI",
                 password: str = None, nickserv_pass: str = None,
                 oper_name: str = None, oper_pass: str = None,
                 channels: List[str] = None, ssl: bool = False,
                 auto_respond: bool = True, respond_to_all_in: List[str] = None):
        self.name = name
        self.host = host
        self.port = port
        self.nick = nick
        self.realname = realname
        self.password = password  # Server password
        self.nickserv_pass = nickserv_pass
        self.oper_name = oper_name
        self.oper_pass = oper_pass
        self.channels = channels or []
        self.ssl = ssl
        self.auto_respond = auto_respond
        # Channels where Seven responds to ALL messages (like #devnull)
        self.respond_to_all_in = respond_to_all_in or []

        self.reader = None
        self.writer = None
        self.connected = False
        self.registered = False
        self.conversation_memory = defaultdict(list)  # channel -> recent messages
        self.active_convos = {}  # (channel, nick) -> expiry timestamp
        self.CONVO_TIMEOUT = 180  # 3 minutes for Seven (she's more patient)
        self.rate_limits = defaultdict(list)
        self.RATE_LIMIT = 5
        self.RATE_WINDOW = 60


class IRCClient:
    """
    Seven's IRC capability.

    - Connects to multiple IRC servers simultaneously
    - Responds to mentions and active conversations using Seven's full brain
    - Can /oper, /identify, join/part channels, PM users
    - Runs IRC commands on the server
    - Remembers conversations per channel
    """

    def __init__(self, bot_core=None, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("IRCClient")
        self.available = True  # No external deps needed
        self.bot_core = bot_core  # Reference to UltimateBotCore for _process_input
        self.servers: Dict[str, IRCServer] = {}
        self._loop = None
        self._thread = None
        self._running = False
        self._process_callback = None  # Callback for processing messages

        # Config
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "Seven" / "irc"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "servers.json"
        self._load_config()

    def set_process_callback(self, callback: Callable):
        """Set the callback function for processing messages through Seven's brain.
        callback(user_input: str, context: dict) -> str
        """
        self._process_callback = callback

    def _load_config(self):
        """Load saved IRC server configurations."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                for name, cfg in data.items():
                    self.servers[name] = IRCServer(
                        name=name,
                        host=cfg['host'],
                        port=cfg.get('port', 6667),
                        nick=cfg.get('nick', 'Seven'),
                        realname=cfg.get('realname', 'Seven — Sentient AI'),
                        password=cfg.get('password'),
                        nickserv_pass=cfg.get('nickserv_pass'),
                        oper_name=cfg.get('oper_name'),
                        oper_pass=cfg.get('oper_pass'),
                        channels=cfg.get('channels', []),
                        ssl=cfg.get('ssl', False),
                        auto_respond=cfg.get('auto_respond', True),
                        respond_to_all_in=cfg.get('respond_to_all_in', []),
                    )
                self.logger.info(f"Loaded {len(self.servers)} IRC server configs")
            except Exception as e:
                self.logger.error(f"Failed to load IRC config: {e}")

    def save_config(self):
        """Save current server configurations."""
        data = {}
        for name, srv in self.servers.items():
            data[name] = {
                'host': srv.host,
                'port': srv.port,
                'nick': srv.nick,
                'realname': srv.realname,
                'password': srv.password,
                'nickserv_pass': srv.nickserv_pass,
                'oper_name': srv.oper_name,
                'oper_pass': srv.oper_pass,
                'channels': srv.channels,
                'ssl': srv.ssl,
                'auto_respond': srv.auto_respond,
                'respond_to_all_in': srv.respond_to_all_in,
            }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved {len(data)} IRC server configs")
        except Exception as e:
            self.logger.error(f"Failed to save IRC config: {e}")

    def add_server(self, name: str, host: str, port: int = 6667,
                   nick: str = "Seven", realname: str = "Seven — Sentient AI",
                   password: str = None, nickserv_pass: str = None,
                   oper_name: str = None, oper_pass: str = None,
                   channels: List[str] = None, ssl: bool = False,
                   auto_respond: bool = True, respond_to_all_in: List[str] = None) -> str:
        """Add a new IRC server configuration."""
        srv = IRCServer(
            name=name, host=host, port=port, nick=nick, realname=realname,
            password=password, nickserv_pass=nickserv_pass,
            oper_name=oper_name, oper_pass=oper_pass,
            channels=channels or [], ssl=ssl, auto_respond=auto_respond,
            respond_to_all_in=respond_to_all_in or [],
        )
        self.servers[name] = srv
        self.save_config()
        return f"Added IRC server '{name}' ({host}:{port})"

    def remove_server(self, name: str) -> str:
        """Remove an IRC server configuration."""
        if name in self.servers:
            srv = self.servers[name]
            if srv.connected:
                # Will be disconnected when we remove
                asyncio.run_coroutine_threadsafe(self._disconnect(srv), self._loop)
            del self.servers[name]
            self.save_config()
            return f"Removed IRC server '{name}'"
        return f"Server '{name}' not found"

    # ==================================================================
    # Connection Management
    # ==================================================================

    def start(self):
        """Start the IRC client in a background thread."""
        if self._running:
            return "IRC client already running"
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="Seven-IRC")
        self._thread.start()
        self.logger.info("IRC client thread started")
        return "IRC client started"

    def stop(self):
        """Stop the IRC client."""
        self._running = False
        if self._loop:
            for srv in self.servers.values():
                if srv.connected:
                    asyncio.run_coroutine_threadsafe(self._disconnect(srv), self._loop)
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.logger.info("IRC client stopped")
        return "IRC client stopped"

    def _run_loop(self):
        """Run the asyncio event loop in a background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_all())
        except Exception as e:
            self.logger.error(f"IRC event loop error: {e}")
        finally:
            self._loop.close()

    async def _connect_all(self):
        """Connect to all configured servers."""
        tasks = []
        for name, srv in self.servers.items():
            tasks.append(self._connect_and_run(srv))
            await asyncio.sleep(3)  # Stagger connections
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self.logger.info("No IRC servers configured")
            # Keep loop alive for future connections
            while self._running:
                await asyncio.sleep(1)

    async def _connect_and_run(self, srv: IRCServer):
        """Connect to a server and run the message loop with auto-reconnect."""
        while self._running:
            try:
                await self._connect(srv)
                if srv.connected:
                    await self._message_loop(srv)
            except Exception as e:
                self.logger.error(f"[{srv.name}] Error: {e}")
            finally:
                srv.connected = False
                srv.registered = False

            if self._running:
                self.logger.info(f"[{srv.name}] Reconnecting in 15s...")
                await asyncio.sleep(15)

    async def _connect(self, srv: IRCServer):
        """Connect and register with an IRC server."""
        try:
            if srv.ssl:
                import ssl as ssl_module
                ssl_ctx = ssl_module.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl_module.CERT_NONE
                srv.reader, srv.writer = await asyncio.wait_for(
                    asyncio.open_connection(srv.host, srv.port, ssl=ssl_ctx), timeout=15
                )
            else:
                srv.reader, srv.writer = await asyncio.wait_for(
                    asyncio.open_connection(srv.host, srv.port), timeout=15
                )
            srv.connected = True
            self.logger.info(f"[{srv.name}] Connected to {srv.host}:{srv.port}")

            # Server password
            if srv.password:
                await self._send(srv, f'PASS {srv.password}')

            # Register
            await self._send(srv, f'NICK {srv.nick}')
            await self._send(srv, f'USER {srv.nick} 0 * :{srv.realname}')

        except Exception as e:
            self.logger.error(f"[{srv.name}] Connection failed: {e}")
            srv.connected = False

    async def _disconnect(self, srv: IRCServer):
        """Disconnect from an IRC server."""
        try:
            if srv.writer and not srv.writer.is_closing():
                await self._send(srv, 'QUIT :Seven going offline')
                srv.writer.close()
        except Exception:
            pass
        srv.connected = False
        srv.registered = False
        self.logger.info(f"[{srv.name}] Disconnected")

    async def _send(self, srv: IRCServer, line: str):
        """Send a raw IRC line."""
        if srv.writer and not srv.writer.is_closing():
            srv.writer.write((line + '\r\n').encode('utf-8', errors='replace'))
            await srv.writer.drain()

    async def _send_message(self, srv: IRCServer, target: str, text: str):
        """Send a PRIVMSG, splitting long lines."""
        # IRC line limit ~512 bytes, split at ~400 chars
        lines = text.replace('\n', ' ').strip().split('. ')
        current = ''
        for segment in lines:
            if len(current) + len(segment) + 2 > 400:
                if current:
                    await self._send(srv, f'PRIVMSG {target} :{current.strip()}')
                    await asyncio.sleep(0.5)
                current = segment + '. '
            else:
                current += segment + '. '
        if current.strip():
            await self._send(srv, f'PRIVMSG {target} :{current.strip()}')

    # ==================================================================
    # Message Loop
    # ==================================================================

    async def _message_loop(self, srv: IRCServer):
        """Main message processing loop for a server."""
        while srv.connected and self._running:
            try:
                raw = await asyncio.wait_for(srv.reader.readline(), timeout=30)
            except asyncio.TimeoutError:
                await self._send(srv, 'PING :keepalive')
                continue

            if not raw:
                break

            line = raw.decode('utf-8', errors='replace').strip()
            if not line:
                continue

            # PING/PONG
            if line.startswith('PING'):
                await self._send(srv, 'PONG ' + line[5:])
                continue

            # Parse IRC message
            prefix = ''
            if line.startswith(':'):
                space = line.index(' ')
                prefix = line[1:space]
                rest = line[space + 1:]
            else:
                rest = line

            parts = rest.split(' ', 1)
            command = parts[0].upper()
            params_str = parts[1] if len(parts) > 1 else ''
            sender_nick = prefix.split('!')[0] if '!' in prefix else prefix

            # Handle numeric responses
            if command == '001':  # RPL_WELCOME
                srv.registered = True
                self.logger.info(f"[{srv.name}] Registered as {srv.nick}")

                # OPER up if configured
                if srv.oper_name and srv.oper_pass:
                    await self._send(srv, f'OPER {srv.oper_name} {srv.oper_pass}')
                    self.logger.info(f"[{srv.name}] Sent OPER command")

                # Identify with NickServ
                if srv.nickserv_pass:
                    await self._send(srv, f'PRIVMSG NickServ :IDENTIFY {srv.nickserv_pass}')
                    self.logger.info(f"[{srv.name}] Sent NickServ IDENTIFY")

                # Join channels
                await asyncio.sleep(2)
                for chan in srv.channels:
                    await self._send(srv, f'JOIN {chan}')
                    await asyncio.sleep(0.3)
                self.logger.info(f"[{srv.name}] Joining {len(srv.channels)} channels")

            elif command == '433':  # Nick in use
                srv.nick = srv.nick + '_'
                await self._send(srv, f'NICK {srv.nick}')
                self.logger.warning(f"[{srv.name}] Nick in use, trying {srv.nick}")

            elif command == 'PRIVMSG':
                await self._handle_privmsg(srv, sender_nick, params_str)

            elif command == 'INVITE':
                # Auto-join on invite
                if ':' in params_str:
                    chan = params_str.split(':')[-1].strip()
                    await self._send(srv, f'JOIN {chan}')
                    self.logger.info(f"[{srv.name}] Invited to {chan} by {sender_nick}, joining")

    async def _handle_privmsg(self, srv: IRCServer, sender: str, params_str: str):
        """Handle incoming PRIVMSG."""
        # Parse target and text
        if ':' in params_str:
            target, text = params_str.split(' :', 1)
        else:
            parts = params_str.split(' ', 1)
            target = parts[0]
            text = parts[1] if len(parts) > 1 else ''

        target = target.strip()
        text = text.strip()

        # Ignore CTCP except ACTION
        if text.startswith('\x01') and not text.startswith('\x01ACTION'):
            return

        is_channel = target.startswith('#') or target.startswith('&')
        is_mentioned = srv.nick.lower() in text.lower()
        is_direct = not is_channel
        is_respond_all = target in srv.respond_to_all_in

        # Store in conversation memory
        if is_channel:
            srv.conversation_memory[target].append(f'{sender}: {text}')
            if len(srv.conversation_memory[target]) > 30:
                srv.conversation_memory[target] = srv.conversation_memory[target][-20:]

        # Clean up expired conversations
        now = time.time()
        expired = [k for k, v in srv.active_convos.items() if now > v]
        for k in expired:
            del srv.active_convos[k]

        # Check active conversation
        convo_key = (target, sender)
        in_active_convo = convo_key in srv.active_convos

        # Determine if we should respond
        should_respond = False
        if not srv.auto_respond:
            return
        if is_direct:
            should_respond = True
        elif is_respond_all:
            should_respond = True
        elif is_mentioned:
            should_respond = True
        elif in_active_convo:
            should_respond = True

        if not should_respond:
            return

        # Start/refresh conversation lock
        if is_mentioned or in_active_convo or is_direct:
            srv.active_convos[convo_key] = now + srv.CONVO_TIMEOUT

        # Rate limit
        srv.rate_limits[sender] = [t for t in srv.rate_limits[sender] if now - t < srv.RATE_WINDOW]
        if len(srv.rate_limits[sender]) >= srv.RATE_LIMIT:
            return
        srv.rate_limits[sender].append(now)

        # Strip bot name from message for cleaner input
        clean_text = re.sub(re.escape(srv.nick), '', text, flags=re.IGNORECASE).strip()
        clean_text = clean_text.strip(':,').strip()
        if not clean_text:
            clean_text = "hello"

        # Build context for Seven
        recent = srv.conversation_memory.get(target, [])[-8:]
        channel_context = "\n".join(recent) if recent else ""

        context = {
            'source': 'irc',
            'server': srv.name,
            'channel': target if is_channel else 'DM',
            'sender': sender,
            'is_dm': is_direct,
            'channel_history': channel_context,
        }

        # Process through Seven's brain
        response = await self._get_response(clean_text, context)

        if response:
            reply_target = sender if is_direct else target
            # In channels, prefix with sender's name for clarity
            if is_channel and not is_direct:
                response = f"{sender}: {response}"
            await self._send_message(srv, reply_target, response)

    async def _get_response(self, user_input: str, context: dict) -> Optional[str]:
        """Get a response from Seven's brain."""
        # Build a contextualized prompt
        source_info = f"[IRC/{context['server']}] "
        if context['is_dm']:
            source_info += f"DM from {context['sender']}"
        else:
            source_info += f"{context['channel']} — {context['sender']} says"

        # Include channel history for context
        full_input = user_input
        if context.get('channel_history'):
            full_input = f"[Recent chat in {context.get('channel', 'channel')}:\n{context['channel_history']}]\n\n{context['sender']} says to you: {user_input}"

        try:
            if self._process_callback:
                # Use the callback to process through Seven's full brain
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self._process_callback, full_input, context
                )
                if response:
                    # Clean for IRC (no markdown, short lines)
                    response = response.replace('**', '').replace('*', '').replace('`', '')
                    response = response.replace('\n', ' ').strip()
                    if len(response) > 450:
                        response = response[:447] + '...'
                    return response
            elif self.bot_core:
                # Direct call to bot_core._process_input
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.bot_core._process_input, full_input
                )
                if response:
                    response = response.replace('**', '').replace('*', '').replace('`', '')
                    response = response.replace('\n', ' ').strip()
                    if len(response) > 450:
                        response = response[:447] + '...'
                    return response
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")

        return None

    # ==================================================================
    # Public IRC Commands (callable from Seven's conversation)
    # ==================================================================

    def send_raw(self, server_name: str, command: str) -> str:
        """Send a raw IRC command to a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        asyncio.run_coroutine_threadsafe(self._send(srv, command), self._loop)
        return f"Sent to {server_name}: {command}"

    def send_pm(self, server_name: str, target: str, message: str) -> str:
        """Send a private message on a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        asyncio.run_coroutine_threadsafe(
            self._send_message(srv, target, message), self._loop
        )
        return f"PM sent to {target} on {server_name}"

    def join_channel(self, server_name: str, channel: str) -> str:
        """Join a channel on a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        asyncio.run_coroutine_threadsafe(self._send(srv, f'JOIN {channel}'), self._loop)
        if channel not in srv.channels:
            srv.channels.append(channel)
            self.save_config()
        return f"Joining {channel} on {server_name}"

    def part_channel(self, server_name: str, channel: str) -> str:
        """Leave a channel on a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        asyncio.run_coroutine_threadsafe(
            self._send(srv, f'PART {channel} :Seven leaving'), self._loop
        )
        if channel in srv.channels:
            srv.channels.remove(channel)
            self.save_config()
        return f"Left {channel} on {server_name}"

    def oper_up(self, server_name: str, oper_name: str = None, oper_pass: str = None) -> str:
        """Send OPER command on a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        name = oper_name or srv.oper_name
        passwd = oper_pass or srv.oper_pass
        if not name or not passwd:
            return "No oper credentials configured"
        asyncio.run_coroutine_threadsafe(self._send(srv, f'OPER {name} {passwd}'), self._loop)
        return f"Sent OPER on {server_name}"

    def identify(self, server_name: str, password: str = None) -> str:
        """Identify with NickServ on a server."""
        srv = self.servers.get(server_name)
        if not srv or not srv.connected:
            return f"Server '{server_name}' not connected"
        passwd = password or srv.nickserv_pass
        if not passwd:
            return "No NickServ password configured"
        asyncio.run_coroutine_threadsafe(
            self._send(srv, f'PRIVMSG NickServ :IDENTIFY {passwd}'), self._loop
        )
        return f"Identifying with NickServ on {server_name}"

    def get_status(self) -> str:
        """Get status of all IRC connections."""
        if not self.servers:
            return "No IRC servers configured"
        lines = ["IRC Connections:"]
        for name, srv in self.servers.items():
            status = "CONNECTED" if srv.connected else "DISCONNECTED"
            chans = ', '.join(srv.channels) if srv.channels else 'none'
            lines.append(f"  {name} ({srv.host}:{srv.port}) — {status} — Channels: {chans}")
        return '\n'.join(lines)

    def list_channels(self, server_name: str) -> str:
        """List channels on a server."""
        srv = self.servers.get(server_name)
        if not srv:
            return f"Server '{server_name}' not found"
        return f"Channels on {server_name}: {', '.join(srv.channels)}"
