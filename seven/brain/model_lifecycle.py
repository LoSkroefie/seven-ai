"""Discover, benchmark, activate, and roll back local language models."""
from __future__ import annotations

import json
import os
import platform
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from seven import config


class ModelLifecycle:
    """Persisted active/candidate/known-good state with benchmark gates."""

    def __init__(self, brain, state_path: Optional[Path] = None):
        self.brain = brain
        self.state_path = Path(
            state_path or getattr(config, "MODEL_STATE_PATH", config.DATA_DIR / "model_state.json")
        )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "active": self.brain.model,
            "candidate": None,
            "known_good": self.brain.model,
            "benchmarks": {},
            "updated_at": time.time(),
        }

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if not self.state_path.exists():
                return self._default_state()
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else self._default_state()
            except (OSError, ValueError, json.JSONDecodeError):
                return self._default_state()

    def _save(self, state: Dict[str, Any]) -> None:
        state = dict(state)
        state["updated_at"] = time.time()
        temp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp, self.state_path)

    def discover(self) -> Dict[str, Any]:
        url = self.brain.ollama_url.rstrip("/")
        tags = requests.get(f"{url}/api/tags", timeout=10)
        tags.raise_for_status()
        running = requests.get(f"{url}/api/ps", timeout=10)
        running.raise_for_status()
        models = tags.json().get("models") or []
        loaded = running.json().get("models") or []
        return {
            "ok": True,
            "host": platform.node(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "installed": [
                {
                    "name": model.get("name") or model.get("model"),
                    "size": model.get("size"),
                    "digest": model.get("digest"),
                    "details": model.get("details") or {},
                }
                for model in models
            ],
            "loaded": [
                {
                    "name": model.get("name") or model.get("model"),
                    "size": model.get("size"),
                    "size_vram": model.get("size_vram"),
                }
                for model in loaded
            ],
            "state": self.load(),
        }

    def benchmark(self, model: str) -> Dict[str, Any]:
        model = str(model or "").strip()
        if not model:
            raise ValueError("model is required")
        started = time.perf_counter()
        text = self.brain.chat(
            [{"role": "user", "content": "Return exactly SEVEN_MODEL_OK"}],
            model=model,
            temperature=0,
            max_tokens=32,
        )
        text_ok = "SEVEN_MODEL_OK" in str(text.get("content") or "")
        probe_tool = {
            "type": "function",
            "function": {
                "name": "seven_probe",
                "description": "Return a benchmark marker.",
                "parameters": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    "required": ["value"],
                },
            },
        }
        tool = self.brain.chat(
            [{"role": "user", "content": "Call seven_probe with value benchmark-ok."}],
            tools=[probe_tool],
            model=model,
            temperature=0,
            max_tokens=128,
        )
        calls = tool.get("tool_calls") or []
        tool_ok = any(
            call.get("name") == "seven_probe"
            and (call.get("arguments") or {}).get("value") == "benchmark-ok"
            for call in calls
        )
        elapsed = round(time.perf_counter() - started, 3)
        passed = bool(text_ok and tool_ok)
        result = {
            "ok": passed,
            "model": model,
            "text_ok": text_ok,
            "tool_ok": tool_ok,
            "thinking_preserved": "thinking" in text and "thinking" in tool,
            "elapsed_seconds": elapsed,
            "tested_at": time.time(),
        }
        state = self.load()
        state.setdefault("benchmarks", {})[model] = result
        state["candidate"] = model if passed else None
        self._save(state)
        return result

    def activate(self, model: str) -> Dict[str, Any]:
        model = str(model or "").strip()
        state = self.load()
        benchmark = (state.get("benchmarks") or {}).get(model) or {}
        if not benchmark.get("ok"):
            raise ValueError(f"model '{model}' has no passing benchmark")
        previous = state.get("active") or self.brain.model
        state["known_good"] = previous
        state["active"] = model
        state["candidate"] = None
        self._save(state)
        self.brain.model = model
        config.OLLAMA_MODEL = model
        return {"ok": True, "active": model, "known_good": previous}

    def rollback(self) -> Dict[str, Any]:
        state = self.load()
        target = state.get("known_good")
        if not target:
            raise ValueError("no known-good model is recorded")
        previous = state.get("active")
        state["active"] = target
        state["known_good"] = previous
        state["candidate"] = None
        self._save(state)
        self.brain.model = target
        config.OLLAMA_MODEL = target
        return {"ok": True, "active": target, "rolled_back_from": previous}
