"""
Seven AI — LLM Provider Abstraction Layer

Decouples Seven from any single LLM backend. Users can choose their provider.

Supported providers:
    - OllamaProvider     — Local Ollama (default, free, private)
    - OpenAIProvider     — OpenAI API (GPT-4o, GPT-4, GPT-3.5-turbo)
    - AnthropicProvider  — Anthropic API (Claude 3.5, Claude 3)
    - OpenAICompatible   — Any OpenAI-compatible API (DeepSeek, Groq, Together,
                           LM Studio, Mistral, OpenRouter, vLLM, etc.)

Usage:
    from core.llm_provider import create_provider

    # Auto-creates from config.py settings:
    llm = create_provider()

    # Or manually:
    from core.llm_provider import OpenAIProvider
    llm = OpenAIProvider(api_key="sk-...", model="gpt-4o")

    response = llm.generate("Hello, who are you?")
"""

import os
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


# ============================================================
#  OpenAI-Compatible Base (shared by OpenAI, DeepSeek, Groq…)
# ============================================================

class OpenAICompatibleProvider(LLMProvider):
    """
    Works with any API that speaks the OpenAI chat-completions format.

    This covers: OpenAI, DeepSeek, Groq, Together, Mistral, OpenRouter,
    LM Studio, vLLM, text-generation-webui, LocalAI, and more.

    Usage:
        llm = OpenAICompatibleProvider(
            api_key="sk-...",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        )
    """

    def __init__(self, api_key: str = "", base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o", logger: Optional[logging.Logger] = None):
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.logger = logger or logging.getLogger(f"LLM:{self._provider_name}")
        self.circuit = CircuitBreaker(logger=self.logger)
        self._total_calls = 0
        self._total_failures = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    @property
    def _provider_name(self) -> str:
        """Derive a short name from the base URL"""
        host = self.base_url.split("//")[-1].split("/")[0].split(":")[0]
        return host.replace("api.", "").replace(".com", "").replace(".ai", "")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> Optional[str]:
        if not self.circuit.allow_request():
            return None

        self._total_calls += 1
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            # Track token usage if returned
            usage = data.get("usage", {})
            self._total_input_tokens += usage.get("prompt_tokens", 0)
            self._total_output_tokens += usage.get("completion_tokens", 0)

            choice = data.get("choices", [{}])[0]
            text = choice.get("message", {}).get("content", "")

            self.circuit.record_success()
            return text.strip() if text else None

        except requests.exceptions.ConnectionError:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Cannot connect to {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.warning(f"Request to {self._provider_name} timed out")
            return None
        except requests.exceptions.HTTPError as e:
            self._total_failures += 1
            self.circuit.record_failure()
            error_body = ""
            try:
                error_body = e.response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            self.logger.error(f"{self._provider_name} HTTP {e.response.status_code}: {error_body}")
            return None
        except Exception as e:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Unexpected {self._provider_name} error: {e}")
            return None

    def test_connection(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}/models",
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code in (200, 401, 403):
                # 401/403 means the endpoint exists but key is wrong
                self.logger.info(f"Connected to {self._provider_name} ({resp.status_code})")
                return resp.status_code == 200
            return False
        except Exception as e:
            self.logger.error(f"Cannot reach {self._provider_name}: {e}")
            return False

    def get_status(self) -> dict:
        return {
            'provider': self._provider_name,
            'base_url': self.base_url,
            'model': self.model,
            'total_calls': self._total_calls,
            'total_failures': self._total_failures,
            'input_tokens': self._total_input_tokens,
            'output_tokens': self._total_output_tokens,
            'circuit_breaker': self.circuit.get_status(),
        }


# ============================================================
#  OpenAI (convenience subclass)
# ============================================================

class OpenAIProvider(OpenAICompatibleProvider):
    """
    OpenAI API provider (GPT-4o, GPT-4, GPT-3.5-turbo, etc.)

    Usage:
        llm = OpenAIProvider(api_key="sk-...", model="gpt-4o")
        # or set OPENAI_API_KEY env var
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o",
                 logger: Optional[logging.Logger] = None):
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        super().__init__(
            api_key=key,
            base_url="https://api.openai.com/v1",
            model=model,
            logger=logger or logging.getLogger("OpenAI"),
        )


# ============================================================
#  Anthropic (Claude) — different API format
# ============================================================

class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider (Claude 3.5 Sonnet, Claude 3 Opus, etc.)

    Usage:
        llm = AnthropicProvider(api_key="sk-ant-...", model="claude-3-5-sonnet-20241022")
        # or set ANTHROPIC_API_KEY env var
    """

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str = "", model: str = "claude-3-5-sonnet-20241022",
                 logger: Optional[logging.Logger] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.logger = logger or logging.getLogger("Anthropic")
        self.circuit = CircuitBreaker(logger=self.logger)
        self._total_calls = 0
        self._total_failures = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30,
    ) -> Optional[str]:
        if not self.circuit.allow_request():
            return None

        self._total_calls += 1

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_message:
            payload["system"] = system_message

        try:
            resp = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            usage = data.get("usage", {})
            self._total_input_tokens += usage.get("input_tokens", 0)
            self._total_output_tokens += usage.get("output_tokens", 0)

            content_blocks = data.get("content", [])
            text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text += block.get("text", "")

            self.circuit.record_success()
            return text.strip() if text else None

        except requests.exceptions.ConnectionError:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error("Cannot connect to Anthropic API")
            return None
        except requests.exceptions.Timeout:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.warning("Anthropic request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            self._total_failures += 1
            self.circuit.record_failure()
            error_body = ""
            try:
                error_body = e.response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            self.logger.error(f"Anthropic HTTP {e.response.status_code}: {error_body}")
            return None
        except Exception as e:
            self._total_failures += 1
            self.circuit.record_failure()
            self.logger.error(f"Unexpected Anthropic error: {e}")
            return None

    def test_connection(self) -> bool:
        try:
            # Anthropic doesn't have a /models endpoint; send a tiny request
            result = self.generate("Say 'ok'", max_tokens=5, timeout=10)
            return result is not None
        except Exception:
            return False

    def get_status(self) -> dict:
        return {
            'provider': 'anthropic',
            'model': self.model,
            'total_calls': self._total_calls,
            'total_failures': self._total_failures,
            'input_tokens': self._total_input_tokens,
            'output_tokens': self._total_output_tokens,
            'circuit_breaker': self.circuit.get_status(),
        }


# ============================================================
#  Provider Factory
# ============================================================

# Well-known OpenAI-compatible endpoints
KNOWN_PROVIDERS = {
    'ollama':      {'base_url': 'http://localhost:11434',                'default_model': 'llama3.2'},
    'openai':      {'base_url': 'https://api.openai.com/v1',            'default_model': 'gpt-4o'},
    'anthropic':   {'base_url': 'https://api.anthropic.com/v1',         'default_model': 'claude-3-5-sonnet-20241022'},
    'deepseek':    {'base_url': 'https://api.deepseek.com/v1',          'default_model': 'deepseek-chat'},
    'groq':        {'base_url': 'https://api.groq.com/openai/v1',       'default_model': 'llama-3.3-70b-versatile'},
    'together':    {'base_url': 'https://api.together.xyz/v1',          'default_model': 'meta-llama/Llama-3.3-70B-Instruct-Turbo'},
    'mistral':     {'base_url': 'https://api.mistral.ai/v1',            'default_model': 'mistral-large-latest'},
    'openrouter':  {'base_url': 'https://openrouter.ai/api/v1',         'default_model': 'openai/gpt-4o'},
    'lmstudio':    {'base_url': 'http://localhost:1234/v1',              'default_model': 'local-model'},
    'vllm':        {'base_url': 'http://localhost:8000/v1',              'default_model': 'default'},
}


def create_provider(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMProvider:
    """
    Factory function to create the right LLM provider.

    Priority:
        1. Explicit arguments
        2. config.py settings (LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
        3. Environment variables (LLM_PROVIDER, LLM_API_KEY, etc.)
        4. Default: Ollama (local, free, private)

    Examples:
        llm = create_provider()                          # Ollama (default)
        llm = create_provider("openai")                  # OpenAI with env key
        llm = create_provider("deepseek", api_key="sk-...")
        llm = create_provider("anthropic", model="claude-3-opus-20240229")
        llm = create_provider(base_url="http://myserver:8000/v1", model="custom")
    """
    # Resolve settings from config.py or env vars
    try:
        import config
        provider = provider or getattr(config, 'LLM_PROVIDER', None)
        api_key = api_key or getattr(config, 'LLM_API_KEY', None)
        base_url = base_url or getattr(config, 'LLM_BASE_URL', None)
        model = model or getattr(config, 'LLM_MODEL', None)
    except ImportError:
        pass

    provider = provider or os.environ.get('LLM_PROVIDER', 'ollama')
    api_key = api_key or os.environ.get('LLM_API_KEY', '')
    provider = provider.lower().strip()

    logger = logging.getLogger(f"LLM:{provider}")

    # Ollama (special — not OpenAI-compatible API format)
    if provider == 'ollama':
        return OllamaProvider(
            base_url=base_url or 'http://localhost:11434',
            model=model or 'llama3.2',
            logger=logger,
        )

    # Anthropic (special — different API format)
    if provider == 'anthropic':
        return AnthropicProvider(
            api_key=api_key or os.environ.get('ANTHROPIC_API_KEY', ''),
            model=model or 'claude-3-5-sonnet-20241022',
            logger=logger,
        )

    # OpenAI and all OpenAI-compatible providers
    known = KNOWN_PROVIDERS.get(provider, {})
    resolved_base = base_url or known.get('base_url', 'https://api.openai.com/v1')
    resolved_model = model or known.get('default_model', 'gpt-4o')

    # Provider-specific env var fallbacks
    if not api_key:
        env_map = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'groq': 'GROQ_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'mistral': 'MISTRAL_API_KEY',
            'openrouter': 'OPENROUTER_API_KEY',
        }
        env_var = env_map.get(provider, 'LLM_API_KEY')
        api_key = os.environ.get(env_var, '')

    return OpenAICompatibleProvider(
        api_key=api_key,
        base_url=resolved_base,
        model=resolved_model,
        logger=logger,
    )
