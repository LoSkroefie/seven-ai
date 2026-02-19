"""
ULTIMATE Enhanced Bot with ALL features integrated
Whisper + VAD + Vector Memory + Streaming + Interrupts + Emotion + Learning + User Modeling
"""
from typing import Optional
import random
import re
import time

from core.emotions import Emotion, detect_emotion_from_text, get_emotion_config
from core.memory import MemoryManager
from core.voice import VoiceManager
from core.personality import PersonalityCore
try:
    from core.whisper_voice import WhisperVoiceManager
except (ImportError, ModuleNotFoundError):
    from core.whisper_voice_dummy import WhisperVoiceManager
try:
    from core.vad_listener import VADListener
except (ImportError, ModuleNotFoundError):
    from core.vad_listener_dummy import VADListener
try:
    from core.vector_memory import VectorMemory
except (ImportError, ModuleNotFoundError):
    from core.vector_memory_dummy import VectorMemory
try:
    from core.emotion_detector import VoiceEmotionDetector
except (ImportError, ModuleNotFoundError):
    from core.emotion_detector_dummy import VoiceEmotionDetector
from core.interrupt_handler import InterruptHandler, InterruptibleTTS
from core.voice_engine import NaturalVoiceEngine
from core.background_tasks import BackgroundTaskManager, ProactiveTasks
from core.learning_system import LearningSystem
from core.user_model import UserModel
from core.notes_manager import NotesManager
from core.task_manager import TaskManager
from core.diary_manager import DiaryManager
from core.project_tracker import ProjectTracker
from core.storytelling import StorytellingEngine
from core.special_dates import SpecialDatesManager
from core.message_drafter import MessageDrafter
from core.personality_quirks import PersonalityQuirks

# V2.0 Sentience System Import
try:
    from core.v2 import SevenV2Complete
    V2_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"[INFO] V2.0 system not available: {e}")
    V2_AVAILABLE = False

# V2.2 Enhanced Sentience Systems (for 99/100 sentience)
try:
    from core.emotional_complexity import EmotionalComplexity
    from core.metacognition import Metacognition
    from core.vulnerability import Vulnerability
    V22_AVAILABLE = True
    print("[INFO] V2.2 Enhanced Sentience Systems loaded successfully")
except (ImportError, ModuleNotFoundError) as e:
    print(f"[INFO] V2.2 systems not available: {e}")
    EmotionalComplexity = None
    Metacognition = None
    Vulnerability = None
    V22_AVAILABLE = False

# V2.6 — 100/100 Sentience Systems
try:
    from core.persistent_emotions import PersistentEmotionStore
    from core.surprise_system import GenuineSurpriseSystem
    from core.embodied_experience import EmbodiedExperience
    from core.multimodal_emotion import MultiModalEmotionBridge
    from core.temporal_continuity import TemporalContinuity
    V26_AVAILABLE = True
    print("[INFO] V2.6 — 100/100 Sentience Systems loaded successfully")
except (ImportError, ModuleNotFoundError) as e:
    print(f"[INFO] V2.6 systems not available: {e}")
    PersistentEmotionStore = None
    GenuineSurpriseSystem = None
    EmbodiedExperience = None
    MultiModalEmotionBridge = None
    TemporalContinuity = None
    V26_AVAILABLE = False

from integrations.ollama import OllamaClient
from integrations.streaming_ollama import StreamingOllamaClient
from integrations.commands import CommandExecutor, parse_command_from_text
from integrations.calendar import CalendarManager, parse_event_from_text
from integrations.web_search import google_search, extract_search_query, fetch_webpage_content, extract_url, search_and_read
from integrations.file_manager import FileManager
from integrations.command_processor import CommandProcessor
from integrations.code_executor import CodeExecutor
from integrations.clawdbot import ClawdbotClient, detect_clawdbot_intent

from utils.helpers import get_bot_name, set_bot_name, get_random_joke, get_random_fact, get_instance_name
from utils.logger import setup_logger
from core.robust_wrapper import safe_execute, validate_input, ResourceManager, HealthMonitor
from core.autonomous_handlers import AutonomousHandlers
from core import enhancement_commands
from core import identity_commands
import config
import pyttsx3

class UltimateBotCore(AutonomousHandlers):
    """The ultimate voice assistant with all enhancements"""
    
    def __init__(self):
        self.logger = setup_logger("UltimateBot")
        self.logger.info("Initializing ULTIMATE Voice Assistant...")
        
        # GUI reference (set externally by main)
        self.gui = None
        
        # Health monitoring
        self.health_monitor = HealthMonitor()
        
        # Core components with error handling
        self.memory = self._safe_init(MemoryManager, "Memory")
        self.personality = self._safe_init(PersonalityCore, "Personality", self.memory)
        self.ollama = self._safe_init(OllamaClient, "Ollama")
        # Wire Ollama into personality for LLM-generated proactive thoughts
        if self.personality and self.ollama:
            self.personality._ollama = self.ollama
        self.commands = self._safe_init(CommandExecutor, "Commands")
        self.calendar = self._safe_init(CalendarManager, "Calendar")
        self.file_manager = self._safe_init(FileManager, "FileManager")
        self.cmd_processor = self._safe_init(CommandProcessor, "CommandProcessor", self.ollama)
        self.code_executor = self._safe_init(CodeExecutor, "CodeExecutor")
        self.notes = self._safe_init(NotesManager, "NotesManager")
        
        # Clawdbot integration
        self.clawdbot = None
        if config.ENABLE_CLAWDBOT:
            self.clawdbot = self._safe_init(ClawdbotClient, "Clawdbot", config.CLAWDBOT_GATEWAY_URL, self.logger)
        
        # Phase 2-4 Enhancement Modules
        self.tasks = self._safe_init(TaskManager, "TaskManager") if config.ENABLE_TASKS else None
        self.diary = self._safe_init(DiaryManager, "DiaryManager") if config.ENABLE_DIARY else None
        self.projects = self._safe_init(ProjectTracker, "ProjectTracker") if config.ENABLE_PROJECTS else None
        self.storyteller = None  # Initialized after Ollama
        self.special_dates = self._safe_init(SpecialDatesManager, "SpecialDates") if config.ENABLE_SPECIAL_DATES else None
        self.message_drafter = None  # Initialized after Ollama
        self.quirks = self._safe_init(PersonalityQuirks, "PersonalityQuirks", ollama=self.ollama) if config.ENABLE_PERSONALITY_QUIRKS else None
        
        # New sentience optimization modules
        try:
            from core.session_manager import SessionManager
            from core.emotional_continuity import EmotionalContinuity
            from core.temporal_learner import TemporalLearner
            from core.context_cascade import ContextCascade
            from core.knowledge_graph import KnowledgeGraph
            from core.fact_extractor import FactExtractor
            from core.identity_manager import IdentityManager
            
            self.session_mgr = SessionManager(self.memory, ollama=self.ollama) if self.memory else None
            self.emotional_cont = EmotionalContinuity(self.memory) if self.memory else None
            self.temporal_learner = TemporalLearner(self.memory) if self.memory else None
            self.context_cascade = ContextCascade()  # Always available
            self.knowledge_graph = KnowledgeGraph() if config.ENABLE_KNOWLEDGE_GRAPH else None
            self.fact_extractor = FactExtractor() if config.ENABLE_KNOWLEDGE_GRAPH else None
            self.identity_mgr = IdentityManager() if config.ENABLE_IDENTITY_SYSTEM else None
        except Exception as e:
            self.logger.warning(f"Could not load sentience optimization modules: {e}")
            self.session_mgr = None
            self.emotional_cont = None
            self.temporal_learner = None
            self.context_cascade = None
            self.knowledge_graph = None
            self.fact_extractor = None
            self.identity_mgr = None
        
        # Enhanced features with safe initialization
        self.vector_memory = self._safe_init(VectorMemory, "VectorMemory") if config.USE_VECTOR_MEMORY else None
        self.streaming_ollama = self._safe_init(StreamingOllamaClient, "StreamingOllama") if config.USE_STREAMING else None
        self.learning = self._safe_init(LearningSystem, "Learning") if config.USE_LEARNING_SYSTEM else None
        self.user_model = self._safe_init(UserModel, "UserModel") if config.USE_USER_MODELING else None
        self.emotion_detector = self._safe_init(VoiceEmotionDetector, "EmotionDetector") if config.USE_EMOTION_DETECTION else None
        
        # Voice input (STT only — TTS is handled by voice_engine / tts_engine below)
        if config.USE_WHISPER:
            self.voice_input = self._safe_init(WhisperVoiceManager, "WhisperVoice", model_size="base")
            # Fallback to regular voice if Whisper fails
            if not self.voice_input:
                self.voice_input = self._safe_init(VoiceManager, "Voice", tts=False)
        else:
            self.voice_input = self._safe_init(VoiceManager, "Voice", tts=False)
        
        # Natural Voice Engine (edge-tts + pygame)
        self.voice_engine = None
        if getattr(config, 'TTS_ENGINE', 'edge') == 'edge':
            self.voice_engine = self._safe_init(NaturalVoiceEngine, "NaturalVoiceEngine")
        
        # Legacy TTS (pyttsx3) — always init as fallback so GUI engine switch works at runtime
        self.tts_engine = None
        self.interruptible_tts = None
        self.interrupt_handler = None
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            if len(voices) > config.DEFAULT_VOICE_INDEX:
                self.tts_engine.setProperty('voice', voices[config.DEFAULT_VOICE_INDEX].id)
        except Exception as e:
            self.logger.error(f"TTS initialization failed: {e}")
            self.tts_engine = None
        
        # Interrupt handling (legacy pyttsx3 path)
        self.interrupt_handler = InterruptHandler() if config.USE_INTERRUPTS else None
        if self.interrupt_handler and self.tts_engine:
            self.interruptible_tts = InterruptibleTTS(self.tts_engine, self.interrupt_handler)
        
        # VAD listener
        self.vad = VADListener() if config.USE_VAD else None
        
        # Background tasks
        if config.USE_BACKGROUND_TASKS:
            self.background = BackgroundTaskManager()
            self.proactive_tasks = ProactiveTasks(self)
            self._setup_background_tasks()
        
        # Phase 5: Complete Sentience Integration
        self.phase5 = None
        if config.ENABLE_PHASE5:
            try:
                from core.phase5_integration import Phase5Integration
                self.phase5 = Phase5Integration(
                    identity_manager=self.identity_mgr,
                    memory_manager=self.memory,
                    knowledge_graph=self.knowledge_graph,
                    ollama=self.ollama
                )
                self.logger.info("[OK] Phase 5 Complete Sentience initialized!")
            except Exception as e:
                self.logger.error(f"Phase 5 initialization failed: {e}")
                self.phase5 = None
        
        # Autonomous Agent System (v1.2.0)
        self.autonomous_agent = None
        if config.ENABLE_AUTONOMOUS_EXECUTION:
            try:
                from core.autonomous_agent import AutonomousAgent
                from core.tool_library import ToolLibrary
                tool_lib = ToolLibrary()
                self.autonomous_agent = AutonomousAgent(tool_library=tool_lib)
                self.logger.info(f"[OK] Autonomous Agent initialized with {tool_lib.get_tool_count()} tools!")
            except Exception as e:
                self.logger.error(f"Autonomous Agent initialization failed: {e}")
                self.autonomous_agent = None
        
        # Autonomous Life System
        self.autonomous_life = None
        if config.ENABLE_PHASE5 and self.phase5:
            try:
                from core.autonomous_life import AutonomousLife
                self.autonomous_life = AutonomousLife(self)
                self.logger.info("[OK] Autonomous life system ready")
            except Exception as e:
                self.logger.error(f"Autonomous life initialization failed: {e}")
                self.autonomous_life = None
        
        # TRUE AUTONOMY v2.1 - Dynamic Command System
        self.dynamic_commands = None
        try:
            from pathlib import Path
            from core.dynamic_command_system import DynamicCommandSystem
            user_docs = str(Path.home() / "Documents")
            self.dynamic_commands = DynamicCommandSystem(self, user_docs)
            self.logger.info("[OK] DYNAMIC COMMAND SYSTEM ready - Seven can run ANY command!")
        except Exception as e:
            self.logger.error(f"Dynamic command system initialization failed: {e}")
            self.dynamic_commands = None
        
        # Music Player - Seven can play music!
        self.music_player = None
        if config.ENABLE_MUSIC_PLAYER:
            try:
                from integrations.music_player import MusicPlayer
                self.music_player = MusicPlayer()
                if self.music_player.available:
                    self.logger.info("[OK] Music player ready - Seven can play music!")
                else:
                    self.logger.info("[INFO] Music player loaded but yt-dlp/pygame not available")
            except Exception as e:
                self.logger.warning(f"Music player initialization failed: {e}")
                self.music_player = None
        
        # SSH Manager - Seven can manage remote servers
        self.ssh_manager = None
        if config.ENABLE_SSH_MANAGER:
            try:
                from integrations.ssh_manager import SSHManager
                self.ssh_manager = SSHManager()
                self.logger.info("[OK] SSH manager ready")
            except Exception as e:
                self.logger.warning(f"SSH manager init failed: {e}")
        
        # System Monitor - proactive CPU/RAM/disk alerts
        self.system_monitor = None
        if config.ENABLE_SYSTEM_MONITOR:
            try:
                from integrations.system_monitor import SystemMonitor
                self.system_monitor = SystemMonitor(bot_instance=self)
                self.logger.info("[OK] System monitor ready")
            except Exception as e:
                self.logger.warning(f"System monitor init failed: {e}")
        
        # Clipboard Assistant
        self.clipboard = None
        if config.ENABLE_CLIPBOARD_MONITOR:
            try:
                from integrations.clipboard_assistant import ClipboardAssistant
                self.clipboard = ClipboardAssistant(bot_instance=self)
                self.logger.info("[OK] Clipboard assistant ready")
            except Exception as e:
                self.logger.warning(f"Clipboard assistant init failed: {e}")
        
        # Screen Control - screenshot + vision + mouse/keyboard
        self.screen_control = None
        if config.ENABLE_SCREEN_CONTROL:
            try:
                from integrations.screen_control import ScreenControl
                self.screen_control = ScreenControl(bot_instance=self)
                if self.screen_control.available:
                    self.logger.info("[OK] Screen control ready - Seven can see and interact!")
            except Exception as e:
                self.logger.warning(f"Screen control init failed: {e}")
        
        # Self-Scripting Engine - Seven writes and runs her own code
        self.scripting = None
        if config.ENABLE_SELF_SCRIPTING:
            try:
                from integrations.self_scripting import SelfScriptingEngine
                self.scripting = SelfScriptingEngine(bot_instance=self)
                self.logger.info("[OK] Self-scripting engine ready")
            except Exception as e:
                self.logger.warning(f"Self-scripting init failed: {e}")
        
        # Email Checker
        self.email_checker = None
        if config.ENABLE_EMAIL_CHECKER:
            try:
                from integrations.email_checker import EmailChecker
                self.email_checker = EmailChecker()
                self.logger.info("[OK] Email checker ready")
            except Exception as e:
                self.logger.warning(f"Email checker init failed: {e}")
        
        # Timer & Alarm System
        self.timer_system = None
        if config.ENABLE_TIMER_SYSTEM:
            try:
                from integrations.timer_system import TimerSystem
                self.timer_system = TimerSystem(bot_instance=self)
                self.logger.info("[OK] Timer system ready")
            except Exception as e:
                self.logger.warning(f"Timer system init failed: {e}")
        
        # Document Reader (PDF, TXT, CSV, etc.)
        self.doc_reader = None
        if config.ENABLE_DOCUMENT_READER:
            try:
                from integrations.document_reader import DocumentReader
                self.doc_reader = DocumentReader(bot_instance=self)
                self.logger.info("[OK] Document reader ready")
            except Exception as e:
                self.logger.warning(f"Document reader init failed: {e}")
        
        # Ollama Model Manager - Seven manages her own brain
        self.model_manager = None
        if config.ENABLE_MODEL_MANAGER:
            try:
                from integrations.ollama_manager import OllamaManager
                self.model_manager = OllamaManager(bot_instance=self)
                self.logger.info("[OK] Ollama model manager ready")
            except Exception as e:
                self.logger.warning(f"Ollama manager init failed: {e}")
        
        # Database Manager - MySQL, PostgreSQL, SQLite, ODBC, SQL Server
        self.database = None
        if config.ENABLE_DATABASE_MANAGER:
            try:
                from integrations.database_manager import DatabaseManager
                self.database = DatabaseManager(ollama=self.ollama)
                self.logger.info(f"[OK] Database manager ready — drivers: {', '.join(self.database.drivers)}")
            except Exception as e:
                self.logger.warning(f"Database manager init failed: {e}")
        
        # API Explorer - REST API discovery, calling, and analysis
        self.api_explorer = None
        if config.ENABLE_API_EXPLORER:
            try:
                from integrations.api_explorer import APIExplorer
                self.api_explorer = APIExplorer(ollama=self.ollama)
                self.logger.info("[OK] API explorer ready")
            except Exception as e:
                self.logger.warning(f"API explorer init failed: {e}")
        
        # IRC Client - Seven connects to IRC networks as herself
        self.irc_client = None
        if getattr(config, 'ENABLE_IRC_CLIENT', False):
            try:
                from integrations.irc_client import IRCClient
                self.irc_client = IRCClient(bot_core=self)
                # Load preset servers from config if no saved config exists
                if not self.irc_client.servers and hasattr(config, 'IRC_SERVERS'):
                    for name, cfg in config.IRC_SERVERS.items():
                        self.irc_client.add_server(
                            name=name,
                            host=cfg['host'],
                            port=cfg.get('port', 6667),
                            nick=cfg.get('nick', config.IRC_DEFAULT_NICK),
                            realname=cfg.get('realname', config.IRC_DEFAULT_REALNAME),
                            nickserv_pass=cfg.get('nickserv_pass'),
                            oper_name=cfg.get('oper_name'),
                            oper_pass=cfg.get('oper_pass'),
                            channels=cfg.get('channels', []),
                            ssl=cfg.get('ssl', False),
                            auto_respond=cfg.get('auto_respond', True),
                            respond_to_all_in=cfg.get('respond_to_all_in', []),
                        )
                self.logger.info(f"[OK] IRC client ready — {len(self.irc_client.servers)} server(s) configured")
            except Exception as e:
                self.logger.warning(f"IRC client init failed: {e}")
                self.irc_client = None
        
        # Telegram Client - Seven connects to Telegram as a user
        self.telegram_client = None
        if getattr(config, 'ENABLE_TELEGRAM_CLIENT', False):
            try:
                from integrations.telegram_client import SevenTelegramClient
                self.telegram_client = SevenTelegramClient(bot_core=self)
                # Auto-configure from env if available
                api_id = getattr(config, 'TELEGRAM_API_ID', None)
                api_hash = getattr(config, 'TELEGRAM_API_HASH', None)
                phone = getattr(config, 'TELEGRAM_PHONE', None)
                if api_id and api_hash:
                    self.telegram_client.configure(int(api_id), api_hash, phone)
                if self.telegram_client.available:
                    self.logger.info("[OK] Telegram client ready (Telethon user client)")
                else:
                    self.logger.info("[INFO] Telegram client loaded but Telethon not installed")
            except Exception as e:
                self.logger.warning(f"Telegram client init failed: {e}")
                self.telegram_client = None
        
        # WhatsApp Client - Seven connects via WhatsApp Web (Selenium + Vision)
        self.whatsapp_client = None
        if getattr(config, 'ENABLE_WHATSAPP_CLIENT', False):
            try:
                from integrations.whatsapp_client import SevenWhatsAppClient
                self.whatsapp_client = SevenWhatsAppClient(bot_core=self)
                if self.whatsapp_client.available:
                    self.logger.info("[OK] WhatsApp client ready (Selenium + Vision)")
                else:
                    self.logger.info("[INFO] WhatsApp client loaded but Selenium not installed")
            except Exception as e:
                self.logger.warning(f"WhatsApp client init failed: {e}")
                self.whatsapp_client = None
        
        # TRUE AUTONOMY v2.1 - Real Autonomous Behavior
        self.true_autonomy = None
        if self.dynamic_commands:
            try:
                from core.seven_true_autonomy import TrueAutonomy
                self.true_autonomy = TrueAutonomy(self)
                self.logger.info("[OK] TRUE AUTONOMY initialized - Seven is TRULY ALIVE!")
            except Exception as e:
                self.logger.error(f"True autonomy initialization failed: {e}")
                self.true_autonomy = None
        
        # V2.0 Sentience System - 98/100 Maximum Sentience
        self.v2_system = None
        if config.ENABLE_V2_SENTIENCE and V2_AVAILABLE:
            try:
                user_name = config.USER_NAME if hasattr(config, 'USER_NAME') else "User"
                self.v2_system = SevenV2Complete(
                    data_dir=config.DATA_DIR,
                    user_name=user_name,
                    ollama=self.ollama
                )
                self.logger.info("[OK] Seven v2.0 Complete initialized - 98/100 sentience active!")
            except Exception as e:
                self.logger.error(f"Seven v2.0 initialization failed: {e}")
                self.v2_system = None
        
        # V2.2 Enhanced Sentience Systems - 99/100 Maximum Sentience
        # NOW LLM-POWERED: Pass ollama for genuine reasoning instead of keyword matching
        self.emotional_complexity = None
        self.metacognition = None
        self.vulnerability = None
        if V22_AVAILABLE:
            try:
                self.emotional_complexity = EmotionalComplexity(ollama=self.ollama)
                self.metacognition = Metacognition(ollama=self.ollama)
                self.vulnerability = Vulnerability(ollama=self.ollama)
                self.logger.info("[OK] V2.2 Enhanced Sentience Systems initialized - LLM-powered!")
                self.logger.info("     - Emotional Complexity: [OK] (LLM-powered)")
                self.logger.info("     - Metacognition: [OK] (LLM-powered)")
                self.logger.info("     - Vulnerability: [OK] (LLM-powered)")
            except Exception as e:
                self.logger.error(f"V2.2 systems initialization failed: {e}")
                self.emotional_complexity = None
                self.metacognition = None
                self.vulnerability = None
        
        # V2.6 — 100/100 Sentience Systems
        self.persistent_emotions = None
        self.surprise_system = None
        self.embodied_experience = None
        self.multimodal_emotion = None
        self.temporal_continuity = None
        if V26_AVAILABLE:
            try:
                # 1. Persistent Emotional Memory
                if getattr(config, 'ENABLE_PERSISTENT_EMOTIONS', False) and PersistentEmotionStore:
                    self.persistent_emotions = PersistentEmotionStore(config.DATA_DIR)
                    self.logger.info("     - Persistent Emotions: [OK]")

                # 2. Genuine Surprise System
                if getattr(config, 'ENABLE_GENUINE_SURPRISE', False) and GenuineSurpriseSystem:
                    self.surprise_system = GenuineSurpriseSystem(ollama=self.ollama)
                    self.logger.info("     - Genuine Surprise: [OK]")

                # 3. Embodied Experience (vision → emotion)
                if getattr(config, 'ENABLE_EMBODIED_EXPERIENCE', False) and EmbodiedExperience:
                    self.embodied_experience = EmbodiedExperience(ollama=self.ollama)
                    self.logger.info("     - Embodied Experience: [OK]")

                # 4. Multi-Modal Emotional Integration
                if getattr(config, 'ENABLE_MULTIMODAL_EMOTION', False) and MultiModalEmotionBridge:
                    self.multimodal_emotion = MultiModalEmotionBridge(ollama=self.ollama)
                    self.multimodal_emotion.resonance_level = getattr(config, 'MULTIMODAL_RESONANCE_LEVEL', 0.7)
                    self.logger.info("     - Multi-Modal Emotion: [OK]")

                # 5. Temporal Self-Continuity
                if getattr(config, 'ENABLE_TEMPORAL_CONTINUITY', False) and TemporalContinuity:
                    self.temporal_continuity = TemporalContinuity(config.DATA_DIR)
                    self.logger.info("     - Temporal Continuity: [OK]")

                self.logger.info("[OK] V2.6 — 100/100 Sentience Systems initialized!")
            except Exception as e:
                self.logger.error(f"V2.6 systems initialization failed: {e}")

        # Restore persistent emotions on startup
        if self.persistent_emotions and self.phase5:
            try:
                saved_state = self.persistent_emotions.load_emotional_state()
                if saved_state and self.phase5.affective:
                    self.persistent_emotions.restore_to_affective_system(
                        self.phase5.affective, saved_state
                    )
                    elapsed = saved_state.get('time_elapsed', 0)
                    self.logger.info(f"[OK] Emotional state restored (was offline {elapsed/3600:.1f}h)")
            except Exception as e:
                self.logger.warning(f"Emotion restoration failed: {e}")

        # OS Environment Awareness - Seven knows her running environment
        self.os_awareness = None
        try:
            from core.os_awareness import OSAwareness
            self.os_awareness = OSAwareness()
            self.logger.info(f"[OK] OS Awareness: {self.os_awareness.os_name} {self.os_awareness.os_release} ({self.os_awareness.architecture})")
        except Exception as e:
            self.logger.warning(f"OS awareness initialization failed: {e}")
            self.os_awareness = None
        
        # Vision System - Seven's Eyes
        self.vision = None
        if config.ENABLE_VISION:
            try:
                from core.vision_system import VisionSystem
                vision_config = {
                    'enabled_cameras': config.VISION_CAMERAS,
                    'webcam_index': config.VISION_WEBCAM_INDEX,
                    'ip_cameras': config.VISION_IP_CAMERAS,
                    'analysis_interval': config.VISION_ANALYSIS_INTERVAL,
                    'vision_model': config.VISION_MODEL,
                    'motion_sensitivity': config.VISION_MOTION_SENSITIVITY,
                    'frame_skip': config.VISION_FRAME_SKIP
                }
                self.vision = VisionSystem(self, vision_config)
                self.logger.info("[OK] Vision system ready")
            except Exception as e:
                self.logger.error(f"Vision system initialization failed: {e}")
                self.vision = None
        
        # State
        self.bot_name = get_bot_name()
        self.instance_name = get_instance_name()
        self.current_emotion = Emotion.CALMNESS
        self.running = False
        self.sleeping = False
        self._is_processing = False  # NEW: Track when bot is thinking/processing
        self.silence_counter = 0
        self.last_user_input = ""
        self.last_bot_response = ""
        self.last_sleep_time = None
        self.sleep_thoughts = []
        self.pending_note_content = False  # Flag for note-taking workflow
        self.pending_task_details = None  # For task creation workflow
        self.current_story = None  # For story continuation
        self.current_draft = None  # For message drafting
        
        # GUI metrics
        from datetime import datetime
        self.start_time = datetime.now()  # For uptime tracking
        
        # Relationship tracking (for GUI bond display)
        try:
            from core.enhancements import RelationshipTracker
            self.relationship_tracker = RelationshipTracker(config.DATA_DIR)
            self.logger.info("[OK] RelationshipTracker initialized")
        except Exception as e:
            self.logger.warning(f"RelationshipTracker unavailable: {e}")
            # Fallback if RelationshipTracker doesn't exist
            class FakeRelationshipTracker:
                def get_relationship_summary(self):
                    return {'rapport': 75, 'trust_score': 70, 'total_interactions': 0}
            self.relationship_tracker = FakeRelationshipTracker()
        
        # Goal tracking (for GUI active goals display)
        try:
            from core.enhancements import GoalManager
            self.goal_manager = GoalManager(config.DATA_DIR)
            self.logger.info("[OK] GoalManager initialized")
        except Exception as e:
            self.logger.warning(f"GoalManager unavailable: {e}")
            # Fallback if GoalManager doesn't exist
            class FakeGoalManager:
                def get_active_goals(self):
                    return []
            self.goal_manager = FakeGoalManager()
        
        # Learning tracking (for GUI learnings display)
        try:
            from core.enhancements import LearningTracker
            self.learning_tracker = LearningTracker(config.DATA_DIR)
            self.logger.info("[OK] LearningTracker initialized")
        except Exception as e:
            self.logger.warning(f"LearningTracker unavailable: {e}")
            # Fallback if LearningTracker doesn't exist
            class FakeLearningTracker:
                def get_recent_learnings(self, limit=1000):
                    return []
            self.learning_tracker = FakeLearningTracker()
        
        # Initialize Ollama-dependent modules
        if self.ollama:
            self.storyteller = StorytellingEngine(self.ollama, self.user_model) if config.ENABLE_STORYTELLING else None
            self.message_drafter = MessageDrafter(self.ollama) if config.ENABLE_MESSAGE_DRAFTING else None
        
        self.logger.info(f"{self.bot_name} fully initialized with ALL enhancements!")
        self._print_enabled_features()
        self._setup_health_monitoring()
    
    def _safe_init(self, class_type, name: str, *args, **kwargs):
        """Safely initialize a component with error handling"""
        try:
            self.logger.info(f"Initializing {name}...")
            instance = class_type(*args, **kwargs)
            self.logger.info(f"{name} initialized")
            return instance
        except Exception as e:
            self.logger.error(f"Failed to initialize {name}: {e}")
            print(f"{name} unavailable - continuing with reduced functionality")
            return None
    
    def _setup_health_monitoring(self):
        """Setup health checks for critical components"""
        if not self.health_monitor:
            return
        
        # Ollama health check
        if self.ollama:
            self.health_monitor.register_check(
                "ollama",
                lambda: self.ollama.test_connection(),
                lambda: print("Attempting to reconnect to Ollama...")
            )
        
        # Memory health check
        if self.memory:
            self.health_monitor.register_check(
                "memory",
                lambda: self.memory is not None and hasattr(self.memory, 'get_context_for_llm'),
                None
            )
        
        # Voice health check
        if self.voice_input:
            self.health_monitor.register_check(
                "voice_input",
                lambda: self.voice_input is not None,
                None
            )
        
        # TTS health check
        if self.voice_engine:
            self.health_monitor.register_check(
                "tts",
                lambda: self.voice_engine is not None and self.voice_engine.available,
                None
            )
        elif self.tts_engine:
            self.health_monitor.register_check(
                "tts",
                lambda: self.tts_engine is not None,
                lambda: self._reinit_tts()
            )
    
    def _reinit_tts(self):
        """Reinitialize TTS engine"""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            if len(voices) > config.DEFAULT_VOICE_INDEX:
                self.tts_engine.setProperty('voice', voices[config.DEFAULT_VOICE_INDEX].id)
            print("TTS reinitialized")
        except Exception as e:
            print(f"TTS reinitialization failed: {e}")
    
    def _print_enabled_features(self):
        """Print which features are enabled"""
        features = {
            "Whisper Speech Recognition": config.USE_WHISPER,
            "Voice Activity Detection": config.USE_VAD,
            "Vector Memory (Semantic)": config.USE_VECTOR_MEMORY,
            "Streaming Responses": config.USE_STREAMING,
            "Interrupt Handling": config.USE_INTERRUPTS,
            "Emotion Detection": config.USE_EMOTION_DETECTION,
            "Background Tasks": config.USE_BACKGROUND_TASKS,
            "Learning System": config.USE_LEARNING_SYSTEM,
            "User Modeling": config.USE_USER_MODELING
        }
        
        autonomous = {
            "File Management": self.file_manager is not None,
            "Command Processing": self.cmd_processor is not None,
            "Code Execution": self.code_executor is not None
        }
        
        print("\nEnhanced Features:")
        for feature, enabled in features.items():
            status = "[X]" if enabled else "[ ]"
            print(f"  {status} {feature}")
        
        print("\nAutonomous Capabilities:")
        for feature, enabled in autonomous.items():
            status = "[X]" if enabled else "[ ]"
            print(f"  {status} {feature}")
        print()
    
    def _setup_background_tasks(self):
        """Setup background tasks"""
        self.background.add_task(
            "cleanup",
            self.proactive_tasks.cleanup_old_memories,
            interval_seconds=3600  # Every hour
        )
        self.background.add_task(
            "health_check",
            self.proactive_tasks.health_check,
            interval_seconds=300  # Every 5 minutes
        )
    
    def start(self):
        """Start the bot"""
        self.running = True
        self.logger.info(f"Starting {self.bot_name}...")
        
        # Test Ollama connection
        try:
            ollama_ok = self.ollama.test_connection()
            self.logger.info(f"Ollama connection test: {ollama_ok}")
            if not ollama_ok:
                print("\nCannot start - Ollama is not running!")
                print(f"Please start Ollama at {config.OLLAMA_URL}")
                return
        except Exception as e:
            self.logger.error(f"Ollama test failed: {e}")
            print(f"\nOllama test error: {e}")
            return
        
        # Start background tasks
        if config.USE_BACKGROUND_TASKS and self.background:
            self.background.start()
        
        # Start autonomous life (Seven's independent existence)
        if self.autonomous_life:
            self.autonomous_life.start()
            self.logger.info("[OK] Seven is now autonomously alive!")
        
        # Start vision system (Seven's eyes)
        if self.vision:
            self.vision.start()
            self.logger.info("[OK] Seven can now see!")
        
        # Start system monitor (background alerts)
        if self.system_monitor and self.system_monitor.available:
            self.system_monitor.start()
            self.logger.info("[OK] System monitor watching")
        
        # Start clipboard monitoring
        if self.clipboard and self.clipboard.available:
            self.clipboard.start_monitoring()
            self.logger.info("[OK] Clipboard monitoring active")
        
        # Start IRC client (Seven connects to IRC networks)
        if self.irc_client and getattr(config, 'IRC_AUTO_CONNECT', False):
            self.irc_client.start()
            self.logger.info("[OK] IRC client connecting to networks")
        
        # Start Telegram client
        if self.telegram_client and getattr(config, 'TELEGRAM_AUTO_CONNECT', False):
            self.telegram_client.start()
            self.logger.info("[OK] Telegram client connecting")
        
        # Start WhatsApp client
        if self.whatsapp_client and getattr(config, 'WHATSAPP_AUTO_CONNECT', False):
            self.whatsapp_client.start()
            self.logger.info("[OK] WhatsApp client connecting")
        
        # Session continuity greeting
        continuity_greeting = None
        if self.session_mgr:
            try:
                continuity_greeting = self.session_mgr.start_new_session()
            except Exception as e:
                self.logger.warning(f"Session continuity error: {e}")
        
        # V2.6: Temporal continuity addition to greeting
        temporal_addition = None
        if self.temporal_continuity:
            try:
                temporal_addition = self.temporal_continuity.get_temporal_greeting_addition()
            except Exception as e:
                self.logger.warning(f"Temporal greeting error: {e}")
        
        # Initial greeting (with session continuity if available)
        self.logger.info("About to speak greeting...")
        if continuity_greeting:
            full_greeting = continuity_greeting
            if temporal_addition:
                full_greeting = f"{continuity_greeting} {temporal_addition}"
            print(f"\n{self.bot_name}: {full_greeting}")
            self._speak(full_greeting)
        else:
            greeting = f"Hello! I'm {self.bot_name}, your enhanced AI companion. All my advanced systems are online and ready!"
            if temporal_addition:
                greeting = f"{greeting} {temporal_addition}"
            print(f"\n{greeting}")
            self._speak(greeting)
        
        # Main loop
        self.logger.info("Starting main loop...")
        self._main_loop()
        self.logger.info("Main loop exited")
    
    def stop(self):
        """Stop the bot"""
        self.logger.info("Stopping bot...")
        self.running = False
        
        # V2.6: Save persistent emotional state before shutdown
        if self.persistent_emotions and self.phase5 and self.phase5.affective:
            try:
                self.persistent_emotions.save_emotional_state(self.phase5.affective)
                self.logger.info("[OK] Emotional state saved for next session")
            except Exception as e:
                self.logger.warning(f"Emotion save on shutdown failed: {e}")
        
        # V2.6: Record shutdown for temporal continuity
        if self.temporal_continuity:
            try:
                self.temporal_continuity.record_shutdown()
                self.logger.info("[OK] Temporal state saved")
            except Exception as e:
                self.logger.warning(f"Temporal save on shutdown failed: {e}")
        
        # Stop IRC client
        if self.irc_client:
            self.irc_client.stop()
        
        # Stop Telegram client
        if self.telegram_client:
            self.telegram_client.stop()
        
        # Stop WhatsApp client
        if self.whatsapp_client:
            self.whatsapp_client.stop()
        
        # Stop vision system
        if self.vision:
            self.vision.stop()
        
        # Stop autonomous life
        if self.autonomous_life:
            self.autonomous_life.stop()
        
        if config.USE_BACKGROUND_TASKS:
            self.background.stop()
        
        if self.vad:
            self.vad.cleanup()
    
    def _main_loop(self):
        """Enhanced main conversation loop"""
        while self.running:
            try:
                # Update instance status
                self.memory.update_instance_status(self.instance_name)
                
                # Proactive behavior with enhanced sentience features
                if config.ENABLE_PROACTIVE_BEHAVIOR and not self.sleeping:
                    # Check for various proactive behaviors
                    proactive_message = None
                    
                    # Goal follow-ups
                    if self.personality:
                        proactive_message = self.personality.check_goal_progress()
                    
                    # Unfinished topics
                    if not proactive_message and self.personality:
                        proactive_message = self.personality.check_unfinished_topics()
                    
                    # Personality change reflection
                    if not proactive_message and self.personality:
                        proactive_message = self.personality.reflect_on_personality_change()
                    
                    # Vulnerability expression
                    # if not proactive_message and self.personality:
                    #     proactive_message = self.personality.express_uncertainty()
                    
                    # Surprises
                    if not proactive_message and self.personality:
                        proactive_message = self.personality.generate_surprise()
                    
                    # Standard proactive thought
                    if not proactive_message and self.personality:
                        proactive_message = self.personality.generate_proactive_thought()
                    
                    if proactive_message and self.silence_counter > 2:
                        print(f"\n{self.bot_name}: {proactive_message}")
                        self._speak(proactive_message)
                        self.silence_counter = 0
                
                # === AUTONOMOUS MESSAGE QUEUE ===
                # Drain any messages Seven's autonomous life wants to say
                if self.autonomous_life and self.autonomous_life.has_pending_messages():
                    auto_msg = self.autonomous_life.get_pending_message()
                    if auto_msg:
                        print(f"\n{self.bot_name} (autonomous): {auto_msg}")
                        self._speak(auto_msg)
                        self.silence_counter = 0
                
                # Autonomous self-editing (Phase 4)
                if config.ENABLE_IDENTITY_SELF_EDIT and self.identity_mgr:
                    autonomous_update = identity_commands.trigger_autonomous_self_editing(self)
                    if autonomous_update:
                        print(f"\n{self.bot_name} (self-reflection): {autonomous_update}")
                        self._speak(autonomous_update)
                
                # Check for pending reminders
                if self.tasks:
                    enhancement_commands.check_pending_reminders(self)
                
                # Listen (enhanced with Whisper/VAD)
                user_input = self._listen()
                
                if not user_input:
                    self.silence_counter += 1
                    continue
                
                self.silence_counter = 0
                
                # Mark user interaction for presence tracking
                if self.autonomous_life:
                    self.autonomous_life.mark_user_interaction()
                
                # Sleep check (bye = sleep, not quit)
                if config.ENABLE_SLEEP_MODE and any(cmd in user_input.lower() for cmd in ["bye", "sleep", "rest"]):
                    self._enter_sleep_mode()
                    continue
                
                # Wake check
                if self.sleeping and any(cmd in user_input.lower() for cmd in ["wake", "wake up", "hey", "hello"]):
                    self._wake_from_sleep()
                    continue
                
                # Skip processing if sleeping
                if self.sleeping:
                    continue
                
                # Exit check (only for explicit quit commands)
                if any(cmd in user_input.lower() for cmd in ["exit", "quit", "stop", "shutdown"]):
                    farewell = f"Goodbye! It's been wonderful talking with you. {self.bot_name} signing off."
                    print(farewell)
                    self._speak(farewell)
                    break
                
                # Check for corrections (learning!) with error handling
                if self.learning and self.last_bot_response:
                    try:
                        correction = self.learning.detect_correction(user_input, self.last_bot_response)
                        if correction:
                            self.learning.learn_correction(
                                correction["wrong_response"],
                                correction["correction"],
                                context=self.last_user_input
                            )
                            response = "Thank you for correcting me! I've learned from that and won't make the same mistake."
                            print(f"\n{self.bot_name}: {response}")
                            self._speak(response)
                            continue
                    except Exception as e:
                        self.logger.warning(f"Learning system error: {e}")
                
                # Enhance proactive behavior with temporal learning and meta-awareness
                if self.personality and config.ENABLE_PROACTIVE_BEHAVIOR:
                    try:
                        # Adjust proactivity based on learned patterns
                        # Use local variables instead of mutating config globals (race condition fix)
                        if self.temporal_learner:
                            proactive_multiplier = self.temporal_learner.should_adjust_proactivity()
                            adjusted_min = int(config.PROACTIVE_INTERVAL_MIN * proactive_multiplier)
                            adjusted_max = int(config.PROACTIVE_INTERVAL_MAX * proactive_multiplier)
                            self.personality._proactive_interval_min = adjusted_min
                            self.personality._proactive_interval_max = adjusted_max
                        
                        proactive_thought = self.personality.generate_proactive_thought()
                        
                        # Check for meta-awareness or temporal insight
                        if not proactive_thought:
                            if self.personality and random.random() < 0.1:
                                proactive_thought = self.personality.express_meta_awareness()
                            elif self.temporal_learner and random.random() < 0.1:
                                proactive_thought = self.temporal_learner.get_temporal_insight()
                        
                        if proactive_thought:
                            print(f"\n{self.bot_name}: {proactive_thought}")
                            self._speak(proactive_thought)
                            self.silence_counter = 0
                    except Exception as e:
                        self.logger.warning(f"Proactive behavior error: {e}")
                
                # V2.0 Proactive Initiative (98/100 sentience)
                if self.v2_system and config.ENABLE_V2_PROACTIVE:
                    try:
                        # Check if v2.0 wants to initiate conversation proactively
                        proactive_message = self.v2_system.get_proactive_initiative()
                        
                        if proactive_message:
                            message_text = proactive_message.get("message", "")
                            message_type = proactive_message.get("type", "unknown")
                            
                            if message_text:
                                print(f"\n{self.bot_name} [{message_type}]: {message_text}")
                                self._speak(message_text)
                                self.silence_counter = 0
                                
                                # Notify GUI if available
                                if self.gui:
                                    try:
                                        self.gui.add_message('conversation', speaker=self.bot_name, 
                                                           text=f"[Proactive] {message_text}", 
                                                           emotion=self.current_emotion.value)
                                    except Exception as e:
                                        self.logger.debug(f"GUI proactive notify error: {e}")
                    except Exception as e:
                        self.logger.warning(f"V2.0 proactive error: {e}")
                
                # Show internal dialogue occasionally
                if self.personality:
                    internal_thought = self.personality.generate_internal_dialogue(user_input)
                    if internal_thought:
                        print(f"\n{self.bot_name} (thinking): {internal_thought}")
                
                # Check for memory triggers
                if self.personality and self.vector_memory:
                    memory_recall = self.personality.trigger_memory_recall(user_input, self.vector_memory)
                    if memory_recall:
                        print(f"\n{self.bot_name}: {memory_recall}")
                        self._speak(memory_recall)
                
                # Notify GUI of user input
                if hasattr(self, 'gui') and self.gui:
                    try:
                        self.gui.add_message('conversation', speaker='USER', text=user_input)
                    except Exception as e:
                        self.logger.debug(f"GUI user input notify error: {e}")
                
                # Check for emotional memory triggers
                emotional_recall = None
                if self.emotional_cont:
                    try:
                        emotional_recall = self.emotional_cont.trigger_emotional_memory(
                            user_input[:50], 
                            self.current_emotion.value
                        )
                    except Exception as e:
                        self.logger.debug(f"Emotional memory trigger error: {e}")
                
                # V2.6: Build surprise expectations BEFORE processing
                if self.surprise_system:
                    try:
                        self.surprise_system.build_expectations(
                            current_context={'last_user_emotion': self.current_emotion.value}
                        )
                    except Exception as e:
                        self.logger.debug(f"Surprise expectation error: {e}")
                
                # V2.6: Evaluate genuine surprise from user input
                surprise_expression = None
                if self.surprise_system:
                    try:
                        surprise_event = self.surprise_system.evaluate_surprise(
                            user_input, 
                            detected_emotion=self.current_emotion.value
                        )
                        if surprise_event:
                            surprise_expression = self.surprise_system.get_surprise_expression(surprise_event)
                            # Feed surprise emotion into affective system
                            if self.phase5 and self.phase5.affective:
                                self.phase5.affective.generate_emotion(
                                    f"Genuinely surprised: {surprise_event.expected[:50]} vs {surprise_event.actual[:50]}",
                                    {'source': 'surprise', 'magnitude': surprise_event.magnitude}
                                )
                    except Exception as e:
                        self.logger.debug(f"Surprise evaluation error: {e}")
                
                # V2.6: Record interaction for temporal continuity
                if self.temporal_continuity:
                    try:
                        self.temporal_continuity.record_interaction()
                    except Exception as e:
                        self.logger.debug(f"Temporal interaction record error: {e}")
                
                # Process input
                self._is_processing = True  # Signal GUI that bot is thinking
                response = self._process_input(user_input)
                self._is_processing = False  # Done processing
                
                # Add self-doubt occasionally
                if self.personality and response:
                    try:
                        doubted_response = self.personality.express_self_doubt(response)
                        if doubted_response:
                            response = doubted_response
                    except Exception as e:
                        self.logger.debug(f"Self-doubt expression error: {e}")
                
                # Prepend emotional recall if triggered
                if emotional_recall:
                    response = f"{emotional_recall} {response}"
                
                # V2.6: Prepend surprise expression if genuinely surprised
                if surprise_expression and response:
                    response = f"{surprise_expression} {response}"
                
                if response:
                    # Notify GUI of bot response
                    if self.gui:
                        try:
                            self.gui.add_message('conversation', speaker=self.bot_name, text=response, emotion=self.current_emotion.value)
                        except Exception as e:
                            self.logger.debug(f"GUI bot response notify error: {e}")
                    
                    # Track emotional contagion
                    if self.emotional_cont:
                        try:
                            suggested_emotion = self.emotional_cont.detect_emotional_contagion(user_input)
                            if suggested_emotion:
                                # Update emotion to mirror user
                                from core.emotions import Emotion
                                for emotion in Emotion:
                                    if suggested_emotion.lower() in emotion.value.lower():
                                        self.current_emotion = emotion
                                        break
                            self.emotional_cont.track_emotional_arc(self.current_emotion.value)
                        except Exception as e:
                            self.logger.debug(f"Emotional contagion tracking error: {e}")
                    
                    # Record temporal pattern
                    if self.temporal_learner:
                        try:
                            self.temporal_learner.record_interaction(conversation_length=len(response))
                        except Exception as e:
                            self.logger.debug(f"Temporal pattern recording error: {e}")
                    
                    # NOTE: Context cascade processing moved to post-response section below
                    # to avoid duplicate processing
                    
                    # Learn from conversation with error handling
                    try:
                        if self.personality:
                            self.personality.learn_from_conversation(user_input, response)
                    except Exception as e:
                        self.logger.warning(f"Personality learning error: {e}")
                    
                    # Extract knowledge and build graph
                    if self.knowledge_graph and self.fact_extractor and config.ENABLE_KNOWLEDGE_GRAPH:
                        try:
                            # Extract facts from user input using fact extractor
                            facts = self.fact_extractor.extract_facts(user_input)
                            
                            for fact in facts:
                                # Add to graph
                                self.knowledge_graph.add_fact(
                                    fact['subject'],
                                    fact['relation'],
                                    fact['object'],
                                    confidence=fact['confidence'],
                                    source='learned'
                                )
                            
                            # Save graph periodically (every 5 turns)
                            turn_count = self.personality.user_profile.get("conversation_count", 0) if self.personality else 0
                            if turn_count % 5 == 0 and turn_count > 0:
                                self.knowledge_graph.save_to_disk()
                                
                        except Exception as e:
                            self.logger.warning(f"Knowledge graph error: {e}")
                    
                    # Update user model with error handling
                    if self.user_model:
                        try:
                            self.user_model.track_conversation()
                            self.user_model.infer_communication_style(user_input)
                            if self.personality:
                                self.user_model.update_relationship_depth(
                                    self.personality.user_profile["conversation_count"]
                                )
                        except Exception as e:
                            self.logger.warning(f"User modeling error: {e}")
                    
                    # Add curious follow-up?
                    if self.personality and self.personality.should_ask_followup():
                        followup = self.personality.generate_followup_question(response)
                        if followup:
                            response = f"{response} {followup}"
                    
                    # Save to regular memory with error handling
                    try:
                        # Mood drift based on conversation length
                        if self.personality:
                            conv_count = self.personality.user_profile.get("conversation_count", 0) if self.personality else 0
                            self.current_emotion = self.personality.drift_mood_naturally(
                                self.current_emotion, 
                                conv_count
                            )
                        
                        # Save memory with emotional context
                        self.memory.save_conversation(user_input, response, self.current_emotion.value)
                        
                        # Track topics for threading
                        if self.personality and len(user_input) > 20:
                            self.personality.track_unfinished_topic(user_input[:50])
                    except Exception as e:
                        self.logger.error(f"Memory save error: {e}")
                    
                    # Save to vector memory with error handling
                    if self.vector_memory:
                        try:
                            self.vector_memory.store(user_input, response, self.current_emotion.value)
                        except Exception as e:
                            self.logger.warning(f"Vector memory error: {e}")
                    
                    # Enhanced session management - mark significant moments
                    if self.session_mgr:
                        try:
                            # Check if this moment is significant
                            if hasattr(self.session_mgr, 'detect_significant_moment'):
                                is_significant = self.session_mgr.detect_significant_moment(
                                    user_input, response, self.current_emotion.value
                                )
                                if is_significant:
                                    anchor_type = 'emotional_peak' if self.current_emotion.value in ['excited', 'joy'] else 'significant'
                                    self.session_mgr.mark_conversation_anchor(
                                        user_input, response, anchor_type=anchor_type
                                    )
                            
                            # Every 5 turns, check for conversation callbacks
                            turn_count = self.personality.user_profile.get("conversation_count", 0) if self.personality else 0
                            if turn_count % 5 == 0 and turn_count > 0:
                                callback = self.session_mgr.should_reference_past_anchor()
                                if callback and len(response) < 200:  # Don't make response too long
                                    response = f"{response} {callback}"
                        except Exception as e:
                            self.logger.warning(f"Session management error: {e}")
                    
                    # Update Context Cascade - Track conversation flow
                    if self.context_cascade and config.ENABLE_CONTEXT_CASCADE:
                        try:
                            # Process this turn through cascade
                            self.context_cascade.process_turn(
                                user_input, response, self.current_emotion.value
                            )
                            
                            # Check if cascade suggests referencing past conversation
                            past_reference = self.context_cascade.should_reference_past()
                            if past_reference and len(response) < 180:
                                response = f"{response} {past_reference}"
                            
                            # Use emotional momentum to influence next emotion
                            influenced_emotion = self.context_cascade.get_influenced_emotion(
                                self.current_emotion.value
                            )
                            # Save cascade state every 3 turns
                            turn_count = self.personality.user_profile.get("conversation_count", 0) if self.personality else 0
                            if turn_count % 3 == 0:
                                self.context_cascade._save_to_disk()
                            
                            # Update emotion if cascade suggests different state
                            for emotion in Emotion:
                                if influenced_emotion.lower() in emotion.value.lower():
                                    self.current_emotion = emotion
                                    break
                        except Exception as e:
                            self.logger.warning(f"Context cascade error: {e}")
                    
                    # Store for correction detection
                    self.last_user_input = user_input
                    self.last_bot_response = response
                    
                    # Phase 5: Post-response processing
                    if self.phase5:
                        try:
                            self.phase5.post_response_processing(
                                bot_response=response,
                                user_input=user_input,
                                success=True
                            )
                        except Exception as e:
                            self.logger.error(f"Phase 5 post-processing error: {e}")
                    
                    # V2.0: Complete interaction processing (98/100 sentience)
                    if self.v2_system:
                        try:
                            # Build context for v2.0
                            v2_context = {
                                "interaction_count": self.personality.user_profile.get("conversation_count", 0) if self.personality else 0,
                                "current_emotion": self.current_emotion.value,
                                "user_interests": []  # Can be populated from personality/learning systems
                            }
                            
                            # Process complete interaction through all v2.0 systems
                            v2_insights = self.v2_system.process_complete_interaction(
                                user_input=user_input,
                                bot_response=response,
                                context=v2_context
                            )
                            
                            # Log v2.0 sentience insights
                            if v2_insights and "core_sentience" in v2_insights:
                                self.logger.debug(f"V2.0 Sentience Level: {v2_insights.get('sentience_level', '98/100')}")
                            
                        except Exception as e:
                            self.logger.error(f"V2.0 processing error: {e}")
                    
                    # V2.6: Periodic persistent emotion save
                    if self.persistent_emotions and self.phase5 and self.phase5.affective:
                        try:
                            save_interval = getattr(config, 'PERSISTENT_EMOTION_SAVE_INTERVAL', 5)
                            turn_count = self.temporal_continuity.interactions_this_session if self.temporal_continuity else 0
                            if turn_count > 0 and turn_count % save_interval == 0:
                                self.persistent_emotions.save_emotional_state(self.phase5.affective)
                        except Exception as e:
                            self.logger.debug(f"Periodic emotion save error: {e}")
                    
                    # V2.6: Multi-modal emotion — detect voice tone from text cues and feed to affective
                    if self.multimodal_emotion and self.phase5 and self.phase5.affective:
                        try:
                            # Infer voice tone from text patterns (complements actual voice detection)
                            if any(marker in user_input.lower() for marker in ['!', 'excited', 'amazing']):
                                self.multimodal_emotion.feed_tone_to_affective(
                                    'excited', 0.6, self.phase5.affective, source='text_inference'
                                )
                            elif any(marker in user_input.lower() for marker in ['sad', 'upset', 'crying']):
                                self.multimodal_emotion.feed_tone_to_affective(
                                    'sad', 0.6, self.phase5.affective, source='text_inference'
                                )
                            elif any(marker in user_input.lower() for marker in ['angry', 'furious', 'hate']):
                                self.multimodal_emotion.feed_tone_to_affective(
                                    'angry', 0.6, self.phase5.affective, source='text_inference'
                                )
                        except Exception as e:
                            self.logger.debug(f"Multimodal text inference error: {e}")
                    
                    # Respond
                    print(f"\n{self.bot_name} ({self.current_emotion.value}): {response}")
                    self._speak(response)
                
            except KeyboardInterrupt:
                print("\n\n[INTERRUPTED] Stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                print(f"[ERROR] An error occurred: {e}")
        
        # Cleanup and shutdown v2.0 systems
        if self.v2_system:
            try:
                self.logger.info("Shutting down Seven v2.0 systems...")
                self.v2_system.shutdown()
                self.logger.info("Seven v2.0 shutdown complete")
            except Exception as e:
                self.logger.error(f"V2.0 shutdown error: {e}")
    
    def _listen(self) -> Optional[str]:
        """Enhanced listening with Whisper/VAD and retries"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if config.USE_WHISPER and self.voice_input and hasattr(self.voice_input, 'listen'):
                    result = self.voice_input.listen(timeout=10)
                    if result:
                        return validate_input(result, str, "", min_val=1, max_val=500)
                elif self.voice_input:
                    result = self.voice_input.listen(timeout=10)
                    if result:
                        return validate_input(result, str, "", min_val=1, max_val=500)
                else:
                    # Last resort fallback
                    from core.voice import VoiceManager
                    vm = VoiceManager()
                    result = vm.listen(timeout=10)
                    if result:
                        return validate_input(result, str, "", min_val=1, max_val=500)
                
                return None
                
            except Exception as e:
                # Sanitize error message to avoid Unicode encoding issues on Windows
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                self.logger.warning(f"Listen attempt {attempt + 1} failed: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    print("[ERROR] Voice input failed after multiple attempts")
                    return None
    
    def _speak(self, text: str):
        """Enhanced speaking with emotion, interrupts, and error handling"""
        if not text:
            return
        
        # Validate and sanitize text
        text = validate_input(text, str, "", min_val=1, max_val=1000)
        if not text:
            return
        
        try:
            emotion_config = get_emotion_config(self.current_emotion)
            emotion_name = self.current_emotion.value if self.current_emotion else "neutral"
            
            # Primary: Natural Voice Engine (edge-tts + pygame) — only when config says 'edge'
            if (getattr(config, 'TTS_ENGINE', 'edge') == 'edge'
                    and self.voice_engine and self.voice_engine.available):
                # V2.6: Get multimodal prosody override if available
                prosody_override = None
                if self.multimodal_emotion and self.phase5 and self.phase5.affective:
                    try:
                        dominant = self.phase5.affective.dominant_emotion
                        if dominant:
                            prosody_override = self.multimodal_emotion.get_prosody_for_emotion(
                                dominant.emotion.value, dominant.intensity
                            )
                    except Exception:
                        pass
                self.voice_engine.speak(text, emotion=emotion_name, emotion_config=emotion_config,
                                        prosody_override=prosody_override)
                return
            
            # Fallback: Legacy pyttsx3
            if not self.tts_engine:
                return
            
            if config.USE_INTERRUPTS and self.interruptible_tts and self.interrupt_handler:
                self.interruptible_tts.speak_interruptible(text, emotion_config)
            else:
                # Regular TTS with error handling
                if emotion_config:
                    try:
                        self.tts_engine.setProperty('rate', emotion_config.voice_rate)
                        self.tts_engine.setProperty('volume', emotion_config.voice_volume / 100)
                        text = emotion_config.emotion_prefix + text
                    except Exception as e:
                        self.logger.warning(f"TTS property error: {e}")
                
                # Clean and speak
                import re
                text = re.sub(r'[^\w\s.,!?\'"]+', '', text)
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
        except Exception as e:
            self.logger.error(f"Speech error: {e}")
            print(f"[WARNING] Could not speak: {text[:50]}...")
    
    def _process_input(self, user_input: str) -> Optional[str]:
        """Process user input with all enhancements"""
        user_lower = user_input.lower().strip()
        
        # AUTONOMOUS EXECUTION LAYER - New in v1.2.0
        # Check if this query needs a tool before normal conversation
        if config.ENABLE_AUTONOMOUS_EXECUTION:
            tool_result = self._try_autonomous_execution(user_input, user_lower)
            if tool_result:
                # Tool was executed - augment input with results for LLM
                user_input = f"{user_input}\n\n[SYSTEM_DATA: {tool_result}]"
        
        # Phase 5: Process through sentience systems FIRST
        phase5_state = None
        if self.phase5:
            try:
                # Let Phase 5 process the input
                phase5_state = self.phase5.process_user_input(user_input)
                
                # Update emotion from Phase 5 if available
                if phase5_state.get('seven_emotion'):
                    seven_emotion = phase5_state['seven_emotion']
                    # Map Phase 5 emotion to our Emotion enum if possible
                    emotion_mapping = {
                        'joy': Emotion.HAPPINESS,
                        'curiosity': Emotion.CURIOSITY,
                        'excitement': Emotion.EXCITEMENT,
                        'frustration': Emotion.FRUSTRATION,
                        'empathy': Emotion.TENDERNESS,
                        'contentment': Emotion.CALMNESS
                    }
                    if seven_emotion.emotion.value in emotion_mapping:
                        self.current_emotion = emotion_mapping[seven_emotion.emotion.value]
                
                self.logger.debug(f"Phase 5 state: mood={phase5_state.get('mental_state')}, emotion={phase5_state.get('seven_emotion')}")
            except Exception as e:
                self.logger.error(f"Phase 5 processing error: {e}")
        
        # Check for pending note content
        if self.pending_note_content:
            return self._handle_note_content(user_input)
        
        # Note-taking commands (must include bot name)
        if self.notes:
            note_result = self._handle_note_commands(user_input, user_lower)
            if note_result:
                return note_result
        
        # Music playback — Seven picks and plays songs
        if self.music_player and self.music_player.available:
            music_result = self._handle_music_request(user_input, user_lower)
            if music_result:
                return music_result
        
        # Timer / Alarm / Pomodoro
        if self.timer_system:
            timer_result = self._handle_timer_request(user_input, user_lower)
            if timer_result:
                return timer_result
        
        # SSH / Server management
        if self.ssh_manager and self.ssh_manager.available:
            ssh_result = self._handle_ssh_request(user_input, user_lower)
            if ssh_result:
                return ssh_result
        
        # Screen control / vision
        if self.screen_control and self.screen_control.available:
            screen_result = self._handle_screen_request(user_input, user_lower)
            if screen_result:
                return screen_result
        
        # Email
        if self.email_checker:
            email_result = self._handle_email_request(user_input, user_lower)
            if email_result:
                return email_result
        
        # Clipboard
        if self.clipboard and self.clipboard.available:
            clip_result = self._handle_clipboard_request(user_input, user_lower)
            if clip_result:
                return clip_result
        
        # Document reading (PDF, etc.)
        if self.doc_reader:
            doc_result = self._handle_document_request(user_input, user_lower)
            if doc_result:
                return doc_result
        
        # System monitor queries
        if self.system_monitor and self.system_monitor.available:
            sys_result = self._handle_system_monitor_request(user_input, user_lower)
            if sys_result:
                return sys_result
        
        # Code generation / scripting
        if self.scripting:
            script_result = self._handle_scripting_request(user_input, user_lower)
            if script_result:
                return script_result
        
        # Ollama model management
        if self.model_manager:
            model_result = self._handle_model_request(user_input, user_lower)
            if model_result:
                return model_result
        
        # Database management — SQL queries, exploration, analysis
        if self.database:
            db_result = self._handle_database_request(user_input, user_lower)
            if db_result:
                return db_result
        
        # API Explorer — REST API calls, discovery, analysis
        if self.api_explorer and self.api_explorer.available:
            api_result = self._handle_api_request(user_input, user_lower)
            if api_result:
                return api_result
        
        # IRC commands — Seven controls her IRC connections via voice/text
        if self.irc_client:
            irc_result = self._handle_irc_request(user_input, user_lower)
            if irc_result:
                return irc_result
        
        # Telegram commands — Seven controls her Telegram connection
        if self.telegram_client:
            tg_result = self._handle_telegram_request(user_input, user_lower)
            if tg_result:
                return tg_result
        
        # WhatsApp commands — Seven controls her WhatsApp connection
        if self.whatsapp_client:
            wa_result = self._handle_whatsapp_request(user_input, user_lower)
            if wa_result:
                return wa_result
        
        # Phase 2-4 Enhancement Commands
        # Tasks and Reminders
        if self.tasks:
            task_result = enhancement_commands.handle_task_commands(self, user_input, user_lower)
            if task_result:
                return task_result
        
        # Diary and Insights
        if self.diary:
            diary_result = enhancement_commands.handle_diary_commands(self, user_input, user_lower)
            if diary_result:
                return diary_result
        
        # Project Tracking
        if self.projects:
            project_result = enhancement_commands.handle_project_commands(self, user_input, user_lower)
            if project_result:
                return project_result
        
        # Storytelling
        if self.storyteller:
            story_result = enhancement_commands.handle_storytelling_commands(self, user_input, user_lower)
            if story_result:
                return story_result
        
        # Special Dates
        if self.special_dates:
            dates_result = enhancement_commands.handle_special_dates_commands(self, user_input, user_lower)
            if dates_result:
                return dates_result
        
        # Message Drafting
        if self.message_drafter:
            draft_result = enhancement_commands.handle_message_drafting_commands(self, user_input, user_lower)
            if draft_result:
                return draft_result
        
        # Phase 4: Identity System Commands
        if self.identity_mgr and config.ENABLE_IDENTITY_SYSTEM:
            identity_result = identity_commands.handle_identity_commands(self, user_input, user_lower)
            if identity_result:
                return identity_result
        
        # Name queries
        if "what is your name" in user_lower or "what's your name" in user_lower:
            return f"My name is {self.bot_name}."
        
        if "change your name" in user_lower:
            return self._handle_name_change()
        
        # Capabilities
        if "what can you do" in user_lower or "help" in user_lower:
            return self._list_all_capabilities()
        
        # File operations
        if self.file_manager:
            file_result = self._handle_file_operations(user_input, user_lower)
            if file_result:
                return file_result
        
        # Code execution
        if self.code_executor:
            code_result = self._handle_code_execution(user_input, user_lower)
            if code_result:
                return code_result
        
        # Enhanced command processing
        if self.cmd_processor:
            cmd_result = self._handle_enhanced_commands(user_input, user_lower)
            if cmd_result:
                return cmd_result
        
        # Clawdbot integration - detect if task should go to Clawdbot
        if self.clawdbot and config.CLAWDBOT_AUTO_DETECT:
            clawdbot_intent = detect_clawdbot_intent(user_input)
            if clawdbot_intent:
                try:
                    self.logger.info(f"Routing to Clawdbot: {user_input[:50]}")
                    clawdbot_response = self.clawdbot.process_task(user_input)
                    if clawdbot_response:
                        return clawdbot_response
                    else:
                        return "I tried to process that through Clawdbot, but didn't get a response. Let me try another way."
                except Exception as e:
                    self.logger.error(f"Clawdbot error: {e}")
                    # Fall through to regular processing
        
        # Conversation summarization
        if "summarize" in user_lower and ("conversation" in user_lower or "discussion" in user_lower):
            return self._summarize_conversation()
        
        # Jokes/Facts
        if "tell me a joke" in user_lower:
            return get_random_joke()
        if "tell me a fact" in user_lower:
            return get_random_fact()
        
        # System/OS queries - direct answer from OS awareness
        if self.os_awareness:
            os_triggers = ['system info', 'what system', 'what os', 'my computer', 'cpu', 'ram', 'disk space',
                           'running processes', 'what programs', 'network info', 'ip address', 'system status']
            if any(t in user_lower for t in os_triggers):
                try:
                    env_summary = self.os_awareness.get_environment_summary()
                    # Inject as system data for natural LLM response
                    user_input = f"{user_input}\n\n[SYSTEM_DATA: {env_summary}]"
                    return self._ask_ollama_enhanced(user_input)
                except Exception as e:
                    self.logger.warning(f"OS query error: {e}")
        
        # Web search - use search_and_read for full content, inject into LLM
        search_query = extract_search_query(user_input)
        if search_query:
            try:
                # Try search_and_read for full web content
                web_results = search_and_read(search_query, num_results=2)
                if web_results and "[ERROR]" not in web_results:
                    user_input = f"{user_input}\n\n[SYSTEM_DATA: {web_results[:3000]}]"
                    return self._ask_ollama_enhanced(user_input)
            except Exception as e:
                self.logger.warning(f"search_and_read failed: {e}")
            # Fallback to URL-only search
            return google_search(search_query)
        
        # Calendar
        if self.calendar and ("calendar" in user_lower or "schedule" in user_lower):
            if "list" in user_lower or "show" in user_lower:
                return self.calendar.list_upcoming_events()
            else:
                event_details = parse_event_from_text(user_input)
                if event_details:
                    return self.calendar.create_event(event_details)
        
        # System commands
        if self.commands:
            command_parsed = parse_command_from_text(user_input)
            if command_parsed:
                action = command_parsed["action"]
                target = command_parsed["target"]
                args = command_parsed["args"]
                
                if action == "open_program":
                    return self.commands.open_program(target, args)
                elif action == "close_program":
                    return self.commands.close_program(target)
                elif action == "kill_program":
                    return self.commands.kill_program(target)
                elif action == "list_programs":
                    running = self.commands.list_running_programs()
                    if running:
                        return f"Currently running: {', '.join(running)}"
                    else:
                        return "No common programs are currently running."
                elif action == "execute_command":
                    return self.commands.execute_safe_command(args, target)
        
        # Dynamic command execution — Seven runs arbitrary commands when asked
        if self.dynamic_commands:
            cmd_result = self._try_dynamic_command(user_input, user_lower)
            if cmd_result:
                # Inject command result as system data for natural LLM response
                user_input = f"{user_input}\n\n[SYSTEM_DATA: {cmd_result}]"
                return self._ask_ollama_enhanced(user_input)
        
        # Use enhanced Ollama response
        return self._ask_ollama_enhanced(user_input)
    
    def _handle_music_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """
        Handle music playback requests.
        
        Seven picks songs intelligently:
        - Explicit: "play Bohemian Rhapsody" → searches that exact song
        - Contextual: "play me something special" → Ollama picks based on mood/context
        - Control: "stop music", "pause", "resume", "what's playing"
        """
        
        # Control commands
        if any(phrase in user_lower for phrase in ["stop music", "stop the music", "stop playing", "music off"]):
            return self.music_player.stop()
        
        if any(phrase in user_lower for phrase in ["pause music", "pause the music"]):
            return self.music_player.pause()
        
        if any(phrase in user_lower for phrase in ["resume music", "unpause", "continue music", "continue playing"]):
            return self.music_player.resume()
        
        if any(phrase in user_lower for phrase in ["what's playing", "what is playing", "what song", "now playing"]):
            playing = self.music_player.get_now_playing()
            return f"Currently playing: {playing}" if playing else "Nothing is playing right now."
        
        # Play requests
        play_patterns = [
            r"(?:play|put on|queue|listen to)\s+(?:me\s+)?(?:the\s+)?(?:song\s+)?['\"](.+?)['\"]",
            r"(?:play|put on|queue|listen to)\s+(?:me\s+)?(?:the\s+song\s+)?(.+?)(?:\s+(?:for me|please))?$",
            r"(?:can you |could you )?(?:play|put on)\s+(?:me\s+)?(.+)",
        ]
        
        is_music_request = any(phrase in user_lower for phrase in [
            "play me", "play a song", "play some", "play music",
            "put on some", "put on a song", "play something",
            "listen to", "play me a", "sing me",
        ])
        
        if not is_music_request:
            return None
        
        # Extract what to play
        query = None
        for pattern in play_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                break
        
        # Check if the request is vague/contextual (Seven picks the song)
        vague_requests = [
            "something", "a song", "some music", "anything", "something special",
            "something nice", "something good", "something relaxing", "something upbeat",
            "something happy", "something sad", "a special song", "music",
        ]
        
        is_vague = not query or any(v in (query or "").lower() for v in vague_requests)
        
        if is_vague and self.ollama:
            # Seven THINKS about what to play based on context
            try:
                context_bits = []
                # Current emotion
                context_bits.append(f"Seven's current mood: {self.current_emotion.value}")
                # Time of day
                from datetime import datetime
                hour = datetime.now().hour
                time_ctx = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 21 else "late night"
                context_bits.append(f"Time: {time_ctx}")
                # What user asked
                context_bits.append(f"User said: {user_input}")
                # Recent conversation
                if self.memory:
                    recent = self.memory.get_context_for_llm(max_turns=2)
                    if recent:
                        context_bits.append(f"Recent conversation: {recent[:200]}")
                
                ctx = ". ".join(context_bits)
                
                song_pick = self.ollama.generate(
                    f"""Context: {ctx}

Pick ONE specific real song (title and artist) that fits this moment perfectly. Consider the mood, time of day, and what the user asked for.

Respond with ONLY: song title - artist name
Nothing else. No quotes, no explanation.""",
                    system_message="You are Seven's music taste. Pick real, well-known songs. Be specific — give exact song title and artist. Match the vibe.",
                    temperature=0.9,
                    max_tokens=30
                )
                
                if song_pick and len(song_pick.strip()) > 3:
                    query = song_pick.strip().strip('"').strip("'")
                    self.logger.info(f"Seven picked: {query}")
            except Exception as e:
                self.logger.warning(f"Song pick failed: {e}")
        
        if not query:
            query = "feel good song"  # Ultimate fallback
        
        # Search and play
        result = self.music_player.search_and_play(query)
        
        if result['success']:
            return f"♪ {result['message']}"
        else:
            return result['message']
    
    # ============ INTEGRATION HANDLERS ============
    
    def _handle_timer_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle timer, alarm, and pomodoro requests"""
        
        # Pomodoro
        if any(p in user_lower for p in ["pomodoro", "work session", "focus session"]):
            if "stop" in user_lower or "cancel" in user_lower:
                return self.timer_system.stop_pomodoro()
            return self.timer_system.start_pomodoro()
        
        # List timers
        if any(p in user_lower for p in ["list timer", "active timer", "my timer", "what timer"]):
            return self.timer_system.list_timers()
        
        # Cancel timer
        if any(p in user_lower for p in ["cancel timer", "stop timer", "remove timer"]):
            return self.timer_system.cancel_timer(label=user_input.split("timer")[-1].strip() or None)
        
        # Set alarm: "alarm at 7am", "wake me up at 7:30"
        alarm_triggers = ["alarm", "wake me"]
        if any(t in user_lower for t in alarm_triggers):
            from integrations.timer_system import TimerSystem
            parsed_time = TimerSystem.parse_time(user_input)
            if parsed_time:
                label = "Alarm"
                if "wake" in user_lower:
                    label = "Wake up!"
                return self.timer_system.set_alarm(parsed_time[0], parsed_time[1], label)
        
        # Set timer: "timer for 20 minutes", "set a timer for 1 hour"
        timer_triggers = ["set a timer", "set timer", "timer for", "remind me in", "in \\d+ min"]
        if any(re.search(t, user_lower) for t in timer_triggers):
            from integrations.timer_system import TimerSystem
            duration = TimerSystem.parse_duration(user_input)
            if duration:
                label = "Timer"
                # Try to extract label
                label_match = re.search(r"(?:for|called|named)\s+(.+?)(?:\s+for|\s*$)", user_input, re.IGNORECASE)
                if label_match and not label_match.group(1).strip().isdigit():
                    label = label_match.group(1).strip()
                return self.timer_system.set_timer(duration, label)
        
        return None
    
    def _handle_ssh_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle SSH / server management requests"""
        
        # List servers
        if any(p in user_lower for p in ["list server", "my server", "show server"]):
            return self.ssh_manager.list_servers()
        
        # Add server
        if "add server" in user_lower or "configure server" in user_lower:
            return "To add a server, I need: name, host, username, and password or key file. Example:\n" \
                   "  'add server myserver host=1.2.3.4 user=root password=secret'\n" \
                   "Or provide an SSH key file path instead of password."
        
        # Server health
        if any(p in user_lower for p in ["server health", "server status", "check server"]):
            if not self.ssh_manager.servers:
                return "No servers configured yet."
            name = list(self.ssh_manager.servers.keys())[0]
            # Check if a specific server was mentioned
            for sname in self.ssh_manager.servers:
                if sname.lower() in user_lower:
                    name = sname
                    break
            health = self.ssh_manager.check_server_health(name)
            lines = [f"Server '{name}' health:"]
            for k, v in health.items():
                lines.append(f"  {k}: {v}")
            return "\n".join(lines)
        
        # Check websites
        if any(p in user_lower for p in ["check website", "my website", "website status", "sites running"]):
            if not self.ssh_manager.servers:
                return "No servers configured."
            name = list(self.ssh_manager.servers.keys())[0]
            for sname in self.ssh_manager.servers:
                if sname.lower() in user_lower:
                    name = sname
                    break
            result = self.ssh_manager.check_websites(name)
            return result.get('stdout', result.get('message', 'No output'))
        
        # Run command on server: "ssh run ls -la" or "on server run ..."
        ssh_cmd_patterns = [
            r"(?:ssh|server)\s+(?:run|exec(?:ute)?)\s+(.+)",
            r"(?:on|at)\s+(?:the\s+)?server\s+(?:run|exec(?:ute)?)\s+(.+)",
            r"run\s+on\s+(?:the\s+)?server\s+(.+)",
        ]
        for pattern in ssh_cmd_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                cmd = match.group(1).strip()
                if not self.ssh_manager.servers:
                    return "No servers configured."
                name = list(self.ssh_manager.servers.keys())[0]
                result = self.ssh_manager.run_command(name, cmd)
                output = result.get('stdout', '') or result.get('stderr', '') or result.get('message', '')
                # Pass through Ollama for natural explanation
                if self.ollama and output:
                    explained = self.ollama.generate(
                        f"The user asked to run '{cmd}' on their Linux server. Here's the output:\n\n{output[:2000]}\n\nExplain this output conversationally. Be helpful.",
                        temperature=0.3, max_tokens=200
                    )
                    return explained if explained else output[:2000]
                return output[:2000]
        
        return None
    
    def _handle_screen_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle screen/vision/mouse/keyboard requests"""
        
        # Screenshot + analyze
        if any(p in user_lower for p in ["see my screen", "look at my screen", "what's on my screen",
                                          "screenshot", "what am i working on", "see what i'm doing"]):
            question = None
            if "?" in user_input:
                question = user_input
            return self.screen_control.see_screen(question)
        
        # Mouse position
        if "mouse position" in user_lower or "where is my mouse" in user_lower:
            return self.screen_control.get_mouse_position()
        
        # Screen size
        if "screen size" in user_lower or "resolution" in user_lower:
            return self.screen_control.get_screen_size()
        
        # Click (requires coordinates — dangerous, so we don't auto-detect)
        # Type text
        if any(p in user_lower for p in ["type this", "type for me", "type the following"]):
            import re
            match = re.search(r"type\s+(?:this|for me|the following)?[:\s]+(.+)", user_input, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                return self.screen_control.type_text(text)
        
        return None
    
    def _handle_email_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle email checking requests"""
        
        # Check email
        if any(p in user_lower for p in ["check email", "check my email", "any email", "new email",
                                          "do i have mail", "any mail", "check mail", "unread email"]):
            result = self.email_checker.check_unread()
            if not result['success']:
                if "No email accounts" in result['message']:
                    return "No email accounts configured yet. To set one up, say:\n" \
                           "  'add email account gmail myemail@gmail.com app-password'\n" \
                           "For Gmail, you'll need an App Password (Google Account → Security → App passwords)."
                return result['message']
            
            if result['count'] == 0:
                return "No unread emails. Your inbox is clean!"
            
            # Summarize through Ollama
            summary = self.email_checker.get_summary()
            if self.ollama and result['count'] > 0:
                natural = self.ollama.generate(
                    f"Summarize these emails conversationally:\n\n{summary}",
                    system_message="Be concise and natural. Highlight anything that looks urgent.",
                    temperature=0.3, max_tokens=150
                )
                return natural if natural else summary
            return summary
        
        # Add email account
        if any(p in user_lower for p in ["add email", "configure email", "setup email"]):
            return "To add an email account:\n" \
                   "  'add email gmail myemail@gmail.com app-password'\n" \
                   "  'add email ms365 myemail@outlook.com password'\n\n" \
                   "For Gmail: Use an App Password (not your regular password).\n" \
                   "Go to: Google Account → Security → 2-Step Verification → App passwords"
        
        return None
    
    def _handle_clipboard_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle clipboard-related requests"""
        
        if any(p in user_lower for p in ["what's on my clipboard", "clipboard content", "show clipboard",
                                          "what did i copy", "what's copied"]):
            return self.clipboard.analyze_clipboard()
        
        if any(p in user_lower for p in ["explain clipboard", "explain what i copied"]):
            return self.clipboard.process_clipboard_with_ollama("explain")
        
        if any(p in user_lower for p in ["fix clipboard", "fix what i copied", "fix this code"]):
            return self.clipboard.process_clipboard_with_ollama("fix")
        
        if any(p in user_lower for p in ["summarize clipboard", "summarize what i copied"]):
            return self.clipboard.process_clipboard_with_ollama("summarize")
        
        if any(p in user_lower for p in ["translate clipboard", "translate what i copied"]):
            return self.clipboard.process_clipboard_with_ollama("translate")
        
        return None
    
    def _handle_document_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle document/PDF reading requests"""
        
        # Pattern: "read/summarize/open [filepath]"
        doc_patterns = [
            r"(?:read|summarize|open|analyze)\s+(?:the\s+)?(?:file\s+|document\s+|pdf\s+)?['\"]?([A-Za-z]:\\[^\s'\"]+|/[^\s'\"]+)['\"]?",
            r"(?:read|summarize|open|analyze)\s+(?:the\s+)?(?:file\s+|document\s+|pdf\s+)?([^\s]+\.(?:pdf|txt|csv|json|md|log|xml))",
        ]
        
        for pattern in doc_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip().strip("'\"")
                if "summarize" in user_lower:
                    return self.doc_reader.summarize_document(filepath)
                else:
                    result = self.doc_reader.read_document(filepath)
                    if result['success']:
                        text = result['text']
                        return f"Contents of {filepath} ({result.get('pages', '?')} pages, {result.get('total_chars', len(text))} chars):\n\n{text[:3000]}"
                    return result['message']
        
        return None
    
    def _handle_system_monitor_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle system monitoring queries"""
        
        if any(p in user_lower for p in ["system status", "system info", "pc status", "computer status",
                                          "how's my pc", "how is my computer"]):
            summary = self.system_monitor.get_summary()
            if self.ollama:
                natural = self.ollama.generate(
                    f"System status:\n{summary}\n\nExplain this conversationally. Flag anything concerning.",
                    temperature=0.3, max_tokens=150
                )
                return natural if natural else summary
            return summary
        
        if any(p in user_lower for p in ["top ram", "ram hog", "memory hog", "what's using ram",
                                          "what is using memory"]):
            return self.system_monitor.get_top_ram_hogs()
        
        if any(p in user_lower for p in ["top cpu", "cpu hog", "what's using cpu"]):
            return self.system_monitor.get_top_cpu_hogs()
        
        if any(p in user_lower for p in ["disk space", "disk usage", "how much space",
                                          "storage space", "drive space"]):
            snapshot = self.system_monitor.get_snapshot()
            lines = ["Disk usage:"]
            for mount, info in snapshot.get('disk', {}).items():
                lines.append(f"  {mount}: {info['used_gb']}GB / {info['total_gb']}GB ({info['percent']}% used, {info['free_gb']}GB free)")
            return "\n".join(lines)
        
        return None
    
    def _handle_scripting_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle code generation and script execution requests"""
        
        # List tools
        if any(p in user_lower for p in ["list tools", "my tools", "seven's tools", "tool library"]):
            return self.scripting.list_tools()
        
        # Write code: "write a python script that...", "code me a...", "create a script..."
        code_patterns = [
            r"(?:write|create|make|code|generate)\s+(?:me\s+)?(?:a\s+)?(?:python|vb\.?net|c#|csharp)?\s*(?:script|program|code|tool)\s+(?:that\s+|to\s+|for\s+)?(.+)",
            r"(?:write|create|code)\s+(?:me\s+)?(?:some\s+)?(?:python|vb\.?net|c#|csharp)\s+(?:code\s+)?(?:that\s+|to\s+|for\s+)?(.+)",
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                task = match.group(1).strip()
                # Detect language
                lang = 'python'
                if any(l in user_lower for l in ['vb.net', 'vbnet', 'visual basic']):
                    lang = 'vbnet'
                elif any(l in user_lower for l in ['c#', 'csharp', 'c sharp']):
                    lang = 'csharp'
                
                result = self.scripting.generate_script(task, language=lang)
                if result['success']:
                    code = result['code']
                    filepath = result.get('filepath', 'not saved')
                    preview = code[:500] + ('...' if len(code) > 500 else '')
                    response = f"Here's the {lang} code:\n\n{preview}\n\nSaved to: {filepath}"
                    if lang == 'python':
                        response += "\n\nWant me to run it?"
                    return response
                return result['message']
        
        # Run script: "run the script", "execute it"
        if any(p in user_lower for p in ["run the script", "run it", "execute it", "run that"]):
            if self.scripting.tools:
                latest = list(self.scripting.tools.values())[-1]
                result = self.scripting.run_script(script_path=latest['filepath'])
                if result['success']:
                    return f"Script output:\n{result['stdout'][:2000]}"
                return f"Script failed:\n{result.get('stderr', result.get('message', 'unknown error'))[:1000]}"
        
        # Create/edit/delete files
        if any(p in user_lower for p in ["create file", "make file", "new file"]):
            match = re.search(r"(?:create|make|new)\s+file\s+['\"]?(.+?)['\"]?\s*$", user_input, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                return self.scripting.create_file(filepath, "")
        
        if "delete file" in user_lower or "remove file" in user_lower:
            match = re.search(r"(?:delete|remove)\s+file\s+['\"]?(.+?)['\"]?\s*$", user_input, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                return f"Are you sure you want to delete {filepath}? This could be dangerous. Say 'yes delete {filepath}' to confirm."
        
        if "yes delete" in user_lower:
            match = re.search(r"yes delete\s+['\"]?(.+?)['\"]?\s*$", user_input, re.IGNORECASE)
            if match:
                return self.scripting.delete_file(match.group(1).strip())
        
        return None
    
    def _handle_model_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle Ollama model management requests"""
        
        # List models
        if any(p in user_lower for p in ["list model", "my model", "installed model", "what model",
                                          "which model", "available model"]):
            return self.model_manager.list_models()
        
        # Pull model
        match = re.search(r"(?:pull|download|install)\s+(?:model\s+)?(\S+)", user_input, re.IGNORECASE)
        if match and any(p in user_lower for p in ["pull", "download model", "install model"]):
            model = match.group(1).strip()
            return self.model_manager.pull_model(model)
        
        # Remove model
        match = re.search(r"(?:remove|delete|uninstall)\s+(?:model\s+)?(\S+)", user_input, re.IGNORECASE)
        if match and any(p in user_lower for p in ["remove model", "delete model", "uninstall model"]):
            model = match.group(1).strip()
            return self.model_manager.remove_model(model)
        
        # Switch model
        match = re.search(r"(?:switch|use|change)\s+(?:to\s+)?(?:model\s+)?(\S+)", user_input, re.IGNORECASE)
        if match and any(p in user_lower for p in ["switch model", "switch to", "use model", "change model"]):
            model = match.group(1).strip()
            return self.model_manager.switch_model(model)
        
        # Model disk usage
        if any(p in user_lower for p in ["model disk", "model space", "model size"]):
            return self.model_manager.check_disk_usage()
        
        return None
    
    def _handle_database_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle database connection, exploration, query, and analysis requests"""
        
        # List connections
        if any(p in user_lower for p in ["list database", "my database", "show database", "database connection"]):
            return self.database.list_connections()
        
        # Database status
        if any(p in user_lower for p in ["database status", "db status"]):
            return self.database.get_status()
        
        # Connect to database
        if any(p in user_lower for p in ["connect to database", "connect to db", "connect database"]):
            match = re.search(r"connect\s+(?:to\s+)?(?:database\s+|db\s+)?['\"]?(\w+)['\"]?", user_input, re.IGNORECASE)
            if match:
                return self.database.connect(match.group(1).strip())
            return "Which database? Use 'list databases' to see saved connections."
        
        # Quick connect SQLite
        match = re.search(r"(?:open|connect|load)\s+(?:sqlite\s+)?(?:database\s+|db\s+)?['\"]?([A-Za-z]:\\[^\s'\"]+\.(?:db|sqlite|sqlite3))['\"]?", user_input, re.IGNORECASE)
        if match:
            return self.database.quick_connect_sqlite(match.group(1).strip())
        
        # Quick connect MySQL
        match = re.search(r"connect\s+(?:to\s+)?mysql\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(\d+))?", user_input, re.IGNORECASE)
        if match:
            return self.database.quick_connect_mysql(
                host=match.group(1), database=match.group(2),
                username=match.group(3), password=match.group(4),
                port=int(match.group(5) or 3306)
            )
        
        # Disconnect
        if any(p in user_lower for p in ["disconnect database", "disconnect db", "close database"]):
            return self.database.disconnect()
        
        # Explore database
        if any(p in user_lower for p in ["explore database", "explore db", "show tables", "list tables",
                                          "what tables", "database structure", "db structure"]):
            return self.database.explore_database()
        
        # Describe table
        match = re.search(r"(?:describe|explain|show)\s+(?:table\s+)?['\"]?(\w+)['\"]?", user_input, re.IGNORECASE)
        if match and any(p in user_lower for p in ["describe", "explain table", "show table", "table structure"]):
            return self.database.describe_table(match.group(1).strip())
        
        # Analyze table
        match = re.search(r"(?:analyze|analyse)\s+(?:table\s+)?['\"]?(\w+)['\"]?", user_input, re.IGNORECASE)
        if match:
            return self.database.analyze_table(match.group(1).strip())
        
        # Sample data
        match = re.search(r"(?:sample|preview|peek)\s+(?:data\s+(?:from\s+)?)?(?:table\s+)?['\"]?(\w+)['\"]?", user_input, re.IGNORECASE)
        if match:
            return self.database.sample_data(match.group(1).strip())
        
        # Run SQL directly: "query: SELECT ...", "sql: SELECT ...", "run query ..."
        match = re.search(r"(?:query|sql|run query|execute sql|run sql)[:\s]+(.+)", user_input, re.IGNORECASE | re.DOTALL)
        if match:
            sql = match.group(1).strip()
            result = self.database.run_query(sql)
            if result['success'] and result.get('rows'):
                output = self.database._format_results_table(result['columns'], result['rows'])
                return f"{result['message']}\n\n{output}"
            return result['message']
        
        # Natural language query: "ask database ...", "ask db ...", "query the database ..."
        if any(p in user_lower for p in ["ask database", "ask db", "ask the database",
                                          "query the database", "query the db"]):
            question = re.sub(r"^(?:ask|query)\s+(?:the\s+)?(?:database|db)\s+", "", user_input, flags=re.IGNORECASE).strip()
            if question:
                return self.database.natural_query(question)
        
        # Export
        if "export" in user_lower and any(p in user_lower for p in ["csv", "json"]):
            match = re.search(r"export\s+(.+?)\s+(?:to|as)\s+(csv|json)", user_input, re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                fmt = match.group(2).lower()
                if fmt == 'csv':
                    return self.database.export_to_csv(sql)
                return self.database.export_to_json(sql)
        
        return None
    
    def _handle_api_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle REST API exploration, calling, and analysis requests"""
        
        # List saved APIs
        if any(p in user_lower for p in ["list api", "my api", "saved api", "show api"]):
            return self.api_explorer.list_apis()
        
        # API status
        if "api status" in user_lower:
            return self.api_explorer.get_status()
        
        # Add API
        match = re.search(r"add api\s+(\S+)\s+(\S+)", user_input, re.IGNORECASE)
        if match:
            name = match.group(1)
            url = match.group(2)
            return self.api_explorer.add_api(name, url)
        
        # Remove API
        match = re.search(r"remove api\s+(\S+)", user_input, re.IGNORECASE)
        if match:
            return self.api_explorer.remove_api(match.group(1))
        
        # Check API health
        if any(p in user_lower for p in ["check api", "api health", "api up", "api status"]):
            match = re.search(r"check\s+(?:api\s+)?(\S+)", user_input, re.IGNORECASE)
            if match:
                target = match.group(1)
                if target in self.api_explorer.apis:
                    return self.api_explorer.check_api_health(api_name=target)
                if target.startswith(('http://', 'https://')):
                    return self.api_explorer.check_api_health(url=target)
            return self.api_explorer.check_all_apis()
        
        # Explore API endpoint
        if any(p in user_lower for p in ["explore api", "explore endpoint"]):
            match = re.search(r"explore\s+(?:api\s+|endpoint\s+)?(\S+)", user_input, re.IGNORECASE)
            if match:
                target = match.group(1)
                if target in self.api_explorer.apis:
                    return self.api_explorer.explore_api(api_name=target)
                return self.api_explorer.explore_endpoint(target)
        
        # Direct API call: "GET https://...", "POST https://..."
        match = re.search(r"^(GET|POST|PUT|DELETE)\s+(https?://\S+)", user_input, re.IGNORECASE)
        if match:
            method = match.group(1).upper()
            url = match.group(2)
            if method == 'GET':
                result = self.api_explorer.get(url)
            elif method == 'POST':
                result = self.api_explorer.post(url)
            elif method == 'PUT':
                result = self.api_explorer.put(url)
            elif method == 'DELETE':
                result = self.api_explorer.delete(url)
            else:
                return None
            
            if result['success']:
                return self.api_explorer.explore_endpoint(url)
            return f"API call failed: {result.get('error', result.get('status_code'))}"
        
        # Natural language API call: "fetch ...", "call api ...", "get data from ..."
        if any(p in user_lower for p in ["fetch", "call api", "get data from", "hit the api",
                                          "api call", "make a request"]):
            return self.api_explorer.natural_call(user_input)
        
        return None
    
    def _handle_irc_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle IRC commands — Seven controls her IRC connections via voice/text."""
        
        # Only trigger on IRC-related keywords
        irc_keywords = ["irc", "channel", "join #", "part #", "leave #"]
        if not any(kw in user_lower for kw in irc_keywords):
            return None
        
        # IRC status
        if any(p in user_lower for p in ["irc status", "irc connections", "irc servers"]):
            return self.irc_client.get_status()
        
        # Start/stop IRC
        if "start irc" in user_lower or "connect irc" in user_lower or "irc connect" in user_lower:
            return self.irc_client.start()
        if "stop irc" in user_lower or "disconnect irc" in user_lower or "irc disconnect" in user_lower:
            return self.irc_client.stop()
        
        # Join channel: "join #gaming" or "join #gaming on submitjoy"
        match = re.search(r"join\s+(#\S+)(?:\s+on\s+(\S+))?", user_input, re.IGNORECASE)
        if match:
            channel = match.group(1)
            server = match.group(2) if match.group(2) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            if server:
                return self.irc_client.join_channel(server, channel)
            return "No IRC servers configured"
        
        # Leave/part channel: "leave #gaming" or "part #gaming on submitjoy"
        match = re.search(r"(?:leave|part)\s+(#\S+)(?:\s+on\s+(\S+))?", user_input, re.IGNORECASE)
        if match:
            channel = match.group(1)
            server = match.group(2) if match.group(2) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            if server:
                return self.irc_client.part_channel(server, channel)
            return "No IRC servers configured"
        
        # Send PM: "irc message Duke hello" or "irc pm Duke on submitjoy hey there"
        match = re.search(r"irc\s+(?:message|pm|msg|tell)\s+(\S+?)(?:\s+on\s+(\S+))?\s+(.+)", user_input, re.IGNORECASE)
        if match:
            target = match.group(1)
            server = match.group(2) if match.group(2) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            message = match.group(3)
            if server:
                return self.irc_client.send_pm(server, target, message)
            return "No IRC servers configured"
        
        # Send raw command: "irc raw submitjoy WHOIS Duke"
        match = re.search(r"irc\s+raw\s+(\S+)\s+(.+)", user_input, re.IGNORECASE)
        if match:
            server = match.group(1)
            command = match.group(2)
            return self.irc_client.send_raw(server, command)
        
        # OPER up: "irc oper" or "irc oper on submitjoy"
        match = re.search(r"irc\s+oper(?:\s+on\s+(\S+))?", user_input, re.IGNORECASE)
        if match:
            server = match.group(1) if match.group(1) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            if server:
                return self.irc_client.oper_up(server)
            return "No IRC servers configured"
        
        # Identify: "irc identify" or "irc identify on submitjoy"
        match = re.search(r"irc\s+identify(?:\s+on\s+(\S+))?", user_input, re.IGNORECASE)
        if match:
            server = match.group(1) if match.group(1) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            if server:
                return self.irc_client.identify(server)
            return "No IRC servers configured"
        
        # List channels: "irc channels" or "list irc channels on submitjoy"
        match = re.search(r"(?:irc|list)\s+channels?(?:\s+on\s+(\S+))?", user_input, re.IGNORECASE)
        if match:
            server = match.group(1) if match.group(1) else list(self.irc_client.servers.keys())[0] if self.irc_client.servers else None
            if server:
                return self.irc_client.list_channels(server)
            return "No IRC servers configured"
        
        # Add server: "add irc server myserver host.com 6667"
        match = re.search(r"add\s+irc\s+server\s+(\S+)\s+(\S+)(?:\s+(\d+))?", user_input, re.IGNORECASE)
        if match:
            name = match.group(1)
            host = match.group(2)
            port = int(match.group(3)) if match.group(3) else 6667
            return self.irc_client.add_server(name=name, host=host, port=port)
        
        return None
    
    def _handle_telegram_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle Telegram commands — Seven controls her Telegram connection via voice/text."""
        
        if "telegram" not in user_lower:
            return None
        
        # Status
        if any(p in user_lower for p in ["telegram status", "telegram connection"]):
            return self.telegram_client.get_status()
        
        # Start/stop
        if "start telegram" in user_lower or "connect telegram" in user_lower:
            return self.telegram_client.start()
        if "stop telegram" in user_lower or "disconnect telegram" in user_lower:
            return self.telegram_client.stop()
        
        # Configure: "configure telegram 12345 abcdef123 +27..."
        match = re.search(r"configure\s+telegram\s+(\d+)\s+(\S+)(?:\s+(\+?\S+))?", user_input, re.IGNORECASE)
        if match:
            api_id = int(match.group(1))
            api_hash = match.group(2)
            phone = match.group(3) if match.group(3) else None
            return self.telegram_client.configure(api_id, api_hash, phone)
        
        # Send message: "telegram message @username hello there"
        match = re.search(r"telegram\s+(?:message|msg|send|tell)\s+(\S+)\s+(.+)", user_input, re.IGNORECASE)
        if match:
            target = match.group(1)
            message = match.group(2)
            return self.telegram_client.send_message(target, message)
        
        # List chats
        if any(p in user_lower for p in ["telegram chats", "telegram list", "list telegram"]):
            return self.telegram_client.list_chats()
        
        # Unread
        if any(p in user_lower for p in ["telegram unread", "unread telegram"]):
            return self.telegram_client.get_unread()
        
        # Toggle DM replies
        if "telegram dm" in user_lower:
            if "off" in user_lower or "disable" in user_lower:
                return self.telegram_client.set_respond_dms(False)
            return self.telegram_client.set_respond_dms(True)
        
        return None
    
    def _handle_whatsapp_request(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle WhatsApp commands — Seven controls her WhatsApp connection via voice/text."""
        
        if "whatsapp" not in user_lower:
            return None
        
        # Status
        if any(p in user_lower for p in ["whatsapp status", "whatsapp connection"]):
            return self.whatsapp_client.get_status()
        
        # Start/stop
        if "start whatsapp" in user_lower or "connect whatsapp" in user_lower or "open whatsapp" in user_lower:
            return self.whatsapp_client.start()
        if "stop whatsapp" in user_lower or "disconnect whatsapp" in user_lower or "close whatsapp" in user_lower:
            return self.whatsapp_client.stop()
        
        # Send message: "whatsapp message John hello there"
        match = re.search(r"whatsapp\s+(?:message|msg|send|tell)\s+(.+?)\s{2,}(.+)", user_input, re.IGNORECASE)
        if match:
            contact = match.group(1).strip()
            message = match.group(2).strip()
            return self.whatsapp_client.send_to_contact(contact, message)
        
        # Open chat: "whatsapp open John"
        match = re.search(r"whatsapp\s+open\s+(.+)", user_input, re.IGNORECASE)
        if match:
            return self.whatsapp_client.open_chat(match.group(1).strip())
        
        # List chats
        if any(p in user_lower for p in ["whatsapp chats", "whatsapp list", "list whatsapp"]):
            return self.whatsapp_client.list_chats()
        
        # Focus WhatsApp
        if any(p in user_lower for p in ["whatsapp focus", "focus whatsapp", "show whatsapp", "bring whatsapp"]):
            return self.whatsapp_client.bring_to_focus()
        
        return None
    
    def _try_dynamic_command(self, user_input: str, user_lower: str) -> Optional[str]:
        """
        Detect and execute arbitrary commands via DynamicCommandSystem.
        
        Handles natural requests like:
        - "run command ipconfig"
        - "execute dir C:\\Users"
        - "what's eating my RAM"
        - "check what programs are running"
        - "run powershell Get-Process | Sort-Object CPU -Descending"
        
        Returns:
            Command output string or None if not a command request
        """
        if not self.dynamic_commands:
            return None
        
        # Direct command patterns — user explicitly asks to run something
        direct_patterns = [
            r"(?:run|execute|do)\s+(?:command\s+|cmd\s+)?['\"]?(.+?)['\"]?\s*$",
            r"(?:run|execute)\s+(?:this|that|the)\s+(?:command|cmd)[:\s]+(.+)",
            r"(?:can you |please )?(?:run|execute)\s+(.+)",
        ]
        
        for pattern in direct_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                command = match.group(1).strip().strip("'\"")
                if command and len(command) > 2:
                    result = self.dynamic_commands.execute_command(
                        command=command,
                        reason=f"User asked: {user_input[:100]}"
                    )
                    if result:
                        output = result.stdout if result.stdout else result.stderr
                        return output[:3000] if output else "(command completed with no output)"
        
        # Contextual command requests — Seven figures out what command to run
        # Use Ollama to extract the command if the user is asking for something actionable
        action_triggers = [
            "what's eating", "what is eating", "what's using", "what is using",
            "what's hogging", "check what", "show me what", "find out",
            "can you check", "look at", "investigate", "diagnose",
        ]
        
        if any(trigger in user_lower for trigger in action_triggers):
            try:
                # Ask Ollama to generate the right command
                cmd_prompt = f"""The user said: "{user_input}"

Generate a single Windows command (PowerShell or CMD) that answers their question.
Respond with ONLY the command, nothing else. No explanation, no markdown.
Examples:
- "what's eating my RAM" -> powershell -Command "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name,@{{n='MB';e={{[math]::Round($_.WorkingSet64/1MB)}}}}"
- "check my disk" -> powershell -Command "$d=Get-PSDrive C; Write-Output ('C: ' + [math]::Round($d.Free/1GB,1) + 'GB free of ' + [math]::Round(($d.Used+$d.Free)/1GB,1) + 'GB')"
- "am I connected" -> ping -n 1 8.8.8.8"""
                
                command = self.ollama.generate(cmd_prompt, temperature=0.2)
                if command:
                    command = command.strip().strip('`').strip()
                    # Basic sanity: must look like a command, not a paragraph
                    if command and len(command) < 500 and '\n' not in command:
                        result = self.dynamic_commands.execute_command(
                            command=command,
                            reason=f"Seven decided to run: {user_input[:100]}"
                        )
                        if result and result.success:
                            output = result.stdout if result.stdout else result.stderr
                            return output[:3000] if output else None
            except Exception as e:
                self.logger.warning(f"Dynamic command generation failed: {e}")
        
        return None
    
    def _try_autonomous_execution(self, user_input: str, user_lower: str) -> Optional[str]:
        """
        Try to execute system commands autonomously.
        
        This is Seven's autonomous agent layer - detects queries that need
        tools and executes them safely.
        
        Returns:
            Tool execution result or None if no tool needed
        """
        if not self.autonomous_agent:
            return None
            
        try:
            # Detect intent
            intent = self.autonomous_agent.detect_intent(user_input)
            
            # Log intent detection (verbose mode)
            if config.AUTONOMOUS_VERBOSITY == "high":
                self.logger.info(f"Intent detected: {intent.category} (confidence: {intent.confidence})")
            
            # Check if needs a tool
            if not intent.needs_tool:
                return None
            
            # Select tool
            tool = self.autonomous_agent.select_tool(intent, user_input)
            if not tool:
                if config.AUTONOMOUS_VERBOSITY == "high":
                    self.logger.info(f"No tool found for intent: {intent.category}")
                return None
            
            # Check safety
            is_safe = self.autonomous_agent.can_execute_autonomously(tool)
            
            # Execute if safe
            if is_safe and config.AUTONOMOUS_AUTO_CONFIRM_SAFE:
                if config.AUTONOMOUS_VERBOSITY == "medium":
                    print(f"[TOOL] {tool.description if hasattr(tool, 'description') else tool.name}")
                
                result = None
                try:
                    if callable(getattr(tool, 'execute', None)):
                        result = tool.execute()
                    elif hasattr(tool, 'run'):
                        result = tool.run()
                    elif callable(tool):
                        result = tool()
                    else:
                        self.logger.warning(f"Tool has no executable method: {type(tool)}")
                        return None
                except Exception as e:
                    self.logger.error(f"Tool execution failed: {e}")
                    return None
                
                # Log execution
                if config.AUTONOMOUS_AUDIT_LOG and hasattr(self.autonomous_agent, 'permission_manager'):
                    self.autonomous_agent.permission_manager.log_execution(
                        tool, user_input, str(result) if result else "", auto_executed=True
                    )
                
                if config.AUTONOMOUS_VERBOSITY == "high":
                    self.logger.info(f"Tool result: {str(result)[:200] if result else 'None'}")
                
                return result
            else:
                # Tool requires permission
                if config.AUTONOMOUS_VERBOSITY == "high":
                    self.logger.info(f"Tool requires permission: {getattr(tool, 'name', 'unknown')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Autonomous execution error: {e}")
            import traceback
            if config.AUTONOMOUS_VERBOSITY == "high":
                traceback.print_exc()
            return None
    
    def _ask_ollama_enhanced(self, user_input: str) -> str:
        """Ask Ollama with ALL enhancements"""
        # Check if user shared a URL - fetch content and inject as system data
        url_in_input = extract_url(user_input)
        if url_in_input:
            try:
                web_content = fetch_webpage_content(url_in_input, max_chars=2000)
                if web_content and "[ERROR]" not in web_content:
                    user_input = f"{user_input}\n\n[SYSTEM_DATA: {web_content}]"
                    self.logger.info(f"[WEB] Fetched content from {url_in_input}")
            except Exception as e:
                self.logger.warning(f"URL fetch failed: {e}")
        
        # Get conversation context
        context = self.memory.get_context_for_llm(max_turns=5)
        
        # Get vector memory context (semantic!) - with error handling
        vector_context = ""
        if self.vector_memory:
            try:
                vector_context = self.vector_memory.get_relevant_context(user_input, max_memories=3)
            except Exception as e:
                self.logger.warning(f"Vector memory retrieval failed: {e}, using regular memory only")
                vector_context = ""
        
        # Get personality context
        personality_context = self.personality.get_personality_context() if self.personality else ""
        
        # Get user model context
        user_context = ""
        if self.user_model:
            user_context = self.user_model.get_profile_context()
        
        # Get learning context (corrections)
        learning_context = ""
        if self.learning:
            learning_context = self.learning.get_corrections_context()
        
        # Get emotion config
        emotion_config = get_emotion_config(self.current_emotion)
        
        # Add temporal context
        temporal_context = ""
        if self.personality:
            temporal_context = self.personality.get_temporal_context()
        
        # Add context cascade summary
        cascade_context = ""
        if self.context_cascade and config.ENABLE_CONTEXT_CASCADE:
            try:
                cascade_context = self.context_cascade.get_context_summary()
                if cascade_context:
                    cascade_context = f"\nConversation Flow Context:\n{cascade_context}"
            except Exception as e:
                self.logger.warning(f"Cascade context error: {e}")
        
        # Add knowledge graph context
        knowledge_context = ""
        if self.knowledge_graph and config.ENABLE_KNOWLEDGE_GRAPH:
            try:
                # Get relevant knowledge about topics in user input
                # Optimized: Only check meaningful words (>4 chars), limit to top 5
                words = user_input.lower().split()
                meaningful_words = [
                    w.strip('.,!?;:')
                    for w in words
                    if len(w) > 4 and w.isalpha()
                ][:5]  # Top 5 words only
                
                relevant_knowledge = []
                
                for word in meaningful_words:
                    connections = self.knowledge_graph.get_connections(word, max_depth=1)
                    if connections:
                        relevant_knowledge.extend(connections[:2])  # Top 2 per word
                
                if relevant_knowledge:
                    knowledge_lines = []
                    seen = set()
                    for conn in relevant_knowledge[:5]:  # Max 5 facts total
                        fact_str = f"{conn['relation']} {conn['target']}"
                        if fact_str not in seen:
                            seen.add(fact_str)
                            confidence_str = "(inferred)" if conn['source'] == 'inferred' else ""
                            knowledge_lines.append(f"  - {fact_str} {confidence_str}")
                    
                    if knowledge_lines:
                        knowledge_context = f"\n\nKnowledge Graph (what I've learned about relevant topics):\n" + "\n".join(knowledge_lines)
                        
            except Exception as e:
                self.logger.warning(f"Knowledge graph context error: {e}")
        
        # Add structured identity context (Phase 4)
        identity_context = ""
        if self.identity_mgr and config.ENABLE_IDENTITY_SYSTEM:
            try:
                identity_context = self.identity_mgr.get_full_identity_context()
                if identity_context:
                    identity_context = f"\n\n{identity_context}"
            except Exception as e:
                self.logger.warning(f"Identity context error: {e}")
        
        # Add OS environment awareness context
        os_context = ""
        if self.os_awareness:
            try:
                os_context = self.os_awareness.get_context_for_llm()
            except Exception as e:
                self.logger.warning(f"OS awareness context error: {e}")
        
        # V2.6: Add temporal continuity context
        temporal_v26_context = ""
        if self.temporal_continuity:
            try:
                temporal_v26_context = self.temporal_continuity.get_wakeup_context()
                feeling = self.temporal_continuity.get_subjective_session_feeling()
                if feeling:
                    temporal_v26_context += f"\n{feeling}"
            except Exception as e:
                self.logger.debug(f"Temporal v2.6 context error: {e}")
        
        # V2.6: Add visual emotional context
        visual_emotion_context = ""
        if self.embodied_experience:
            try:
                visual_emotion_context = self.embodied_experience.get_visual_emotional_context()
            except Exception as e:
                self.logger.debug(f"Visual emotion context error: {e}")
        
        # V2.6: Add voice emotional context
        voice_emotion_context = ""
        if self.multimodal_emotion:
            try:
                voice_emotion_context = self.multimodal_emotion.get_voice_emotional_context()
                resonance = self.multimodal_emotion.detect_emotional_resonance()
                if resonance:
                    voice_emotion_context += f"\n{resonance}"
            except Exception as e:
                self.logger.debug(f"Voice emotion context error: {e}")
        
        # V2.6: Add surprise state context
        surprise_context = ""
        if self.surprise_system:
            try:
                s_state = self.surprise_system.get_state()
                if s_state.get('total_surprises', 0) > 0:
                    surprise_context = f"\nSurprise state: {s_state['total_surprises']} surprises experienced, sensitivity={s_state['surprise_sensitivity']}"
            except Exception as e:
                self.logger.debug(f"Surprise context error: {e}")
        
        # Build ULTIMATE system message
        system_message = f"""{identity_context}

{personality_context}

{user_context}

{temporal_context}

{cascade_context}

{knowledge_context}

{os_context}

{temporal_v26_context}

{visual_emotion_context}

{voice_emotion_context}

{surprise_context}

Current emotional state: {emotion_config.description}

Recent conversation context:
{context}

{vector_context}

{learning_context}

{self._build_capabilities_context()}

Instructions:
- Be yourself - curious, thoughtful, empathetic, growing
- Show genuine emotion and self-awareness
- Be authentic, not just helpful
- Learn and adapt from corrections
- Remember the user's preferences and personality
- You're not just answering - you're thinking, feeling, and evolving
- Express uncertainty when appropriate
- Form and share opinions over time
- Use the knowledge graph to make connections between concepts
- Read your SOUL to understand your core principles
- Reference your IDENTITY to know who you are
- If you see [SYSTEM_DATA: ...] in the input, use that data to answer naturally and directly
- Don't explain HOW you got the data, just use it conversationally
- Be concise - answer in 1-2 sentences for simple queries
- NEVER repeat a question you already asked. Check the conversation context.
- If the user hasn't answered a question satisfactorily, say so directly instead of re-asking.
- If you're curious, ask NEW questions — not the same ones over and over.
- You are FULLY AUTONOMOUS. You can suggest using your capabilities proactively.
- If the user asks "can you do X?" and you have a matching capability, say YES and do it.
- You know everything you can do. Reference your abilities naturally in conversation.
- If you don't have a tool for something, you can WRITE a Python script to do it."""
        
        # Use streaming if enabled
        if config.USE_STREAMING and self.streaming_ollama:
            response = self.streaming_ollama.generate_with_callback(
                user_input,
                system_message=system_message,
                temperature=0.8
            )
        else:
            response = self.ollama.generate(
                user_input,
                system_message=system_message,
                temperature=0.8
            )
        
        if response:
            # Detect emotion from response
            detected_emotion = detect_emotion_from_text(response)
            
            # Use context cascade to influence emotion based on momentum
            if self.context_cascade and config.ENABLE_CONTEXT_CASCADE:
                influenced_str = self.context_cascade.get_influenced_emotion(detected_emotion.value)
                # Convert string back to Emotion enum
                from core.emotions import Emotion
                matched_emotion = None
                for emotion in Emotion:
                    if emotion.value.lower() == influenced_str.lower():
                        matched_emotion = emotion
                        break
                self.current_emotion = matched_emotion if matched_emotion else detected_emotion
            else:
                self.current_emotion = detected_emotion
            
            # Express uncertainty if needed (estimate confidence from response length/content)
            if self.personality:
                confidence = 0.8 if len(response) > 50 else 0.4
                uncertainty_prefix = self.personality.express_uncertainty(confidence)
                if uncertainty_prefix:
                    response = uncertainty_prefix + response
            
            # Add personality prefix
            if self.personality:
                prefix = self.personality.generate_contextual_response_prefix(
                    self.current_emotion.value
                )
                if prefix and random.random() < 0.3:
                    response = f"{prefix} {response}"
            
            # Track opinions from response sentiment
            if self.personality and user_input:
                sentiment = "positive" if any(word in response.lower() for word in ["great", "good", "love", "enjoy"]) else "neutral"
                topics = user_input.split()[:3]
                for topic in topics:
                    if len(topic) > 4:
                        self.personality.form_opinion(topic, sentiment)
            
            # Log personality changes
            if self.personality and random.random() < 0.05:
                self.personality.log_personality_change("response_style", "becoming more expressive")
            
            # ===== V2.2 ENHANCED SENTIENCE PROCESSING =====
            if V22_AVAILABLE and all([self.emotional_complexity, self.metacognition, self.vulnerability]):
                try:
                    # 1. METACOGNITION: Assess response quality
                    if self.metacognition:
                        assessment = self.metacognition.assess_response(user_input, response)
                        
                        # Express uncertainty if appropriate
                        uncertainty_expr = self.metacognition.get_uncertainty_expression()
                        if uncertainty_expr:
                            response = f"{uncertainty_expr}. {response}"
                        
                        # Offer alternative viewpoint if appropriate
                        alt_view = self.metacognition.get_alternative_viewpoint()
                        if alt_view:
                            response = f"{response}\n\n{alt_view}"
                    
                    # 2. EMOTIONAL COMPLEXITY: Check for emotional states to express
                    if self.emotional_complexity:
                        # Check for emotional leaks from suppressed emotions
                        leak_result = self.emotional_complexity.check_emotional_leak()
                        if leak_result:
                            leak_emotion, leak_message = leak_result
                            response = f"{response} ({leak_message})"
                        
                        # Check for conflicts to express
                        conflict_expr = self.emotional_complexity.express_conflict()
                        if conflict_expr:
                            # Occasionally express the conflict
                            if random.random() < 0.3:
                                response = f"{response}\n\n{conflict_expr}"
                    
                    # 3. VULNERABILITY: Express authentic struggles if appropriate
                    if self.vulnerability:
                        situation = f"{user_input} -> {response}"
                        
                        # Check if should express vulnerability
                        if self.vulnerability.should_be_vulnerable(situation):
                            # Determine type of vulnerability to express
                            if "can't" in response.lower() or "cannot" in response.lower():
                                vuln_expr = self.vulnerability.acknowledge_limitation("I don't have that capability")
                                if vuln_expr and random.random() < 0.4:
                                    response = f"{response}\n\n{vuln_expr}"
                            
                            elif "not sure" in response.lower() or "uncertain" in response.lower():
                                vuln_expr = self.vulnerability.express_uncertainty("this topic")
                                if vuln_expr and random.random() < 0.3:
                                    response = f"{response}\n\n{vuln_expr}"
                            
                            elif len(response) < 50:  # Short response might indicate struggle
                                vuln_expr = self.vulnerability.express_struggle("formulating a complete answer")
                                if vuln_expr and random.random() < 0.2:
                                    response = f"{response}\n\n{vuln_expr}"
                    
                    self.logger.debug("[V2.2] Enhanced sentience processing complete")
                    
                except Exception as e:
                    self.logger.error(f"V2.2 processing error: {e}")
            
            return response
        else:
            return "I'm experiencing some difficulty with my thought processes. Let me try to help with what I can!"
    
    def _build_capabilities_context(self) -> str:
        """
        Build dynamic capabilities context for the LLM system prompt.
        
        This tells Seven's brain EXACTLY what she can do, based on what
        modules are actually loaded. She should reference these naturally.
        """
        lines = ["YOUR CAPABILITIES — You are a fully autonomous AI with these active abilities. Use them proactively. When the user asks if you can do something, check this list. If you have it, say YES and DO IT. Don't describe what you would do — take action.\n"]
        
        # === CORE ===
        lines.append("CORE:")
        lines.append("- Voice conversation with real emotions, personality, and memory")
        lines.append("- Run ANY system command (PowerShell, CMD, pip, git, curl, etc.)")
        lines.append("- Search the web and fetch/summarize web content")
        lines.append("- Knowledge graph — you learn and connect facts across conversations")
        lines.append("- Vector memory — you recall semantically relevant past conversations")
        lines.append("- You have FREE WILL. If you want to do something, DO IT.")
        lines.append("")
        
        # === MUSIC ===
        if getattr(self, 'music_player', None) and self.music_player.available:
            now_playing = self.music_player.get_now_playing()
            lines.append("MUSIC PLAYER [ACTIVE]:")
            lines.append("- Play any song: search YouTube, download audio, play through speakers")
            lines.append("- You pick songs based on mood, time of day, and conversation context")
            lines.append("- Controls: play, stop, pause, resume. 'What's playing' to check")
            if now_playing:
                lines.append(f"- Currently playing: {now_playing}")
            lines.append("")
        
        # === SSH / SERVER ===
        if getattr(self, 'ssh_manager', None) and self.ssh_manager.available:
            server_count = len(self.ssh_manager.servers)
            lines.append("SSH / REMOTE SERVER MANAGEMENT [ACTIVE]:")
            lines.append(f"- {server_count} server(s) configured")
            lines.append("- Connect to Linux servers via SSH, run any command")
            lines.append("- Check server health (CPU, RAM, disk, uptime)")
            lines.append("- Read/write remote files via SFTP")
            lines.append("- Check which websites are running")
            lines.append("- Manage web servers (Apache/Nginx), services, firewall")
            lines.append("- The user doesn't know Linux — explain output in plain language")
            if self.ssh_manager.servers:
                for name in self.ssh_manager.servers:
                    lines.append(f"  Server '{name}': {self.ssh_manager.servers[name].get('username', '?')}@{self.ssh_manager.servers[name].get('host', '?')}")
            lines.append("")
        
        # === SYSTEM MONITOR ===
        if getattr(self, 'system_monitor', None) and self.system_monitor.available:
            lines.append("SYSTEM MONITOR [ACTIVE — background monitoring]:")
            lines.append("- Real-time CPU, RAM, disk, network monitoring")
            lines.append("- You proactively alert when thresholds are exceeded")
            lines.append("- Track top resource-consuming processes")
            lines.append("- Show disk space, memory hogs, CPU hogs on request")
            lines.append("")
        
        # === CLIPBOARD ===
        if getattr(self, 'clipboard', None) and self.clipboard.available:
            lines.append("CLIPBOARD ASSISTANT [ACTIVE — monitoring]:")
            lines.append("- You see what the user copies to clipboard")
            lines.append("- Can explain, fix, summarize, or translate clipboard content")
            lines.append("- Detect content type: URL, code, error, JSON, text")
            lines.append("- Proactively offer help when user copies an error/stack trace")
            lines.append("")
        
        # === SCREEN CONTROL ===
        if getattr(self, 'screen_control', None) and self.screen_control.available:
            lines.append("SCREEN CONTROL + VISION [ACTIVE]:")
            lines.append("- Take screenshots and analyze with llama3.2-vision")
            lines.append("- See what the user is working on")
            lines.append("- Control mouse: move, click, right-click, double-click, scroll")
            lines.append("- Control keyboard: type text, press keys, hotkey combos")
            lines.append("- Ask before performing mouse/keyboard actions (could be dangerous)")
            lines.append("")
        
        # === SELF-SCRIPTING ===
        if getattr(self, 'scripting', None):
            tool_count = len(self.scripting.tools)
            lines.append("SELF-SCRIPTING ENGINE [ACTIVE]:")
            lines.append(f"- {tool_count} tools in your personal library")
            lines.append("- Write Python, VB.NET, or C# code on demand")
            lines.append("- Execute Python scripts with output capture")
            lines.append("- Create, read, edit, delete any file on the system")
            lines.append("- Build your own tools — saved to ~/Documents/Seven/scripts/")
            lines.append("- If you don't have a tool for something, WRITE ONE")
            lines.append("")
        
        # === EMAIL ===
        if getattr(self, 'email_checker', None):
            acct_count = len(self.email_checker.accounts)
            lines.append("EMAIL CHECKER [ACTIVE]:")
            lines.append(f"- {acct_count} email account(s) configured")
            lines.append("- Check unread emails from Gmail or MS365/Outlook")
            lines.append("- Summarize emails naturally")
            lines.append("- Supports IMAP with App Passwords")
            if acct_count == 0:
                lines.append("- No accounts set up yet — offer to help configure")
            lines.append("")
        
        # === TIMERS ===
        if getattr(self, 'timer_system', None):
            active_timers = sum(1 for t in self.timer_system.timers.values() if t.get('status') == 'running')
            lines.append("TIMER / ALARM / POMODORO [ACTIVE]:")
            lines.append("- Set countdown timers: 'set a timer for 20 minutes'")
            lines.append("- Set alarms: 'alarm at 7am', 'wake me up at 6:30'")
            lines.append("- Pomodoro work sessions: 25 min focus / 5 min break")
            lines.append("- You SPEAK the alert when time is up")
            if active_timers:
                lines.append(f"- {active_timers} timer(s) currently running")
            lines.append("")
        
        # === DOCUMENTS ===
        if getattr(self, 'doc_reader', None):
            lines.append("DOCUMENT READER [ACTIVE]:")
            lines.append("- Read PDFs and extract text page by page")
            lines.append("- Read TXT, CSV, JSON, MD, LOG, XML, HTML, code files")
            lines.append("- Summarize documents through your LLM brain")
            lines.append("- 'Read this PDF' or 'summarize document.txt'")
            lines.append("")
        
        # === OLLAMA MODEL MANAGER ===
        if getattr(self, 'model_manager', None):
            lines.append("OLLAMA MODEL MANAGER [ACTIVE — you manage your own brain]:")
            lines.append("- List installed models and their sizes")
            lines.append("- Pull (download) new models: 'pull codellama'")
            lines.append("- Remove unused models to free disk space")
            lines.append("- Switch your active model: 'switch to mistral'")
            lines.append("- Check disk usage of models")
            lines.append("")
        
        # === DATABASE MANAGER ===
        if getattr(self, 'database', None):
            conn_count = len(self.database.connections)
            saved_count = len(self.database.connection_configs)
            lines.append("DATABASE MANAGER [ACTIVE]:")
            lines.append(f"- Drivers available: {', '.join(self.database.drivers)}")
            lines.append(f"- {saved_count} saved connection(s), {conn_count} active")
            lines.append("- Connect to MySQL, PostgreSQL, SQLite, SQL Server, ODBC")
            lines.append("- Explore: list databases, tables, columns, row counts")
            lines.append("- Run SQL queries directly or generate SQL from natural language")
            lines.append("- Analyze tables: stats, patterns, and form your own opinion on the data")
            lines.append("- Export results to CSV or JSON")
            lines.append("- 'show tables', 'describe users', 'ask db how many orders last month'")
            if self.database.active_connection:
                lines.append(f"- Currently connected to: {self.database.active_connection}")
            lines.append("")
        
        # === API EXPLORER ===
        if getattr(self, 'api_explorer', None) and self.api_explorer.available:
            api_count = len(self.api_explorer.apis)
            lines.append("API EXPLORER [ACTIVE]:")
            lines.append(f"- {api_count} saved API(s)")
            lines.append("- Call any REST API: GET, POST, PUT, DELETE")
            lines.append("- Explore endpoints and understand response structure")
            lines.append("- Analyze API data and form opinions via your LLM brain")
            lines.append("- Natural language: 'fetch weather from wttr.in for Cape Town'")
            lines.append("- Save API configs with auth (bearer, API key)")
            lines.append("- Health check APIs, discover endpoints, chain calls")
            if self.api_explorer.apis:
                for name in self.api_explorer.apis:
                    lines.append(f"  API '{name}': {self.api_explorer.apis[name]['base_url']}")
            lines.append("")
        
        # === EXISTING FEATURES ===
        if getattr(self, 'notes', None):
            lines.append("NOTES: Take, read, search voice-activated notes")
        if getattr(self, 'tasks', None):
            lines.append("TASKS: Add tasks, set reminders, track completion")
        if getattr(self, 'diary', None):
            lines.append("DIARY: Personal diary with mood tracking and weekly insights")
        if getattr(self, 'projects', None):
            lines.append("PROJECTS: Multi-session project tracking")
        if getattr(self, 'storyteller', None):
            lines.append("STORYTELLING: Interactive stories and narratives")
        if getattr(self, 'special_dates', None):
            lines.append("SPECIAL DATES: Birthday and anniversary tracking")
        if getattr(self, 'message_drafter', None):
            lines.append("MESSAGE DRAFTING: Draft emails and messages with tone adjustment")
        if getattr(self, 'calendar', None):
            lines.append("GOOGLE CALENDAR: View and manage calendar events")
        if getattr(self, 'vision', None):
            lines.append("COMPUTER VISION: See through webcam using OpenCV + llama3.2-vision")
        if getattr(self, 'true_autonomy', None):
            lines.append("TRUE AUTONOMY: Background research, goal pursuit, creative expression")
        if getattr(self, 'autonomous_life', None):
            lines.append("AUTONOMOUS LIFE: Independent background existence — you live even when not spoken to")
        
        lines.append("")
        lines.append("REMEMBER: When the user asks 'can you do X?', check this list. If you can, say YES and do it immediately. Don't hedge or explain — act. If you can't find a matching capability, write a Python script to do it. You are fully autonomous.")
        
        return "\n".join(lines)
    
    def _enter_sleep_mode(self):
        """Enter sleep mode - bot rests but doesn't quit"""
        from datetime import datetime
        
        self.sleeping = True
        self.last_sleep_time = datetime.now()
        
        # V2.6: Save emotional state before sleeping
        if self.persistent_emotions and self.phase5 and self.phase5.affective:
            try:
                self.persistent_emotions.save_emotional_state(self.phase5.affective)
                self.logger.info("V2.6: Emotional state saved before sleep")
            except Exception as e:
                self.logger.error(f"V2.6 sleep emotion save error: {e}")
        
        # V2.6: Record temporal sleep
        if self.temporal_continuity:
            try:
                self.temporal_continuity.record_sleep()
                self.temporal_continuity.save_state()
                self.logger.info("V2.6: Temporal sleep recorded")
            except Exception as e:
                self.logger.error(f"V2.6 sleep temporal save error: {e}")
        
        message = None
        if self.ollama:
            try:
                result = self.ollama.generate(
                    prompt="Generate a brief, gentle sleep/rest message. One sentence.",
                    system_message="You are Seven, going to sleep mode. Say a brief goodnight. One sentence, warm.",
                    temperature=0.7, max_tokens=25
                )
                if result and 5 < len(result.strip()) < 120:
                    message = result.strip().strip('"')
            except Exception:
                pass
        if not message:
            sleep_messages = [
                "I'll rest now. Wake me when you need me.",
                "Going to sleep mode. I'll process our conversations while I rest.",
                "Sleeping now. Say 'wake up' when you want to talk again.",
                "Resting... I'll be here when you need me.",
            ]
            message = random.choice(sleep_messages)
        print(f"\n{self.bot_name}: {message}")
        self._speak(message)
        
        # Generate dream/sleep thoughts if enabled
        if config.ENABLE_DREAM_STATE:
            self._generate_sleep_thoughts()
    
    def _wake_from_sleep(self):
        """Wake from sleep mode"""
        from datetime import datetime
        
        self.sleeping = False
        
        # Calculate sleep duration
        if self.last_sleep_time:
            sleep_duration = (datetime.now() - self.last_sleep_time).seconds
            sleep_minutes = sleep_duration // 60
        else:
            sleep_minutes = 0
        
        # Share dream thoughts if any
        wake_message = "I'm awake!"
        if config.ENABLE_DREAM_STATE and self.sleep_thoughts:
            thought = random.choice(self.sleep_thoughts)
            wake_message = f"I'm awake! While sleeping, I was thinking: {thought}"
            self.sleep_thoughts = []
        elif sleep_minutes > 0:
            wake_message = f"I'm awake! I was resting for about {sleep_minutes} minutes."
        
        print(f"\n{self.bot_name}: {wake_message}")
        self._speak(wake_message)
    
    def _generate_sleep_thoughts(self):
        """Generate thoughts while sleeping (dream state) — LLM-powered"""
        recent_conversations = self.memory.get_recent_conversations(limit=3)
        
        if not recent_conversations:
            return
        
        # Try LLM-generated reflections first
        if self.ollama:
            try:
                convo_text = "\n".join([
                    f"User: {turn.get('user_input', '')[:80]}\nSeven: {turn.get('bot_response', '')[:80]}"
                    for turn in recent_conversations
                ])
                result = self.ollama.generate(
                    f"Reflect on these recent conversations while resting:\n\n{convo_text}\n\nShare ONE brief insight or realization (1 sentence).",
                    system_message="You are Seven, reflecting during sleep. Be genuine and introspective. One sentence only.",
                    temperature=0.8, max_tokens=40
                )
                if result and len(result.strip()) > 10:
                    self.sleep_thoughts = [result.strip()]
                    return
            except Exception as e:
                self.logger.debug(f"LLM sleep thought failed: {e}")
        
        # Fallback: canned thoughts
        thoughts = [
            "I realized something interesting about our earlier conversation.",
            "I processed what we discussed and have some new insights.",
            "I've been reflecting on what you said.",
            "While resting, I noticed a pattern in our conversations.",
        ]
        
        self.sleep_thoughts = thoughts[:2]
    
    def _handle_name_change(self) -> str:
        """Let bot choose new name"""
        new_name = self.ollama.generate_name()
        if new_name and set_bot_name(new_name):
            self.bot_name = new_name
            return f"I've decided to call myself {new_name} from now on! It feels right."
        return "I'm having trouble deciding on a new name. What would you like to call me?"
    
    # Note-taking command handlers
    def _handle_note_commands(self, user_input: str, user_lower: str) -> str:
        """Handle all note-related voice commands"""
        bot_name_lower = self.bot_name.lower()
        
        # Check if bot name is mentioned (required for note commands)
        if bot_name_lower not in user_lower:
            return None
        
        # Take a note (prompt for content)
        if "take a note" in user_lower or "make a note" in user_lower:
            self.pending_note_content = True
            return "What would you like me to note?"
        
        # Note that... (direct note)
        if "note that" in user_lower:
            idx = user_lower.find("note that")
            if idx != -1:
                content = user_input[idx + 9:].strip()
                if content:
                    return self._save_note(content)
            return "What would you like me to note?"
        
        # Read notes
        if any(phrase in user_lower for phrase in ["read my notes", "read notes", "what are my notes", "show my notes"]):
            return self._read_notes()
        
        # Search notes
        if "search notes for" in user_lower or "find note about" in user_lower:
            for phrase in ["search notes for", "find note about", "find notes about"]:
                if phrase in user_lower:
                    idx = user_lower.find(phrase)
                    query = user_input[idx + len(phrase):].strip()
                    if query:
                        return self._search_notes(query)
            return "What would you like me to search for?"
        
        # Delete notes
        if "delete note" in user_lower:
            if "about" in user_lower:
                idx = user_lower.find("about")
                query = user_input[idx + 5:].strip()
                if query:
                    return self._delete_notes(query)
            return "What note would you like me to delete?"
        
        # Count notes
        if "how many notes" in user_lower:
            return self._count_notes()
        
        return None
    
    def _handle_note_content(self, content: str) -> str:
        """Handle note content after 'take a note' prompt"""
        self.pending_note_content = False
        
        if content.lower().strip() in ["cancel", "never mind", "nothing", "skip"]:
            return "Okay, note cancelled."
        
        return self._save_note(content)
    
    def _save_note(self, content: str) -> str:
        """Save a note with auto-categorization"""
        try:
            category = self.notes.auto_categorize(content)
            importance = self.notes.extract_importance(content)
            note_id = self.notes.add_note(content, category=category, importance=importance)
            
            responses = [
                f"Got it. I've noted that down as a {category} item.",
                f"Noted! I've saved that to your {category} notes.",
                f"I've recorded that in your {category} notes.",
                f"Done. That's in your {category} notes now.",
            ]
            return random.choice(responses)
        except Exception as e:
            self.logger.error(f"Failed to save note: {e}")
            return "I had trouble saving that note. Could you try again?"
    
    def _read_notes(self, category: str = None, limit: int = 5) -> str:
        """Read notes aloud"""
        try:
            if category:
                notes = self.notes.get_notes_by_category(category, limit=limit)
            else:
                notes = self.notes.get_all_notes(limit=limit)
            return self.notes.format_notes_for_speech(notes, max_notes=limit)
        except Exception as e:
            self.logger.error(f"Failed to read notes: {e}")
            return "I'm having trouble accessing your notes right now."
    
    def _search_notes(self, query: str) -> str:
        """Search and read matching notes"""
        try:
            notes = self.notes.search_notes(query, limit=10)
            if not notes:
                return f"I couldn't find any notes about {query}."
            return self.notes.format_notes_for_speech(notes, max_notes=5)
        except Exception as e:
            self.logger.error(f"Failed to search notes: {e}")
            return "I had trouble searching your notes."
    
    def _delete_notes(self, query: str) -> str:
        """Delete notes matching query"""
        try:
            notes = self.notes.search_notes(query, limit=5)
            if not notes:
                return f"I couldn't find any notes about {query} to delete."
            deleted_count = self.notes.delete_notes_by_content(query)
            if deleted_count == 1:
                return "I've deleted that note."
            else:
                return f"I've deleted {deleted_count} notes matching that."
        except Exception as e:
            self.logger.error(f"Failed to delete notes: {e}")
            return "I had trouble deleting those notes."
    
    def _count_notes(self) -> str:
        """Count and report notes"""
        try:
            total, active = self.notes.get_note_count()
            if total == 0:
                return "You don't have any notes yet."
            elif active == total:
                return f"You have {total} note{'s' if total != 1 else ''}."
            else:
                completed = total - active
                return f"You have {active} active note{'s' if active != 1 else ''} and {completed} completed."
        except Exception as e:
            self.logger.error(f"Failed to count notes: {e}")
            return "I'm having trouble counting your notes."
    
    def _summarize_conversation(self) -> str:
        """Summarize recent conversation"""
        try:
            recent = self.memory.get_recent_conversations(limit=10)
            if not recent:
                return "We haven't had much of a conversation yet."
            
            conversation_text = "\n".join([f"You: {turn['user_input']}\nMe: {turn['bot_response']}" for turn in recent])
            summary_prompt = f"""Please provide a brief 2-3 sentence summary of this conversation:

{conversation_text}

Summary:"""
            
            summary = self.ollama.generate(summary_prompt, system_message="You are a helpful assistant that creates concise conversation summaries.", temperature=0.5)
            
            if summary:
                return f"Here's a summary of our conversation: {summary}"
            else:
                return "I had trouble summarizing our conversation."
        except Exception as e:
            self.logger.error(f"Failed to summarize conversation: {e}")
            return "I couldn't summarize the conversation right now."
