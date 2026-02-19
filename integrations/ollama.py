"""
Ollama LLM integration with robust error handling
"""
import requests
import json
from typing import Optional, Dict, Any
import config

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = config.OLLAMA_URL, model: str = config.OLLAMA_MODEL):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: int = 30
    ) -> Optional[str]:
        """
        Generate a response from Ollama
        
        Args:
            prompt: User prompt
            system_message: System context/personality
            temperature: Creativity (0.0-1.0)
            max_tokens: Max response length
            timeout: Request timeout in seconds (use 10-15 for background sentience calls)
            
        Returns:
            Generated text or None on error
        """
        try:
            # Build full prompt with system message
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Make streaming request
            response = requests.post(
                self.generate_url,
                json=payload,
                stream=True,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Collect streamed response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        full_response += data.get("response", "")
                        
                        # Check if done
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            return full_response.strip()
            
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to Ollama at {self.base_url}")
            print("[INFO] Make sure Ollama is running: ollama serve")
            return None
        except requests.exceptions.Timeout:
            print("[TIMEOUT] Ollama request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ollama error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None
    
    def ask_with_context(
        self,
        user_input: str,
        conversation_context: str,
        system_message: str
    ) -> Optional[str]:
        """
        Ask Ollama with conversation context
        
        Args:
            user_input: Current user input
            conversation_context: Previous conversation turns
            system_message: Bot personality/instructions
            
        Returns:
            Response text or None
        """
        full_prompt = f"""Context from previous conversation:
{conversation_context}

Current user input: {user_input}

Respond naturally and helpfully based on the context."""
        
        return self.generate(full_prompt, system_message=system_message)
    
    def ask_for_decision(self, user_input: str, capabilities: str) -> Optional[str]:
        """
        Ask Ollama to decide what action to take
        
        Args:
            user_input: User request
            capabilities: List of bot capabilities
            
        Returns:
            Decision/action to take
        """
        prompt = f"""You are a voice assistant. Based on the user's request, decide what action to take.

User request: "{user_input}"

Your capabilities:
{capabilities}

Respond with a clear action to take. Be specific and actionable."""
        
        system = "You are a decision-making assistant. Provide clear, actionable responses."
        return self.generate(prompt, system_message=system, temperature=0.3)
    
    def refine_query(self, unresolved_query: str) -> Optional[str]:
        """
        Refine an unresolved query
        
        Args:
            unresolved_query: Query that needs clarification
            
        Returns:
            Refined/clarified query
        """
        prompt = f"Refine and clarify this query to make it more actionable: '{unresolved_query}'"
        return self.generate(prompt, temperature=0.5)
    
    def generate_name(self) -> Optional[str]:
        """Ask Ollama to generate a name for itself"""
        prompt = "Choose a unique, interesting name for yourself as a voice assistant. Respond with just the name, nothing else."
        response = self.generate(prompt, temperature=0.8, max_tokens=50)
        
        if response:
            # Extract just the first word/name
            words = response.strip().split()
            return words[0].strip('.,!?"\'') if words else None
        return None
    
    def generate_with_vision(
        self,
        prompt: str,
        image_base64: str,
        vision_model: str = "llama3.2-vision",
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Generate response with vision model
        
        Args:
            prompt: Text prompt describing what to analyze
            image_base64: Base64 encoded image
            vision_model: Vision-capable model name
            temperature: Creativity (0.0-1.0)
            
        Returns:
            Dict with 'response' key or None on error
        """
        try:
            payload = {
                "model": vision_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"[ERROR] Vision API error: {e}")
            return None
    
    def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "llama3.2-vision",
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Generate response from an image file using the vision model.
        
        Args:
            prompt: What to ask about the image
            image_path: Path to image file on disk
            model: Vision model name
            temperature: Creativity
            
        Returns:
            Response text or None
        """
        import base64
        try:
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 300
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('response', '').strip() or None
            
        except FileNotFoundError:
            print(f"[ERROR] Image not found: {image_path}")
            return None
        except Exception as e:
            print(f"[ERROR] Vision with image error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            print(f"[OK] Connected to Ollama at {self.base_url}")
            return True
        except Exception as e:
            print(f"[ERROR] Cannot connect to Ollama: {e}")
            print(f"[INFO] Make sure Ollama is running at {self.base_url}")
            return False
