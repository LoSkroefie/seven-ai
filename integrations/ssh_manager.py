"""
SSH Manager - Seven Can Manage Remote Servers

Seven connects to remote Linux servers via SSH, runs commands,
manages files, and understands the output through Ollama.

Requires: paramiko
"""

import os
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger("SSHManager")

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    logger.warning("paramiko not installed — SSH unavailable. pip install paramiko")


class SSHManager:
    """
    Seven's SSH capability.
    
    - Connects to remote servers via SSH
    - Runs commands and processes output
    - Manages files on remote systems
    - Remembers server configs
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("SSHManager")
        self.available = PARAMIKO_AVAILABLE
        
        # Config
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / "Documents" / "Seven" / "ssh"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "servers.json"
        self.servers = self._load_servers()
        
        # Active connections
        self._connections: Dict[str, paramiko.SSHClient] = {}
        self._lock = threading.Lock()
        
        # Command history
        self.command_history = []
        
        if self.available:
            self.logger.info(f"[OK] SSH Manager ready — {len(self.servers)} server(s) configured")
    
    # ============ SERVER CONFIG ============
    
    def add_server(self, name: str, host: str, username: str,
                   password: Optional[str] = None, key_file: Optional[str] = None,
                   port: int = 22) -> str:
        """Add or update a server configuration"""
        self.servers[name] = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,  # TODO: encrypt at rest
            'key_file': key_file,
            'added': datetime.now().isoformat()
        }
        self._save_servers()
        return f"Server '{name}' configured: {username}@{host}:{port}"
    
    def remove_server(self, name: str) -> str:
        """Remove a server configuration"""
        if name in self.servers:
            self.disconnect(name)
            del self.servers[name]
            self._save_servers()
            return f"Server '{name}' removed."
        return f"No server named '{name}' found."
    
    def list_servers(self) -> str:
        """List configured servers"""
        if not self.servers:
            return "No servers configured. Use 'add server' to configure one."
        
        lines = ["Configured servers:"]
        for name, cfg in self.servers.items():
            connected = "🟢" if name in self._connections else "⚪"
            lines.append(f"  {connected} {name}: {cfg['username']}@{cfg['host']}:{cfg['port']}")
        return "\n".join(lines)
    
    # ============ CONNECTION ============
    
    def connect(self, server_name: str) -> str:
        """Connect to a configured server"""
        if not self.available:
            return "SSH not available. Install paramiko: pip install paramiko"
        
        if server_name not in self.servers:
            available = ", ".join(self.servers.keys()) if self.servers else "none"
            return f"Unknown server '{server_name}'. Available: {available}"
        
        if server_name in self._connections:
            # Test if still alive
            try:
                transport = self._connections[server_name].get_transport()
                if transport and transport.is_active():
                    return f"Already connected to {server_name}."
            except Exception:
                pass
            # Dead connection, clean up
            del self._connections[server_name]
        
        cfg = self.servers[server_name]
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': cfg['host'],
                'port': cfg['port'],
                'username': cfg['username'],
                'timeout': 15,
            }
            
            if cfg.get('key_file'):
                connect_kwargs['key_filename'] = cfg['key_file']
            elif cfg.get('password'):
                connect_kwargs['password'] = cfg['password']
            
            client.connect(**connect_kwargs)
            
            with self._lock:
                self._connections[server_name] = client
            
            self.logger.info(f"Connected to {server_name} ({cfg['host']})")
            return f"Connected to {server_name} ({cfg['username']}@{cfg['host']})"
            
        except paramiko.AuthenticationException:
            return f"Authentication failed for {server_name}. Check credentials."
        except paramiko.SSHException as e:
            return f"SSH error connecting to {server_name}: {str(e)[:200]}"
        except Exception as e:
            return f"Failed to connect to {server_name}: {str(e)[:200]}"
    
    def disconnect(self, server_name: str) -> str:
        """Disconnect from a server"""
        with self._lock:
            if server_name in self._connections:
                try:
                    self._connections[server_name].close()
                except Exception:
                    pass
                del self._connections[server_name]
                return f"Disconnected from {server_name}."
        return f"Not connected to {server_name}."
    
    def disconnect_all(self):
        """Disconnect from all servers"""
        with self._lock:
            for name, client in self._connections.items():
                try:
                    client.close()
                except Exception:
                    pass
            self._connections.clear()
    
    # ============ COMMAND EXECUTION ============
    
    def run_command(self, server_name: str, command: str, timeout: int = 30) -> Dict:
        """
        Run a command on a remote server.
        
        Returns:
            Dict with 'success', 'stdout', 'stderr', 'exit_code', 'message'
        """
        if not self.available:
            return {'success': False, 'message': 'SSH not available'}
        
        # Auto-connect if not connected
        if server_name not in self._connections:
            connect_result = self.connect(server_name)
            if server_name not in self._connections:
                return {'success': False, 'message': connect_result}
        
        client = self._connections[server_name]
        
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            out = stdout.read().decode('utf-8', errors='replace')
            err = stderr.read().decode('utf-8', errors='replace')
            
            # Log to history
            self.command_history.append({
                'server': server_name,
                'command': command,
                'exit_code': exit_code,
                'timestamp': datetime.now().isoformat(),
                'output_length': len(out)
            })
            # Keep history reasonable
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
            
            result = {
                'success': exit_code == 0,
                'stdout': out[:5000],
                'stderr': err[:2000],
                'exit_code': exit_code,
                'message': f"Command executed (exit code: {exit_code})"
            }
            
            self.logger.info(f"[{server_name}] {command} -> exit {exit_code} ({len(out)} bytes)")
            return result
            
        except Exception as e:
            self.logger.error(f"Command execution failed on {server_name}: {e}")
            # Connection might be dead
            self.disconnect(server_name)
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1,
                'message': f"Command failed: {str(e)[:200]}"
            }
    
    # ============ FILE OPERATIONS ============
    
    def read_remote_file(self, server_name: str, remote_path: str, max_bytes: int = 50000) -> Dict:
        """Read a file from the remote server"""
        if server_name not in self._connections:
            connect_result = self.connect(server_name)
            if server_name not in self._connections:
                return {'success': False, 'message': connect_result}
        
        try:
            sftp = self._connections[server_name].open_sftp()
            try:
                with sftp.open(remote_path, 'r') as f:
                    content = f.read(max_bytes).decode('utf-8', errors='replace')
                return {'success': True, 'content': content, 'path': remote_path}
            finally:
                sftp.close()
        except FileNotFoundError:
            return {'success': False, 'message': f"File not found: {remote_path}"}
        except Exception as e:
            return {'success': False, 'message': f"Failed to read {remote_path}: {str(e)[:200]}"}
    
    def write_remote_file(self, server_name: str, remote_path: str, content: str) -> Dict:
        """Write content to a file on the remote server"""
        if server_name not in self._connections:
            connect_result = self.connect(server_name)
            if server_name not in self._connections:
                return {'success': False, 'message': connect_result}
        
        try:
            sftp = self._connections[server_name].open_sftp()
            try:
                with sftp.open(remote_path, 'w') as f:
                    f.write(content)
                return {'success': True, 'message': f"Written to {remote_path} ({len(content)} bytes)"}
            finally:
                sftp.close()
        except Exception as e:
            return {'success': False, 'message': f"Failed to write {remote_path}: {str(e)[:200]}"}
    
    def list_remote_dir(self, server_name: str, remote_path: str = "/") -> Dict:
        """List files in a remote directory"""
        result = self.run_command(server_name, f"ls -la {remote_path}")
        return result
    
    # ============ SERVER HEALTH ============
    
    def check_server_health(self, server_name: str) -> Dict:
        """Quick health check on a server"""
        commands = {
            'uptime': 'uptime',
            'disk': "df -h / | tail -1 | awk '{print $5 \" used of \" $2}'",
            'memory': "free -h | grep Mem | awk '{print $3 \" used of \" $2}'",
            'load': "cat /proc/loadavg | awk '{print $1, $2, $3}'",
            'processes': "ps aux | wc -l",
        }
        
        health = {}
        for key, cmd in commands.items():
            result = self.run_command(server_name, cmd, timeout=10)
            if result['success']:
                health[key] = result['stdout'].strip()
            else:
                health[key] = f"error: {result.get('stderr', 'unknown')[:100]}"
        
        return health
    
    def check_websites(self, server_name: str) -> Dict:
        """Check which websites are running on the server"""
        result = self.run_command(server_name, 
            "if command -v httpd &>/dev/null; then httpd -S 2>&1 | grep -E 'namevhost|port'; "
            "elif command -v nginx &>/dev/null; then nginx -T 2>&1 | grep server_name; "
            "elif command -v apache2 &>/dev/null; then apache2ctl -S 2>&1 | grep -E 'namevhost|port'; "
            "else echo 'No web server found'; fi"
        )
        return result
    
    # ============ PERSISTENCE ============
    
    def _load_servers(self) -> Dict:
        """Load server configurations from disk"""
        try:
            if self.config_file.exists():
                data = json.loads(self.config_file.read_text(encoding='utf-8'))
                self.logger.info(f"Loaded {len(data)} server config(s)")
                return data
        except Exception as e:
            self.logger.warning(f"Failed to load server configs: {e}")
        return {}
    
    def _save_servers(self):
        """Save server configurations to disk"""
        try:
            # Don't save passwords in plaintext — just save connection info
            safe_data = {}
            for name, cfg in self.servers.items():
                safe_data[name] = {k: v for k, v in cfg.items() if k != 'password'}
                if cfg.get('password'):
                    safe_data[name]['has_password'] = True
            self.config_file.write_text(json.dumps(safe_data, indent=2), encoding='utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to save server configs: {e}")
