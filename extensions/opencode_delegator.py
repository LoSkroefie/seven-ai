"""
Opencode Delegator Extension — Seven AI v3.2.20

Lets Seven delegate coding / analysis tasks to the `opencode` CLI
(https://github.com/sst/opencode) without reimplementing any of it.

Trigger patterns (matched case-insensitively in on_message):
  - "opencode, <task>"
  - "opencode: <task>"
  - "ask opencode to <task>"
  - "delegate to opencode: <task>"
  - "hey opencode <task>"

Agent selection:
  - DEFAULT: plan (read-only — analyzes code, proposes changes, doesn't touch files)
  - BUILD:   only used when the user explicitly says "build" in the trigger
             AND config.OPENCODE_ALLOW_BUILD is True. This agent CAN modify files.
             Build-mode examples:
               - "opencode build: add a unit test for X"
               - "ask opencode to build me a script that ..."

Config (all optional, safe defaults):
  ENABLE_OPENCODE_DELEGATOR      bool   default False
  OPENCODE_ALLOW_BUILD           bool   default False (build agent disabled)
  OPENCODE_DEFAULT_AGENT         str    default "plan"
  OPENCODE_TIMEOUT_SECONDS       int    default 180
  OPENCODE_WORKING_DIR           str    default None (uses cwd)
  OPENCODE_MAX_REPLY_CHARS       int    default 4000 (truncate long outputs)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from utils.plugin_loader import SevenExtension

logger = logging.getLogger("OpencodeDelegator")

# Optional — Seven extensions load defensively
try:
    import config
except Exception:
    config = None  # type: ignore

try:
    from integrations.opencode import OpencodeClient, AGENT_PLAN, AGENT_BUILD
except Exception:
    OpencodeClient = None  # type: ignore
    AGENT_PLAN = "plan"
    AGENT_BUILD = "build"


# Precompiled trigger patterns. Each regex captures the task text in group 1.
_TRIGGERS = [
    # "opencode, <task>" / "opencode: <task>"
    re.compile(r"^\s*opencode\s*[,:]\s*(.+)$", re.IGNORECASE),
    # "ask opencode to <task>"
    re.compile(r"^\s*ask\s+opencode\s+to\s+(.+)$", re.IGNORECASE),
    # "delegate to opencode[:] <task>"
    re.compile(r"^\s*delegate\s+to\s+opencode\s*[:,]?\s*(.+)$", re.IGNORECASE),
    # "hey opencode <task>"
    re.compile(r"^\s*hey\s+opencode[\s,:]+(.+)$", re.IGNORECASE),
]

# Build-intent markers within the task text. If ANY of these appear AND
# OPENCODE_ALLOW_BUILD is True, the 'build' agent is used.
_BUILD_INTENT = re.compile(
    r"\b(build|write|create|implement|add|modify|edit|refactor|fix|patch|generate)\b",
    re.IGNORECASE,
)

# Explicit "build:" / "build," prefix in the task text is a strong signal.
_BUILD_PREFIX = re.compile(r"^\s*build\s*[:,]\s*(.+)$", re.IGNORECASE)

# Simple help/status intents
_STATUS_PATTERNS = [
    re.compile(r"^\s*opencode\s+(status|info|version)\s*$", re.IGNORECASE),
    re.compile(r"^\s*(is\s+)?opencode\s+(ready|available|working)\s*\??\s*$", re.IGNORECASE),
]


class OpencodeDelegatorExtension(SevenExtension):
    """Bridge on_message -> OpencodeClient.run() for delegated tasks."""

    name = "Opencode Delegator"
    version = "1.0"
    description = (
        "Delegates coding and analysis tasks to the opencode CLI. "
        "Default agent is 'plan' (read-only); 'build' is opt-in and gated by config."
    )
    author = "Seven AI"

    # Passive — no schedule, driven by on_message triggers
    schedule_interval_minutes = 0
    needs_ollama = False

    # -------------------- lifecycle --------------------

    def init(self, bot=None):
        self.bot = bot
        self.enabled: bool = bool(getattr(config, "ENABLE_OPENCODE_DELEGATOR", False))
        self.allow_build: bool = bool(getattr(config, "OPENCODE_ALLOW_BUILD", False))
        self.default_agent: str = str(
            getattr(config, "OPENCODE_DEFAULT_AGENT", AGENT_PLAN)
        ).lower()
        if self.default_agent not in (AGENT_PLAN, AGENT_BUILD):
            self.default_agent = AGENT_PLAN
        self.timeout_seconds: int = int(getattr(config, "OPENCODE_TIMEOUT_SECONDS", 180))
        self.working_dir: Optional[str] = getattr(config, "OPENCODE_WORKING_DIR", None) or None
        self.max_reply_chars: int = int(getattr(config, "OPENCODE_MAX_REPLY_CHARS", 4000))

        # Runtime state
        self.client: Optional[Any] = None
        self._stats = {"plan_runs": 0, "build_runs": 0, "errors": 0, "timeouts": 0}

        if OpencodeClient is None:
            logger.warning("[OPENCODE] integrations.opencode unavailable — delegator disabled")
            self.enabled = False
            return

        try:
            self.client = OpencodeClient(default_cwd=self.working_dir)
        except Exception as e:
            logger.error(f"[OPENCODE] client init failed: {e}")
            self.client = None
            self.enabled = False

        if self.enabled and self.client and not self.client.available:
            logger.warning(
                "[OPENCODE] enabled in config but opencode CLI not on PATH — "
                "install with `npm install -g opencode-ai` or set PATH. "
                "Delegator will still accept commands but return an error message."
            )

    def run(self, context: dict = None) -> dict:
        # Passive extension — no scheduled run
        return {"status": "skipped", "message": "Opencode Delegator is passive"}

    # -------------------- on_message --------------------

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        if not user_message:
            return None
        msg = user_message.strip()

        # Status / version intents first (cheap)
        for pat in _STATUS_PATTERNS:
            if pat.match(msg):
                return self._format_status()

        # Locate a trigger
        task = self._extract_task(msg)
        if task is None:
            return None

        if not self.enabled:
            return (
                "[Seven] opencode delegator is disabled — set "
                "`ENABLE_OPENCODE_DELEGATOR = True` in config.py to enable it."
            )
        if self.client is None or not self.client.available:
            return (
                "[Seven] opencode CLI isn't available on this machine. "
                "Install it with `npm install -g opencode-ai` and check that "
                "`opencode --version` works in a terminal."
            )

        agent = self._pick_agent(task)

        # Strip "build:" prefix from task so opencode gets a clean instruction
        m_build = _BUILD_PREFIX.match(task)
        if m_build:
            task = m_build.group(1).strip()

        logger.info(
            f"[OPENCODE] delegating to agent={agent} "
            f"({len(task)} chars, timeout={self.timeout_seconds}s)"
        )
        result = self.client.run(
            message=task,
            agent=agent,
            timeout=self.timeout_seconds,
        )
        return self._format_result(result, agent, task)

    # -------------------- helpers --------------------

    def _extract_task(self, msg: str) -> Optional[str]:
        for pat in _TRIGGERS:
            m = pat.match(msg)
            if m:
                task = m.group(1).strip().rstrip("?.!")
                return task or None
        return None

    def _pick_agent(self, task: str) -> str:
        """Select plan vs build agent based on task text and config."""
        # Explicit "build:" / "build," prefix always wins when allowed
        if _BUILD_PREFIX.match(task):
            if self.allow_build:
                return AGENT_BUILD
            # User asked for build but it's disabled — still use plan, but
            # _format_result will mention the downgrade.
            return AGENT_PLAN

        # Implicit build-intent words only escalate if build is allowed
        # AND the default is explicitly "build". This keeps things safe:
        # a casual "opencode, fix the off-by-one in foo.py" stays in plan
        # mode unless the user opted into build.
        if self.default_agent == AGENT_BUILD and self.allow_build:
            return AGENT_BUILD

        return AGENT_PLAN

    # -------------------- formatters --------------------

    def _format_result(self, result: Dict[str, Any], agent: str, task: str) -> str:
        status = result.get("status")
        elapsed = result.get("elapsed", 0.0)
        output = (result.get("output") or "").strip()
        stderr = (result.get("stderr") or "").strip()

        if status == "ok":
            if agent == AGENT_BUILD:
                self._stats["build_runs"] += 1
            else:
                self._stats["plan_runs"] += 1
            body = output or "(opencode ran successfully but produced no output)"
            body = self._truncate(body)
            header = f"[Seven -> opencode/{agent}, {elapsed}s]"
            return f"{header}\n{body}"

        if status == "timeout":
            self._stats["timeouts"] += 1
            return (
                f"[Seven] opencode timed out after {elapsed}s. "
                f"Either the task is too big or a network call hung. "
                f"Try breaking it into smaller pieces, or raise "
                f"`OPENCODE_TIMEOUT_SECONDS` in config.py."
            )

        if status == "unavailable":
            return (
                "[Seven] opencode CLI isn't available — install with "
                "`npm install -g opencode-ai`."
            )

        self._stats["errors"] += 1
        err_short = (stderr or output or "unknown error")[:400]
        return (
            f"[Seven] opencode returned an error ({elapsed}s):\n{err_short}"
        )

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_reply_chars:
            return text
        cut = self.max_reply_chars - 80
        return (
            text[:cut]
            + f"\n\n... (truncated at {self.max_reply_chars} chars; "
            + "raise OPENCODE_MAX_REPLY_CHARS to see more)"
        )

    def _format_status(self) -> str:
        if self.client is None:
            return "[Seven] opencode wrapper failed to initialize."
        s = self.client.get_status()
        avail = "available" if s.get("available") else "NOT available"
        ver = s.get("version") or "unknown"
        build = "allowed" if self.allow_build else "disabled (safety)"
        enabled = "enabled" if self.enabled else "disabled"
        return (
            f"[Seven] opencode delegator: {enabled}. "
            f"CLI: {avail} (v{ver}). Build agent: {build}. "
            f"Plan runs: {self._stats['plan_runs']}, "
            f"build runs: {self._stats['build_runs']}, "
            f"timeouts: {self._stats['timeouts']}, "
            f"errors: {self._stats['errors']}."
        )

    # -------------------- plugin status --------------------

    def get_status(self) -> dict:
        cli_status = self.client.get_status() if self.client else {}
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "allow_build": self.allow_build,
            "default_agent": self.default_agent,
            "timeout_seconds": self.timeout_seconds,
            "working_dir": self.working_dir,
            "cli": cli_status,
            "stats": dict(self._stats),
            "running": True,
        }
