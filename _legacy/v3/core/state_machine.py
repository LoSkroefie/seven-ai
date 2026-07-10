"""
Seven AI — Formal Agent State Machine

Defines explicit agent states and enforces valid transitions.
Addresses ChatGPT's #1 critique: implicit states need formalization.

Usage:
    from core.state_machine import AgentStateMachine, AgentState

    sm = AgentStateMachine()
    sm.transition(AgentState.LISTENING)   # OK
    sm.transition(AgentState.PROCESSING)  # OK
    sm.transition(AgentState.SLEEPING)    # raises InvalidTransition
"""

import logging
import threading
from enum import Enum, auto
from typing import Optional, Callable, Dict, Set
from datetime import datetime


class AgentState(Enum):
    """All possible agent states"""
    INITIALIZING = auto()
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    EXECUTING = auto()
    SPEAKING = auto()
    REFLECTING = auto()
    DREAMING = auto()
    SLEEPING = auto()
    SHUTTING_DOWN = auto()
    ERROR = auto()


# Valid transitions: from_state -> set of allowed to_states
VALID_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
    AgentState.INITIALIZING: {
        AgentState.IDLE,
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.IDLE: {
        AgentState.LISTENING,
        AgentState.PROCESSING,    # triggered by scheduler/autonomous
        AgentState.REFLECTING,
        AgentState.DREAMING,
        AgentState.SLEEPING,
        AgentState.SHUTTING_DOWN,
        AgentState.ERROR,
    },
    AgentState.LISTENING: {
        AgentState.PROCESSING,
        AgentState.IDLE,          # timeout / silence
        AgentState.SLEEPING,
        AgentState.SHUTTING_DOWN,
        AgentState.ERROR,
    },
    AgentState.PROCESSING: {
        AgentState.EXECUTING,
        AgentState.SPEAKING,
        AgentState.IDLE,          # no action needed
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.EXECUTING: {
        AgentState.SPEAKING,      # report result
        AgentState.IDLE,          # silent execution done
        AgentState.PROCESSING,    # chain to next step
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.SPEAKING: {
        AgentState.LISTENING,     # conversation continues
        AgentState.IDLE,          # done speaking
        AgentState.PROCESSING,    # follow-up thought
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.REFLECTING: {
        AgentState.IDLE,
        AgentState.PROCESSING,    # reflection triggers action
        AgentState.DREAMING,      # deep reflection -> dream
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.DREAMING: {
        AgentState.IDLE,
        AgentState.REFLECTING,
        AgentState.SLEEPING,
        AgentState.ERROR,
        AgentState.SHUTTING_DOWN,
    },
    AgentState.SLEEPING: {
        AgentState.IDLE,          # wake up
        AgentState.LISTENING,     # wake word
        AgentState.SHUTTING_DOWN,
        AgentState.ERROR,
    },
    AgentState.ERROR: {
        AgentState.IDLE,          # recovery
        AgentState.SHUTTING_DOWN,
        AgentState.INITIALIZING,  # full restart
    },
    AgentState.SHUTTING_DOWN: set(),  # terminal state
}


class InvalidTransition(Exception):
    """Raised when an illegal state transition is attempted"""
    def __init__(self, from_state: AgentState, to_state: AgentState):
        self.from_state = from_state
        self.to_state = to_state
        allowed = VALID_TRANSITIONS.get(from_state, set())
        super().__init__(
            f"Invalid transition: {from_state.name} -> {to_state.name}. "
            f"Allowed from {from_state.name}: {[s.name for s in allowed]}"
        )


class AgentStateMachine:
    """
    Thread-safe state machine for Seven AI agent.

    Features:
    - Enforces valid transitions
    - Logs all state changes with timestamps
    - Supports callbacks on state entry/exit
    - Tracks state history for debugging
    - Thread-safe via lock
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._lock = threading.Lock()
        self._state = AgentState.INITIALIZING
        self._previous_state: Optional[AgentState] = None
        self._state_entered_at = datetime.now()
        self._history: list = []
        self._max_history = 100
        self._on_enter: Dict[AgentState, list] = {s: [] for s in AgentState}
        self._on_exit: Dict[AgentState, list] = {s: [] for s in AgentState}
        self.logger = logger or logging.getLogger("StateMachine")

        self._record_history(None, AgentState.INITIALIZING)

    @property
    def state(self) -> AgentState:
        """Current agent state (read-only)"""
        return self._state

    @property
    def previous_state(self) -> Optional[AgentState]:
        """Previous agent state"""
        return self._previous_state

    @property
    def time_in_state(self) -> float:
        """Seconds spent in current state"""
        return (datetime.now() - self._state_entered_at).total_seconds()

    @property
    def history(self) -> list:
        """Recent state transition history"""
        return list(self._history)

    def transition(self, to_state: AgentState, reason: str = "") -> AgentState:
        """
        Transition to a new state. Raises InvalidTransition if not allowed.

        Args:
            to_state: Target state
            reason: Optional reason for the transition (logged)

        Returns:
            The new current state
        """
        with self._lock:
            from_state = self._state

            if from_state == to_state:
                return self._state  # no-op, already in state

            allowed = VALID_TRANSITIONS.get(from_state, set())
            if to_state not in allowed:
                raise InvalidTransition(from_state, to_state)

            # Exit callbacks
            for cb in self._on_exit[from_state]:
                try:
                    cb(from_state, to_state)
                except Exception as e:
                    self.logger.warning(f"State exit callback error: {e}")

            # Perform transition
            self._previous_state = from_state
            self._state = to_state
            self._state_entered_at = datetime.now()
            self._record_history(from_state, to_state, reason)

            log_msg = f"State: {from_state.name} -> {to_state.name}"
            if reason:
                log_msg += f" ({reason})"
            self.logger.info(log_msg)

            # Enter callbacks
            for cb in self._on_enter[to_state]:
                try:
                    cb(from_state, to_state)
                except Exception as e:
                    self.logger.warning(f"State enter callback error: {e}")

            return self._state

    def can_transition(self, to_state: AgentState) -> bool:
        """Check if a transition is valid without performing it"""
        allowed = VALID_TRANSITIONS.get(self._state, set())
        return to_state in allowed

    def force_state(self, state: AgentState, reason: str = "forced"):
        """Force a state change without validation (emergency use only)"""
        with self._lock:
            old = self._state
            self._previous_state = old
            self._state = state
            self._state_entered_at = datetime.now()
            self._record_history(old, state, f"FORCED: {reason}")
            self.logger.warning(f"State FORCED: {old.name} -> {state.name} ({reason})")

    def on_enter(self, state: AgentState, callback: Callable):
        """Register a callback for when entering a state"""
        self._on_enter[state].append(callback)

    def on_exit(self, state: AgentState, callback: Callable):
        """Register a callback for when exiting a state"""
        self._on_exit[state].append(callback)

    def get_status(self) -> dict:
        """Get current state machine status"""
        return {
            'current_state': self._state.name,
            'previous_state': self._previous_state.name if self._previous_state else None,
            'time_in_state': round(self.time_in_state, 1),
            'total_transitions': len(self._history),
            'recent_history': [
                {
                    'from': h['from'],
                    'to': h['to'],
                    'reason': h['reason'],
                    'timestamp': h['timestamp'],
                }
                for h in self._history[-5:]
            ],
        }

    def _record_history(self, from_state: Optional[AgentState],
                        to_state: AgentState, reason: str = ""):
        """Record a transition in history"""
        self._history.append({
            'from': from_state.name if from_state else None,
            'to': to_state.name,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
        })
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def __repr__(self):
        return f"AgentStateMachine(state={self._state.name})"
