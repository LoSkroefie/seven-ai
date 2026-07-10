"""Model selection for Seven — pick best available local model for agents/tools."""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import requests

from seven import config

logger = logging.getLogger("seven.models")

# Preference order for companion + tool calling on ~8GB VRAM
PREFERRED_MODELS = [
    "qwen2.5:7b",
    "qwen2.5:7b-instruct",
    "qwen2.5-coder:7b",
    "qwen3:8b",
    "llama3.1:8b",
    "mistral:7b",
    "artifish/llama3.2-uncensored",
    "llama3.2",
    "llama3.2:latest",
    "neural-chat",
]


def list_local_models(ollama_url: Optional[str] = None) -> List[str]:
    url = (ollama_url or config.OLLAMA_URL).rstrip("/")
    try:
        r = requests.get(f"{url}/api/tags", timeout=8)
        r.raise_for_status()
        return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception as e:
        logger.warning("list models failed: %s", e)
        return []


def _match(preferred: str, available: List[str]) -> Optional[str]:
    pref_base = preferred.split(":")[0]
    # exact
    for a in available:
        if a == preferred or a == preferred + ":latest":
            return a
    # base match
    for a in available:
        if a.split(":")[0] == pref_base or preferred in a:
            return a
    return None


def pick_best_model(
    ollama_url: Optional[str] = None,
    configured: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Returns (model_name, reason).
    Honors configured if present locally; else first preferred available.
    """
    available = list_local_models(ollama_url)
    cfg = configured or config.OLLAMA_MODEL
    if cfg:
        hit = _match(cfg, available)
        if hit:
            return hit, f"configured and available: {hit}"
    for pref in PREFERRED_MODELS:
        hit = _match(pref, available)
        if hit:
            return hit, f"best available preferred: {hit}"
    if available:
        return available[0], f"fallback first installed: {available[0]}"
    return cfg or "llama3.2", "none installed — default name (pull required)"


def apply_best_model_to_config() -> str:
    model, reason = pick_best_model()
    config.OLLAMA_MODEL = model
    logger.info("Model selected: %s (%s)", model, reason)
    return f"{model} ({reason})"
