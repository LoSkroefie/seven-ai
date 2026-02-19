"""
Seven AI Daemon — 24/7 Background Service

Runs Seven as a persistent background process that survives terminal close.
On Windows: runs as a background process with optional Windows Service support.
On Linux: uses proper daemonization.

Usage:
    python seven_daemon.py start       # Start daemon
    python seven_daemon.py stop        # Stop daemon
    python seven_daemon.py status      # Check if running
    python seven_daemon.py restart     # Restart
    python seven_daemon.py foreground  # Run in foreground (debug)
"""

import sys
import os
import time
import json
import signal
import atexit
import logging
import threading
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

PID_FILE = Path.home() / ".chatbot" / "seven_daemon.pid"
LOG_FILE = Path.home() / ".chatbot" / "seven_daemon.log"
STATE_FILE = Path.home() / ".chatbot" / "daemon_state.json"

# Ensure dirs exist
PID_FILE.parent.mkdir(parents=True, exist_ok=True)


class SevenDaemon:
    """
    Seven AI background daemon.
    
    Manages the bot lifecycle as a persistent background process:
    - Starts bot core + autonomous life + scheduler + API server
    - Handles graceful shutdown on signals
    - Writes PID file for management
    - Auto-restarts on crash (configurable)
    - Persists state across restarts
    """

    def __init__(self):
        self.bot = None
        self.api_server = None
        self.scheduler = None
        self.running = False
        self.restart_on_crash = True
        self.max_restarts = 5
        self.restart_count = 0
        self.start_time = None
        
        # Setup logging
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Configure daemon logging to file + console"""
        logger = logging.getLogger("SevenDaemon")
        logger.setLevel(logging.INFO)
        
        # File handler (persistent)
        fh = logging.FileHandler(str(LOG_FILE), encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(fh)
        
        # Console handler (when running in foreground)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(ch)
        
        return logger

    def _write_pid(self):
        """Write PID file"""
        PID_FILE.write_text(str(os.getpid()))
        self.logger.info(f"PID {os.getpid()} written to {PID_FILE}")

    def _remove_pid(self):
        """Remove PID file"""
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def _read_pid(self):
        """Read PID from file, return None if not running"""
        if not PID_FILE.exists():
            return None
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is actually running
            if self._is_process_alive(pid):
                return pid
            else:
                # Stale PID file
                self._remove_pid()
                return None
        except (ValueError, OSError):
            return None

    @staticmethod
    def _is_process_alive(pid):
        """Check if a process with given PID is running"""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback without psutil
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True, text=True
                )
                return str(pid) in result.stdout
            else:
                try:
                    os.kill(pid, 0)
                    return True
                except OSError:
                    return False

    def _save_state(self):
        """Save daemon state for persistence"""
        state = {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'restart_count': self.restart_count,
            'pid': os.getpid(),
            'last_heartbeat': datetime.now().isoformat()
        }
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        self.logger.info(f"Received signal {sig_name} — shutting down gracefully...")
        self.running = False

    def _init_bot(self):
        """Initialize the bot core"""
        from core.enhanced_bot import UltimateBotCore
        self.bot = UltimateBotCore()
        return self.bot

    def _init_scheduler(self):
        """Initialize persistent scheduler"""
        try:
            from seven_scheduler import SevenScheduler
            self.scheduler = SevenScheduler(self.bot)
            self.scheduler.start()
            self.logger.info("[DAEMON] Scheduler started")
        except Exception as e:
            self.logger.error(f"Scheduler init failed: {e}")
            self.scheduler = None

    def _init_api(self):
        """Initialize API server in background thread"""
        try:
            from seven_api import create_app
            import uvicorn
            
            app = create_app(self.bot)
            
            api_thread = threading.Thread(
                target=uvicorn.run,
                kwargs={
                    'app': app,
                    'host': '127.0.0.1',
                    'port': 7777,
                    'log_level': 'warning'
                },
                daemon=True,
                name="SevenAPI"
            )
            api_thread.start()
            self.logger.info("[DAEMON] API server started on http://127.0.0.1:7777")
        except Exception as e:
            self.logger.error(f"API server init failed: {e}")

    def run(self):
        """Main daemon run loop"""
        self.running = True
        self.start_time = datetime.now()
        
        # Write PID
        self._write_pid()
        atexit.register(self._remove_pid)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        if sys.platform != 'win32':
            signal.signal(signal.SIGHUP, self._signal_handler)
        
        self.logger.info("=" * 60)
        self.logger.info("  SEVEN AI DAEMON STARTING")
        self.logger.info(f"  PID: {os.getpid()}")
        self.logger.info(f"  Time: {self.start_time.isoformat()}")
        self.logger.info("=" * 60)
        
        while self.running:
            try:
                # Initialize bot
                self.logger.info("[DAEMON] Initializing Seven AI...")
                self._init_bot()
                
                # Start the bot (tests Ollama, starts subsystems)
                self.bot.start()
                
                # Start scheduler
                self._init_scheduler()
                
                # Start API server
                self._init_api()
                
                self.logger.info("[DAEMON] Seven AI is fully operational — daemon running 24/7")
                self._save_state()
                
                # Heartbeat loop — keep daemon alive
                while self.running:
                    time.sleep(30)
                    self._save_state()
                    
                    # Check bot health
                    if self.bot and hasattr(self.bot, 'health_monitor') and self.bot.health_monitor:
                        try:
                            self.bot.health_monitor.run_checks()
                        except Exception:
                            pass
                
            except KeyboardInterrupt:
                self.logger.info("[DAEMON] Keyboard interrupt — shutting down")
                self.running = False
                
            except Exception as e:
                self.restart_count += 1
                self.logger.error(f"[DAEMON] Crash #{self.restart_count}: {e}", exc_info=True)
                
                if self.restart_on_crash and self.restart_count < self.max_restarts:
                    wait = min(60, 5 * self.restart_count)
                    self.logger.info(f"[DAEMON] Restarting in {wait}s (attempt {self.restart_count}/{self.max_restarts})...")
                    time.sleep(wait)
                else:
                    self.logger.error(f"[DAEMON] Max restarts reached ({self.max_restarts}). Stopping.")
                    self.running = False
        
        # Cleanup
        self._shutdown()

    def _shutdown(self):
        """Clean shutdown of all components"""
        self.logger.info("[DAEMON] Shutting down all components...")
        
        try:
            if self.scheduler:
                self.scheduler.stop()
                self.logger.info("[DAEMON] Scheduler stopped")
        except Exception as e:
            self.logger.error(f"Scheduler shutdown error: {e}")
        
        try:
            if self.bot:
                if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                    self.bot.autonomous_life.stop()
                if hasattr(self.bot, 'vision') and self.bot.vision:
                    self.bot.vision.stop()
                self.bot.running = False
                self.logger.info("[DAEMON] Bot stopped")
        except Exception as e:
            self.logger.error(f"Bot shutdown error: {e}")
        
        self._remove_pid()
        self.logger.info("[DAEMON] Seven AI daemon stopped.")


def cmd_start():
    """Start the daemon"""
    daemon = SevenDaemon()
    pid = daemon._read_pid()
    if pid:
        print(f"Seven daemon is already running (PID {pid})")
        return
    
    if sys.platform == 'win32':
        # On Windows, spawn detached process
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, __file__, 'foreground'],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=open(str(LOG_FILE), 'a'),
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL
        )
        print(f"Seven daemon started (PID {proc.pid})")
        print(f"Log: {LOG_FILE}")
        print(f"API: http://127.0.0.1:7777")
    else:
        # On Linux/Mac, fork
        pid = os.fork()
        if pid > 0:
            print(f"Seven daemon started (PID {pid})")
            print(f"Log: {LOG_FILE}")
            print(f"API: http://127.0.0.1:7777")
            sys.exit(0)
        else:
            # Child process — become daemon
            os.setsid()
            daemon.run()


def cmd_stop():
    """Stop the daemon"""
    daemon = SevenDaemon()
    pid = daemon._read_pid()
    if not pid:
        print("Seven daemon is not running")
        return
    
    print(f"Stopping Seven daemon (PID {pid})...")
    try:
        if sys.platform == 'win32':
            import subprocess
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
        
        # Wait for shutdown
        for _ in range(10):
            if not SevenDaemon._is_process_alive(pid):
                break
            time.sleep(1)
        
        daemon._remove_pid()
        print("Seven daemon stopped.")
    except Exception as e:
        print(f"Error stopping daemon: {e}")


def cmd_status():
    """Check daemon status"""
    daemon = SevenDaemon()
    pid = daemon._read_pid()
    
    if not pid:
        print("Seven daemon: NOT RUNNING")
        return
    
    print(f"Seven daemon: RUNNING (PID {pid})")
    
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            start = state.get('start_time', 'unknown')
            restarts = state.get('restart_count', 0)
            heartbeat = state.get('last_heartbeat', 'unknown')
            print(f"  Started: {start}")
            print(f"  Restarts: {restarts}")
            print(f"  Last heartbeat: {heartbeat}")
        except Exception:
            pass
    
    print(f"  Log: {LOG_FILE}")
    print(f"  API: http://127.0.0.1:7777")


def cmd_foreground():
    """Run in foreground (for debugging or detached spawn)"""
    daemon = SevenDaemon()
    daemon.run()


def main():
    if len(sys.argv) < 2:
        print("Usage: python seven_daemon.py {start|stop|status|restart|foreground}")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        cmd_start()
    elif command == 'stop':
        cmd_stop()
    elif command == 'status':
        cmd_status()
    elif command == 'restart':
        cmd_stop()
        time.sleep(2)
        cmd_start()
    elif command == 'foreground':
        cmd_foreground()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python seven_daemon.py {start|stop|status|restart|foreground}")
        sys.exit(1)


if __name__ == '__main__':
    main()
