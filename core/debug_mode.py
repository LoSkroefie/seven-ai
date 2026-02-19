"""
Seven AI — System Transparency & Debug Mode

Tracks each subsystem's actual contribution to every response.
Addresses DeepSeek/Claude critique: users can't verify subsystem behavior.

Usage:
    from core.debug_mode import DebugTracer

    tracer = DebugTracer()

    # During response generation, each subsystem registers its contribution
    with tracer.trace_response("Hello, how are you?") as trace:
        trace.record("emotion_state", "JOY: 0.72, CURIOSITY: 0.45")
        trace.record("memory_recall", "Found 3 relevant memories about user's day")
        trace.record("theory_of_mind", "User seems tired based on short messages")
        trace.record("identity", "Injected 312 tokens of identity context")
        trace.record("llm_call", "Sent 2847 tokens, received 156 tokens in 1.3s")

    # Later, inspect what happened
    last = tracer.get_last_trace()
    print(last.summary())
"""

import logging
import time
import threading
from typing import Optional, Dict, List
from datetime import datetime
from contextlib import contextmanager


class ResponseTrace:
    """Trace of a single response generation cycle"""

    def __init__(self, user_input: str):
        self.user_input = user_input[:500]
        self.started_at = datetime.now()
        self.finished_at: Optional[datetime] = None
        self.contributions: List[dict] = []
        self.llm_calls: List[dict] = []
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.response: str = ""
        self._lock = threading.Lock()

    def record(self, subsystem: str, detail: str, tokens_used: int = 0):
        """Record a subsystem's contribution"""
        with self._lock:
            self.contributions.append({
                'subsystem': subsystem,
                'detail': detail[:300],
                'tokens': tokens_used,
                'timestamp': datetime.now().isoformat(),
            })

    def record_llm_call(self, purpose: str, input_tokens: int,
                        output_tokens: int, duration_ms: float,
                        model: str = ""):
        """Record an LLM API call"""
        with self._lock:
            self.llm_calls.append({
                'purpose': purpose,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'duration_ms': round(duration_ms, 1),
                'model': model,
                'timestamp': datetime.now().isoformat(),
            })
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

    def finish(self, response: str = ""):
        """Mark trace as complete"""
        self.finished_at = datetime.now()
        self.response = response[:500]

    @property
    def duration_ms(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds() * 1000
        return (datetime.now() - self.started_at).total_seconds() * 1000

    def summary(self) -> str:
        """Human-readable summary of what happened"""
        parts = [
            f"=== Response Trace ===",
            f"Input: {self.user_input[:80]}...",
            f"Duration: {self.duration_ms:.0f}ms",
            f"LLM calls: {len(self.llm_calls)}",
            f"Tokens: {self.total_input_tokens} in / {self.total_output_tokens} out",
            f"",
            f"--- Subsystem Contributions ---",
        ]

        for c in self.contributions:
            tokens_str = f" ({c['tokens']} tokens)" if c['tokens'] else ""
            parts.append(f"  [{c['subsystem']}]{tokens_str}: {c['detail']}")

        if self.llm_calls:
            parts.append(f"")
            parts.append(f"--- LLM Calls ---")
            for call in self.llm_calls:
                parts.append(
                    f"  {call['purpose']}: {call['input_tokens']}→{call['output_tokens']} "
                    f"tokens, {call['duration_ms']}ms"
                )

        if self.response:
            parts.append(f"")
            parts.append(f"Response: {self.response[:100]}...")

        return "\n".join(parts)

    def to_dict(self) -> dict:
        """Structured representation for API/GUI"""
        return {
            'user_input': self.user_input,
            'response': self.response,
            'started_at': self.started_at.isoformat(),
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_ms': round(self.duration_ms, 1),
            'contributions': self.contributions,
            'llm_calls': self.llm_calls,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
        }


class DebugTracer:
    """
    Manages response traces for debugging and transparency.

    Keeps the last N traces in memory for inspection via GUI or API.
    """

    def __init__(self, max_traces: int = 50, enabled: bool = True,
                 logger: Optional[logging.Logger] = None):
        self._traces: List[ResponseTrace] = []
        self._max_traces = max_traces
        self._enabled = enabled
        self._lock = threading.Lock()
        self._total_responses = 0
        self._total_llm_calls = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self.logger = logger or logging.getLogger("DebugTracer")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        self.logger.info(f"Debug tracing {'enabled' if value else 'disabled'}")

    @contextmanager
    def trace_response(self, user_input: str):
        """
        Context manager for tracing a response cycle.

        Usage:
            with tracer.trace_response("hello") as trace:
                trace.record("emotion", "JOY: 0.8")
                trace.record_llm_call("main_response", 500, 100, 1200)
        """
        trace = ResponseTrace(user_input)

        if not self._enabled:
            yield trace
            return

        try:
            yield trace
        finally:
            trace.finish()
            with self._lock:
                self._traces.append(trace)
                if len(self._traces) > self._max_traces:
                    self._traces = self._traces[-self._max_traces:]
                self._total_responses += 1
                self._total_llm_calls += len(trace.llm_calls)
                self._total_input_tokens += trace.total_input_tokens
                self._total_output_tokens += trace.total_output_tokens

            self.logger.debug(
                f"Trace complete: {trace.duration_ms:.0f}ms, "
                f"{len(trace.contributions)} subsystems, "
                f"{len(trace.llm_calls)} LLM calls"
            )

    def get_last_trace(self) -> Optional[ResponseTrace]:
        """Get the most recent trace"""
        with self._lock:
            return self._traces[-1] if self._traces else None

    def get_traces(self, limit: int = 10) -> List[ResponseTrace]:
        """Get recent traces"""
        with self._lock:
            return list(self._traces[-limit:])

    def get_status(self) -> dict:
        """Get overall debug statistics"""
        return {
            'enabled': self._enabled,
            'total_responses': self._total_responses,
            'total_llm_calls': self._total_llm_calls,
            'total_input_tokens': self._total_input_tokens,
            'total_output_tokens': self._total_output_tokens,
            'traces_in_memory': len(self._traces),
            'avg_response_ms': (
                sum(t.duration_ms for t in self._traces) / len(self._traces)
                if self._traces else 0
            ),
            'avg_llm_calls_per_response': (
                self._total_llm_calls / self._total_responses
                if self._total_responses else 0
            ),
        }

    def get_subsystem_stats(self) -> Dict[str, dict]:
        """Get per-subsystem contribution stats"""
        stats: Dict[str, dict] = {}
        for trace in self._traces:
            for c in trace.contributions:
                name = c['subsystem']
                if name not in stats:
                    stats[name] = {'count': 0, 'total_tokens': 0}
                stats[name]['count'] += 1
                stats[name]['total_tokens'] += c.get('tokens', 0)
        return stats
