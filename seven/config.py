"""
Seven Real configuration.
All knobs in one place. Local-first, multi-provider ready.
"""
from __future__ import annotations

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("SEVEN_DATA_DIR", Path.home() / ".seven"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "seven.db"
LOG_PATH = DATA_DIR / "seven.log"
IDENTITY_DIR = PACKAGE_DIR / "identity"
WORKSPACE_DIR = Path(os.getenv("SEVEN_WORKSPACE", DATA_DIR / "workspace"))
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ── Identity ───────────────────────────────────────────────────────────
BOT_NAME = os.getenv("SEVEN_NAME", "Seven")
USER_NAME = os.getenv("SEVEN_USER_NAME", os.getenv("USERNAME", "User"))

# ── LLM — local first ─────────────────────────────────────────────────
# 8GB VRAM: qwen2.5:7b is best balance for tools+chat; auto-picks if missing.
LLM_PROVIDER = os.getenv("SEVEN_LLM_PROVIDER", "ollama")  # ollama | openai | anthropic | openai_compatible
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")
# Auto-select best installed model from preferred list on startup
AUTO_SELECT_MODEL = os.getenv("SEVEN_AUTO_MODEL", "1") != "0"

# Cloud / remote (only used when provider != ollama or as explicit fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
# Generic OpenAI-compatible (OpenRouter, local llama.cpp server, etc.)
COMPAT_API_KEY = os.getenv("SEVEN_COMPAT_API_KEY", "")
COMPAT_BASE_URL = os.getenv("SEVEN_COMPAT_BASE_URL", "")
COMPAT_MODEL = os.getenv("SEVEN_COMPAT_MODEL", "")

LLM_TEMPERATURE = float(os.getenv("SEVEN_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("SEVEN_MAX_TOKENS", "2048"))
# Cold model load on 8GB VRAM can take minutes if another model is swapping
LLM_TIMEOUT = int(os.getenv("SEVEN_LLM_TIMEOUT", "300"))
OLLAMA_OPERATION_TIMEOUT = int(os.getenv("SEVEN_OLLAMA_OPERATION_TIMEOUT", "1800"))
# How many tool rounds before forcing a final answer
MAX_TOOL_ROUNDS = int(os.getenv("SEVEN_MAX_TOOL_ROUNDS", "12"))

# Tool schema exposure for the model: "core" (lean, better for llama3.2) or "full"
# Execution is still L4 — tier only limits what the model *sees* in schemas.
# full = expose all tools to the model (user wants full capability; no artificial schema gate)
TOOL_TIER = os.getenv("SEVEN_TOOL_TIER", "full").lower()  # core | full

# ── Autonomy (L4) ─────────────────────────────────────────────────────
# User requested unrestricted L4. Tools execute. Audit log still written.
AUTONOMY_LEVEL = 4
REQUIRE_CONFIRMATION = False  # L4: act, don't nag
SHELL_TIMEOUT = int(os.getenv("SEVEN_SHELL_TIMEOUT", "120"))
SHELL_DEFAULT_CWD = str(WORKSPACE_DIR)

# ── Memory ─────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS = int(os.getenv("SEVEN_MAX_HISTORY", "40"))
# Soft cap chars per message when building LLM context (keeps small models focused)
MAX_MESSAGE_CHARS = int(os.getenv("SEVEN_MAX_MSG_CHARS", "4000"))
# When history exceeds this many messages, compact older ones into a summary fact
COMPACT_AFTER_MESSAGES = int(os.getenv("SEVEN_COMPACT_AFTER", "30"))
MEMORY_SEARCH_LIMIT = 8

# ── Free will (default ON — she chooses goals/actions without /commands) ─
ENABLE_FREEWILL = os.getenv("SEVEN_FREEWILL", "1") != "0"
FREEWILL_SPEAK_GAP = float(os.getenv("SEVEN_SPEAK_GAP", "180"))  # min sec between unsolicited speech
FREEWILL_INVENT_GAP = float(os.getenv("SEVEN_INVENT_GAP", "900"))  # min sec between self-goals
FREEWILL_SPEAK_IDLE_MIN = float(os.getenv("SEVEN_SPEAK_IDLE", "8"))
FREEWILL_INVENT_IDLE_MIN = float(os.getenv("SEVEN_INVENT_IDLE", "5"))

# ── Voice (talk mode turns this on; SEVEN_VOICE=1 also) ───────────────
ENABLE_VOICE = os.getenv("SEVEN_VOICE", "0") == "1"
TALK_LISTEN_TIMEOUT = float(os.getenv("SEVEN_TALK_LISTEN", "12"))
TALK_PHRASE_LIMIT = float(os.getenv("SEVEN_TALK_PHRASE", "25"))
TTS_ENGINE = os.getenv("SEVEN_TTS", "edge")  # edge | pyttsx3 | none | auto
# Ava: warm, natural US female neural (not robotic SAPI)
EDGE_TTS_VOICE = os.getenv("SEVEN_EDGE_VOICE", "en-US-AvaNeural")
EDGE_TTS_RATE = os.getenv("SEVEN_EDGE_RATE", "-5%")   # slightly slower = more natural
EDGE_TTS_PITCH = os.getenv("SEVEN_EDGE_PITCH", "+2Hz")  # subtle lift
VOICE_BARGE_IN = os.getenv("SEVEN_BARGE_IN", "1") != "0"
BARGE_IN_SENSITIVITY = float(os.getenv("SEVEN_BARGE_SENS", "3.2"))
USE_WHISPER = os.getenv("SEVEN_WHISPER", "1") != "0"
WHISPER_MODEL = os.getenv("SEVEN_WHISPER_MODEL", "base")  # tiny|base|small
WHISPER_DEVICE = os.getenv("SEVEN_WHISPER_DEVICE", "auto")  # cuda|cpu|auto
WHISPER_LANGUAGE = os.getenv("SEVEN_WHISPER_LANG", "en")  # empty = auto-detect
MIC_INDEX = os.getenv("SEVEN_MIC_INDEX")  # None = default
MIC_INDEX = int(MIC_INDEX) if MIC_INDEX not in (None, "") else None
DEFAULT_SPEECH_RATE = int(os.getenv("SEVEN_SPEECH_RATE", "165"))

# ── Sensors ────────────────────────────────────────────────────────────
ENABLE_CAMERA = os.getenv("SEVEN_CAMERA", "0") == "1"
CAMERA_INDEX = int(os.getenv("SEVEN_CAMERA_INDEX", "0"))
ENABLE_SCREEN = True
# Vision model image prep (8GB VRAM friendly)
VISION_MAX_EDGE = int(os.getenv("SEVEN_VISION_MAX_EDGE", "1280"))
VISION_JPEG_QUALITY = int(os.getenv("SEVEN_VISION_JPEG_QUALITY", "75"))
VISION_KEEP_ALIVE = os.getenv("SEVEN_VISION_KEEP_ALIVE", "2m")  # free VRAM after analysis

# ── Background / continuous ────────────────────────────────────────────
# No spam greetings. Background only for real scheduled work or sensor events.
ENABLE_HEARTBEAT = True
HEARTBEAT_SECONDS = int(os.getenv("SEVEN_HEARTBEAT", "300"))  # 5 min
PROACTIVE_IDLE_MINUTES = int(os.getenv("SEVEN_PROACTIVE_IDLE", "60"))
# Only proactively speak if there is something concrete (overdue task, sensor, goal)
PROACTIVE_REQUIRES_CONTENT = True
# Autonomy: minutes idle before heartbeat chases active goals (work session ignores this)
AUTONOMY_GOAL_IDLE_MIN = float(os.getenv("SEVEN_AUTONOMY_IDLE", "10"))
# Min seconds between autonomous goal steps (prevents thrash)
AUTONOMY_MIN_INTERVAL = float(os.getenv("SEVEN_AUTONOMY_MIN_INTERVAL", "60"))
# Default work session length (minutes)
WORK_SESSION_MINUTES = float(os.getenv("SEVEN_WORK_MINUTES", "15"))
# Daemon: how often to refresh world/self (seconds)
DAEMON_SENSE_SECONDS = float(os.getenv("SEVEN_DAEMON_SENSE", "60"))

# ── Embodiment (robot-ready bus; no hardware required) ─────────────────
ENABLE_ROBOTICS = os.getenv("SEVEN_ROBOTICS", "0") == "1"
ROBOTICS_PORT = os.getenv("SEVEN_ROBOT_PORT", "")
ROBOTICS_BAUD = int(os.getenv("SEVEN_ROBOT_BAUD", "9600"))

# ── External coding agents (legitimate local CLIs) ─────────────────────
ENABLE_OPENCODE = True
OPENCODE_TIMEOUT = 180
OPENCODE_ALLOW_BUILD = os.getenv("SEVEN_OPENCODE_BUILD", "1") == "1"

# ── API / MCP ──────────────────────────────────────────────────────────
ENABLE_API = os.getenv("SEVEN_API", "0") == "1"
API_HOST = "127.0.0.1"
API_PORT = int(os.getenv("SEVEN_API_PORT", "7777"))

# ── Logging ────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("SEVEN_LOG_LEVEL", "INFO")
