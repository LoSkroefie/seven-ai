"""
Streaming responses from Ollama for instant feedback
"""
import requests
import json
import time
from typing import Optional, Callable, Iterator
import config

class StreamingOllamaClient:
    """Ollama client with streaming support"""

    FALLBACK_ORDER = [
        'gemma:2b-instruct', 'gemma:2b', 'phi3:mini', 'tinyllama',
        'llama3.2:1b', 'llama3.2', 'mistral', 'llama3.1',
    ]
    
    def __init__(self, base_url: str = config.OLLAMA_URL, model: str = config.OLLAMA_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._primary_model = model
        self._active_model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self._fallback_chain = []
        self._oom_since = None
        self._primary_retry_interval = 300

    def _build_fallback_chain(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            available_full = {m['name'] for m in resp.json().get('models', [])}
            available_base = {n.split(':')[0] for n in available_full}
            chain = []
            for c in self.FALLBACK_ORDER:
                if c == self._primary_model:
                    continue
                if c in available_full or c + ':latest' in available_full or c in available_base:
                    chain.append(c)
            self._fallback_chain = chain
        except Exception:
            self._fallback_chain = []

    def _is_oom_error(self, error) -> bool:
        try:
            body = error.response.text if hasattr(error, 'response') and error.response else ''
            return 'requires more system memory' in body.lower() or 'not enough memory' in body.lower()
        except Exception:
            return False
    
    def generate_stream(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        on_token: Optional[Callable[[str], None]] = None
    ) -> Iterator[str]:
        """
        Generate response with streaming
        
        Args:
            prompt: User prompt
            system_message: System context
            temperature: Creativity
            on_token: Callback for each token (for TTS streaming)
            
        Yields:
            Each token as it's generated
        """
        try:
            # Build prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"
            
            # Periodically retry primary model if on fallback
            if (self._active_model != self._primary_model and
                    self._oom_since and
                    time.time() - self._oom_since >= self._primary_retry_interval):
                self._active_model = self._primary_model
                self._oom_since = None

            payload = {
                "model": self._active_model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": 500
                }
            }
            
            # Stream request
            response = requests.post(
                self.generate_url,
                json=payload,
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            # Process stream
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        
                        if token:
                            # Call callback if provided
                            if on_token:
                                on_token(token)
                            
                            # Yield token
                            yield token
                        
                        # Check if done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except requests.exceptions.RequestException as e:
            if self._is_oom_error(e):
                if not self._fallback_chain:
                    self._build_fallback_chain()
                for fallback in self._fallback_chain:
                    try:
                        payload['model'] = fallback
                        print(f"[OOM] Streaming fallback: {fallback}")
                        r = requests.post(self.generate_url, json=payload, stream=True, timeout=60)
                        r.raise_for_status()
                        self._active_model = fallback
                        self._oom_since = self._oom_since or time.time()
                        for line in r.iter_lines():
                            if line:
                                try:
                                    d = json.loads(line)
                                    token = d.get('response', '')
                                    if token:
                                        if on_token:
                                            on_token(token)
                                        yield token
                                    if d.get('done'):
                                        return
                                except json.JSONDecodeError:
                                    continue
                    except requests.exceptions.RequestException:
                        continue
            print(f"[ERROR] Streaming error: {e}")
            yield ""
    
    def generate_with_callback(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        on_token: Optional[Callable[[str], None]] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate full response while calling callback for each token
        
        Returns:
            Complete response
        """
        full_response = ""
        
        for token in self.generate_stream(prompt, system_message, temperature, on_token):
            full_response += token
        
        return full_response.strip()
