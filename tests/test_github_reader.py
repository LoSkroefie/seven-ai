import base64
import json

import requests

import seven.tools.github_reader as github


class Response:
    def __init__(self, status, data, headers=None, text=""):
        self.status_code = status
        self._data = data
        self.headers = headers or {}
        self.text = text
        self.ok = 200 <= status < 300

    def json(self):
        if isinstance(self._data, Exception):
            raise self._data
        return self._data


def test_headers_use_environment_token_without_status_disclosure(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    headers = github._headers()
    assert headers["Authorization"] == "Bearer secret-token"
    status = json.loads(github.github_status())
    assert status["authenticated_by_environment"] is True
    assert "secret-token" not in json.dumps(status)
    assert status["token_persisted_by_seven"] is False


def test_repo_metadata_and_rate_limit(monkeypatch):
    data = {"full_name": "owner/repo", "description": "real", "license": {"spdx_id": "MIT"}, "topics": ["ai"], "private": False}
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(200, data, {"X-RateLimit-Remaining": "59"}))
    result = json.loads(github.github_repo("owner", "repo"))
    assert result["ok"] is True
    assert result["repository"]["full_name"] == "owner/repo"
    assert result["repository"]["license"] == "MIT"
    assert result["rate_limit"]["remaining"] == "59"


def test_errors_are_distinct_and_transport_is_visible(monkeypatch):
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(403, {"message": "API rate limit exceeded"}, {"X-RateLimit-Remaining": "0"}))
    result = json.loads(github.github_repo("owner", "repo"))
    assert result["status"] == 403 and result["error"] == "API rate limit exceeded"

    def offline(*args, **kwargs):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(github.requests, "get", offline)
    result = json.loads(github.github_repo("owner", "repo"))
    assert result["status"] is None and "offline" in result["error"]


def test_directory_and_file_content_are_bounded(monkeypatch):
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(200, [{"name": str(i), "path": str(i), "type": "file", "size": i} for i in range(205)]))
    listing = json.loads(github.github_contents("owner", "repo"))
    assert len(listing["entries"]) == 200 and listing["truncated"] is True

    encoded = base64.encodebytes(("Seven\n" * 100).encode()).decode()
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(200, {"name": "README", "path": "README", "type": "file", "size": 600, "encoding": "base64", "content": encoded}))
    file = json.loads(github.github_contents("owner", "repo", "README", max_chars=100))
    assert len(file["content"]) == 100
    assert file["content_truncated"] is True and file["total_chars"] == 600


def test_commits_issues_and_validation(monkeypatch):
    commits = [{"sha": "abc", "html_url": "url", "commit": {"message": "subject\nbody", "author": {"name": "Jan", "date": "now"}}}]
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(200, commits))
    assert json.loads(github.github_commits("owner", "repo"))["commits"][0]["sha"] == "abc"

    issues = [{"number": 1, "title": "PR", "state": "open", "pull_request": {}, "user": {"login": "jan"}, "labels": [{"name": "bug"}]}]
    monkeypatch.setattr(github.requests, "get", lambda *a, **k: Response(200, issues))
    assert json.loads(github.github_issues("owner", "repo"))["items"][0]["kind"] == "pull_request"
    assert json.loads(github.github_repo("bad/owner", "repo"))["ok"] is False
    assert json.loads(github.github_contents("owner", "repo", "../secret"))["ok"] is False
