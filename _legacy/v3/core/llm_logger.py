"""
Seven AI — LLM Observability Logger

Tracks every LLM call: tokens, latency, which subsystem triggered it,
what it influenced. Inspired by PentAGI's Langfuse integration, but
local-first using SQLite.

Usage:
    from core.llm_logger import LLMLogger

    logger = LLMLogger()

    with logger.track("emotion_analysis", model="llama3.2") as call:
        result = ollama.generate(prompt)
        call.set_tokens(input_tokens=500, output_tokens=120)
        call.set_result(result)

    # Later: analyze usage
    stats = logger.get_stats()
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Avg latency: {stats['avg_latency_ms']}ms")
"""

import sqlite3
import time
import threading
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

try:
    import config
    DATA_DIR = getattr(config, 'DATA_DIR', Path.home() / '.chatbot')
except ImportError:
    DATA_DIR = Path.home() / '.chatbot'


class LLMCallTracker:
    """Context object for tracking a single LLM call"""

    def __init__(self, subsystem: str, model: str, purpose: str = ""):
        self.subsystem = subsystem
        self.model = model
        self.purpose = purpose
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.prompt_length = 0
        self.response_length = 0
        self.success = True
        self.error: Optional[str] = None
        self.result_preview = ""

    def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def set_prompt(self, prompt: str):
        self.prompt_length = len(prompt)
        if not self.input_tokens:
            self.input_tokens = len(prompt) // 4  # estimate

    def set_result(self, result: Optional[str]):
        if result:
            self.response_length = len(result)
            self.result_preview = result[:200]
            if not self.output_tokens:
                self.output_tokens = len(result) // 4  # estimate

    def set_error(self, error: str):
        self.success = False
        self.error = error[:500]

    def finish(self):
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


class LLMLogger:
    """
    SQLite-backed LLM call logger for observability.
    Thread-safe. Minimal overhead per call.
    """

    def __init__(self, db_path: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        if db_path is None:
            db_path = str(Path(DATA_DIR) / "llm_calls.db")

        self._db_path = db_path
        self._logger = logger or logging.getLogger("LLMLogger")
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create the calls table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    subsystem TEXT NOT NULL,
                    model TEXT NOT NULL,
                    purpose TEXT DEFAULT '',
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    prompt_length INTEGER DEFAULT 0,
                    response_length INTEGER DEFAULT 0,
                    duration_ms REAL DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error TEXT DEFAULT NULL,
                    result_preview TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_llm_calls_timestamp
                ON llm_calls(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_llm_calls_subsystem
                ON llm_calls(subsystem)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            self._logger.error(f"LLM Logger DB init error: {e}")

    @contextmanager
    def track(self, subsystem: str, model: str = "", purpose: str = ""):
        """
        Context manager to track an LLM call.

        Usage:
            with logger.track("emotion_analysis") as call:
                call.set_prompt(prompt)
                result = ollama.generate(prompt)
                call.set_result(result)
        """
        tracker = LLMCallTracker(subsystem, model, purpose)
        try:
            yield tracker
        except Exception as e:
            tracker.set_error(str(e))
            raise
        finally:
            tracker.finish()
            self._store(tracker)

    def log_call(self, subsystem: str, model: str = "",
                 input_tokens: int = 0, output_tokens: int = 0,
                 duration_ms: float = 0, success: bool = True,
                 error: str = "", purpose: str = ""):
        """Direct logging without context manager"""
        tracker = LLMCallTracker(subsystem, model, purpose)
        tracker.input_tokens = input_tokens
        tracker.output_tokens = output_tokens
        tracker.success = success
        tracker.error = error if error else None
        tracker.end_time = tracker.start_time + (duration_ms / 1000)
        self._store(tracker)

    def _store(self, tracker: LLMCallTracker):
        """Store a call record in SQLite"""
        with self._lock:
            try:
                conn = sqlite3.connect(self._db_path)
                conn.execute("""
                    INSERT INTO llm_calls
                    (timestamp, subsystem, model, purpose, input_tokens,
                     output_tokens, prompt_length, response_length,
                     duration_ms, success, error, result_preview)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    tracker.subsystem,
                    tracker.model,
                    tracker.purpose,
                    tracker.input_tokens,
                    tracker.output_tokens,
                    tracker.prompt_length,
                    tracker.response_length,
                    round(tracker.duration_ms, 1),
                    1 if tracker.success else 0,
                    tracker.error,
                    tracker.result_preview[:200],
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                self._logger.error(f"Error storing LLM call: {e}")

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregate statistics for the last N hours"""
        try:
            conn = sqlite3.connect(self._db_path)
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            row = conn.execute("""
                SELECT
                    COUNT(*) as total_calls,
                    SUM(input_tokens) as total_input,
                    SUM(output_tokens) as total_output,
                    AVG(duration_ms) as avg_latency,
                    MAX(duration_ms) as max_latency,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
                FROM llm_calls WHERE timestamp > ?
            """, (cutoff,)).fetchone()

            conn.close()
            return {
                'period_hours': hours,
                'total_calls': row[0] or 0,
                'total_input_tokens': row[1] or 0,
                'total_output_tokens': row[2] or 0,
                'total_tokens': (row[1] or 0) + (row[2] or 0),
                'avg_latency_ms': round(row[3] or 0, 1),
                'max_latency_ms': round(row[4] or 0, 1),
                'failures': row[5] or 0,
            }
        except Exception as e:
            self._logger.error(f"Error getting stats: {e}")
            return {}

    def get_subsystem_breakdown(self, hours: int = 24) -> List[Dict]:
        """Get per-subsystem token usage breakdown"""
        try:
            conn = sqlite3.connect(self._db_path)
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            rows = conn.execute("""
                SELECT
                    subsystem,
                    COUNT(*) as calls,
                    SUM(input_tokens + output_tokens) as total_tokens,
                    AVG(duration_ms) as avg_latency,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
                FROM llm_calls WHERE timestamp > ?
                GROUP BY subsystem
                ORDER BY total_tokens DESC
            """, (cutoff,)).fetchall()

            conn.close()
            return [
                {
                    'subsystem': r[0],
                    'calls': r[1],
                    'total_tokens': r[2] or 0,
                    'avg_latency_ms': round(r[3] or 0, 1),
                    'failures': r[4] or 0,
                }
                for r in rows
            ]
        except Exception as e:
            self._logger.error(f"Error getting breakdown: {e}")
            return []

    def get_recent_calls(self, limit: int = 20) -> List[Dict]:
        """Get recent LLM calls"""
        try:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute("""
                SELECT timestamp, subsystem, model, purpose,
                       input_tokens, output_tokens, duration_ms,
                       success, error
                FROM llm_calls ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
            conn.close()
            return [
                {
                    'timestamp': r[0],
                    'subsystem': r[1],
                    'model': r[2],
                    'purpose': r[3],
                    'input_tokens': r[4],
                    'output_tokens': r[5],
                    'duration_ms': r[6],
                    'success': bool(r[7]),
                    'error': r[8],
                }
                for r in rows
            ]
        except Exception as e:
            self._logger.error(f"Error getting recent calls: {e}")
            return []

    def get_token_usage_timeline(self, hours: int = 24,
                                  bucket_minutes: int = 60) -> List[Dict]:
        """Get token usage over time in buckets"""
        try:
            conn = sqlite3.connect(self._db_path)
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            rows = conn.execute("""
                SELECT
                    substr(timestamp, 1, 13) as hour_bucket,
                    SUM(input_tokens + output_tokens) as tokens,
                    COUNT(*) as calls
                FROM llm_calls WHERE timestamp > ?
                GROUP BY hour_bucket
                ORDER BY hour_bucket
            """, (cutoff,)).fetchall()

            conn.close()
            return [
                {'hour': r[0], 'tokens': r[1] or 0, 'calls': r[2]}
                for r in rows
            ]
        except Exception as e:
            self._logger.error(f"Error getting timeline: {e}")
            return []
