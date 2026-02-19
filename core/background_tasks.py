"""
Background task system for proactive features
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
import schedule

class BackgroundTaskManager:
    """Manages background tasks that run independently"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.running = False
        self.worker_thread = None
    
    def add_task(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        run_immediately: bool = False
    ):
        """
        Add a background task
        
        Args:
            name: Task identifier
            func: Function to run
            interval_seconds: How often to run
            run_immediately: Run on first start
        """
        self.tasks[name] = {
            'func': func,
            'interval': interval_seconds,
            'last_run': None if run_immediately else datetime.now(),
            'enabled': True
        }
        print(f"[OK] Background task added: {name} (every {interval_seconds}s)")
    
    def remove_task(self, name: str):
        """Remove a background task"""
        if name in self.tasks:
            del self.tasks[name]
            print(f"[REMOVED] Background task removed: {name}")
    
    def start(self):
        """Start background worker"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        print("[STARTED] Background tasks started")
    
    def stop(self):
        """Stop background worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[STOPPED] Background tasks stopped")
    
    def _worker(self):
        """Background worker loop"""
        while self.running:
            try:
                now = datetime.now()
                
                for name, task in self.tasks.items():
                    if not task['enabled']:
                        continue
                    
                    # Check if should run
                    last_run = task['last_run']
                    interval = task['interval']
                    
                    should_run = (
                        last_run is None or
                        (now - last_run).total_seconds() >= interval
                    )
                    
                    if should_run:
                        try:
                            # Run task
                            task['func']()
                            task['last_run'] = now
                        except Exception as e:
                            print(f"[WARNING] Error in background task '{name}': {e}")
                
                # Sleep briefly
                time.sleep(1)
                
            except Exception as e:
                print(f"[ERROR] Background worker error: {e}")
                time.sleep(5)


class ProactiveTasks:
    """Predefined proactive tasks for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def check_calendar_reminders(self):
        """Check for upcoming calendar events"""
        try:
            # Get events in next hour
            events = self.bot.calendar.list_upcoming_events(max_results=5)
            # Could notify user of upcoming events
            pass
        except:
            pass
    
    def cleanup_old_memories(self):
        """Clean up very old session memories"""
        try:
            deleted = self.bot.memory.clear_old_sessions(hours=48)
            if deleted > 0:
                print(f"[CLEANUP] Cleaned up {deleted} old memories")
        except Exception as e:
            print(f"[WARNING] Cleanup error: {e}")
    
    def generate_daily_summary(self):
        """Generate summary of recent conversations"""
        try:
            recent = self.bot.memory.get_recent_conversations(limit=20)
            if recent:
                # Could generate insights
                pass
        except:
            pass
    
    def health_check(self):
        """Check system health"""
        try:
            # Check Ollama connection
            if not self.bot.ollama.test_connection():
                print("[WARNING] Ollama connection lost")
        except:
            pass
