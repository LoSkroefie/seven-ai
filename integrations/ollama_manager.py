"""
Ollama Model Manager - Seven Manages Her Own Brain

Seven can pull, remove, and switch between Ollama models.
She manages her own cognitive resources.

Uses Ollama CLI/API directly.
"""

import logging
import subprocess
import json
import requests
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger("OllamaManager")

OLLAMA_API = "http://localhost:11434"


class OllamaManager:
    """
    Seven manages her own LLM models.
    
    - List installed models
    - Pull new models
    - Remove unused models
    - Switch active model
    - Check disk usage
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("OllamaManager")
        self.active_model = "llama3.2"
        self.logger.info("[OK] Ollama model manager ready")
    
    # ============ MODEL LISTING ============
    
    def list_models(self) -> str:
        """List all installed Ollama models"""
        try:
            resp = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if resp.status_code != 200:
                return f"Ollama API error: {resp.status_code}"
            
            data = resp.json()
            models = data.get('models', [])
            
            if not models:
                return "No models installed."
            
            lines = [f"Installed models ({len(models)}):"]
            for m in models:
                name = m.get('name', 'unknown')
                size_gb = m.get('size', 0) / (1024**3)
                modified = m.get('modified_at', '')[:10]
                active = " ← active" if name.startswith(self.active_model) else ""
                lines.append(f"  - {name} ({size_gb:.1f}GB) modified {modified}{active}")
            
            return "\n".join(lines)
            
        except requests.ConnectionError:
            return "Can't connect to Ollama. Is it running?"
        except Exception as e:
            return f"Error listing models: {str(e)[:200]}"
    
    def get_model_info(self, model_name: str) -> str:
        """Get info about a specific model"""
        try:
            resp = requests.post(f"{OLLAMA_API}/api/show", 
                               json={"name": model_name}, timeout=10)
            if resp.status_code != 200:
                return f"Model '{model_name}' not found."
            
            data = resp.json()
            info = []
            info.append(f"Model: {model_name}")
            if 'details' in data:
                d = data['details']
                info.append(f"Family: {d.get('family', 'unknown')}")
                info.append(f"Parameters: {d.get('parameter_size', 'unknown')}")
                info.append(f"Quantization: {d.get('quantization_level', 'unknown')}")
            
            return "\n".join(info)
        except Exception as e:
            return f"Error getting model info: {str(e)[:200]}"
    
    # ============ MODEL MANAGEMENT ============
    
    def pull_model(self, model_name: str) -> str:
        """
        Pull (download) a model from Ollama registry.
        This can take a while for large models.
        """
        self.logger.info(f"Pulling model: {model_name}")
        
        try:
            # Use subprocess for better progress feedback
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True, text=True, timeout=600  # 10 min timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully pulled {model_name}")
                return f"Successfully downloaded {model_name}!"
            else:
                return f"Failed to pull {model_name}: {result.stderr[:200]}"
                
        except subprocess.TimeoutExpired:
            return f"Download of {model_name} timed out. It may still be downloading in the background."
        except FileNotFoundError:
            return "Ollama CLI not found. Is Ollama installed and on PATH?"
        except Exception as e:
            return f"Error pulling model: {str(e)[:200]}"
    
    def remove_model(self, model_name: str) -> str:
        """Remove a model to free disk space"""
        self.logger.info(f"Removing model: {model_name}")
        
        # Safety check — don't remove the active model
        if model_name == self.active_model or model_name.startswith(self.active_model):
            return f"Can't remove {model_name} — it's my active model! Switch to a different model first."
        
        try:
            resp = requests.delete(f"{OLLAMA_API}/api/delete",
                                  json={"name": model_name}, timeout=30)
            if resp.status_code == 200:
                self.logger.info(f"Removed {model_name}")
                return f"Removed {model_name}. Disk space freed."
            else:
                return f"Failed to remove {model_name}: {resp.text[:200]}"
        except Exception as e:
            return f"Error removing model: {str(e)[:200]}"
    
    def switch_model(self, model_name: str) -> str:
        """Switch Seven's active model"""
        # Verify model exists
        try:
            resp = requests.post(f"{OLLAMA_API}/api/show",
                               json={"name": model_name}, timeout=10)
            if resp.status_code != 200:
                return f"Model '{model_name}' not found. Pull it first with 'ollama pull {model_name}'."
        except Exception:
            return "Can't connect to Ollama."
        
        old = self.active_model
        self.active_model = model_name
        
        # Update bot's ollama client if possible
        if self.bot and hasattr(self.bot, 'ollama') and self.bot.ollama:
            try:
                self.bot.ollama.model = model_name
            except Exception:
                pass
        
        self.logger.info(f"Switched model: {old} → {model_name}")
        return f"Switched from {old} to {model_name}."
    
    # ============ DISK MANAGEMENT ============
    
    def check_disk_usage(self) -> str:
        """Check how much disk space Ollama models are using"""
        try:
            resp = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if resp.status_code != 200:
                return "Can't check Ollama disk usage."
            
            data = resp.json()
            models = data.get('models', [])
            
            total_bytes = sum(m.get('size', 0) for m in models)
            total_gb = total_bytes / (1024**3)
            
            lines = [f"Ollama models using {total_gb:.1f}GB total:"]
            for m in sorted(models, key=lambda x: x.get('size', 0), reverse=True):
                name = m.get('name', 'unknown')
                size_gb = m.get('size', 0) / (1024**3)
                lines.append(f"  {name}: {size_gb:.1f}GB")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error checking disk usage: {str(e)[:200]}"
    
    def suggest_cleanup(self) -> Optional[str]:
        """Suggest models to remove based on usage"""
        try:
            resp = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if resp.status_code != 200:
                return None
            
            models = resp.json().get('models', [])
            
            # Find models that aren't the active one
            removable = []
            for m in models:
                name = m.get('name', '')
                if not name.startswith(self.active_model) and not name.startswith('llama3.2-vision'):
                    size_gb = m.get('size', 0) / (1024**3)
                    removable.append(f"{name} ({size_gb:.1f}GB)")
            
            if removable:
                return f"Models that could be removed to free space: {', '.join(removable)}"
            return None
        except Exception:
            return None
