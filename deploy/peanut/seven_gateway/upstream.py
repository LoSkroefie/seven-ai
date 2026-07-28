from __future__ import annotations

import json
import urllib.error
import urllib.request


class SevenUpstreamError(RuntimeError):
    """An intentionally content-free upstream failure."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SevenUpstream:
    def __init__(self, base_url: str, token: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout

    def chat(self, message: str) -> str:
        body = json.dumps({"message": message}).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/chat",
            method="POST",
            data=body,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            opener = urllib.request.build_opener(_NoRedirect)
            with opener.open(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise SevenUpstreamError("seven_unavailable")
                raw = response.read(2_000_001)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError):
            raise SevenUpstreamError("seven_unavailable") from None
        if len(raw) > 2_000_000:
            raise SevenUpstreamError("seven_response_too_large")
        try:
            payload = json.loads(raw.decode("utf-8"))
            reply = payload["reply"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            raise SevenUpstreamError("seven_invalid_response") from None
        if not isinstance(reply, str) or not reply.strip():
            raise SevenUpstreamError("seven_empty_response")
        return reply.strip()

    @property
    def token_for_tests_only(self) -> str:
        """Avoid using this outside tests; the HTTP layer never accesses it."""
        return self._token
