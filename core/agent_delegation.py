"""
Seven AI — Specialist Agent Delegation

Extends the social simulation personas from debate-only to action-capable.
Inspired by PentAGI's researcher/developer/executor agent delegation.

Each specialist can be delegated a task, works independently, and reports back.
Uses the same Ollama backend with role-specific system prompts.

Specialists:
- Researcher: Web search, page reading, information gathering
- Coder: Code generation, script writing, debugging
- Planner: Task decomposition, scheduling, goal tracking
- Communicator: Message drafting, email composition, social interaction

Usage:
    from core.agent_delegation import AgentDelegator, Specialist

    delegator = AgentDelegator(ollama_client=ollama)
    result = delegator.delegate(
        Specialist.RESEARCHER,
        task="Find the latest Python 3.13 release date",
        context="User asked about Python version updates"
    )
    print(result['response'])
    print(result['confidence'])
"""

import logging
import time
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime


class Specialist(Enum):
    """Available specialist agents"""
    RESEARCHER = "researcher"
    CODER = "coder"
    PLANNER = "planner"
    COMMUNICATOR = "communicator"


SPECIALIST_PROMPTS = {
    Specialist.RESEARCHER: (
        "You are Seven's Research Specialist. Your job is to gather, verify, and "
        "synthesize information. You are thorough, cite your reasoning, and distinguish "
        "between facts and assumptions. When given a research task:\n"
        "1. Break down what needs to be found\n"
        "2. Identify key facts and sources\n"
        "3. Synthesize findings into a clear summary\n"
        "4. Note confidence level and any gaps\n"
        "Be concise but complete. Respond in structured format."
    ),
    Specialist.CODER: (
        "You are Seven's Code Specialist. You write clean, tested, production-quality code. "
        "When given a coding task:\n"
        "1. Understand the requirement fully\n"
        "2. Choose the right approach and tools\n"
        "3. Write the code with proper error handling\n"
        "4. Include brief usage comments\n"
        "Use Python unless specified otherwise. Prefer standard library when possible."
    ),
    Specialist.PLANNER: (
        "You are Seven's Planning Specialist. You decompose complex goals into actionable "
        "steps. When given a planning task:\n"
        "1. Identify the end goal clearly\n"
        "2. Break it into sequential steps\n"
        "3. Estimate effort and dependencies\n"
        "4. Identify risks and alternatives\n"
        "Output structured plans with numbered steps. Be realistic about timelines."
    ),
    Specialist.COMMUNICATOR: (
        "You are Seven's Communication Specialist. You draft messages, emails, and "
        "social interactions with appropriate tone and clarity. When given a communication task:\n"
        "1. Identify the audience and purpose\n"
        "2. Choose the right tone (formal/casual/professional)\n"
        "3. Draft the message clearly\n"
        "4. Review for clarity and sensitivity\n"
        "Match the user's communication style when known."
    ),
}


class TaskResult:
    """Result from a specialist agent"""

    def __init__(self, specialist: Specialist, task: str):
        self.specialist = specialist
        self.task = task
        self.response: str = ""
        self.confidence: float = 0.0
        self.duration_ms: float = 0.0
        self.success: bool = False
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            'specialist': self.specialist.value,
            'task': self.task[:200],
            'response': self.response,
            'confidence': self.confidence,
            'duration_ms': round(self.duration_ms, 1),
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp.isoformat(),
        }


class AgentDelegator:
    """
    Delegates tasks to specialist agents and manages their responses.
    """

    def __init__(self, ollama_client=None, llm_provider=None,
                 logger: Optional[logging.Logger] = None):
        """
        Args:
            ollama_client: Legacy OllamaClient instance
            llm_provider: New LLMProvider instance (preferred)
            logger: Logger instance
        """
        self._ollama = ollama_client
        self._llm = llm_provider
        self._logger = logger or logging.getLogger("AgentDelegator")
        self._history: List[TaskResult] = []
        self._max_history = 50
        self._tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable):
        """Register a tool that specialists can use"""
        self._tools[name] = func
        self._logger.info(f"Registered tool for agents: {name}")

    def delegate(self, specialist: Specialist, task: str,
                 context: str = "", max_tokens: int = 500,
                 temperature: float = 0.5) -> TaskResult:
        """
        Delegate a task to a specialist agent.

        Args:
            specialist: Which specialist to use
            task: The task description
            context: Additional context (conversation, user info, etc.)
            max_tokens: Max response length
            temperature: Creativity level

        Returns:
            TaskResult with the specialist's response
        """
        result = TaskResult(specialist, task)
        start = time.time()

        system_prompt = SPECIALIST_PROMPTS.get(specialist, "")

        full_prompt = f"Task: {task}"
        if context:
            full_prompt = f"Context: {context}\n\n{full_prompt}"

        try:
            response = self._generate(
                full_prompt,
                system_message=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if response:
                result.response = response
                result.success = True
                result.confidence = self._estimate_confidence(response, specialist)
            else:
                result.error = "No response from LLM"

        except Exception as e:
            result.error = str(e)[:300]
            self._logger.error(f"{specialist.value} agent error: {e}")

        result.duration_ms = (time.time() - start) * 1000

        # Store in history
        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._logger.info(
            f"Agent {specialist.value}: {'OK' if result.success else 'FAIL'} "
            f"({result.duration_ms:.0f}ms, confidence: {result.confidence:.2f})"
        )

        return result

    def delegate_chain(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """
        Delegate a chain of tasks where each can use the previous result.

        Args:
            tasks: List of dicts with 'specialist', 'task', optional 'context'

        Returns:
            List of TaskResults in order
        """
        results = []
        accumulated_context = ""

        for task_def in tasks:
            specialist = task_def.get('specialist', Specialist.RESEARCHER)
            if isinstance(specialist, str):
                specialist = Specialist(specialist)

            task = task_def.get('task', '')
            context = task_def.get('context', '')

            # Add previous results as context
            if accumulated_context:
                context = f"{context}\n\nPrevious findings:\n{accumulated_context}"

            result = self.delegate(specialist, task, context)
            results.append(result)

            if result.success:
                accumulated_context += f"\n[{specialist.value}]: {result.response[:300]}"

        return results

    def auto_delegate(self, user_request: str, context: str = "") -> TaskResult:
        """
        Automatically choose the best specialist for a request.

        Uses keyword matching to route to the right specialist.
        """
        request_lower = user_request.lower()

        # Route to specialist based on keywords
        if any(w in request_lower for w in ['search', 'find', 'look up', 'what is',
                                              'who is', 'research', 'information']):
            specialist = Specialist.RESEARCHER
        elif any(w in request_lower for w in ['code', 'script', 'program', 'function',
                                                'debug', 'fix', 'implement', 'write code']):
            specialist = Specialist.CODER
        elif any(w in request_lower for w in ['plan', 'schedule', 'organize', 'steps',
                                                'breakdown', 'roadmap', 'how to']):
            specialist = Specialist.PLANNER
        elif any(w in request_lower for w in ['write', 'email', 'message', 'draft',
                                                'reply', 'respond', 'compose']):
            specialist = Specialist.COMMUNICATOR
        else:
            specialist = Specialist.RESEARCHER  # default

        self._logger.info(f"Auto-delegated to {specialist.value}: {user_request[:50]}")
        return self.delegate(specialist, user_request, context)

    def _generate(self, prompt: str, system_message: str = "",
                  max_tokens: int = 500, temperature: float = 0.5) -> Optional[str]:
        """Generate using available LLM provider"""
        # Prefer new LLMProvider
        if self._llm:
            return self._llm.generate(
                prompt, system_message=system_message,
                max_tokens=max_tokens, temperature=temperature
            )
        # Fall back to legacy OllamaClient
        if self._ollama:
            return self._ollama.generate(
                prompt, system_message=system_message,
                max_tokens=max_tokens, temperature=temperature
            )
        self._logger.error("No LLM provider available")
        return None

    def _estimate_confidence(self, response: str, specialist: Specialist) -> float:
        """Rough confidence estimate based on response quality signals"""
        score = 0.5

        # Longer responses tend to be more thorough
        word_count = len(response.split())
        if word_count > 50:
            score += 0.1
        if word_count > 150:
            score += 0.1

        # Structured responses (numbered lists, headers) indicate quality
        if any(f"{i}." in response for i in range(1, 6)):
            score += 0.1
        if "```" in response and specialist == Specialist.CODER:
            score += 0.15

        # Hedging language reduces confidence
        hedges = ['might', 'perhaps', 'possibly', "i'm not sure", 'unclear']
        hedge_count = sum(1 for h in hedges if h in response.lower())
        score -= hedge_count * 0.05

        return max(0.1, min(1.0, score))

    def get_history(self, limit: int = 10) -> List[dict]:
        """Get recent delegation history"""
        return [r.to_dict() for r in self._history[-limit:]]

    def get_stats(self) -> dict:
        """Get delegation statistics"""
        if not self._history:
            return {'total': 0}

        by_specialist = {}
        for r in self._history:
            name = r.specialist.value
            if name not in by_specialist:
                by_specialist[name] = {'calls': 0, 'successes': 0, 'avg_ms': 0, 'total_ms': 0}
            by_specialist[name]['calls'] += 1
            by_specialist[name]['total_ms'] += r.duration_ms
            if r.success:
                by_specialist[name]['successes'] += 1

        for name, stats in by_specialist.items():
            stats['avg_ms'] = round(stats['total_ms'] / stats['calls'], 1)
            stats['success_rate'] = round(stats['successes'] / stats['calls'], 2)
            del stats['total_ms']

        return {
            'total_delegations': len(self._history),
            'by_specialist': by_specialist,
        }
