"""
Streaming responses from Ollama for instant feedback
"""
import requests
import json
from typing import Optional, Callable, Iterator
import config

class StreamingOllamaClient:
    """Ollama client with streaming support"""
    
    def __init__(self, base_url: str = config.OLLAMA_URL, model: str = config.OLLAMA_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
    
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
            
            payload = {
                "model": self.model,
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
