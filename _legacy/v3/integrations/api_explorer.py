"""
Seven AI - API Explorer
========================
Discover, call, and analyze REST APIs. Seven can explore any web API,
understand its structure, and use data from it conversationally.

Seven can:
- Call any REST API (GET, POST, PUT, DELETE)
- Save API configurations with base URLs and auth headers
- Explore API endpoints and understand response structure
- Parse and analyze JSON/XML responses via Ollama
- Chain API calls and correlate data
- Monitor APIs for changes or uptime

Dependencies: requests (already installed)
"""

import os
import json
import logging
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin, urlparse

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger("Seven.APIExplorer")


class APIExplorer:
    """REST API explorer with Ollama-powered analysis and natural language interaction."""

    def __init__(self, ollama=None):
        self.ollama = ollama
        self.available = HAS_REQUESTS

        # Saved API configurations
        self.apis: Dict[str, Dict] = {}
        self.call_history: List[Dict] = []
        self.max_history = 200

        # Config
        self.config_dir = Path.home() / "Documents" / "Seven" / "apis"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "apis.json"

        # Default timeout
        self.timeout = 15

        # Load saved APIs
        self._load_configs()

        logger.info(f"APIExplorer initialized. Saved APIs: {len(self.apis)}")

    def _load_configs(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.apis = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load API configs: {e}")

    def _save_configs(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.apis, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save API configs: {e}")

    # ==================== API MANAGEMENT ====================

    def add_api(self, name: str, base_url: str, headers: Dict = None,
                auth_type: str = None, api_key: str = None, description: str = "") -> str:
        """
        Save an API configuration.

        Args:
            name: Friendly name
            base_url: Base URL (e.g., https://api.example.com/v1)
            headers: Custom headers dict
            auth_type: none, bearer, api_key, basic
            api_key: API key or bearer token
            description: What this API does
        """
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url

        config = {
            'base_url': base_url.rstrip('/'),
            'headers': headers or {},
            'auth_type': auth_type or 'none',
            'description': description,
            'added': datetime.now().isoformat(),
        }

        # Set up auth headers
        if auth_type == 'bearer' and api_key:
            config['headers']['Authorization'] = f'Bearer {api_key}'
        elif auth_type == 'api_key' and api_key:
            config['headers']['X-API-Key'] = api_key
            config['api_key'] = api_key

        self.apis[name] = config
        self._save_configs()

        return f"API '{name}' saved: {base_url}"

    def remove_api(self, name: str) -> str:
        if name not in self.apis:
            return f"No API named '{name}'."
        del self.apis[name]
        self._save_configs()
        return f"API '{name}' removed."

    def list_apis(self) -> str:
        if not self.apis:
            return "No saved APIs. Use 'add api' to configure one."

        lines = ["**Saved APIs:**\n"]
        for name, cfg in self.apis.items():
            desc = cfg.get('description', 'No description')
            lines.append(f"- **{name}** \u2014 {cfg['base_url']} ({desc})")
        return "\n".join(lines)

    # ==================== HTTP REQUESTS ====================

    def _build_headers(self, api_name: str = None, extra_headers: Dict = None) -> Dict:
        """Build request headers from saved config + extras."""
        headers = {'User-Agent': 'Seven-AI/2.4', 'Accept': 'application/json'}

        if api_name and api_name in self.apis:
            headers.update(self.apis[api_name].get('headers', {}))

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _resolve_url(self, url: str, api_name: str = None) -> str:
        """Resolve URL against saved API base URL."""
        if url.startswith(('http://', 'https://')):
            return url

        if api_name and api_name in self.apis:
            base = self.apis[api_name]['base_url']
            return f"{base}/{url.lstrip('/')}"

        return url

    def get(self, url: str, params: Dict = None, api_name: str = None,
            headers: Dict = None) -> Dict:
        """HTTP GET request."""
        return self._request('GET', url, params=params, api_name=api_name, headers=headers)

    def post(self, url: str, data: Any = None, json_data: Any = None,
             api_name: str = None, headers: Dict = None) -> Dict:
        """HTTP POST request."""
        return self._request('POST', url, data=data, json_data=json_data,
                           api_name=api_name, headers=headers)

    def put(self, url: str, data: Any = None, json_data: Any = None,
            api_name: str = None, headers: Dict = None) -> Dict:
        """HTTP PUT request."""
        return self._request('PUT', url, data=data, json_data=json_data,
                           api_name=api_name, headers=headers)

    def delete(self, url: str, api_name: str = None, headers: Dict = None) -> Dict:
        """HTTP DELETE request."""
        return self._request('DELETE', url, api_name=api_name, headers=headers)

    def _request(self, method: str, url: str, params: Dict = None,
                 data: Any = None, json_data: Any = None,
                 api_name: str = None, headers: Dict = None) -> Dict:
        """Execute an HTTP request."""
        if not self.available:
            return {'success': False, 'error': 'requests library not available'}

        full_url = self._resolve_url(url, api_name)
        req_headers = self._build_headers(api_name, headers)

        start = time.time()
        try:
            response = requests.request(
                method=method,
                url=full_url,
                params=params,
                data=data,
                json=json_data,
                headers=req_headers,
                timeout=self.timeout,
                verify=True,
            )
            elapsed = round(time.time() - start, 2)

            # Parse response
            content_type = response.headers.get('Content-Type', '')
            body = None

            if 'json' in content_type:
                try:
                    body = response.json()
                except Exception:
                    body = response.text
            elif 'xml' in content_type or 'html' in content_type:
                body = response.text
            else:
                body = response.text

            result = {
                'success': response.ok,
                'status_code': response.status_code,
                'status_text': response.reason,
                'headers': dict(response.headers),
                'body': body,
                'elapsed': elapsed,
                'url': full_url,
                'method': method,
                'content_type': content_type,
                'size': len(response.content),
            }

            # Log
            self._log_call(method, full_url, response.status_code, elapsed)

            return result

        except requests.exceptions.Timeout:
            return {'success': False, 'error': f'Request timed out after {self.timeout}s', 'url': full_url}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Connection failed \u2014 check URL and network', 'url': full_url}
        except Exception as e:
            return {'success': False, 'error': str(e), 'url': full_url}

    def _log_call(self, method: str, url: str, status: int, elapsed: float):
        self.call_history.append({
            'method': method,
            'url': url,
            'status': status,
            'elapsed': elapsed,
            'timestamp': datetime.now().isoformat(),
        })
        if len(self.call_history) > self.max_history:
            self.call_history = self.call_history[-self.max_history:]

    # ==================== EXPLORATION ====================

    def explore_endpoint(self, url: str, api_name: str = None) -> str:
        """Call a GET endpoint and analyze its structure."""
        result = self.get(url, api_name=api_name)

        if not result['success']:
            return f"Failed to reach {result.get('url', url)}: {result.get('error', result.get('status_code'))}"

        lines = [f"**Endpoint:** `{result['method']} {result['url']}`"]
        lines.append(f"**Status:** {result['status_code']} {result['status_text']}")
        lines.append(f"**Response time:** {result['elapsed']}s | **Size:** {result['size']} bytes")
        lines.append(f"**Content-Type:** {result['content_type']}")

        body = result['body']

        if isinstance(body, dict):
            lines.append(f"\n**Response structure:**")
            lines.append(self._describe_json_structure(body))

            # Show sample
            sample = json.dumps(body, indent=2, default=str)
            if len(sample) > 2000:
                sample = sample[:2000] + "\n..."
            lines.append(f"\n**Sample response:**\n```json\n{sample}\n```")

        elif isinstance(body, list):
            lines.append(f"\n**Response:** Array of {len(body)} items")
            if body:
                lines.append(f"**Item structure:**")
                lines.append(self._describe_json_structure(body[0] if isinstance(body[0], dict) else {'value': body[0]}))
                sample = json.dumps(body[:3], indent=2, default=str)
                if len(sample) > 1500:
                    sample = sample[:1500] + "\n..."
                lines.append(f"\n**First 3 items:**\n```json\n{sample}\n```")
        else:
            text = str(body)[:1000]
            lines.append(f"\n**Response (text):**\n{text}")

        # Ollama analysis
        if self.ollama and body:
            try:
                body_preview = json.dumps(body, default=str)[:1500] if not isinstance(body, str) else body[:1500]
                analysis = self.ollama.generate(
                    f"Analyze this API response from {result['url']}:\n{body_preview}\n\nWhat data does this API provide? What's interesting? How could this data be useful?",
                    system_message="You are Seven, analyzing an API response. Be concise and insightful.",
                    temperature=0.5, max_tokens=100
                )
                if analysis:
                    lines.append(f"\n**My analysis:** {analysis.strip()}")
            except Exception:
                pass

        return "\n".join(lines)

    def explore_api(self, api_name: str = None, base_url: str = None) -> str:
        """Try common API endpoints to discover what's available."""
        if api_name and api_name in self.apis:
            base = self.apis[api_name]['base_url']
        elif base_url:
            base = base_url.rstrip('/')
        else:
            return "Provide an API name or base URL to explore."

        # Common REST patterns to probe
        common_paths = [
            '', '/', '/api', '/api/v1', '/api/v2',
            '/health', '/status', '/info', '/version',
            '/docs', '/swagger.json', '/openapi.json', '/api-docs',
            '/users', '/items', '/products', '/posts', '/data',
        ]

        lines = [f"**Exploring API:** {base}\n"]
        found = []

        for path in common_paths:
            url = f"{base}{path}"
            try:
                resp = requests.get(url, headers={'User-Agent': 'Seven-AI/2.4', 'Accept': 'application/json'},
                                   timeout=5, allow_redirects=True)
                if resp.status_code < 400:
                    ct = resp.headers.get('Content-Type', '')
                    size = len(resp.content)
                    found.append((path or '/', resp.status_code, ct[:40], size))
                    lines.append(f"\u2713 `{path or '/'}` \u2014 {resp.status_code} ({ct[:30]}, {size}B)")
            except Exception:
                pass

        if not found:
            lines.append("No accessible endpoints found. The API may require authentication.")
        else:
            lines.append(f"\n**Found {len(found)} accessible endpoint(s).**")

        return "\n".join(lines)

    def _describe_json_structure(self, obj: Any, prefix: str = "", max_depth: int = 3) -> str:
        """Describe the structure of a JSON object."""
        if max_depth <= 0:
            return f"{prefix}..."

        lines = []
        if isinstance(obj, dict):
            for key, val in list(obj.items())[:20]:
                vtype = type(val).__name__
                if isinstance(val, dict):
                    lines.append(f"{prefix}- **{key}**: object ({len(val)} keys)")
                    lines.append(self._describe_json_structure(val, prefix + "  ", max_depth - 1))
                elif isinstance(val, list):
                    item_type = type(val[0]).__name__ if val else "empty"
                    lines.append(f"{prefix}- **{key}**: array[{len(val)}] of {item_type}")
                else:
                    sample = str(val)[:50]
                    lines.append(f"{prefix}- **{key}**: {vtype} = `{sample}`")
        elif isinstance(obj, list):
            lines.append(f"{prefix}Array of {len(obj)} items")
            if obj and isinstance(obj[0], dict):
                lines.append(self._describe_json_structure(obj[0], prefix, max_depth - 1))

        return "\n".join(lines)

    # ==================== NATURAL LANGUAGE API CALLS ====================

    def natural_call(self, request: str) -> str:
        """
        Make an API call described in natural language.

        Example: "Get the current weather in Cape Town from wttr.in"
        Example: "Fetch the top posts from JSONPlaceholder"
        """
        if not self.ollama:
            return "Need Ollama to interpret natural language API requests."

        try:
            # Build context of saved APIs
            api_ctx = ""
            if self.apis:
                api_ctx = "Saved APIs:\n" + "\n".join(f"- {n}: {c['base_url']} ({c.get('description', '')})" for n, c in self.apis.items())

            plan = self.ollama.generate(
                f"""{api_ctx}

User request: {request}

Generate a JSON object with these fields:
- "method": HTTP method (GET, POST, PUT, DELETE)
- "url": Full URL to call
- "params": Query parameters dict or null
- "body": Request body dict or null
- "api_name": Name of saved API to use (or null for direct URL)

Return ONLY the JSON object.""",
                system_message="You are an API expert. Generate the correct HTTP request as JSON. Return ONLY valid JSON.",
                temperature=0.1, max_tokens=200
            )

            if not plan:
                return "I couldn't figure out how to make that API call."

            # Parse the plan
            plan = plan.strip()
            if plan.startswith('```'):
                plan = plan.split('\n', 1)[1] if '\n' in plan else plan[3:]
            if plan.endswith('```'):
                plan = plan[:-3]
            plan = plan.strip()

            call_plan = json.loads(plan)

            # Execute
            method = call_plan.get('method', 'GET').upper()
            url = call_plan.get('url', '')
            params = call_plan.get('params')
            body = call_plan.get('body')
            api_name = call_plan.get('api_name')

            if not url:
                return "Couldn't determine the URL to call."

            result = self._request(method, url, params=params, json_data=body, api_name=api_name)

            if not result['success']:
                return f"API call failed: {result.get('error', result.get('status_code'))}"

            # Format + interpret
            output = f"**{method} {result['url']}** \u2014 {result['status_code']} ({result['elapsed']}s)\n\n"

            body_data = result['body']
            if isinstance(body_data, (dict, list)):
                preview = json.dumps(body_data, indent=2, default=str)
                if len(preview) > 2000:
                    preview = preview[:2000] + "\n..."
                output += f"```json\n{preview}\n```\n"
            else:
                output += str(body_data)[:1000] + "\n"

            # Interpret
            if self.ollama:
                try:
                    body_str = json.dumps(body_data, default=str)[:2000] if not isinstance(body_data, str) else body_data[:2000]
                    interpretation = self.ollama.generate(
                        f"User asked: {request}\nAPI returned:\n{body_str}\n\nAnswer the user's question using this data. Be conversational.",
                        system_message="You are Seven, interpreting API data for the user. Be helpful and natural.",
                        temperature=0.5, max_tokens=150
                    )
                    if interpretation:
                        output += f"\n**Summary:** {interpretation.strip()}"
                except Exception:
                    pass

            return output

        except json.JSONDecodeError:
            return f"I tried to plan the API call but got confused. Can you be more specific about the URL?"
        except Exception as e:
            return f"Error: {e}"

    # ==================== MONITORING ====================

    def check_api_health(self, api_name: str = None, url: str = None) -> str:
        """Check if an API is responsive."""
        if api_name and api_name in self.apis:
            target_url = self.apis[api_name]['base_url']
        elif url:
            target_url = url
        else:
            return "Provide an API name or URL to check."

        result = self.get(target_url, api_name=api_name)

        if result['success']:
            return f"\u2713 **{target_url}** is UP \u2014 {result['status_code']} in {result['elapsed']}s"
        else:
            return f"\u2717 **{target_url}** is DOWN \u2014 {result.get('error', result.get('status_code'))}"

    def check_all_apis(self) -> str:
        """Health check all saved APIs."""
        if not self.apis:
            return "No saved APIs to check."

        lines = ["**API Health Check:**\n"]
        for name, cfg in self.apis.items():
            result = self.get(cfg['base_url'], api_name=name)
            if result['success']:
                status = f"\u2713 UP ({result['status_code']}, {result['elapsed']}s)"
            else:
                status = f"\u2717 DOWN ({result.get('error', result.get('status_code', 'unknown'))[:50]})"

            lines.append(f"- **{name}**: {status}")

        return "\n".join(lines)

    # ==================== STATUS ====================

    def get_status(self) -> str:
        lines = ["**API Explorer Status:**"]
        lines.append(f"- Available: {self.available}")
        lines.append(f"- Saved APIs: {len(self.apis)}")
        lines.append(f"- Call history: {len(self.call_history)} calls")
        if self.call_history:
            last = self.call_history[-1]
            lines.append(f"- Last call: {last['method']} {last['url']} ({last['status']})")
        return "\n".join(lines)
