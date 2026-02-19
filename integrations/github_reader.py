"""
Seven AI — GitHub Repository Analyzer

Reads and analyzes public GitHub repositories via the GitHub REST API.
Seven can do what Perplexity, Meta AI, and Mistral cannot.

Usage:
    from integrations.github_reader import GitHubReader

    reader = GitHubReader()
    analysis = reader.analyze_repo("LoSkroefie/seven-ai")
    print(analysis['summary'])

No authentication required for public repos (60 requests/hour unauthenticated).
Set GITHUB_TOKEN env var for 5000 requests/hour.
"""

import os
import logging
import requests
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime


class GitHubReader:
    """Read and analyze public GitHub repositories"""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.logger = logger or logging.getLogger("GitHubReader")
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Seven-AI/3.2",
        })
        if self.token:
            self._session.headers["Authorization"] = f"token {self.token}"

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make a GitHub API request"""
        url = f"{self.API_BASE}/{endpoint.lstrip('/')}"
        try:
            resp = self._session.get(url, params=params, timeout=15)
            if resp.status_code == 404:
                self.logger.warning(f"Not found: {endpoint}")
                return None
            if resp.status_code == 403:
                self.logger.warning("GitHub API rate limit hit")
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            self.logger.error(f"GitHub API error: {e}")
            return None

    def get_repo_info(self, owner_repo: str) -> Optional[Dict[str, Any]]:
        """Get basic repository information"""
        data = self._get(f"repos/{owner_repo}")
        if not data:
            return None
        return {
            'name': data.get('name'),
            'full_name': data.get('full_name'),
            'description': data.get('description'),
            'language': data.get('language'),
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'watchers': data.get('subscribers_count', 0),
            'open_issues': data.get('open_issues_count', 0),
            'created': data.get('created_at'),
            'updated': data.get('updated_at'),
            'pushed': data.get('pushed_at'),
            'license': data.get('license', {}).get('spdx_id') if data.get('license') else None,
            'topics': data.get('topics', []),
            'default_branch': data.get('default_branch', 'main'),
            'size_kb': data.get('size', 0),
            'archived': data.get('archived', False),
            'fork': data.get('fork', False),
            'homepage': data.get('homepage'),
            'url': data.get('html_url'),
        }

    def get_directory_tree(self, owner_repo: str, path: str = "",
                           max_depth: int = 2, _depth: int = 0) -> List[dict]:
        """Get directory structure recursively"""
        if _depth >= max_depth:
            return []

        data = self._get(f"repos/{owner_repo}/contents/{path}")
        if not data or not isinstance(data, list):
            return []

        tree = []
        for item in sorted(data, key=lambda x: (x['type'] != 'dir', x['name'])):
            entry = {
                'name': item['name'],
                'type': item['type'],
                'path': item['path'],
                'size': item.get('size', 0),
            }
            if item['type'] == 'dir' and _depth < max_depth - 1:
                entry['children'] = self.get_directory_tree(
                    owner_repo, item['path'], max_depth, _depth + 1
                )
            tree.append(entry)
        return tree

    def get_file_content(self, owner_repo: str, path: str) -> Optional[str]:
        """Read a file from the repository"""
        data = self._get(f"repos/{owner_repo}/contents/{path}")
        if not data or data.get('type') != 'file':
            return None
        content = data.get('content', '')
        encoding = data.get('encoding', 'base64')
        if encoding == 'base64' and content:
            try:
                return base64.b64decode(content).decode('utf-8', errors='replace')
            except Exception:
                return None
        return content

    def get_readme(self, owner_repo: str) -> Optional[str]:
        """Get the README content"""
        data = self._get(f"repos/{owner_repo}/readme")
        if not data:
            return None
        content = data.get('content', '')
        if data.get('encoding') == 'base64' and content:
            try:
                return base64.b64decode(content).decode('utf-8', errors='replace')
            except Exception:
                return None
        return content

    def get_recent_commits(self, owner_repo: str, limit: int = 10) -> List[dict]:
        """Get recent commits"""
        data = self._get(f"repos/{owner_repo}/commits", params={"per_page": limit})
        if not data or not isinstance(data, list):
            return []
        return [
            {
                'sha': c['sha'][:7],
                'message': c['commit']['message'].split('\n')[0][:100],
                'author': c['commit']['author']['name'],
                'date': c['commit']['author']['date'],
            }
            for c in data
        ]

    def get_languages(self, owner_repo: str) -> Optional[Dict[str, int]]:
        """Get language breakdown (bytes per language)"""
        return self._get(f"repos/{owner_repo}/languages")

    def count_lines_estimate(self, languages: Dict[str, int]) -> int:
        """Rough line count estimate from language bytes (avg ~40 bytes/line)"""
        total_bytes = sum(languages.values())
        return total_bytes // 40

    def analyze_repo(self, owner_repo: str) -> Dict[str, Any]:
        """
        Full repository analysis — the thing Perplexity and Meta AI can't do.

        Returns a comprehensive analysis dict with:
        - Basic info (stars, language, license, etc.)
        - Directory structure
        - README content
        - Language breakdown
        - Recent commits
        - Summary text
        """
        self.logger.info(f"Analyzing repository: {owner_repo}")
        result = {
            'owner_repo': owner_repo,
            'analyzed_at': datetime.now().isoformat(),
        }

        # Basic info
        info = self.get_repo_info(owner_repo)
        if not info:
            result['error'] = f"Could not access repository: {owner_repo}"
            return result
        result['info'] = info

        # Languages
        languages = self.get_languages(owner_repo)
        result['languages'] = languages or {}
        result['estimated_lines'] = self.count_lines_estimate(languages) if languages else 0

        # Directory structure
        result['tree'] = self.get_directory_tree(owner_repo, max_depth=2)

        # README
        readme = self.get_readme(owner_repo)
        result['readme'] = readme[:5000] if readme else None
        result['readme_length'] = len(readme) if readme else 0

        # Recent commits
        result['recent_commits'] = self.get_recent_commits(owner_repo, limit=5)

        # Generate summary
        result['summary'] = self._generate_summary(result)

        return result

    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        info = analysis.get('info', {})
        langs = analysis.get('languages', {})
        total_bytes = sum(langs.values())
        commits = analysis.get('recent_commits', [])

        parts = []
        parts.append(f"## {info.get('full_name', 'Unknown')} — Repository Analysis\n")

        if info.get('description'):
            parts.append(f"**Description:** {info['description']}\n")

        parts.append(f"**Language:** {info.get('language', 'Unknown')}")
        parts.append(f"**Stars:** {info.get('stars', 0)} | "
                      f"**Forks:** {info.get('forks', 0)} | "
                      f"**Issues:** {info.get('open_issues', 0)}")

        if info.get('license'):
            parts.append(f"**License:** {info['license']}")
        if info.get('topics'):
            parts.append(f"**Topics:** {', '.join(info['topics'])}")

        parts.append(f"\n**Size:** {info.get('size_kb', 0):,} KB")
        parts.append(f"**Estimated lines:** ~{analysis.get('estimated_lines', 0):,}")

        if langs:
            parts.append(f"\n### Languages")
            for lang, bytes_count in sorted(langs.items(), key=lambda x: -x[1]):
                pct = (bytes_count / total_bytes * 100) if total_bytes else 0
                parts.append(f"- **{lang}**: {pct:.1f}%")

        if commits:
            parts.append(f"\n### Recent Commits")
            for c in commits[:5]:
                parts.append(f"- `{c['sha']}` {c['message']} ({c['author']})")

        # Directory overview
        tree = analysis.get('tree', [])
        if tree:
            dirs = [t['name'] for t in tree if t['type'] == 'dir']
            files = [t['name'] for t in tree if t['type'] == 'file']
            parts.append(f"\n### Root Structure")
            if dirs:
                parts.append(f"**Directories:** {', '.join(dirs[:20])}")
            if files:
                key_files = [f for f in files if f.lower() in
                             ('readme.md', 'setup.py', 'requirements.txt',
                              'pyproject.toml', 'package.json', 'cargo.toml',
                              'go.mod', 'dockerfile', 'docker-compose.yml',
                              'makefile', '.gitignore', 'license')]
                if key_files:
                    parts.append(f"**Key files:** {', '.join(key_files)}")

        return "\n".join(parts)

    def format_tree(self, tree: List[dict], indent: int = 0) -> str:
        """Format directory tree as text"""
        lines = []
        for item in tree:
            prefix = "  " * indent
            if item['type'] == 'dir':
                lines.append(f"{prefix}{item['name']}/")
                if 'children' in item:
                    lines.append(self.format_tree(item['children'], indent + 1))
            else:
                size = item.get('size', 0)
                lines.append(f"{prefix}{item['name']} ({size:,} bytes)")
        return "\n".join(lines)
