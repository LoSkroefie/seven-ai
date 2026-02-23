"""
System Health Extension — Seven AI

Monitors CPU, RAM, disk usage and alerts Seven when resources are low.
Runs every 5 minutes by default.
"""

import logging
import platform
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("SystemHealth")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemHealthExtension(SevenExtension):
    """Monitor system resources and alert on low thresholds"""

    name = "System Health Monitor"
    version = "1.0"
    description = "Monitors CPU, RAM, disk and alerts when resources are low"
    author = "Seven AI"

    schedule_interval_minutes = 5
    needs_ollama = False

    # Alert thresholds
    CPU_WARN = 85       # percent
    RAM_WARN = 85       # percent
    DISK_WARN = 90      # percent

    def init(self, bot=None):
        self.bot = bot
        self.alerts = []
        self.last_snapshot = {}

    def run(self, context: dict = None) -> dict:
        if not HAS_PSUTIL:
            return {"message": "psutil not installed — system monitoring unavailable", "status": "unavailable"}

        snapshot = {}
        alerts = []

        # CPU
        cpu = psutil.cpu_percent(interval=1)
        snapshot['cpu_percent'] = cpu
        if cpu > self.CPU_WARN:
            alerts.append(f"CPU usage high: {cpu}%")

        # RAM
        mem = psutil.virtual_memory()
        snapshot['ram_percent'] = mem.percent
        snapshot['ram_used_gb'] = round(mem.used / (1024**3), 1)
        snapshot['ram_total_gb'] = round(mem.total / (1024**3), 1)
        if mem.percent > self.RAM_WARN:
            alerts.append(f"RAM usage high: {mem.percent}% ({snapshot['ram_used_gb']}GB / {snapshot['ram_total_gb']}GB)")

        # Disk
        disk = psutil.disk_usage('/')
        snapshot['disk_percent'] = disk.percent
        snapshot['disk_free_gb'] = round(disk.free / (1024**3), 1)
        if disk.percent > self.DISK_WARN:
            alerts.append(f"Disk usage high: {disk.percent}% ({snapshot['disk_free_gb']}GB free)")

        # Battery (if applicable)
        battery = psutil.sensors_battery()
        if battery:
            snapshot['battery_percent'] = battery.percent
            snapshot['battery_plugged'] = battery.power_plugged
            if battery.percent < 20 and not battery.power_plugged:
                alerts.append(f"Battery low: {battery.percent}% (not plugged in)")

        # System info
        snapshot['platform'] = platform.system()
        snapshot['hostname'] = platform.node()

        self.last_snapshot = snapshot
        self.alerts = alerts

        result = {"snapshot": snapshot, "status": "ok"}
        if alerts:
            result["alerts"] = alerts
            result["message"] = "System alerts: " + "; ".join(alerts)
            logger.warning(f"[SystemHealth] {result['message']}")
        else:
            result["message"] = f"System healthy — CPU: {cpu}%, RAM: {mem.percent}%, Disk: {disk.percent}%"

        return result

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "last_snapshot": self.last_snapshot,
            "active_alerts": len(self.alerts),
            "running": True,
        }
