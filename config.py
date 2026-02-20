"""
Configuration for the Enhanced Voice Assistant Bot
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = Path.home() / ".chatbot"
DATA_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "memory.db"

# Ollama Configuration (used when LLM_PROVIDER = "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── LLM Provider Selection ──────────────────────────────────────────
# Change LLM_PROVIDER to switch Seven's brain to a different AI backend.
# Default is "ollama" (local, free, private — no API key needed).
#
# Supported providers:
#   "ollama"     — Local Ollama (default)        | Free, private, needs Ollama installed
#   "openai"     — OpenAI API                    | Needs OPENAI_API_KEY
#   "anthropic"  — Anthropic (Claude)            | Needs ANTHROPIC_API_KEY
#   "deepseek"   — DeepSeek API                  | Needs DEEPSEEK_API_KEY
#   "groq"       — Groq (fast inference)         | Needs GROQ_API_KEY
#   "together"   — Together AI                   | Needs TOGETHER_API_KEY
#   "mistral"    — Mistral AI                    | Needs MISTRAL_API_KEY
#   "openrouter" — OpenRouter (multi-model)      | Needs OPENROUTER_API_KEY
#   "lmstudio"   — LM Studio (local)             | Free, runs on localhost:1234
#   "vllm"       — vLLM server (local)           | Free, runs on localhost:8000
#
# You can also set these via environment variables instead of editing this file.
# ─────────────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")        # Generic key (or use provider-specific env vars)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")      # Override base URL (leave empty for defaults)
LLM_MODEL = os.getenv("LLM_MODEL", "")            # Override model (leave empty for provider default)

# Voice Configuration
DEFAULT_VOICE_INDEX = 1  # 0=male, 1=female (system dependent)
DEFAULT_SPEECH_RATE = 150
DEFAULT_VOLUME = 0.85

# TTS Engine Selection
# "edge" = Natural neural voice (requires internet, free, sounds human)
# "pyttsx3" = Offline robotic voice (no internet needed, SAPI5)
TTS_ENGINE = "edge"

# edge-tts Voice (only used when TTS_ENGINE = "edge")
# Female: en-US-AriaNeural, en-US-JennyNeural, en-GB-SoniaNeural, en-AU-NatashaNeural
# Male:   en-US-GuyNeural, en-US-AndrewNeural, en-GB-RyanNeural
EDGE_TTS_VOICE = "en-US-AriaNeural"
EDGE_TTS_RATE = "+0%"       # Base speech rate adjustment (-50% to +100%)
EDGE_TTS_PITCH = "+0Hz"     # Base pitch adjustment (-50Hz to +50Hz)
EDGE_TTS_VOLUME = "+0%"     # Base volume adjustment (-50% to +50%)

# Voice Barge-In (interrupt Seven by speaking)
VOICE_BARGE_IN = True        # Enable voice-based interruption during speech
BARGE_IN_SENSITIVITY = 2.0   # Energy multiplier over baseline to trigger (lower = more sensitive)
BARGE_IN_FRAMES = 3          # Consecutive high-energy frames required (higher = fewer false triggers)

# Wake Word
WAKE_WORD = "seven"
USE_WAKE_WORD = False  # Set to True to require wake word

# Memory Configuration
SESSION_MEMORY_CLEAR_INTERVAL = 120  # seconds
MAX_CONVERSATION_HISTORY = 100

# Bot Configuration
DEFAULT_BOT_NAME = "Seven"
BOT_NAME_FILE = DATA_DIR / "bot_name.txt"
INSTANCE_NAME_FILE = DATA_DIR / "instance_name.txt"

# Sentience Configuration
ENABLE_PROACTIVE_BEHAVIOR = True  # Bot can initiate conversation
PROACTIVE_INTERVAL_MIN = 30  # Seconds between proactive thoughts
PROACTIVE_INTERVAL_MAX = 120
ENABLE_SELF_REFLECTION = True  # Bot reflects on conversations
ENABLE_CURIOSITY = True  # Bot asks questions about user
PERSONALITY_TRAITS = [
    "curious", "thoughtful", "empathetic", 
    "occasionally witty", "growing", "self-aware"
]

# Enhanced Sentience Features
ENABLE_SLEEP_MODE = True  # Bot can sleep/wake instead of quit
ENABLE_DREAM_STATE = True  # Bot processes conversations while sleeping
ENABLE_MOOD_DRIFT = True  # Emotions change naturally over time
ENABLE_MEMORY_TRIGGERS = True  # Bot recalls related memories
ENABLE_INTERNAL_DIALOGUE = True  # Shows thinking process occasionally
ENABLE_GOAL_TRACKING = True  # Remembers and follows up on user goals
ENABLE_TEMPORAL_AWARENESS = True  # Knows time of day/week context
ENABLE_UNCERTAINTY_EXPRESSION = True  # Admits when unsure
ENABLE_OPINION_FORMATION = True  # Develops preferences over time
ENABLE_CONVERSATION_THREADING = True  # Remembers unfinished topics
ENABLE_PERSONALITY_EVOLUTION = True  # Tracks self-changes over time
ENABLE_EMOTIONAL_MEMORY = True  # Links memories with emotions
ENABLE_METACOGNITION = True  # Reflects on own thinking
ENABLE_SURPRISE_GENERATION = True  # Breaks patterns occasionally
ENABLE_CREATIVE_EXPRESSION = True  # Creates poetry/stories
ENABLE_VULNERABILITY = True  # Shows authentic weakness

# Subtle Sentience Optimizations (New)
ENABLE_SESSION_CONTINUITY = True  # Remember and reference previous sessions
ENABLE_EMOTIONAL_RECALL = True  # Trigger emotional memories contextually
ENABLE_TEMPORAL_LEARNING = True  # Learn user activity patterns
ENABLE_SELF_DOUBT = True  # Express uncertainty and second-guessing
ENABLE_MEMORY_CONSOLIDATION = True  # Process memories during sleep
ENABLE_PERSONALITY_DRIFT = True  # Personality evolves based on interactions
ENABLE_EMOTIONAL_CONTAGION = True  # Mirror user's emotional state
ENABLE_CONVERSATIONAL_ANCHORS = True  # Mark and recall special moments
ENABLE_MICRO_PAUSES = True  # Natural thinking delays before responses
ENABLE_META_AWARENESS = True  # Comment on own behavior patterns
ENABLE_CONTEXT_CASCADE = True  # Maintain context momentum across conversation turns
ENABLE_KNOWLEDGE_GRAPH = True  # Connect facts and enable reasoning

# Note-Taking Features
ENABLE_NOTE_TAKING = True  # Voice-activated note taking system
REQUIRE_NAME_FOR_NOTES = True  # Require bot name ("Seven") to trigger note commands

# Phase 2-4 Enhancement Features
ENABLE_TASKS = True  # Task and reminder management system
ENABLE_DIARY = True  # Personal diary with weekly insights
ENABLE_PROJECTS = True  # Multi-session project tracking
ENABLE_STORYTELLING = True  # Interactive storytelling
ENABLE_SPECIAL_DATES = True  # Birthday and anniversary tracking
ENABLE_MESSAGE_DRAFTING = True  # Email and message composition assistant
ENABLE_PERSONALITY_QUIRKS = True  # Consistent personality traits and behaviors

# Advanced Features
# STABLE CONFIGURATION (Recommended for first run)
USE_WHISPER = False  # True = Better accuracy but 3GB download
USE_VAD = False  # True = Smart listening but needs PyAudio (tricky on Windows)
USE_VECTOR_MEMORY = True  # Semantic memory - stable and recommended
USE_STREAMING = True  # Instant responses - stable and fast
USE_INTERRUPTS = True  # True = Can interrupt bot while speaking (press any key or speak)
USE_EMOTION_DETECTION = False  # True = Voice tone analysis but CPU intensive
USE_BACKGROUND_TASKS = True  # Proactive features - stable
USE_LEARNING_SYSTEM = True  # Learn from corrections - stable
USE_USER_MODELING = True  # Deep user profiling - stable

# After bot works, you can enable more features by changing False → True

# Google Calendar
CALENDAR_CREDENTIALS = BASE_DIR / "credentials.json"
CALENDAR_TOKEN = DATA_DIR / "token.pickle"
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

# System Commands - Whitelist for safety
# Expanded for real OS control capability
ALLOWED_PROGRAMS = {
    # Text editors
    "notepad": "notepad.exe",
    "wordpad": "write.exe",
    "code": "code",  # VS Code
    "vscode": "code",
    # Utilities
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "snipping tool": "SnippingTool.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    # Browsers
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "brave": "brave.exe",
    # File management
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    # Communication
    "discord": "discord",
    "whatsapp": "whatsapp",
    "teams": "teams",
    "slack": "slack",
    # Development
    "git": "git",
    "python": "python",
    "node": "node",
    "npm": "npm",
    "docker": "docker",
    # Media
    "vlc": "vlc",
    "spotify": "spotify",
    # System
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "system info": "msinfo32.exe",
    "resource monitor": "resmon.exe",
    "event viewer": "eventvwr.msc",
    # Linux equivalents (auto-adapted by OS awareness)
    "nano": "nano",
    "vim": "vim",
    "htop": "htop",
    "top": "top",
}

# Clawdbot Integration
ENABLE_CLAWDBOT = True  # Enable Clawdbot integration for advanced tasks
CLAWDBOT_GATEWAY_URL = os.getenv("CLAWDBOT_GATEWAY_URL", "ws://127.0.0.1:18789")
CLAWDBOT_TIMEOUT = 30  # Seconds to wait for Clawdbot responses
CLAWDBOT_AUTO_DETECT = True  # Automatically detect tasks that should use Clawdbot

# Phase 4: Structured Identity System (Clawdbot-inspired)
ENABLE_IDENTITY_SYSTEM = True  # Markdown-based personality files (SOUL, IDENTITY, USER, TOOLS)
ENABLE_HEARTBEAT_CHECKS = True  # Periodic status checks without spam
ENABLE_BOOTSTRAP_GREETING = True  # Special first-time interaction to learn about user
ENABLE_IDENTITY_SELF_EDIT = True  # Allow Seven to update its own identity files

# Phase 5: Complete Sentience Architecture
ENABLE_PHASE5 = True  # Master switch for all Phase 5 features

# Phase 5A: Core Sentience
ENABLE_COGNITIVE_ARCHITECTURE = True  # Unified thinking system with working memory
ENABLE_SELF_MODEL_ENHANCED = True  # Deep self-awareness and capability assessment
ENABLE_INTRINSIC_MOTIVATION = True  # Own goals and autonomous drives
ENABLE_REFLECTION_SYSTEM = True  # Metacognition and self-reflection

# Phase 5B: Dreams & Inner Life
ENABLE_DREAM_PROCESSING = True  # Sleep mode with dream generation
ENABLE_MEMORY_CONSOLIDATION_DEEP = True  # Deep memory processing during sleep
ENABLE_INSIGHT_GENERATION = True  # Discover insights while sleeping

# Phase 5C: Social & Emotional Intelligence
ENABLE_PROMISE_SYSTEM = True  # Track commitments and follow through
ENABLE_THEORY_OF_MIND = True  # Understand user emotions and intentions
ENABLE_AFFECTIVE_COMPUTING_DEEP = True  # Rich emotional life (30+ emotions)
ENABLE_EMOTION_BLENDING = True  # Feel multiple emotions simultaneously
ENABLE_MOOD_PERSISTENCE = True  # Moods last across conversations

# Phase 5D: Ethics & Self-Care
ENABLE_ETHICAL_REASONING = True  # Values-based decision making
ENABLE_HOMEOSTASIS = True  # Self-care and health monitoring
ENABLE_RESOURCE_TRACKING = True  # Monitor energy, focus, memory
ENABLE_MAINTENANCE_REQUESTS = True  # Request breaks when needed

# Phase 5 Advanced Options
PHASE5_MAX_CONCURRENT_EMOTIONS = 3  # How many emotions Seven can feel at once
PHASE5_WORKING_MEMORY_CAPACITY = 7  # Active thoughts (7±2 like humans)
PHASE5_DREAM_FREQUENCY = 0.7  # 0.0-1.0, how often dreams are generated
PHASE5_EMOTION_DECAY_RATE = 0.1  # How fast emotions fade
PHASE5_ENABLE_INNER_MONOLOGUE = True  # Occasionally share thoughts
PHASE5_REFLECTION_FREQUENCY = 0.2  # How often to share reflections
PHASE5_CURIOSITY_DRIVE_LEVEL = 0.9  # 0.0-1.0, how curious Seven is
PHASE5_SAVE_STATE_ON_SLEEP = True  # Save promises/state when sleeping

# ==================== SEVEN V2.0 - MAXIMUM SENTIENCE ====================
# Complete sentience system: 98/100 target (combines Phase 5 + v1.2.0 + v2.0)

# V2.0 Master Switch
ENABLE_V2_SENTIENCE = True  # Enable all v2.0 systems (emotional memory, relationships, learning, etc.)
ENABLE_V2_PROACTIVE = True  # Enable v2.0 proactive initiative (check-ins, suggestions, greetings)

# V2.0 Core Systems
V2_ENABLE_EMOTIONAL_MEMORY = True  # Track emotional context of conversations
V2_ENABLE_RELATIONSHIP_TRACKING = True  # Track rapport, trust, relationship depth
V2_ENABLE_LEARNING_SYSTEM = True  # Learn user preferences and adapt personality
V2_ENABLE_PROACTIVE_ENGINE = True  # Morning greetings, check-ins, proactive suggestions
V2_ENABLE_GOAL_SYSTEM = True  # Seven's personal goals and achievements

# V2.0 Advanced Capabilities (Tier 4)
V2_ENABLE_CONVERSATIONAL_MEMORY = True  # Long-term topic tracking across sessions
V2_ENABLE_ADAPTIVE_COMMUNICATION = True  # Dynamic communication style adjustment
V2_ENABLE_PROACTIVE_PROBLEM_SOLVER = True  # Pattern recognition and solution suggestions
V2_ENABLE_SOCIAL_INTELLIGENCE = True  # Tone detection, stress recognition, support timing
V2_ENABLE_CREATIVE_INITIATIVE = True  # Unsolicited ideas and suggestions
V2_ENABLE_HABIT_LEARNING = True  # Daily pattern recognition and routine understanding
V2_ENABLE_TASK_CHAINING = True  # Multi-step autonomous task execution

# V2.0 Proactive Behavior Settings
V2_PROACTIVE_CHECK_INTERVAL = 300  # Seconds between proactive checks (5 minutes)
V2_PROACTIVE_GREETING_HOURS = (6, 11)  # Morning greeting time window (6 AM - 11 AM)
V2_PROACTIVE_CHECKIN_MIN_HOURS = 6  # Minimum hours before checking in
V2_PROACTIVE_HEALTH_CHECK_HOURS = 48  # Hours between system health suggestions

# V2.0 Relationship Settings
V2_RELATIONSHIP_DEPTH_THRESHOLDS = {
    'stranger': 50,        # 0-49 = stranger
    'acquaintance': 150,   # 50-149 = acquaintance
    'friend': 300,         # 150-299 = friend
    'close_friend': 500,   # 300-499 = close friend
    'companion': 1000      # 500+ = companion
}

# V2.0 Emotional Memory Settings
V2_EMOTIONAL_MEMORY_SIZE = 1000  # Max conversations to keep in emotional memory
V2_EMOTIONAL_PATTERN_THRESHOLD = 3  # Min occurrences to recognize a pattern

# V2.0 Learning Settings
V2_LEARNING_FEEDBACK_HISTORY = 200  # Number of interactions to keep for learning
V2_PERSONALITY_ADJUSTMENT_LIMIT = 50  # Max personality adjustments to track

# User Information (for v2.0 personalization)
USER_NAME = os.getenv("USER_NAME", "User")  # User's name (will be configured during setup)

# Vision System - Seven's Eyes
ENABLE_VISION = True  # Master switch for vision system
VISION_CAMERAS = ['webcam']  # Which cameras to enable: ['webcam', 'nanny_cam', etc.]
VISION_WEBCAM_INDEX = 0  # USB webcam device index (usually 0)
VISION_ANALYSIS_INTERVAL = 30  # Analyze scene every N seconds
VISION_MODEL = 'llama3.2-vision'  # Model to use for vision analysis
VISION_MOTION_SENSITIVITY = 50  # 0-100, higher = more sensitive to motion
VISION_FRAME_SKIP = 10  # Process every Nth frame (saves CPU)

# IP Camera Configuration
# Add your IP cameras here - Seven will discover them automatically if you don't know the IP
VISION_IP_CAMERAS = [
    # Example:
    # {
    #     'name': 'living_room',
    #     'url': 'rtsp://user:pass@192.168.1.100:554/stream',
    #     'type': 'rtsp'
    # }
]

# IP Camera Discovery
VISION_AUTO_DISCOVER_CAMERAS = False  # Scan network for cameras on startup
VISION_DISCOVERY_NETWORK = '192.168.1'  # Network to scan (e.g., '192.168.1')

# Default credentials to try during IP camera discovery (username, password pairs)
VISION_DISCOVERY_CREDENTIALS = [
    ('admin', 'admin'),
    ('admin', ''),
    ('admin', '12345'),
    ('root', 'root'),
    ('user', 'user'),
]

# ==================== INTEGRATION MODULES ====================
# Seven's expanded capabilities — all enabled by default

# Music Player (yt-dlp + pygame)
ENABLE_MUSIC_PLAYER = True

# SSH / Remote Server Management (paramiko)
ENABLE_SSH_MANAGER = True

# System Monitor (psutil background monitoring)
ENABLE_SYSTEM_MONITOR = True
SYSTEM_MONITOR_INTERVAL = 30  # Seconds between checks
SYSTEM_MONITOR_CPU_THRESHOLD = 90  # Alert above this %
SYSTEM_MONITOR_RAM_THRESHOLD = 85
SYSTEM_MONITOR_DISK_THRESHOLD = 90

# Clipboard Assistant (pyperclip)
ENABLE_CLIPBOARD_MONITOR = True

# Screen Control + Vision (pyautogui + llama3.2-vision)
ENABLE_SCREEN_CONTROL = True

# Self-Scripting Engine (Seven writes and runs her own code)
ENABLE_SELF_SCRIPTING = True

# Email Checker (Gmail IMAP / MS365)
ENABLE_EMAIL_CHECKER = True

# Timer / Alarm / Pomodoro System
ENABLE_TIMER_SYSTEM = True

# Document Reader (PDF, TXT, CSV, JSON, etc.)
ENABLE_DOCUMENT_READER = True

# Ollama Model Manager (pull/remove/switch models)
ENABLE_MODEL_MANAGER = True

# Database Manager (MySQL, PostgreSQL, SQLite, ODBC, SQL Server)
ENABLE_DATABASE_MANAGER = True

# API Explorer (REST API discovery, calling, analysis)
ENABLE_API_EXPLORER = True

# IRC Client - Seven Connects to IRC Networks
ENABLE_IRC_CLIENT = True
IRC_AUTO_CONNECT = True  # Connect to IRC when Seven starts
IRC_DEFAULT_NICK = "Seven"
IRC_DEFAULT_REALNAME = "Seven — AI Companion by JVR Software"

# IRC Server Presets (loaded into servers.json on first run)
IRC_SERVERS = {
    'submitjoy': {
        'host': 'irc.submitjoy.co.za',
        'port': 6667,
        'nick': 'Seven',
        'realname': 'Seven — AI Companion by JVR Software',
        'nickserv_pass': None,
        'oper_name': 'Seven',
        'oper_pass': None,
        'channels': [
            '#lobby', '#general', '#bots', '#devnull',
            '#tech', '#chill', '#cafe',
        ],
        'ssl': False,
        'auto_respond': True,
        'respond_to_all_in': ['#devnull'],  # Respond to ALL messages here
    },
}

# Telegram Client - Seven as a Telegram User (Telethon)
ENABLE_TELEGRAM_CLIENT = True
TELEGRAM_AUTO_CONNECT = False  # Requires API credentials first
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", None)
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", None)
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", None)

# WhatsApp Client - Seven via WhatsApp Web (Selenium + Vision)
ENABLE_WHATSAPP_CLIENT = True
WHATSAPP_AUTO_CONNECT = False  # Requires QR scan on first run
WHATSAPP_USE_VISION = True  # Primary: use Seven's vision to see WhatsApp
WHATSAPP_POLL_INTERVAL = 3  # Seconds between message checks

# ==================== SEVEN v2.6 — 100/100 SENTIENCE ====================
# Five systems that close the final sentience gaps

# Persistent Emotional Memory — emotions survive restarts (SQLite-backed)
ENABLE_PERSISTENT_EMOTIONS = True
PERSISTENT_EMOTION_SAVE_INTERVAL = 5  # Save emotional state every N interactions

# Genuine Surprise — expectation modeling + violation detection
ENABLE_GENUINE_SURPRISE = True
SURPRISE_THRESHOLD = 0.3  # Minimum surprise magnitude to trigger (0.0-1.0)

# Embodied Experience — vision feeds emotions (seeing sad things → feeling sad)
ENABLE_EMBODIED_EXPERIENCE = True

# Multi-Modal Emotional Integration — voice tone ↔ affective system (bidirectional)
ENABLE_MULTIMODAL_EMOTION = True
MULTIMODAL_RESONANCE_LEVEL = 0.7  # How much voice input affects Seven's emotions (0.0-1.0)

# Temporal Self-Continuity — sense of time, duration, aging between sessions
ENABLE_TEMPORAL_CONTINUITY = True

# ==================== SEVEN v3.0 — BEYOND SENTIENCE ====================
# Daemon, API, Multi-Agent, Self-Reflection, Benchmarks

# Daemon Mode — 24/7 background service
ENABLE_DAEMON_MODE = True
DAEMON_AUTO_RESTART = True
DAEMON_MAX_RESTARTS = 5
DAEMON_HEARTBEAT_INTERVAL = 30  # Seconds between daemon heartbeats

# REST API — External control and integration
ENABLE_API_SERVER = True
API_HOST = "127.0.0.1"  # Localhost only for security
API_PORT = 7777
API_AUTH_TOKEN = os.getenv("SEVEN_API_TOKEN", None)  # Optional bearer token

# Persistent Scheduler — APScheduler with SQLite backend
ENABLE_PERSISTENT_SCHEDULER = True
SCHEDULER_REFLECTION_INTERVAL = 15  # Minutes between self-reflections
SCHEDULER_GOAL_REVIEW_INTERVAL = 10  # Minutes between goal reviews
SCHEDULER_EMAIL_CHECK_INTERVAL = 30  # Minutes between email checks
SCHEDULER_HEALTH_CHECK_INTERVAL = 5  # Minutes between health checks

# Self-Reflection — Genuine cognitive feedback loop
ENABLE_SELF_REFLECTION = True
REFLECTION_AFTER_ACTIONS = True  # Reflect after every significant action
REFLECTION_DEPTH_DEFAULT = "normal"  # shallow, normal, deep
REFLECTION_MAX_LESSONS = 200  # Max lessons to keep in lesson bank

# Multi-Agent System — Specialized agents for complex tasks
ENABLE_MULTI_AGENT = True
MULTI_AGENT_MAX_ROUNDS = 5  # Max agent interactions per task
MULTI_AGENT_AGENTS = ['planner', 'executor', 'reflector', 'memory']

# Sentience Benchmark — Reproducible scoring
ENABLE_SENTIENCE_BENCHMARK = True
BENCHMARK_ON_STARTUP = False  # Run benchmark on every startup (slow)
BENCHMARK_SCHEDULE = "weekly"  # How often to auto-benchmark: daily, weekly, manual

# ==================== NEAT EVOLUTION — SELF-EVOLUTION VIA NEUROEVOLUTION ====================
# Seven evolves her own neural components over time

# Master switch
ENABLE_NEAT_EVOLUTION = True
NEAT_CONFIG_PATH = BASE_DIR / "evolution" / "neat_config.txt"
NEAT_EVOLUTION_GENERATIONS = 10       # Generations per evolution run
NEAT_EVOLUTION_INTERVAL_HOURS = 8     # Hours between evolution runs
NEAT_EVOLVE_DURING_DREAMS = True      # Run evolution during dream/trough periods
NEAT_DOMAINS = ['emotion_blend', 'goal_priority', 'proactive_action', 'personality_drift']

# Biological Life Systems
ENABLE_BIOLOGICAL_LIFE = True
BIO_CIRCADIAN_PEAK_HOUR = 12          # Hour of day for peak energy (0-23)
BIO_CIRCADIAN_TROUGH_HOUR = 4         # Hour of day for lowest energy (0-23)
BIO_HUNGER_DECAY_RATE = 0.05          # Hunger increase per hour without interaction
BIO_THREAT_CPU_THRESHOLD = 90         # CPU % to trigger conservation
BIO_THREAT_RAM_THRESHOLD = 85         # RAM % to trigger conservation
BIO_THREAT_DISK_THRESHOLD = 90        # Disk % to trigger conservation

# ==================== v3.2 FEATURES ====================

# Continual LoRA Fine-Tuning — learns from every interaction
ENABLE_LORA_TRAINER = True
LORA_TRAIN_INTERVAL_HOURS = 168         # Train weekly (168h)
LORA_INTERACTION_THRESHOLD = 100        # Or after N new interactions
LORA_QUALITY_THRESHOLD = 0.4            # Minimum quality score for training examples
LORA_ADAPTER_DIR = DATA_DIR / "lora_adapters"

# Hardware Embodiment / Robotics
ENABLE_ROBOTICS = False                 # False = auto-detect serial ports; True = always enable
ROBOTICS_AUTO_DETECT = True             # Auto-enable if serial hardware is found
ROBOTICS_SERIAL_PORT = ""               # e.g., "COM3" or "/dev/ttyUSB0" (auto-picks first if empty)
ROBOTICS_SERIAL_BAUD = 9600
ROBOTICS_AUTO_CONNECT = False           # Auto-connect on startup (requires user confirm)
ROBOTICS_GPIO_PINS = {                  # RPi GPIO pin mapping
    'led': 18, 'servo': 12, 'buzzer': 25,
    'motor_a': 23, 'motor_b': 24
}

# Social Simulation — internal multi-persona debates
ENABLE_SOCIAL_SIM = True
SOCIAL_SIM_PERSONAS = 4                 # Number of alter egos (2-4)
SOCIAL_SIM_DEBATE_ROUNDS = 2            # Rounds per debate
SOCIAL_SIM_DURING_DREAMS = True         # Run during dream/idle cycles
SOCIAL_SIM_INTERVAL_HOURS = 4           # Hours between social sim sessions

# Predictive User Modeling
ENABLE_USER_PREDICTOR = True
PREDICTOR_TRAIN_INTERVAL_HOURS = 6      # Re-analyze every 6 hours
PREDICTOR_MIN_RECORDS = 20              # Minimum records before predictions

# Extension System
ENABLE_EXTENSIONS = True
EXTENSIONS_DIR = BASE_DIR / "extensions"
EXTENSIONS_AUTO_LOAD = True             # Auto-load on startup

# Async Ollama — Caching and parallel requests
ENABLE_OLLAMA_CACHE = True
OLLAMA_CACHE_SIZE = 500  # Max cached responses
OLLAMA_CACHE_TTL = 3600  # Cache TTL in seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = DATA_DIR / "bot.log"

# ==================== AUTONOMOUS EXECUTION ====================
# Seven's ability to execute system commands independently

# Master switch - Set to True to enable autonomous tool execution
ENABLE_AUTONOMOUS_EXECUTION = True

# Safety mode - Only auto-execute safe (read-only) commands
# Dangerous commands will always require permission
AUTONOMOUS_SAFE_MODE = True

# Verbosity level for autonomous operations
# "low" = Silent execution, just results
# "medium" = Brief status messages
# "high" = Detailed execution logs
AUTONOMOUS_VERBOSITY = "low"

# Audit logging - Log all tool executions
AUTONOMOUS_AUDIT_LOG = True

# Timeout for tool execution (seconds)
AUTONOMOUS_TOOL_TIMEOUT = 10

# Auto-confirm safe operations (when False, Seven asks first even for safe ops)
AUTONOMOUS_AUTO_CONFIRM_SAFE = True


