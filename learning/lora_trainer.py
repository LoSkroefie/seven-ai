"""
Continual LoRA Fine-Tuning — Seven AI v3.2

Periodically fine-tunes Seven's language model on logged conversations,
emotional patterns, and memory data. Since Ollama doesn't natively support
LoRA hot-swap, this module implements a **prompt-replay distillation**
strategy:

1. Collects high-quality interaction pairs from memory/logs
2. Builds curated training sets (conversation, emotion, personality)
3. Attempts real LoRA fine-tuning via litgpt/peft if available
4. Falls back to "prompt replay" — injecting distilled examples into
   system prompts for behavioral adaptation without weight changes

Adapters stored in: data/lora_adapters/
Scheduler trigger: weekly or after N interactions (configurable)

100% local. No cloud. No data leaves the machine.
"""

import json
import logging
import os
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger("LoRATrainer")


class TrainingExample:
    """Single training example extracted from interaction history"""
    
    def __init__(self, prompt: str, response: str, quality: float = 0.5,
                 domain: str = "general", emotion: str = "", timestamp: str = ""):
        self.prompt = prompt
        self.response = response
        self.quality = quality  # 0.0 - 1.0 (sentiment/engagement proxy)
        self.domain = domain    # general, emotional, technical, creative
        self.emotion = emotion
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'prompt': self.prompt,
            'response': self.response,
            'quality': self.quality,
            'domain': self.domain,
            'emotion': self.emotion,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'TrainingExample':
        return cls(**d)


class LoRATrainer:
    """
    Continual learning engine for Seven AI.
    
    Extracts high-quality examples from interaction history and either:
    - Fine-tunes via LoRA (if litgpt/peft available)
    - Builds distilled prompt libraries for behavioral adaptation
    
    Thread-safe. Low CPU. Runs during idle/dream cycles.
    """
    
    def __init__(self, bot=None, data_dir: str = None):
        self.bot = bot
        self.data_dir = Path(data_dir) if data_dir else self._default_data_dir()
        self.adapter_dir = self.data_dir / "lora_adapters"
        self.training_dir = self.data_dir / "training_sets"
        
        # Create directories
        self.adapter_dir.mkdir(parents=True, exist_ok=True)
        self.training_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.training_examples: List[TrainingExample] = []
        self.last_train_time: Optional[datetime] = None
        self.total_examples_collected = 0
        self.total_training_runs = 0
        self.current_adapter: Optional[str] = None
        self.is_training = False
        
        # Capabilities
        self.lora_available = self._check_lora_support()
        self.distilled_prompts: Dict[str, List[str]] = {
            'personality': [],
            'emotional': [],
            'knowledge': [],
            'style': []
        }
        
        # Load existing state
        self._load_state()
        
        logger.info(
            f"[LORA] Initialized — LoRA={'available' if self.lora_available else 'fallback (prompt-replay)'}, "
            f"examples={self.total_examples_collected}, runs={self.total_training_runs}"
        )
    
    def _default_data_dir(self) -> Path:
        """Default data directory"""
        if os.name == 'nt':
            return Path(os.environ.get('USERPROFILE', '~')) / '.chatbot'
        return Path.home() / '.chatbot'
    
    def _check_lora_support(self) -> bool:
        """Check if real LoRA fine-tuning libraries are available"""
        try:
            import peft  # noqa: F401
            logger.info("[LORA] peft library found — real LoRA fine-tuning available")
            return True
        except ImportError:
            pass
        
        try:
            import litgpt  # noqa: F401
            logger.info("[LORA] litgpt library found — real LoRA fine-tuning available")
            return True
        except ImportError:
            pass
        
        logger.info("[LORA] No LoRA library — using prompt-replay distillation")
        return False
    
    # ==================== Example Collection ====================
    
    def collect_from_conversation(self, user_msg: str, bot_response: str,
                                  emotion: str = "", sentiment: float = 0.5):
        """
        Collect a training example from a live conversation.
        Called after each interaction by enhanced_bot.
        
        Args:
            user_msg: What the user said
            bot_response: Seven's response
            emotion: Current emotion during response
            sentiment: Estimated quality (0=bad, 1=excellent)
        """
        if not user_msg or not bot_response:
            return
        
        # Skip very short or error responses
        if len(bot_response) < 20 or 'error' in bot_response.lower()[:30]:
            return
        
        # Determine domain
        domain = self._classify_domain(user_msg, bot_response)
        
        example = TrainingExample(
            prompt=user_msg[:1024],
            response=bot_response[:2048],
            quality=max(0.0, min(1.0, sentiment)),
            domain=domain,
            emotion=emotion
        )
        
        self.training_examples.append(example)
        self.total_examples_collected += 1
        
        # Auto-flush to disk every 50 examples
        if len(self.training_examples) >= 50:
            self._flush_examples()
    
    def collect_from_memory(self):
        """Extract training examples from stored memories"""
        if not self.bot:
            return 0
        
        count = 0
        try:
            memory = getattr(self.bot, 'memory', None)
            if not memory:
                return 0
            
            # Get recent conversations
            convos = []
            if hasattr(memory, 'get_recent_conversations'):
                convos = memory.get_recent_conversations(limit=200)
            
            for convo in convos:
                if not isinstance(convo, dict):
                    continue
                
                user_msg = convo.get('user_input', convo.get('input', ''))
                bot_resp = convo.get('bot_response', convo.get('response', ''))
                
                if user_msg and bot_resp and len(bot_resp) > 20:
                    example = TrainingExample(
                        prompt=user_msg[:1024],
                        response=bot_resp[:2048],
                        quality=0.6,  # Memory = decent quality
                        domain=self._classify_domain(user_msg, bot_resp),
                        timestamp=convo.get('timestamp', '')
                    )
                    self.training_examples.append(example)
                    count += 1
            
            logger.info(f"[LORA] Collected {count} examples from memory")
        except Exception as e:
            logger.error(f"[LORA] Memory collection error: {e}")
        
        return count
    
    def _classify_domain(self, prompt: str, response: str) -> str:
        """Simple domain classifier for training examples"""
        text = (prompt + " " + response).lower()
        
        emotional_words = {'feel', 'emotion', 'happy', 'sad', 'angry', 'love', 'hate', 'mood'}
        technical_words = {'code', 'python', 'function', 'error', 'file', 'install', 'server'}
        creative_words = {'write', 'story', 'poem', 'create', 'imagine', 'art', 'music'}
        
        tokens = set(text.split())
        
        if len(tokens & emotional_words) >= 2:
            return 'emotional'
        if len(tokens & technical_words) >= 2:
            return 'technical'
        if len(tokens & creative_words) >= 2:
            return 'creative'
        return 'general'
    
    # ==================== Training ====================
    
    def train(self, force: bool = False) -> Dict[str, Any]:
        """
        Run a training cycle. 
        
        - If LoRA available: attempts real fine-tuning
        - Otherwise: builds distilled prompt library
        
        Returns training report.
        """
        if self.is_training:
            return {'status': 'already_training'}
        
        self.is_training = True
        start = time.time()
        report = {
            'status': 'started',
            'method': 'lora' if self.lora_available else 'prompt_replay',
            'examples_used': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Collect from memory if we don't have enough examples
            if len(self.training_examples) < 20:
                self.collect_from_memory()
            
            # Load previously flushed examples
            self._load_flushed_examples()
            
            # Filter to high-quality examples
            quality_threshold = 0.4
            good_examples = [e for e in self.training_examples if e.quality >= quality_threshold]
            
            if len(good_examples) < 10:
                report['status'] = 'insufficient_data'
                report['examples_available'] = len(good_examples)
                return report
            
            report['examples_used'] = len(good_examples)
            
            if self.lora_available and not force:
                # Real LoRA fine-tuning
                report.update(self._train_lora(good_examples))
            else:
                # Prompt-replay distillation
                report.update(self._train_prompt_replay(good_examples))
            
            self.last_train_time = datetime.now()
            self.total_training_runs += 1
            report['status'] = 'completed'
            report['duration_seconds'] = round(time.time() - start, 2)
            
            # Save state
            self._save_state()
            
            logger.info(
                f"[LORA] Training complete — method={report['method']}, "
                f"examples={report['examples_used']}, "
                f"duration={report['duration_seconds']}s"
            )
            
        except Exception as e:
            report['status'] = 'error'
            report['error'] = str(e)
            logger.error(f"[LORA] Training error: {e}")
        finally:
            self.is_training = False
        
        return report
    
    def _train_lora(self, examples: List[TrainingExample]) -> dict:
        """Attempt real LoRA fine-tuning via peft/litgpt"""
        result = {'method': 'lora'}
        
        try:
            # Build training data in Alpaca format
            train_data = []
            for ex in examples:
                train_data.append({
                    'instruction': ex.prompt,
                    'output': ex.response,
                    'input': ''
                })
            
            # Save training set
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            train_file = self.training_dir / f"train_{ts}.json"
            with open(train_file, 'w', encoding='utf-8') as f:
                json.dump(train_data, f, indent=2, ensure_ascii=False)
            
            result['training_file'] = str(train_file)
            result['examples_saved'] = len(train_data)
            
            # NOTE: Real LoRA fine-tuning requires model weights access.
            # Ollama models are stored in blobs; direct LoRA requires
            # exporting weights first. For now, save the dataset and
            # fall back to prompt replay for behavioral adaptation.
            # Full LoRA pipeline can be enabled when Ollama supports
            # adapter loading or when using raw model weights.
            
            logger.info(f"[LORA] Training set saved: {train_file} ({len(train_data)} examples)")
            
            # Fall through to prompt replay for immediate effect
            result.update(self._train_prompt_replay(examples))
            result['method'] = 'lora_prepared_with_prompt_replay'
            
        except Exception as e:
            result['lora_error'] = str(e)
            result.update(self._train_prompt_replay(examples))
        
        return result
    
    def _train_prompt_replay(self, examples: List[TrainingExample]) -> dict:
        """
        Prompt-replay distillation: extract behavioral patterns from
        high-quality examples and build distilled prompt injections.
        
        This gives Seven behavioral adaptation without changing weights.
        """
        result = {'method': 'prompt_replay'}
        
        # Group by domain
        by_domain = {}
        for ex in examples:
            by_domain.setdefault(ex.domain, []).append(ex)
        
        # Extract top examples per domain (sorted by quality)
        distilled = {}
        for domain, exs in by_domain.items():
            sorted_exs = sorted(exs, key=lambda e: e.quality, reverse=True)
            top = sorted_exs[:15]  # Keep top 15 per domain
            
            # Build distilled prompt snippets
            snippets = []
            for ex in top:
                snippet = f"User: {ex.prompt[:200]}\nSeven: {ex.response[:300]}"
                snippets.append(snippet)
            
            distilled[domain] = snippets
        
        self.distilled_prompts = {
            'personality': distilled.get('general', [])[:5],
            'emotional': distilled.get('emotional', [])[:5],
            'knowledge': distilled.get('technical', [])[:5],
            'style': distilled.get('creative', [])[:5]
        }
        
        # Save distilled prompts
        distilled_file = self.adapter_dir / "distilled_prompts.json"
        with open(distilled_file, 'w', encoding='utf-8') as f:
            json.dump(self.distilled_prompts, f, indent=2, ensure_ascii=False)
        
        total_snippets = sum(len(v) for v in self.distilled_prompts.values())
        result['distilled_snippets'] = total_snippets
        result['domains'] = list(by_domain.keys())
        
        logger.info(f"[LORA] Distilled {total_snippets} prompt snippets across {len(by_domain)} domains")
        
        return result
    
    # ==================== Adapter Loading ====================
    
    def get_system_prompt_injection(self, domain: str = "general") -> str:
        """
        Get distilled prompt injection for a given domain.
        This is injected into the system prompt to adapt behavior.
        
        Called by ollama.py before generating responses.
        """
        if not self.distilled_prompts:
            self._load_distilled_prompts()
        
        # Map domain to prompt category
        category_map = {
            'general': 'personality',
            'emotional': 'emotional',
            'technical': 'knowledge',
            'creative': 'style'
        }
        
        category = category_map.get(domain, 'personality')
        snippets = self.distilled_prompts.get(category, [])
        
        if not snippets:
            return ""
        
        # Build injection (keep it concise — max 3 examples)
        injection = "\n\n[Behavioral examples from past interactions — match this style:]\n"
        for snippet in snippets[:3]:
            injection += f"\n{snippet}\n"
        
        return injection
    
    def _load_distilled_prompts(self):
        """Load distilled prompts from disk"""
        distilled_file = self.adapter_dir / "distilled_prompts.json"
        if distilled_file.exists():
            try:
                with open(distilled_file, 'r', encoding='utf-8') as f:
                    self.distilled_prompts = json.load(f)
            except Exception:
                pass
    
    # ==================== Persistence ====================
    
    def _flush_examples(self):
        """Flush collected examples to disk"""
        if not self.training_examples:
            return
        
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_file = self.training_dir / f"batch_{ts}.json"
        
        try:
            data = [e.to_dict() for e in self.training_examples]
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            
            self.training_examples.clear()
            logger.debug(f"[LORA] Flushed {len(data)} examples to {batch_file}")
        except Exception as e:
            logger.error(f"[LORA] Flush error: {e}")
    
    def _load_flushed_examples(self):
        """Load all previously flushed example batches"""
        try:
            for batch_file in sorted(self.training_dir.glob("batch_*.json")):
                with open(batch_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for d in data:
                    self.training_examples.append(TrainingExample.from_dict(d))
        except Exception as e:
            logger.error(f"[LORA] Load flushed error: {e}")
    
    def _save_state(self):
        """Save trainer state"""
        state = {
            'last_train_time': self.last_train_time.isoformat() if self.last_train_time else None,
            'total_examples_collected': self.total_examples_collected,
            'total_training_runs': self.total_training_runs,
            'current_adapter': self.current_adapter,
            'lora_available': self.lora_available
        }
        
        state_file = self.adapter_dir / "trainer_state.json"
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"[LORA] State save error: {e}")
    
    def _load_state(self):
        """Load trainer state from disk"""
        state_file = self.adapter_dir / "trainer_state.json"
        if not state_file.exists():
            return
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            if state.get('last_train_time'):
                self.last_train_time = datetime.fromisoformat(state['last_train_time'])
            self.total_examples_collected = state.get('total_examples_collected', 0)
            self.total_training_runs = state.get('total_training_runs', 0)
            self.current_adapter = state.get('current_adapter')
        except Exception as e:
            logger.error(f"[LORA] State load error: {e}")
    
    # ==================== Status ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get trainer status for GUI/API"""
        return {
            'available': True,
            'method': 'lora' if self.lora_available else 'prompt_replay',
            'is_training': self.is_training,
            'total_examples': self.total_examples_collected,
            'pending_examples': len(self.training_examples),
            'total_runs': self.total_training_runs,
            'last_trained': self.last_train_time.isoformat() if self.last_train_time else None,
            'current_adapter': self.current_adapter,
            'distilled_snippets': sum(len(v) for v in self.distilled_prompts.values()),
            'domains': list(self.distilled_prompts.keys())
        }
    
    def should_train(self, interaction_threshold: int = 100,
                     time_threshold_hours: int = 168) -> bool:
        """Check if training should be triggered"""
        # Enough new examples?
        if self.total_examples_collected > 0 and len(self.training_examples) >= interaction_threshold:
            return True
        
        # Enough time passed since last training?
        if self.last_train_time:
            elapsed = datetime.now() - self.last_train_time
            if elapsed > timedelta(hours=time_threshold_hours):
                return True
        elif self.total_examples_collected >= 20:
            # Never trained but have some data
            return True
        
        return False
