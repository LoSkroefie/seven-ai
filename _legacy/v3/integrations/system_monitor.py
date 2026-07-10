"""
System Monitor - Seven Watches Over Your PC

Proactive monitoring of CPU, RAM, disk, network, and processes.
Pushes alerts through the autonomous message queue when thresholds are exceeded.

Requires: psutil
"""

import logging
import threading
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger("SystemMonitor")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed — system monitoring unavailable")


class SystemMonitor:
    """
    Seven's eyes on the local system.
    
    - Monitors CPU, RAM, disk, network continuously
    - Alerts via autonomous_life message queue when thresholds hit
    - Tracks top resource hogs
    - Provides on-demand system snapshots
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("SystemMonitor")
        self.available = PSUTIL_AVAILABLE
        
        # Thresholds
        self.thresholds = {
            'cpu_percent': 90,
            'ram_percent': 85,
            'disk_percent': 90,
            'process_ram_mb': 2000,
        }
        
        # Alert cooldowns (don't spam)
        self._last_alerts = {}
        self._alert_cooldown = 300  # 5 min between same alert
        
        # Background thread
        self._thread = None
        self._running = False
        self._interval = 30  # Check every 30 seconds
        
        # History for trend detection
        self.history = []
        self._max_history = 120  # Keep 1 hour at 30s intervals
        
        if self.available:
            self.logger.info("[OK] System monitor ready")
    
    def start(self):
        """Start background monitoring"""
        if self._running or not self.available:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="SystemMonitor")
        self._thread.start()
        self.logger.info("System monitor started")
    
    def stop(self):
        """Stop background monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                snapshot = self.get_snapshot()
                self.history.append(snapshot)
                if len(self.history) > self._max_history:
                    self.history = self.history[-self._max_history:]
                
                # Check thresholds and alert
                self._check_thresholds(snapshot)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
            
            time.sleep(self._interval)
    
    # ============ SNAPSHOTS ============
    
    def get_snapshot(self) -> Dict:
        """Get current system state"""
        if not self.available:
            return {'error': 'psutil not available'}
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count': psutil.cpu_count(),
            'ram': self._get_ram(),
            'disk': self._get_disk(),
            'network': self._get_network(),
            'top_processes': self._get_top_processes(5),
        }
        return snapshot
    
    def get_summary(self) -> str:
        """Get human-readable system summary"""
        if not self.available:
            return "System monitoring not available (psutil not installed)"
        
        s = self.get_snapshot()
        ram = s['ram']
        disk = s['disk']
        top = s['top_processes']
        
        lines = [
            f"CPU: {s['cpu_percent']}% ({s['cpu_count']} cores)",
            f"RAM: {ram['used_gb']:.1f}GB / {ram['total_gb']:.1f}GB ({ram['percent']}%)",
            f"Disk C: {disk.get('C:', {}).get('used_gb', '?')}GB / {disk.get('C:', {}).get('total_gb', '?')}GB ({disk.get('C:', {}).get('percent', '?')}%)",
        ]
        
        if top:
            lines.append("Top processes:")
            for p in top[:5]:
                lines.append(f"  {p['name']}: {p['ram_mb']:.0f}MB RAM, {p['cpu_percent']:.1f}% CPU")
        
        return "\n".join(lines)
    
    def get_top_ram_hogs(self, count: int = 10) -> str:
        """Get processes using the most RAM"""
        if not self.available:
            return "psutil not available"
        
        procs = self._get_top_processes(count, sort_by='ram')
        lines = [f"Top {count} RAM consumers:"]
        for p in procs:
            lines.append(f"  {p['name']} (PID {p['pid']}): {p['ram_mb']:.0f}MB")
        return "\n".join(lines)
    
    def get_top_cpu_hogs(self, count: int = 10) -> str:
        """Get processes using the most CPU"""
        if not self.available:
            return "psutil not available"
        
        procs = self._get_top_processes(count, sort_by='cpu')
        lines = [f"Top {count} CPU consumers:"]
        for p in procs:
            lines.append(f"  {p['name']} (PID {p['pid']}): {p['cpu_percent']:.1f}%")
        return "\n".join(lines)
    
    # ============ INTERNAL ============
    
    def _get_ram(self) -> Dict:
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'used_gb': mem.used / (1024**3),
            'available_gb': mem.available / (1024**3),
            'percent': mem.percent,
        }
    
    def _get_disk(self) -> Dict:
        disks = {}
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks[part.mountpoint.rstrip('\\')] = {
                    'total_gb': round(usage.total / (1024**3), 1),
                    'used_gb': round(usage.used / (1024**3), 1),
                    'free_gb': round(usage.free / (1024**3), 1),
                    'percent': usage.percent,
                }
            except Exception:
                pass
        return disks
    
    def _get_network(self) -> Dict:
        try:
            counters = psutil.net_io_counters()
            return {
                'bytes_sent': counters.bytes_sent,
                'bytes_recv': counters.bytes_recv,
            }
        except Exception:
            return {}
    
    def _get_top_processes(self, count: int = 5, sort_by: str = 'ram') -> List[Dict]:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                ram_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                procs.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'ram_mb': ram_mb,
                    'cpu_percent': info['cpu_percent'] or 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        key = 'ram_mb' if sort_by == 'ram' else 'cpu_percent'
        procs.sort(key=lambda p: p[key], reverse=True)
        return procs[:count]
    
    # ============ ALERTS ============
    
    def _check_thresholds(self, snapshot: Dict):
        """Check if any thresholds are exceeded and alert"""
        now = datetime.now()
        
        # CPU
        if snapshot['cpu_percent'] > self.thresholds['cpu_percent']:
            self._alert('high_cpu', f"CPU is at {snapshot['cpu_percent']}%! Something's working hard.")
        
        # RAM
        ram_pct = snapshot['ram']['percent']
        if ram_pct > self.thresholds['ram_percent']:
            top = snapshot['top_processes'][0] if snapshot['top_processes'] else None
            hog = f" {top['name']} is using {top['ram_mb']:.0f}MB." if top else ""
            self._alert('high_ram', f"RAM is at {ram_pct}%.{hog}")
        
        # Disk
        for mount, info in snapshot['disk'].items():
            if info['percent'] > self.thresholds['disk_percent']:
                self._alert(f'disk_{mount}', f"Disk {mount} is {info['percent']}% full — only {info['free_gb']}GB free.")
    
    def _alert(self, alert_key: str, message: str):
        """Send alert through message queue with cooldown"""
        now = datetime.now()
        last = self._last_alerts.get(alert_key)
        
        if last and (now - last).total_seconds() < self._alert_cooldown:
            return  # Cooldown
        
        self._last_alerts[alert_key] = now
        
        # Push to autonomous message queue
        if self.bot and hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
            self.bot.autonomous_life.queue_message(message, priority="medium")
            self.logger.info(f"Alert: {message}")
        else:
            self.logger.warning(f"Alert (no queue): {message}")
