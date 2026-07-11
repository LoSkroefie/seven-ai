"""Bounded read-only GitHub REST API tools."""
from __future__ import annotations

import base64
import json
import os
import re
from typing import Any
from urllib.parse import quote

import requests

API = "https://api.github.com"
_SLUG = re.compile(r"^[A-Za-z0-9_.-]+$")


def _repo(owner: str, repo: str) -> tuple[str, str]:
    owner, repo = (owner or "").strip(), (repo or "").strip()
    if not _SLUG.fullmatch(owner) or not _SLUG.fullmatch(repo):
        raise ValueError("owner and repo must use GitHub slug characters")
    return owner, repo


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Seven-AI/4.3"}
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, params: dict | None = None, session=requests) -> tuple[dict[str, Any], Any]:
    try:
        response = session.get(f"{API}{path}", params=params or {}, headers=_headers(), timeout=30)
        rate = {
            "limit": response.headers.get("X-RateLimit-Limit"),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset": response.headers.get("X-RateLimit-Reset"),
        }
        envelope = {"ok": response.ok, "status": response.status_code, "rate_limit": rate}
        try:
            data = response.json()
        except ValueError:
            data = None
        if not response.ok:
            message = data.get("message") if isinstance(data, dict) else response.text[:500]
            envelope["error"] = message or f"GitHub HTTP {response.status_code}"
        return envelope, data
    except requests.RequestException as exc:
        return {"ok": False, "status": None, "rate_limit": {}, "error": str(exc)}, None


def github_status() -> str:
    return json.dumps({"api": API, "authenticated_by_environment": bool(os.getenv("GITHUB_TOKEN", "").strip()), "token_persisted_by_seven": False, "mode": "read-only"}, indent=2)


def github_repo(owner: str, repo: str) -> str:
    try:
        owner, repo = _repo(owner, repo)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)
    result, data = _get(f"/repos/{owner}/{repo}")
    if result["ok"] and isinstance(data, dict):
        result["repository"] = {key: data.get(key) for key in (
            "full_name", "description", "private", "fork", "archived", "disabled", "visibility",
            "default_branch", "language", "stargazers_count", "forks_count", "open_issues_count",
            "size", "created_at", "updated_at", "pushed_at", "html_url",
        )}
        result["repository"]["license"] = (data.get("license") or {}).get("spdx_id")
        result["repository"]["topics"] = data.get("topics") or []
    return json.dumps(result, ensure_ascii=False, indent=2)


def github_contents(owner: str, repo: str, path: str = "", ref: str = "", max_chars: int = 50_000) -> str:
    try:
        owner, repo = _repo(owner, repo)
        if "\x00" in path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("path must be repository-relative without parent traversal")
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)
    result, data = _get(f"/repos/{owner}/{repo}/contents/{quote(path, safe='/')}", {"ref": ref} if ref else None)
    if result["ok"] and isinstance(data, list):
        result["entries"] = [{key: item.get(key) for key in ("name", "path", "type", "size", "sha", "download_url")} for item in data[:200]]
        result["truncated"] = len(data) > 200
    elif result["ok"] and isinstance(data, dict):
        content = data.get("content") or ""
        if data.get("encoding") == "base64":
            try:
                raw = base64.b64decode(re.sub(r"\s+", "", content), validate=True)
                text = raw.decode("utf-8", errors="replace")
            except (ValueError, UnicodeError) as exc:
                return json.dumps({**result, "ok": False, "error": f"content decode failed: {exc}"}, indent=2)
        else:
            text = str(content)
        max_chars = max(100, min(int(max_chars), 200_000))
        result["file"] = {key: data.get(key) for key in ("name", "path", "type", "size", "sha", "html_url")}
        result["content"] = text[:max_chars]
        result["content_truncated"] = len(text) > max_chars
        result["total_chars"] = len(text)
    return json.dumps(result, ensure_ascii=False, indent=2)


def github_commits(owner: str, repo: str, ref: str = "", limit: int = 20) -> str:
    try:
        owner, repo = _repo(owner, repo)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)
    limit = max(1, min(int(limit), 100))
    params = {"per_page": limit, **({"sha": ref} if ref else {})}
    result, data = _get(f"/repos/{owner}/{repo}/commits", params)
    if result["ok"] and isinstance(data, list):
        result["commits"] = [{
            "sha": item.get("sha"), "html_url": item.get("html_url"),
            "message": ((item.get("commit") or {}).get("message") or "")[:1000],
            "author": (((item.get("commit") or {}).get("author") or {}).get("name")),
            "date": (((item.get("commit") or {}).get("author") or {}).get("date")),
        } for item in data]
    return json.dumps(result, ensure_ascii=False, indent=2)


def github_issues(owner: str, repo: str, state: str = "open", limit: int = 30) -> str:
    try:
        owner, repo = _repo(owner, repo)
        if state not in {"open", "closed", "all"}:
            raise ValueError("state must be open, closed, or all")
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)
    limit = max(1, min(int(limit), 100))
    result, data = _get(f"/repos/{owner}/{repo}/issues", {"state": state, "per_page": limit})
    if result["ok"] and isinstance(data, list):
        result["items"] = [{
            "number": item.get("number"), "kind": "pull_request" if "pull_request" in item else "issue",
            "state": item.get("state"), "title": item.get("title"), "user": (item.get("user") or {}).get("login"),
            "labels": [label.get("name") for label in item.get("labels") or []],
            "created_at": item.get("created_at"), "updated_at": item.get("updated_at"), "html_url": item.get("html_url"),
        } for item in data]
    return json.dumps(result, ensure_ascii=False, indent=2)


def register(reg):
    from seven.tools.registry import Tool
    base = {"owner": {"type": "string"}, "repo": {"type": "string"}}
    reg.register(Tool("github_status", "Report Seven's read-only GitHub REST authentication mode without exposing tokens.", {"type": "object", "properties": {}}, github_status))
    reg.register(Tool("github_repo", "Read bounded GitHub repository metadata.", {"type": "object", "properties": base, "required": ["owner", "repo"]}, github_repo))
    reg.register(Tool("github_contents", "List a repository directory or read bounded UTF-8 file content.", {"type": "object", "properties": {**base, "path": {"type": "string"}, "ref": {"type": "string"}, "max_chars": {"type": "integer", "minimum": 100, "maximum": 200000}}, "required": ["owner", "repo"]}, github_contents))
    reg.register(Tool("github_commits", "Read one bounded page of repository commits.", {"type": "object", "properties": {**base, "ref": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["owner", "repo"]}, github_commits))
    reg.register(Tool("github_issues", "Read one bounded page of issues and pull requests, distinguished by kind.", {"type": "object", "properties": {**base, "state": {"type": "string", "enum": ["open", "closed", "all"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["owner", "repo"]}, github_issues))
