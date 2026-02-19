"""
Seven AI — LLM Provider Abstraction Layer

Decouples Seven from Ollama, enabling swappable backends.
Addresses ChatGPT's critique: tight coupling to Ollama with no way to swap providers.

Usage:
    from core.llm_provider import OllamaProvider

    llm = OllamaProvider()
    response = llm.generate("Hello, who are you?")

To add a new provider, subclass LLMProvider and implement generate().
"""

import time
import logging
import threading
import requests
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All providers must implement generate() at minimum.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> Optional[str]:
        """Generate a text response from a prompt"""
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider is available"""
        ...

    def generate_with_context(
        self,
        user_input: str,
        conversation_context: str,
        system_message: str,
    ) -> Optional[str]:
        """Generate with conversation context (default implementation)"""
        full_prompt = (
            f"Context from previous conversation:\n{conversation_context}\n\n"
            f"Current user input: {user_input}\n\n"
            f"Respond naturally and helpfully based on the context."
        )
        return self.generate(full_prompt, system_message=system_message)


class CircuitBreaker:
    """
    Circuit breaker pattern for LLM connection resilience.
    Addresses Grok/DeepSeek critique: Ollama going down causes cascading failures.

    States:
        CLOSED  — normal operation, requests pass through
        OPEN    — too many failures, requests immediately return None
        HALF    — testing if service recovered, one request allowed through
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0,
                 logger: Optional[logging.Logger] = None):
        self._lock = threading.Lock()
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"
        self.logger = logger or logging.getLogger("CircuitBreaker")

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == "OPEN" and self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self._recovery_timeout:
                    self._state = "HALF"
            return self._state

    def record_success(self):
        with self._lock:
            self._failure_count = 0
            self._state = "CLOSED"

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self._failure_threshold:
                self._state = "OPEN"
                self.logger.warning(
                    f"Circuit OPEN after {self._failure_count} failures. "
                    f"Will retry in {self._recovery_timeout}s."
                )

    def allow_request(self) -> bool:
        state = self.state
        if state == "CLOSED":
            return True
        if state == "HALF":
            self.logger.info("Circuit HALF-OPEN — allowing test request")
            return True
        return False

    def get_status(self) -> dict:
        return {
            'state': self.state,
            'failure_count': self._failure_count,
            'failure_threshold': self._failure_threshold,
            'recovery_timeout': self._recovery_timeout,
        }


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider with circuit breaker resilience.
    Drop-in replacement for OllamaClient with the same interface.
    """

    def __init__(self, base_url: str = None, model: str = None,
                 logger: Optional[logging.Logger] = None):
        import config
        self.base_url = (base_url or getattr(config, 'OLLAMA_URL', 'http://localhost:11434')).rstrip('/')
        self.model = model or getattr(config, 'OLLAMA_MODEL', 'llama3.2')
        self.generate_url = f"{self.base_url}/api/generate"
        self.logger = logger or logging.getLogger("OllamaProvider")
        self.circuit = CircuitBreaker(logger=self.logger)
        self._total_calls = 0
        self._total_failures = 0
        self._total_tokens_est = 0

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> Optional[str]:
        """Generate a response from Ollama with circuit breaker protection"""

        if not self.circuit.allow_request():
            self.logger.debug("Circuit breaker OPEN — skipping Ollama call")
            return None

        self._total_calls += 1

        try:
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            response = requests.post(
                self.generate_url,
                json=payload,
                stream=True,
                timeout=timeout,
            )
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        full_response += data.get("response", "")
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

            self.circuit.record_success()
            result = full_response.strip()
            self._total_tokens_est += len(result.split())
            return result

        except requests.exceptions.ConnectionError:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.warning("Ollama request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Ollama error: {e}")
            return None
        except Exception as e:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Unexpected LLM error: {e}")
            return None

    def ask_with_context(
        self,
        user_input: str,
        conversation_context: str,
        system_message: str,
    ) -> Optional[str]:
        """Compatibility wrapper matching OllamaClient interface"""
        return self.generate_with_context(user_input, conversation_context, system_message)

    def ask_for_decision(self, user_input: str, capabilities: str) -> Optional[str]:
        """Compatibility wrapper matching OllamaClient interface"""
        prompt = (
            f'You are a voice assistant. Based on the user\'s request, decide what action to take.\n\n'
            f'User request: "{user_input}"\n\n'
            f'Your capabilities:\n{capabilities}\n\n'
            f'Respond with a clear action to take. Be specific and actionable.'
        )
        system = "You are a decision-making assistant. Provide clear, actionable responses."
        return self.generate(prompt, system_message=system, temperature=0.3)

    def refine_query(self, unresolved_query: str) -> Optional[str]:
        """Compatibility wrapper matching OllamaClient interface"""
        prompt = f"Refine and clarify this query to make it more actionable: '{unresolved_query}'"
        return self.generate(prompt, temperature=0.5)

    def generate_name(self) -> Optional[str]:
        """Compatibility wrapper matching OllamaClient interface"""
        prompt = "Choose a unique, interesting name for yourself as a voice assistant. Respond with just the name, nothing else."
        response = self.generate(prompt, temperature=0.8, max_tokens=50)
        if response:
            words = response.strip().split()
            return words[0].strip('.,!?"\'') if words else None
        return None

    def generate_with_vision(
        self,
        prompt: str,
        image_base64: str,
        vision_model: str = "llama3.2-vision",
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """Compatibility wrapper matching OllamaClient interface"""
        if not self.circuit.allow_request():
            return None
        try:
            payload = {
                "model": vision_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {"temperature": temperature},
            }
            response = requests.post(self.generate_url, json=payload, timeout=30)
            response.raise_for_status()
            self.circuit.record_success()
            return response.json()
        except Exception as e:
            self.circuit.record_failure()
            self.logger.error(f"Vision API error: {e}")
            return None

    def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "llama3.2-vision",
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Compatibility wrapper matching OllamaClient interface"""
        import base64
        try:
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 300},
            }
            response = requests.post(self.generate_url, json=payload, timeout=60)
            response.raise_for_status()
            self.circuit.record_success()
            data = response.json()
            return data.get('response', '').strip() or None
        except FileNotFoundError:
            self.logger.error(f"Image not found: {image_path}")
            return None
        except Exception as e:
            self.circuit.record_failure()
            self.logger.error(f"Vision with image error: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            self.circuit.record_success()
            self.logger.info(f"Connected to Ollama at {self.base_url}")
            return True
        except Exception as e:
            self.circuit.record_failure()
            self.logger.error(f"Cannot connect to Ollama: {e}")
            return False

    def get_status(self) -> dict:
        """Get provider status including circuit breaker state"""
        return {
            'provider': 'ollama',
            'base_url': self.base_url,
            'model': self.model,
            'total_calls': self._total_calls,
            'total_failures': self._total_failures,
            'estimated_tokens': self._total_tokens_est,
            'circuit_breaker': self.circuit.get_status(),
        }
