"""Manage the local Ollama runtime through its supported HTTP API."""
from __future__ import annotations

import json
from typing import Any

import requests

from seven import config


def _url(path: str) -> str:
    return config.OLLAMA_URL.rstrip("/") + path


def _request(method: str, path: str, *, timeout: int | None = None, **kwargs):
    try:
        response = requests.request(
            method,
            _url(path),
            timeout=timeout or config.LLM_TIMEOUT,
            **kwargs,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        raise RuntimeError(f"Ollama {method} {path} failed: {exc}") from exc


def ollama_status() -> str:
    try:
        version = _request("GET", "/api/version", timeout=8).json().get("version", "unknown")
        installed = _request("GET", "/api/tags", timeout=8).json().get("models", [])
        running = _request("GET", "/api/ps", timeout=8).json().get("models", [])
        return json.dumps({
            "ok": True,
            "url": config.OLLAMA_URL,
            "version": version,
            "installed_count": len(installed),
            "running": [m.get("name") or m.get("model") for m in running],
        }, indent=2)
    except (RuntimeError, ValueError) as exc:
        return f"ERROR: {exc}"


def ollama_list() -> str:
    try:
        models = _request("GET", "/api/tags", timeout=10).json().get("models", [])
        rows = []
        for model in models:
            rows.append({
                "name": model.get("name") or model.get("model"),
                "size": model.get("size"),
                "modified_at": model.get("modified_at"),
                "digest": model.get("digest"),
                "details": model.get("details") or {},
            })
        return json.dumps(rows, indent=2)
    except (RuntimeError, ValueError) as exc:
        return f"ERROR: {exc}"


def ollama_show(model: str) -> str:
    if not (model or "").strip():
        return "ERROR: model is required"
    try:
        payload = _request("POST", "/api/show", json={"model": model.strip()}, timeout=30).json()
        payload.pop("license", None)  # can be extremely large; model metadata remains
        payload.pop("modelfile", None)
        return json.dumps(payload, indent=2)[:50000]
    except (RuntimeError, ValueError) as exc:
        return f"ERROR: {exc}"


def ollama_pull(model: str) -> str:
    if not (model or "").strip():
        return "ERROR: model is required"
    try:
        response = _request(
            "POST", "/api/pull", json={"model": model.strip(), "stream": True},
            stream=True, timeout=config.OLLAMA_OPERATION_TIMEOUT,
        )
        last: dict[str, Any] = {}
        updates = 0
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            last = json.loads(line)
            updates += 1
            if last.get("error"):
                return f"ERROR: {last['error']}"
        return json.dumps({"ok": True, "model": model.strip(), "updates": updates, "final": last}, indent=2)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return f"ERROR: {exc}"


def ollama_copy(source: str, destination: str) -> str:
    if not (source or "").strip() or not (destination or "").strip():
        return "ERROR: source and destination are required"
    try:
        _request("POST", "/api/copy", json={"source": source.strip(), "destination": destination.strip()}, timeout=60)
        return f"OK copied {source.strip()} -> {destination.strip()}"
    except RuntimeError as exc:
        return f"ERROR: {exc}"


def ollama_delete(model: str) -> str:
    if not (model or "").strip():
        return "ERROR: model is required"
    try:
        _request("DELETE", "/api/delete", json={"model": model.strip()}, timeout=60)
        return f"OK deleted {model.strip()}"
    except RuntimeError as exc:
        return f"ERROR: {exc}"


def ollama_load(model: str, keep_alive: str = "5m") -> str:
    if not (model or "").strip():
        return "ERROR: model is required"
    try:
        _request(
            "POST", "/api/generate",
            json={"model": model.strip(), "prompt": "", "stream": False, "keep_alive": keep_alive or "5m"},
            timeout=config.OLLAMA_OPERATION_TIMEOUT,
        )
        return f"OK loaded {model.strip()} keep_alive={keep_alive or '5m'}"
    except RuntimeError as exc:
        return f"ERROR: {exc}"


def ollama_unload(model: str) -> str:
    if not (model or "").strip():
        return "ERROR: model is required"
    try:
        _request(
            "POST", "/api/generate",
            json={"model": model.strip(), "prompt": "", "stream": False, "keep_alive": 0}, timeout=60,
        )
        return f"OK unloaded {model.strip()}"
    except RuntimeError as exc:
        return f"ERROR: {exc}"


def register(reg):
    from seven.tools.registry import Tool

    definitions = [
        ("ollama_status", "Show local Ollama version, endpoint and running models.", {}, lambda: ollama_status()),
        ("ollama_list", "List installed local Ollama models and metadata.", {}, lambda: ollama_list()),
        ("ollama_show", "Show metadata for an installed Ollama model.", {"model": {"type": "string"}}, ollama_show),
        ("ollama_pull", "Download or update an Ollama model. This can use substantial bandwidth and disk space.", {"model": {"type": "string"}}, ollama_pull),
        ("ollama_copy", "Copy/tag an installed Ollama model.", {"source": {"type": "string"}, "destination": {"type": "string"}}, ollama_copy),
        ("ollama_delete", "Delete an installed Ollama model and reclaim its storage.", {"model": {"type": "string"}}, ollama_delete),
        ("ollama_load", "Load an Ollama model into memory.", {"model": {"type": "string"}, "keep_alive": {"type": "string"}}, ollama_load),
        ("ollama_unload", "Unload an Ollama model from memory.", {"model": {"type": "string"}}, ollama_unload),
    ]
    for name, description, properties, handler in definitions:
        reg.register(Tool(
            name=name,
            description=description,
            parameters={"type": "object", "properties": properties, "required": list(properties) if name not in {"ollama_load"} else ["model"]},
            handler=handler,
        ))
