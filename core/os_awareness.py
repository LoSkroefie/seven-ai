"""
OS Environment Awareness - Seven's Understanding of Her Running Environment

Gives Seven real-time awareness of:
- Operating system (Windows/Linux/Mac)
- System resources (CPU, RAM, disk)
- Running processes
- Network status
- User environment
- Hardware info
- Installed software
- Platform-appropriate command adaptation

This is critical for true autonomy: Seven must know WHERE she is running
to execute commands correctly and adapt behavior to the environment.
"""

import os
import sys
import platform
import subprocess
import shutil
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class OSAwareness:
    """
    Seven's awareness of her operating system environment.
    
    Enables platform-aware command execution, resource monitoring,
    and environmental adaptation. Works on Windows and Linux.
    """
    
    def __init__(self):
        # Detect OS once at init
        self.os_type = platform.system().lower()  # 'windows', 'linux', 'darwin'
        self.os_name = platform.system()
        self.os_version = platform.version()
        self.os_release = platform.release()
        self.architecture = platform.machine()
        self.hostname = platform.node()
        self.python_version = platform.python_version()
        self.username = os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
        self.home_dir = str(Path.home())
        
        # Cache for expensive lookups
        self._system_info_cache = None
        self._cache_time = None
        self._cache_ttl = 60  # seconds
        
        logger.info(f"[OS] Detected: {self.os_name} {self.os_release} ({self.architecture})")
    
    @property
    def is_windows(self) -> bool:
        return self.os_type == 'windows'
    
    @property
    def is_linux(self) -> bool:
        return self.os_type == 'linux'
    
    @property
    def is_mac(self) -> bool:
        return self.os_type == 'darwin'
    
    def get_shell(self) -> str:
        """Get the appropriate shell for this OS"""
        if self.is_windows:
            return 'powershell' if shutil.which('powershell') else 'cmd'
        return os.getenv('SHELL', '/bin/bash')
    
    def adapt_command(self, command: str) -> str:
        """
        Adapt a command for the current OS.
        Takes a generic command intent and returns the platform-specific version.
        """
        # Common command translations
        translations = {
            'windows': {
                'ls': 'dir',
                'cat': 'type',
                'rm': 'del',
                'rm -rf': 'rmdir /s /q',
                'cp': 'copy',
                'mv': 'move',
                'clear': 'cls',
                'which': 'where',
                'grep': 'findstr',
                'ps aux': 'tasklist',
                'kill': 'taskkill /f /pid',
                'ifconfig': 'ipconfig',
                'pwd': 'cd',
                'touch': 'type nul >',
                'chmod': 'icacls',
                'df -h': 'wmic logicaldisk get size,freespace,caption',
                'free -h': 'systeminfo | findstr Memory',
                'uname -a': 'systeminfo | findstr /B /C:"OS"',
                'whoami': 'whoami',
            },
            'linux': {
                'dir': 'ls -la',
                'type': 'cat',
                'del': 'rm',
                'copy': 'cp',
                'move': 'mv',
                'cls': 'clear',
                'where': 'which',
                'findstr': 'grep',
                'tasklist': 'ps aux',
                'taskkill': 'kill',
                'ipconfig': 'ifconfig',
                'systeminfo': 'uname -a && free -h && df -h',
            }
        }
        
        os_key = 'windows' if self.is_windows else 'linux'
        command_lower = command.strip().lower()
        
        # Check for direct translations
        for generic, specific in translations.get(os_key, {}).items():
            if command_lower.startswith(generic):
                remainder = command[len(generic):]
                return specific + remainder
        
        return command
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        resources = {
            'os': f"{self.os_name} {self.os_release}",
            'architecture': self.architecture,
            'hostname': self.hostname,
            'username': self.username,
        }
        
        # CPU count
        resources['cpu_count'] = os.cpu_count() or 0
        
        # Disk usage
        try:
            disk = shutil.disk_usage(self.home_dir)
            resources['disk_total_gb'] = round(disk.total / (1024**3), 1)
            resources['disk_free_gb'] = round(disk.free / (1024**3), 1)
            resources['disk_used_pct'] = round((disk.used / disk.total) * 100, 1)
        except Exception:
            pass
        
        # RAM (platform-specific)
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['wmic', 'OS', 'get', 'FreePhysicalMemory,TotalVisibleMemorySize', '/value'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('TotalVisibleMemorySize='):
                            total_kb = int(line.split('=')[1])
                            resources['ram_total_gb'] = round(total_kb / (1024**2), 1)
                        elif line.startswith('FreePhysicalMemory='):
                            free_kb = int(line.split('=')[1])
                            resources['ram_free_gb'] = round(free_kb / (1024**2), 1)
                    if 'ram_total_gb' in resources and 'ram_free_gb' in resources:
                        used = resources['ram_total_gb'] - resources['ram_free_gb']
                        resources['ram_used_pct'] = round((used / resources['ram_total_gb']) * 100, 1)
            else:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        total_kb = int(line.split()[1])
                        resources['ram_total_gb'] = round(total_kb / (1024**2), 1)
                    elif line.startswith('MemAvailable:'):
                        avail_kb = int(line.split()[1])
                        resources['ram_free_gb'] = round(avail_kb / (1024**2), 1)
                if 'ram_total_gb' in resources and 'ram_free_gb' in resources:
                    used = resources['ram_total_gb'] - resources['ram_free_gb']
                    resources['ram_used_pct'] = round((used / resources['ram_total_gb']) * 100, 1)
        except Exception as e:
            logger.debug(f"RAM info error: {e}")
        
        return resources
    
    def get_running_processes(self, filter_name: str = None) -> List[Dict[str, str]]:
        """Get list of running processes"""
        processes = []
        try:
            if self.is_windows:
                cmd = ['tasklist', '/fo', 'csv', '/nh']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.strip().strip('"').split('","')
                        if len(parts) >= 2:
                            name = parts[0].strip('"')
                            pid = parts[1].strip('"')
                            if filter_name and filter_name.lower() not in name.lower():
                                continue
                            processes.append({'name': name, 'pid': pid})
            else:
                cmd = ['ps', 'aux', '--no-headers']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split(None, 10)
                        if len(parts) >= 11:
                            name = parts[10]
                            pid = parts[1]
                            if filter_name and filter_name.lower() not in name.lower():
                                continue
                            processes.append({'name': name, 'pid': pid})
        except Exception as e:
            logger.debug(f"Process list error: {e}")
        
        return processes[:50]  # Cap at 50
    
    def is_process_running(self, process_name: str) -> bool:
        """Check if a specific process is running"""
        return len(self.get_running_processes(filter_name=process_name)) > 0
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get basic network information"""
        info = {}
        try:
            if self.is_windows:
                result = subprocess.run(
                    ['ipconfig'], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    info['raw'] = result.stdout[:500]
                    # Extract IPv4
                    for line in result.stdout.split('\n'):
                        if 'IPv4' in line and ':' in line:
                            info['ipv4'] = line.split(':')[-1].strip()
                            break
            else:
                result = subprocess.run(
                    ['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    info['raw'] = result.stdout[:500]
                    import re
                    ips = re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                    info['ipv4_addresses'] = [ip for ip in ips if ip != '127.0.0.1']
        except Exception as e:
            logger.debug(f"Network info error: {e}")
        
        return info
    
    def get_installed_software(self) -> List[str]:
        """Get a sample of installed software (quick check)"""
        software = []
        
        # Check for common tools
        tools = [
            'python', 'python3', 'node', 'npm', 'git', 'docker',
            'code', 'ollama', 'ffmpeg', 'curl', 'wget',
            'gcc', 'g++', 'make', 'cmake', 'java', 'javac',
            'pip', 'pip3', 'conda', 'rustc', 'cargo', 'go',
        ]
        
        for tool in tools:
            if shutil.which(tool):
                software.append(tool)
        
        return software
    
    def get_environment_summary(self) -> str:
        """
        Get a complete environment summary for LLM context.
        This is what Seven uses to understand where she's running.
        """
        resources = self.get_system_resources()
        software = self.get_installed_software()
        
        summary = f"""=== OS ENVIRONMENT AWARENESS ===
Platform: {self.os_name} {self.os_release} ({self.architecture})
Hostname: {self.hostname}
User: {self.username}
Home: {self.home_dir}
Shell: {self.get_shell()}
Python: {self.python_version}

System Resources:
- CPU cores: {resources.get('cpu_count', 'unknown')}
- RAM: {resources.get('ram_total_gb', '?')} GB total, {resources.get('ram_free_gb', '?')} GB free ({resources.get('ram_used_pct', '?')}% used)
- Disk: {resources.get('disk_total_gb', '?')} GB total, {resources.get('disk_free_gb', '?')} GB free ({resources.get('disk_used_pct', '?')}% used)

Available Tools: {', '.join(software) if software else 'unknown'}

I am running on {'Windows' if self.is_windows else 'Linux' if self.is_linux else 'macOS'}.
Commands should use {'PowerShell/CMD syntax' if self.is_windows else 'Bash syntax'}.
"""
        return summary
    
    def execute_safe(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command with OS-aware safety.
        Adapts the command for the current platform.
        """
        adapted = self.adapt_command(command)
        
        try:
            if self.is_windows:
                result = subprocess.run(
                    adapted,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.home_dir
                )
            else:
                result = subprocess.run(
                    adapted,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.home_dir
                )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout[:2000],
                'stderr': result.stderr[:500] if result.stderr else '',
                'return_code': result.returncode,
                'command_executed': adapted,
                'platform': self.os_name
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {timeout}s',
                'command_executed': adapted
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command_executed': adapted
            }
    
    def get_context_for_llm(self) -> str:
        """Compact context string for inclusion in LLM prompts"""
        return (
            f"[OS: {self.os_name} {self.os_release} | "
            f"Arch: {self.architecture} | "
            f"User: {self.username} | "
            f"Shell: {self.get_shell()}]"
        )


# Quick test
if __name__ == "__main__":
    os_aware = OSAwareness()
    print(os_aware.get_environment_summary())
    print("\nNetwork:")
    net = os_aware.get_network_info()
    print(f"  IPv4: {net.get('ipv4', net.get('ipv4_addresses', 'unknown'))}")
    print("\nOllama running?", os_aware.is_process_running('ollama'))
    print("\nAdapt 'ls -la':", os_aware.adapt_command('ls -la'))
    print("Adapt 'cat file.txt':", os_aware.adapt_command('cat file.txt'))
