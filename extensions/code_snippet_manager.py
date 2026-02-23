"""
Code Snippet Manager Extension — Seven AI

Save, search, and recall code snippets from conversations.
Seven automatically detects when code is shared and offers to save it.
Persists snippets to disk with tags and language detection.

Commands:
  "save snippet" (saves last code from conversation)
  "my snippets" / "list snippets"
  "search snippets for python sort"
  "show snippet 3"
  "delete snippet 3"
"""

import logging
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("CodeSnippetManager")


class CodeSnippetManagerExtension(SevenExtension):
    """Save and recall code snippets from conversations"""

    name = "Code Snippet Manager"
    version = "1.0"
    description = "Save, tag, search, and recall code snippets"
    author = "Seven AI"

    schedule_interval_minutes = 0  # Passive
    needs_ollama = False

    # Language detection hints
    LANG_HINTS = {
        'python': ['def ', 'import ', 'class ', 'print(', 'self.', 'elif ', '__init__'],
        'javascript': ['const ', 'let ', 'function ', '=>', 'console.log', 'require('],
        'csharp': ['using System', 'namespace ', 'public class', 'static void', 'Console.'],
        'vbnet': ['Dim ', 'Sub ', 'Function ', 'Module ', 'Imports '],
        'html': ['<html', '<div', '<body', '<!DOCTYPE', '<script'],
        'css': ['{', 'color:', 'margin:', 'padding:', '@media'],
        'sql': ['SELECT ', 'FROM ', 'WHERE ', 'INSERT ', 'CREATE TABLE'],
        'bash': ['#!/bin/bash', 'echo ', 'if [', 'fi', 'done'],
        'powershell': ['Get-', 'Set-', '$_', 'Write-Host', '-Path'],
    }

    def init(self, bot=None):
        self.bot = bot
        self._data_file = Path.home() / ".chatbot" / "code_snippets.json"
        self.snippets = self._load()
        self._last_detected_code = None

    def run(self, context: dict = None) -> dict:
        return {
            "message": f"Code Snippet Manager: {len(self.snippets)} snippets saved",
            "count": len(self.snippets),
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Detect code in messages and handle snippet commands"""
        lower = user_message.lower()

        # Detect code blocks in bot response for potential saving
        code_blocks = self._extract_code_blocks(bot_response)
        if code_blocks:
            self._last_detected_code = code_blocks[-1]  # Remember last code block

        # Save snippet: "save snippet", "save that code", "keep that code"
        if any(p in lower for p in ["save snippet", "save that code", "keep that code",
                                     "save the code", "remember that code"]):
            if self._last_detected_code:
                code = self._last_detected_code['code']
                lang = self._last_detected_code.get('lang', self._detect_language(code))
                return self._save_snippet(code, lang, user_message[:50])
            return "No recent code to save. Share some code first!"

        # Save with explicit code: "save snippet: <code>"
        match = re.search(r"save\s+snippet[:\s]+```(.+?)```", user_message, re.DOTALL)
        if match:
            code = match.group(1).strip()
            lang = self._detect_language(code)
            return self._save_snippet(code, lang, "manual save")

        # List snippets
        if any(p in lower for p in ["my snippet", "list snippet", "show snippet", "all snippet"]):
            return self._list_snippets()

        # Search snippets
        match = re.search(r"search\s+snippet(?:s)?\s+(?:for\s+)?(.+)", user_message, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            return self._search_snippets(query)

        # Show specific snippet
        match = re.search(r"show\s+snippet\s+#?(\d+)", user_message, re.IGNORECASE)
        if match:
            idx = int(match.group(1))
            return self._show_snippet(idx)

        # Delete snippet
        match = re.search(r"(?:delete|remove)\s+snippet\s+#?(\d+)", user_message, re.IGNORECASE)
        if match:
            idx = int(match.group(1))
            return self._delete_snippet(idx)

        return None

    def _save_snippet(self, code: str, language: str, context: str) -> str:
        """Save a code snippet"""
        snippet = {
            'id': len(self.snippets) + 1,
            'code': code[:5000],
            'language': language,
            'context': context,
            'tags': self._auto_tag(code, language),
            'created': datetime.now().isoformat(),
        }
        self.snippets.append(snippet)
        self._save()
        return f"Snippet #{snippet['id']} saved ({language}, {len(code)} chars). Tags: {', '.join(snippet['tags'])}"

    def _list_snippets(self) -> str:
        """List all saved snippets"""
        if not self.snippets:
            return "No snippets saved yet."
        lines = [f"Code snippets ({len(self.snippets)}):"]
        for s in self.snippets[-10:]:  # Last 10
            preview = s['code'][:60].replace('\n', ' ')
            lines.append(f"  #{s['id']}: [{s['language']}] {preview}...")
        if len(self.snippets) > 10:
            lines.append(f"  ... and {len(self.snippets) - 10} more")
        return "\n".join(lines)

    def _search_snippets(self, query: str) -> str:
        """Search snippets by content or tags"""
        query_lower = query.lower()
        matches = []
        for s in self.snippets:
            if (query_lower in s['code'].lower() or
                query_lower in s['language'].lower() or
                any(query_lower in t for t in s.get('tags', []))):
                matches.append(s)

        if not matches:
            return f"No snippets matching '{query}'."

        lines = [f"Found {len(matches)} snippet(s) matching '{query}':"]
        for s in matches[:5]:
            preview = s['code'][:60].replace('\n', ' ')
            lines.append(f"  #{s['id']}: [{s['language']}] {preview}...")
        return "\n".join(lines)

    def _show_snippet(self, idx: int) -> str:
        """Show a specific snippet by ID"""
        for s in self.snippets:
            if s['id'] == idx:
                return f"Snippet #{idx} ({s['language']}):\n\n{s['code'][:2000]}\n\nTags: {', '.join(s.get('tags', []))}"
        return f"Snippet #{idx} not found."

    def _delete_snippet(self, idx: int) -> str:
        """Delete a snippet by ID"""
        for i, s in enumerate(self.snippets):
            if s['id'] == idx:
                self.snippets.pop(i)
                self._save()
                return f"Snippet #{idx} deleted."
        return f"Snippet #{idx} not found."

    def _extract_code_blocks(self, text: str) -> List[Dict]:
        """Extract code blocks from markdown-style text"""
        blocks = []
        pattern = r"```(\w+)?\n(.*?)```"
        for match in re.finditer(pattern, text, re.DOTALL):
            lang = match.group(1) or "unknown"
            code = match.group(2).strip()
            if len(code) > 10:
                blocks.append({'lang': lang, 'code': code})
        return blocks

    def _detect_language(self, code: str) -> str:
        """Simple language detection from code content"""
        scores = {}
        for lang, hints in self.LANG_HINTS.items():
            score = sum(1 for h in hints if h in code)
            if score > 0:
                scores[lang] = score
        if scores:
            return max(scores, key=scores.get)
        return "unknown"

    def _auto_tag(self, code: str, language: str) -> List[str]:
        """Auto-generate tags from code"""
        tags = [language]

        keywords = {
            'sort': 'sorting', 'search': 'search', 'file': 'file-io',
            'http': 'networking', 'api': 'api', 'database': 'database',
            'sql': 'database', 'class': 'oop', 'async': 'async',
            'test': 'testing', 'loop': 'loops', 'regex': 'regex',
            'json': 'json', 'csv': 'csv', 'math': 'math',
        }
        code_lower = code.lower()
        for keyword, tag in keywords.items():
            if keyword in code_lower and tag not in tags:
                tags.append(tag)

        return tags[:5]

    def _load(self) -> List[Dict]:
        try:
            if self._data_file.exists():
                return json.loads(self._data_file.read_text(encoding='utf-8'))
        except Exception:
            pass
        return []

    def _save(self):
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            self._data_file.write_text(json.dumps(self.snippets, indent=2), encoding='utf-8')
        except Exception:
            pass

    def stop(self):
        self._save()

    def get_status(self) -> dict:
        langs = {}
        for s in self.snippets:
            lang = s.get('language', 'unknown')
            langs[lang] = langs.get(lang, 0) + 1
        return {
            "name": self.name,
            "version": self.version,
            "total_snippets": len(self.snippets),
            "languages": langs,
            "running": True,
        }
