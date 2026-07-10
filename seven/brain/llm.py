"""
Brain — multi-provider LLM client with tool-calling.
Primary path: local Ollama. Optional: OpenAI, Anthropic, OpenAI-compatible.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from seven import config

logger = logging.getLogger("seven.brain")


class BrainError(Exception):
    pass


class Brain:
    """Unified chat + tools interface."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        vision_model: Optional[str] = None,
    ):
        self.provider = (provider or config.LLM_PROVIDER).lower()
        self.model = model or config.OLLAMA_MODEL
        self.vision_model = vision_model or config.OLLAMA_VISION_MODEL
        self.ollama_url = config.OLLAMA_URL.rstrip("/")
        self._session = requests.Session()

    # ── public API ─────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
          {
            "role": "assistant",
            "content": str | None,
            "tool_calls": [ {id, name, arguments: dict} ] | [],
            "raw": ...
          }
        """
        temperature = config.LLM_TEMPERATURE if temperature is None else temperature
        max_tokens = config.LLM_MAX_TOKENS if max_tokens is None else max_tokens
        model = model or self.model

        if self.provider == "ollama":
            return self._ollama_chat(messages, tools, temperature, max_tokens, model)
        if self.provider == "openai":
            return self._openai_chat(
                messages, tools, temperature, max_tokens, model or config.OPENAI_MODEL,
                config.OPENAI_BASE_URL, config.OPENAI_API_KEY,
            )
        if self.provider == "anthropic":
            return self._anthropic_chat(messages, tools, temperature, max_tokens)
        if self.provider in ("openai_compatible", "compat"):
            return self._openai_chat(
                messages, tools, temperature, max_tokens,
                model or config.COMPAT_MODEL,
                config.COMPAT_BASE_URL, config.COMPAT_API_KEY,
            )
        raise BrainError(f"Unknown provider: {self.provider}")

    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = self.chat(messages, tools=None, **kwargs)
        return (result.get("content") or "").strip()

    def vision(self, prompt: str, image_b64: str, system: Optional[str] = None) -> str:
        """
        Analyze an image (base64). Uses vision model on Ollama.
        On 8GB VRAM this may unload the text model — expected. keep_alive is short
        so VRAM frees after the call for the text model to return.
        """
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"},
        ]
        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_b64],
        })
        if self.provider == "ollama":
            # Short keep_alive so vision doesn't hog 8GB after analysis
            keep = getattr(config, "VISION_KEEP_ALIVE", "2m")
            payload_model = self.vision_model
            try:
                result = self._ollama_chat(
                    messages, None, 0.2, 1024, payload_model, keep_alive=keep
                )
                return (result.get("content") or "").strip()
            except BrainError as e:
                # Fallback: /api/generate with images (older Ollama)
                logger.warning("Vision chat failed (%s); trying generate API", e)
                return self._ollama_vision_generate(prompt, image_b64, system, keep)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        return (self.chat(messages, model=config.OPENAI_MODEL).get("content") or "").strip()

    def _ollama_vision_generate(
        self, prompt: str, image_b64: str, system: Optional[str], keep_alive: str
    ) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "model": self.vision_model,
            "prompt": full_prompt,
            "images": [image_b64],
            "stream": False,
            "keep_alive": keep_alive,
            "options": {"temperature": 0.2, "num_predict": 1024},
        }
        r = self._session.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=config.LLM_TIMEOUT,
        )
        if r.status_code >= 400:
            raise BrainError(f"Ollama vision generate HTTP {r.status_code}: {r.text[:400]}")
        return (r.json().get("response") or "").strip()

    def ping(self) -> Dict[str, Any]:
        """Health check for configured provider. Includes VRAM-resident model info."""
        if self.provider == "ollama":
            try:
                r = self._session.get(f"{self.ollama_url}/api/tags", timeout=5)
                r.raise_for_status()
                models = [m.get("name") for m in r.json().get("models", [])]
                loaded = self.ollama_ps()
                swapping = any(
                    "stopp" in str(m.get("status", "")).lower()
                    or "load" in str(m.get("status", "")).lower()
                    for m in loaded
                )
                # api/ps often has no status field — detect multi-model thrash by size
                loaded_names = [m.get("name") or m.get("model") for m in loaded if m]
                hint = None
                if swapping:
                    hint = (
                        "Ollama may be mid load/unload (VRAM swap). "
                        "Wait or restart Ollama if chat hangs. Check: ollama ps"
                    )
                elif loaded_names and not any(
                    self.model.split(":")[0] in (n or "") for n in loaded_names
                ):
                    hint = (
                        f"Primary model '{self.model}' not in VRAM; loaded={loaded_names}. "
                        f"First request may take 30–60s on 8GB cards."
                    )
                return {
                    "ok": True,
                    "provider": "ollama",
                    "url": self.ollama_url,
                    "model": self.model,
                    "models": models,
                    "has_primary": any(self.model in (m or "") for m in models),
                    "has_vision": any(self.vision_model.split(":")[0] in (m or "") for m in models),
                    "loaded": loaded_names,
                    "loaded_detail": loaded,
                    "hint": hint,
                }
            except Exception as e:
                return {
                    "ok": False,
                    "provider": "ollama",
                    "url": self.ollama_url,
                    "model": self.model,
                    "error": str(e),
                    "hint": "Is Ollama running? ollama serve  |  check ollama ps if hung on Stopping…",
                }
        return {"ok": True, "provider": self.provider, "model": self.model}

    def ollama_ps(self) -> List[Dict[str, Any]]:
        """Models currently in memory (VRAM/RAM)."""
        try:
            r = self._session.get(f"{self.ollama_url}/api/ps", timeout=5)
            r.raise_for_status()
            return list(r.json().get("models") or [])
        except Exception:
            return []

    def list_ollama_models(self) -> List[str]:
        try:
            r = self._session.get(f"{self.ollama_url}/api/tags", timeout=5)
            r.raise_for_status()
            return [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            return []

    def _ollama_loaded_model(self) -> Optional[str]:
        """Return name of a model currently resident in VRAM, if any."""
        try:
            r = self._session.get(f"{self.ollama_url}/api/ps", timeout=5)
            r.raise_for_status()
            models = r.json().get("models") or []
            if not models:
                return None
            # Prefer non-stopping runners
            for m in models:
                name = m.get("name") or m.get("model")
                if name:
                    return name
            return None
        except Exception:
            return None

    # ── Ollama ─────────────────────────────────────────────────────────

    def _ollama_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        model: str,
        keep_alive: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._normalize_messages_for_ollama(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if tools:
            payload["tools"] = tools

        url = f"{self.ollama_url}/api/chat"
        # Default keep_alive warms text model; vision passes short keep_alive
        payload["keep_alive"] = keep_alive if keep_alive is not None else "30m"
        try:
            r = self._session.post(url, json=payload, timeout=config.LLM_TIMEOUT)
            if r.status_code >= 400:
                # Retry without tools if model rejects tool schema
                if tools and r.status_code in (400, 404, 500):
                    logger.warning("Ollama tools rejected (%s); retrying tool-free + text protocol", r.status_code)
                    return self._ollama_text_tool_fallback(messages, tools, temperature, max_tokens, model)
                raise BrainError(f"Ollama HTTP {r.status_code}: {r.text[:500]}")
            data = r.json()
        except requests.Timeout as e:
            # Cold load / model swap on 8GB VRAM can exceed one shot — try loaded model
            loaded = self._ollama_loaded_model()
            if loaded and loaded.split(":")[0] != model.split(":")[0]:
                logger.warning("Timeout on %s — retrying with already-loaded %s", model, loaded)
                payload["model"] = loaded
                try:
                    r = self._session.post(url, json=payload, timeout=config.LLM_TIMEOUT)
                    r.raise_for_status()
                    data = r.json()
                    model = loaded
                except requests.RequestException as e2:
                    raise BrainError(
                        f"Ollama timeout on {self.model} and fallback {loaded} failed: {e2}. "
                        f"Wait for model load (ollama ps) or free VRAM."
                    ) from e2
            else:
                raise BrainError(
                    f"Ollama timed out after {config.LLM_TIMEOUT}s loading/running '{model}'. "
                    f"Check `ollama ps` — another model may be unloading. Retry in a moment."
                ) from e
        except requests.RequestException as e:
            raise BrainError(f"Ollama unreachable at {self.ollama_url}: {e}") from e

        msg = data.get("message") or {}
        content = msg.get("content") or ""
        tool_calls = self._parse_ollama_tool_calls(msg)

        # If model wrote tool calls as text (common on smaller models)
        if not tool_calls and content and tools:
            parsed = self._extract_text_tool_calls(content)
            if parsed:
                tool_calls = parsed
                content = ""

        return {
            "role": "assistant",
            "content": content.strip() or None,
            "tool_calls": tool_calls,
            "raw": data,
            "model": model,
        }

    def _ollama_text_tool_fallback(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> Dict[str, Any]:
        """When native tools fail, inject a tool protocol into the system prompt."""
        tool_desc = json.dumps(
            [{"name": t["function"]["name"], "description": t["function"].get("description", ""),
              "parameters": t["function"].get("parameters", {})} for t in tools],
            indent=2,
        )
        protocol = (
            "You have tools. To call a tool, respond ONLY with JSON:\n"
            '{"tool_call": {"name": "TOOL_NAME", "arguments": {...}}}\n'
            "You may chain by calling one tool per response. "
            "When done, reply with normal text (no JSON wrapper).\n"
            f"Available tools:\n{tool_desc}"
        )
        msgs = list(messages)
        if msgs and msgs[0].get("role") == "system":
            msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n\n" + protocol}
        else:
            msgs.insert(0, {"role": "system", "content": protocol})

        payload = {
            "model": model,
            "messages": self._normalize_messages_for_ollama(msgs),
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        r = self._session.post(f"{self.ollama_url}/api/chat", json=payload, timeout=config.LLM_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        content = (data.get("message") or {}).get("content") or ""
        tool_calls = self._extract_text_tool_calls(content)
        if tool_calls:
            content = ""
        return {
            "role": "assistant",
            "content": content.strip() or None,
            "tool_calls": tool_calls,
            "raw": data,
            "model": model,
        }

    @staticmethod
    def _normalize_messages_for_ollama(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for m in messages:
            nm: Dict[str, Any] = {"role": m["role"]}
            if "content" in m and m["content"] is not None:
                c = m["content"]
                if isinstance(c, list):
                    # flatten multimodal text parts
                    texts = [p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"]
                    nm["content"] = "\n".join(texts) if texts else str(c)
                else:
                    nm["content"] = c
            if "images" in m:
                nm["images"] = m["images"]
            if m.get("role") == "tool":
                nm["role"] = "tool"
                nm["content"] = m.get("content", "")
                if m.get("name"):
                    nm["name"] = m["name"]
            if m.get("tool_calls"):
                nm["tool_calls"] = m["tool_calls"]
            out.append(nm)
        return out

    @staticmethod
    def _parse_ollama_tool_calls(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw = msg.get("tool_calls") or []
        parsed = []
        for i, tc in enumerate(raw):
            fn = tc.get("function") or {}
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except json.JSONDecodeError:
                    args = {"raw": args}
            parsed.append({
                "id": tc.get("id") or f"call_{i}",
                "name": fn.get("name") or tc.get("name") or "",
                "arguments": args if isinstance(args, dict) else {"value": args},
            })
        return [p for p in parsed if p["name"]]

    @staticmethod
    def _extract_text_tool_calls(content: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from messy model text.
        Supports:
          {"tool_call": {"name":..., "arguments":...}}
          {"name": "web_search", "arguments": {...}}
          {"name": "web_search", "parameters": {...}}
          prose + embedded JSON
        """
        content = (content or "").strip()
        if not content:
            return []
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        candidates: List[dict] = []
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                candidates.append(data)
            elif isinstance(data, list):
                candidates.extend([x for x in data if isinstance(x, dict)])
        except json.JSONDecodeError:
            pass

        # Scan for embedded {...} blocks (greedy last-brace per open)
        if not candidates:
            import re
            for m in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, flags=re.S):
                try:
                    obj = json.loads(m.group(0))
                    if isinstance(obj, dict):
                        candidates.append(obj)
                except json.JSONDecodeError:
                    continue

        parsed: List[Dict[str, Any]] = []
        for i, data in enumerate(candidates):
            if "tool_call" in data and isinstance(data["tool_call"], dict):
                tc = data["tool_call"]
                name = tc.get("name") or tc.get("tool")
                args = tc.get("arguments") or tc.get("args") or tc.get("parameters") or {}
                if name:
                    parsed.append({
                        "id": f"text_{i}",
                        "name": str(name),
                        "arguments": args if isinstance(args, dict) else {"value": args},
                    })
                continue
            name = data.get("name") or data.get("tool")
            if not name:
                continue
            args = (
                data.get("arguments")
                or data.get("args")
                or data.get("parameters")
                or data.get("input")
                or {}
            )
            # skip pure identity-looking JSON without tool-ish shape
            if not any(k in data for k in ("arguments", "args", "parameters", "input", "tool_call")):
                # still allow {"name":"run_shell","command":"..."} flat form
                flat = {k: v for k, v in data.items() if k not in ("name", "tool", "type")}
                if not flat:
                    continue
                args = flat
            parsed.append({
                "id": f"text_{i}",
                "name": str(name),
                "arguments": args if isinstance(args, dict) else {"value": args},
            })
        return parsed

    # ── OpenAI-compatible ──────────────────────────────────────────────

    def _openai_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
        model: str,
        base_url: str,
        api_key: str,
    ) -> Dict[str, Any]:
        if not api_key and "localhost" not in (base_url or "") and "127.0.0.1" not in (base_url or ""):
            raise BrainError("API key missing for OpenAI-compatible provider")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        url = base_url.rstrip("/") + "/chat/completions"
        r = self._session.post(url, headers=headers, json=payload, timeout=config.LLM_TIMEOUT)
        if r.status_code >= 400:
            raise BrainError(f"OpenAI-compat HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        tool_calls = []
        for i, tc in enumerate(msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            args = fn.get("arguments") or "{}"
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"raw": args}
            tool_calls.append({
                "id": tc.get("id") or f"call_{i}",
                "name": fn.get("name", ""),
                "arguments": args,
            })
        return {
            "role": "assistant",
            "content": msg.get("content"),
            "tool_calls": tool_calls,
            "raw": data,
            "model": model,
        }

    def _anthropic_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        if not config.ANTHROPIC_API_KEY:
            raise BrainError("ANTHROPIC_API_KEY not set")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        }
        system = ""
        norm = []
        for m in messages:
            if m["role"] == "system":
                system += (m.get("content") or "") + "\n"
            else:
                norm.append({"role": m["role"] if m["role"] != "tool" else "user",
                             "content": m.get("content") or ""})
        payload: Dict[str, Any] = {
            "model": config.ANTHROPIC_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": norm,
        }
        if system.strip():
            payload["system"] = system.strip()
        if tools:
            payload["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters") or {"type": "object", "properties": {}},
                }
                for t in tools
            ]
        r = self._session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers, json=payload, timeout=config.LLM_TIMEOUT,
        )
        if r.status_code >= 400:
            raise BrainError(f"Anthropic HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        content_text = ""
        tool_calls = []
        for i, block in enumerate(data.get("content") or []):
            if block.get("type") == "text":
                content_text += block.get("text") or ""
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id") or f"call_{i}",
                    "name": block.get("name", ""),
                    "arguments": block.get("input") or {},
                })
        return {
            "role": "assistant",
            "content": content_text or None,
            "tool_calls": tool_calls,
            "raw": data,
            "model": config.ANTHROPIC_MODEL,
        }
