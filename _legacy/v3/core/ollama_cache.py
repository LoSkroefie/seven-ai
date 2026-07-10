"""
Ollama Response Cache — Reduce latency for repeated/similar prompts

LRU cache with TTL for Ollama responses. Especially useful on CPU-only
servers where inference takes 30-60+ seconds.

Features:
    - LRU eviction (configurable max size)
    - TTL expiry (stale responses auto-removed)
    - Hash-based key (prompt + system + temperature + max_tokens)
    - Cache hit/miss stats
    - Thread-safe
"""

import hashlib
import json
import time
import threading
import logging
from typing import Optional, Dict, Any
from collections import OrderedDict

logger = logging.getLogger("OllamaCache")


class OllamaCache:
    """
    Thread-safe LRU cache with TTL for Ollama responses.
    
    Wraps the existing OllamaClient to transparently cache responses.
    Identical prompts (same params) return cached results instantly.
    """
    
    def __init__(self, ollama_client, max_size: int = 500, ttl: int = 3600):
        """
        Args:
            ollama_client: Existing OllamaClient instance to wrap
            max_size: Max cached responses (LRU eviction)
            ttl: Cache TTL in seconds (default 1 hour)
        """
        self.client = ollama_client
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._lock = threading.Lock()
        
        # Stats
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.info(f"[CACHE] Initialized: max_size={max_size}, ttl={ttl}s")
    
    def _make_key(self, prompt: str, system_message: str = "",
                  temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Create a deterministic cache key from request parameters"""
        key_data = f"{prompt}|{system_message}|{temperature}|{max_tokens}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if a cache entry has expired"""
        return (time.time() - entry['timestamp']) > self.ttl
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache exceeds max size"""
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
            self.evictions += 1
    
    def _cleanup_expired(self):
        """Remove expired entries (called periodically)"""
        now = time.time()
        expired = [k for k, v in self._cache.items() if (now - v['timestamp']) > self.ttl]
        for k in expired:
            del self._cache[k]
    
    def generate(self, prompt: str, system_message: str = "",
                 temperature: float = 0.7, max_tokens: int = 500,
                 bypass_cache: bool = False, **kwargs) -> Optional[str]:
        """
        Generate response with caching.
        
        Transparent drop-in for OllamaClient.generate().
        Cache is bypassed for high-temperature requests (>0.9)
        and when bypass_cache=True.
        """
        # Don't cache high-temperature (creative) requests
        if temperature > 0.9 or bypass_cache:
            return self.client.generate(
                prompt=prompt, system_message=system_message,
                temperature=temperature, max_tokens=max_tokens, **kwargs
            )
        
        key = self._make_key(prompt, system_message, temperature, max_tokens)
        
        # Check cache
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry):
                    # Cache hit — move to end (LRU)
                    self._cache.move_to_end(key)
                    self.hits += 1
                    logger.debug(f"[CACHE] HIT (key={key[:8]})")
                    return entry['response']
                else:
                    # Expired — remove
                    del self._cache[key]
        
        # Cache miss — call Ollama
        self.misses += 1
        logger.debug(f"[CACHE] MISS (key={key[:8]})")
        
        response = self.client.generate(
            prompt=prompt, system_message=system_message,
            temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        
        # Store in cache
        if response:
            with self._lock:
                self._cache[key] = {
                    'response': response,
                    'timestamp': time.time(),
                    'prompt_preview': prompt[:50]
                }
                self._evict_if_needed()
                
                # Periodic cleanup (every 100 misses)
                if self.misses % 100 == 0:
                    self._cleanup_expired()
        
        return response
    
    def test_connection(self) -> bool:
        """Proxy to underlying client"""
        return self.client.test_connection()
    
    def invalidate(self, prompt: str = None, system_message: str = ""):
        """Invalidate a specific cache entry or all entries"""
        with self._lock:
            if prompt:
                key = self._make_key(prompt, system_message)
                self._cache.pop(key, None)
            else:
                self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self._cache),
            'max_size': self.max_size,
            'evictions': self.evictions,
            'ttl': self.ttl
        }
    
    def __getattr__(self, name):
        """Proxy all other attributes to the underlying client"""
        return getattr(self.client, name)
