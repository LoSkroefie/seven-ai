"""
Seven AI - Complete Test Suite
================================
Tests all systems, integrations, and capabilities.

Run: python -m pytest tests/test_seven_complete.py -v
Or:  python tests/test_seven_complete.py
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================
# TEST RESULTS TRACKER
# ============================================================
class TestTracker:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []
    
    def record(self, name, passed, message="", skipped=False):
        if skipped:
            self.skipped += 1
            status = "SKIP"
        elif passed:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"
        self.results.append((status, name, message))
        symbol = "✓" if passed else ("⊘" if skipped else "✗")
        print(f"  {symbol} {name}" + (f" — {message}" if message else ""))

tracker = TestTracker()


# ============================================================
# 1. IMPORT TESTS — Can everything load?
# ============================================================
print("\n" + "="*60)
print("1. IMPORT TESTS")
print("="*60)

def test_import(module_path, name):
    try:
        parts = module_path.rsplit('.', 1)
        mod = __import__(module_path, fromlist=[parts[-1]])
        tracker.record(f"Import {name}", True)
        return mod
    except Exception as e:
        tracker.record(f"Import {name}", False, str(e)[:100])
        return None

# Core modules
test_import("core.enhanced_bot", "enhanced_bot")
test_import("core.autonomous_life", "autonomous_life")
test_import("core.seven_true_autonomy", "seven_true_autonomy")
test_import("core.personality", "personality")
test_import("core.emotions", "emotions")
test_import("core.memory", "memory")
test_import("core.knowledge_graph", "knowledge_graph")
test_import("core.dream_system", "dream_system")
test_import("core.emotional_complexity", "emotional_complexity")
test_import("core.metacognition", "metacognition")
test_import("core.vulnerability", "vulnerability")

# Integration modules
test_import("integrations.ollama", "ollama")
test_import("integrations.music_player", "music_player")
test_import("integrations.ssh_manager", "ssh_manager")
test_import("integrations.system_monitor", "system_monitor")
test_import("integrations.clipboard_assistant", "clipboard_assistant")
test_import("integrations.screen_control", "screen_control")
test_import("integrations.self_scripting", "self_scripting")
test_import("integrations.email_checker", "email_checker")
test_import("integrations.timer_system", "timer_system")
test_import("integrations.document_reader", "document_reader")
test_import("integrations.ollama_manager", "ollama_manager")
test_import("integrations.web_search", "web_search")

# Config
import config


# ============================================================
# 2. OLLAMA CLIENT TESTS
# ============================================================
print("\n" + "="*60)
print("2. OLLAMA CLIENT TESTS")
print("="*60)

try:
    from integrations.ollama import OllamaClient
    oc = OllamaClient()
    
    # Test connection
    connected = oc.test_connection()
    tracker.record("Ollama connection", connected, "" if connected else "Ollama not running")
    
    # Test generate method exists
    tracker.record("OllamaClient.generate exists", callable(getattr(oc, 'generate', None)))
    tracker.record("OllamaClient.generate_with_vision exists", callable(getattr(oc, 'generate_with_vision', None)))
    tracker.record("OllamaClient.generate_with_image exists", callable(getattr(oc, 'generate_with_image', None)))
    tracker.record("OllamaClient.ask_with_context exists", callable(getattr(oc, 'ask_with_context', None)))
    tracker.record("OllamaClient.ask_for_decision exists", callable(getattr(oc, 'ask_for_decision', None)))
    
    # Test actual generation (only if connected)
    if connected:
        result = oc.generate("Say 'hello' and nothing else.", temperature=0.1, max_tokens=10, timeout=10)
        tracker.record("Ollama generate works", result is not None and len(result) > 0, f"Got: {result[:50] if result else 'None'}")
    else:
        tracker.record("Ollama generate works", False, "Skipped — not connected", skipped=True)
        
except Exception as e:
    tracker.record("Ollama client tests", False, str(e)[:100])


# ============================================================
# 3. MUSIC PLAYER TESTS
# ============================================================
print("\n" + "="*60)
print("3. MUSIC PLAYER TESTS")
print("="*60)

try:
    from integrations.music_player import MusicPlayer
    mp = MusicPlayer()
    
    tracker.record("MusicPlayer init", True)
    tracker.record("MusicPlayer.available", mp.available)
    tracker.record("MusicPlayer has search_and_play", callable(getattr(mp, 'search_and_play', None)))
    tracker.record("MusicPlayer has stop", callable(getattr(mp, 'stop', None)))
    tracker.record("MusicPlayer has pause", callable(getattr(mp, 'pause', None)))
    tracker.record("MusicPlayer has resume", callable(getattr(mp, 'resume', None)))
    tracker.record("MusicPlayer has get_now_playing", callable(getattr(mp, 'get_now_playing', None)))
    
    # Test search (no play)
    if mp.available:
        info = mp._search_youtube("test audio")
        tracker.record("YouTube search works", info is not None, f"Found: {info.get('title', '?')[:50]}" if info else "No results")
    else:
        tracker.record("YouTube search works", False, "yt-dlp not available", skipped=True)
        
except Exception as e:
    tracker.record("Music player tests", False, str(e)[:100])


# ============================================================
# 4. SSH MANAGER TESTS
# ============================================================
print("\n" + "="*60)
print("4. SSH MANAGER TESTS")
print("="*60)

try:
    from integrations.ssh_manager import SSHManager
    ssh = SSHManager()
    
    tracker.record("SSHManager init", True)
    tracker.record("SSHManager.available", ssh.available)
    tracker.record("SSHManager has add_server", callable(getattr(ssh, 'add_server', None)))
    tracker.record("SSHManager has connect", callable(getattr(ssh, 'connect', None)))
    tracker.record("SSHManager has run_command", callable(getattr(ssh, 'run_command', None)))
    tracker.record("SSHManager has read_remote_file", callable(getattr(ssh, 'read_remote_file', None)))
    tracker.record("SSHManager has check_server_health", callable(getattr(ssh, 'check_server_health', None)))
    tracker.record("SSHManager has check_websites", callable(getattr(ssh, 'check_websites', None)))
    tracker.record("Config dir exists", ssh.config_dir.exists())
    
except Exception as e:
    tracker.record("SSH manager tests", False, str(e)[:100])


# ============================================================
# 5. SYSTEM MONITOR TESTS
# ============================================================
print("\n" + "="*60)
print("5. SYSTEM MONITOR TESTS")
print("="*60)

try:
    from integrations.system_monitor import SystemMonitor
    sm = SystemMonitor()
    
    tracker.record("SystemMonitor init", True)
    tracker.record("SystemMonitor.available", sm.available)
    
    if sm.available:
        snapshot = sm.get_snapshot()
        tracker.record("Snapshot has cpu_percent", 'cpu_percent' in snapshot)
        tracker.record("Snapshot has ram", 'ram' in snapshot)
        tracker.record("Snapshot has disk", 'disk' in snapshot)
        tracker.record("Snapshot has top_processes", 'top_processes' in snapshot)
        tracker.record("CPU percent valid", 0 <= snapshot.get('cpu_percent', -1) <= 100)
        tracker.record("RAM percent valid", 0 <= snapshot['ram'].get('percent', -1) <= 100)
        
        summary = sm.get_summary()
        tracker.record("Summary is string", isinstance(summary, str) and len(summary) > 20)
    else:
        tracker.record("System monitor snapshot", False, "psutil not available", skipped=True)
        
except Exception as e:
    tracker.record("System monitor tests", False, str(e)[:100])


# ============================================================
# 6. CLIPBOARD ASSISTANT TESTS
# ============================================================
print("\n" + "="*60)
print("6. CLIPBOARD ASSISTANT TESTS")
print("="*60)

try:
    from integrations.clipboard_assistant import ClipboardAssistant
    cb = ClipboardAssistant()
    
    tracker.record("ClipboardAssistant init", True)
    tracker.record("ClipboardAssistant.available", cb.available)
    
    # Test content type detection
    tracker.record("Detect URL", cb.detect_content_type("https://example.com") == 'url')
    tracker.record("Detect code", cb.detect_content_type("def hello():\n    pass") == 'code')
    tracker.record("Detect error", cb.detect_content_type("Traceback (most recent call last):") == 'error')
    tracker.record("Detect JSON", cb.detect_content_type('{"key": "value"}') == 'json')
    tracker.record("Detect filepath", cb.detect_content_type("C:\\Users\\test\\file.txt") == 'filepath')
    
    if cb.available:
        content = cb.get_clipboard()
        tracker.record("Get clipboard", content is not None)
    
except Exception as e:
    tracker.record("Clipboard tests", False, str(e)[:100])


# ============================================================
# 7. SCREEN CONTROL TESTS
# ============================================================
print("\n" + "="*60)
print("7. SCREEN CONTROL TESTS")
print("="*60)

try:
    from integrations.screen_control import ScreenControl
    sc = ScreenControl()
    
    tracker.record("ScreenControl init", True)
    tracker.record("ScreenControl.available", sc.available)
    tracker.record("Has take_screenshot", callable(getattr(sc, 'take_screenshot', None)))
    tracker.record("Has see_screen", callable(getattr(sc, 'see_screen', None)))
    tracker.record("Has mouse_click", callable(getattr(sc, 'mouse_click', None)))
    tracker.record("Has type_text", callable(getattr(sc, 'type_text', None)))
    tracker.record("Has hotkey", callable(getattr(sc, 'hotkey', None)))
    tracker.record("Has cleanup", callable(getattr(sc, 'cleanup', None)))
    
    if sc.available:
        size = sc.get_screen_size()
        tracker.record("Screen size", "x" in size.lower(), size)
    
except Exception as e:
    tracker.record("Screen control tests", False, str(e)[:100])


# ============================================================
# 8. SELF-SCRIPTING ENGINE TESTS
# ============================================================
print("\n" + "="*60)
print("8. SELF-SCRIPTING ENGINE TESTS")
print("="*60)

try:
    from integrations.self_scripting import SelfScriptingEngine
    se = SelfScriptingEngine()
    
    tracker.record("SelfScriptingEngine init", True)
    tracker.record("Scripts dir exists", se.scripts_dir.exists())
    tracker.record("Has generate_script", callable(getattr(se, 'generate_script', None)))
    tracker.record("Has run_script", callable(getattr(se, 'run_script', None)))
    tracker.record("Has generate_and_run", callable(getattr(se, 'generate_and_run', None)))
    tracker.record("Has create_file", callable(getattr(se, 'create_file', None)))
    tracker.record("Has edit_file", callable(getattr(se, 'edit_file', None)))
    tracker.record("Has delete_file", callable(getattr(se, 'delete_file', None)))
    tracker.record("Has read_file", callable(getattr(se, 'read_file', None)))
    
    # Test run_script with a simple script
    result = se.run_script(code="print('Seven test OK')")
    tracker.record("Run script works", result.get('success', False) and 'Seven test OK' in result.get('stdout', ''))
    
except Exception as e:
    tracker.record("Self-scripting tests", False, str(e)[:100])


# ============================================================
# 9. EMAIL CHECKER TESTS
# ============================================================
print("\n" + "="*60)
print("9. EMAIL CHECKER TESTS")
print("="*60)

try:
    from integrations.email_checker import EmailChecker
    ec = EmailChecker()
    
    tracker.record("EmailChecker init", True)
    tracker.record("Has add_account", callable(getattr(ec, 'add_account', None)))
    tracker.record("Has check_unread", callable(getattr(ec, 'check_unread', None)))
    tracker.record("Has read_email", callable(getattr(ec, 'read_email', None)))
    tracker.record("Has get_summary", callable(getattr(ec, 'get_summary', None)))
    tracker.record("Providers defined", len(ec.PROVIDERS) >= 3)
    
    # Test with no accounts
    result = ec.check_unread()
    tracker.record("No-account check handled", not result['success'] and 'No email' in result.get('message', ''))
    
except Exception as e:
    tracker.record("Email checker tests", False, str(e)[:100])


# ============================================================
# 10. TIMER SYSTEM TESTS
# ============================================================
print("\n" + "="*60)
print("10. TIMER SYSTEM TESTS")
print("="*60)

try:
    from integrations.timer_system import TimerSystem
    ts = TimerSystem()
    
    tracker.record("TimerSystem init", True)
    
    # Test duration parsing
    tracker.record("Parse '20 minutes'", TimerSystem.parse_duration("20 minutes") == 1200)
    tracker.record("Parse '1 hour'", TimerSystem.parse_duration("1 hour") == 3600)
    tracker.record("Parse '90 seconds'", TimerSystem.parse_duration("90 seconds") == 90)
    tracker.record("Parse '1h30m'", TimerSystem.parse_duration("1h30m") == 5400)
    
    # Test time parsing
    tracker.record("Parse '7am'", TimerSystem.parse_time("7am") == (7, 0))
    tracker.record("Parse '7:30 pm'", TimerSystem.parse_time("7:30 pm") == (19, 30))
    tracker.record("Parse '14:00'", TimerSystem.parse_time("14:00") == (14, 0))
    
    # Test timer set/cancel
    result = ts.set_timer(2, "Test timer")
    tracker.record("Set timer", "Timer set" in result)
    tracker.record("Timer count", len(ts.timers) > 0)
    
    # Cancel it
    for tid in list(ts.timers.keys()):
        ts.cancel_timer(timer_id=tid)
    tracker.record("Cancel timer", all(t['status'] != 'running' for t in ts.timers.values()))
    
    ts.cleanup()
    
except Exception as e:
    tracker.record("Timer system tests", False, str(e)[:100])


# ============================================================
# 11. DOCUMENT READER TESTS
# ============================================================
print("\n" + "="*60)
print("11. DOCUMENT READER TESTS")
print("="*60)

try:
    from integrations.document_reader import DocumentReader
    dr = DocumentReader()
    
    tracker.record("DocumentReader init", True)
    tracker.record("Can read .pdf", dr.can_read("test.pdf"))
    tracker.record("Can read .txt", dr.can_read("test.txt"))
    tracker.record("Can read .csv", dr.can_read("test.csv"))
    tracker.record("Can read .json", dr.can_read("test.json"))
    tracker.record("Can read .py", dr.can_read("test.py"))
    tracker.record("Cannot read .exe", not dr.can_read("test.exe"))
    
    # Test reading a temp file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp.write("Seven AI test content\nLine 2\nLine 3")
    tmp.close()
    
    result = dr.read_document(tmp.name)
    tracker.record("Read txt file", result['success'] and 'Seven AI' in result['text'])
    os.unlink(tmp.name)
    
    # Test missing file
    result = dr.read_document("nonexistent.pdf")
    tracker.record("Missing file handled", not result['success'])
    
except Exception as e:
    tracker.record("Document reader tests", False, str(e)[:100])


# ============================================================
# 12. OLLAMA MODEL MANAGER TESTS
# ============================================================
print("\n" + "="*60)
print("12. OLLAMA MODEL MANAGER TESTS")
print("="*60)

try:
    from integrations.ollama_manager import OllamaManager
    om = OllamaManager()
    
    tracker.record("OllamaManager init", True)
    tracker.record("Has list_models", callable(getattr(om, 'list_models', None)))
    tracker.record("Has pull_model", callable(getattr(om, 'pull_model', None)))
    tracker.record("Has remove_model", callable(getattr(om, 'remove_model', None)))
    tracker.record("Has switch_model", callable(getattr(om, 'switch_model', None)))
    tracker.record("Has check_disk_usage", callable(getattr(om, 'check_disk_usage', None)))
    
    # Test list (requires Ollama running)
    models = om.list_models()
    if "Can't connect" not in models:
        tracker.record("List models works", "Installed" in models or "No models" in models)
    else:
        tracker.record("List models works", False, "Ollama not running", skipped=True)
    
    # Safety check: can't remove active model
    result = om.remove_model("llama3.2")
    tracker.record("Active model removal blocked", "Can't remove" in result)
    
except Exception as e:
    tracker.record("Ollama manager tests", False, str(e)[:100])


# ============================================================
# 12b. DATABASE MANAGER TESTS
# ============================================================
print("\n" + "="*60)
print("12b. DATABASE MANAGER TESTS")
print("="*60)

try:
    from integrations.database_manager import DatabaseManager
    dm = DatabaseManager()
    
    tracker.record("DatabaseManager init", True)
    tracker.record("DB drivers detected", 'sqlite' in dm.drivers)
    tracker.record("Has add_connection", callable(getattr(dm, 'add_connection', None)))
    tracker.record("Has connect", callable(getattr(dm, 'connect', None)))
    tracker.record("Has run_query", callable(getattr(dm, 'run_query', None)))
    tracker.record("Has natural_query", callable(getattr(dm, 'natural_query', None)))
    tracker.record("Has explore_database", callable(getattr(dm, 'explore_database', None)))
    tracker.record("Has describe_table", callable(getattr(dm, 'describe_table', None)))
    tracker.record("Has analyze_table", callable(getattr(dm, 'analyze_table', None)))
    tracker.record("Has export_to_csv", callable(getattr(dm, 'export_to_csv', None)))
    tracker.record("Has export_to_json", callable(getattr(dm, 'export_to_json', None)))
    
    # Test SQLite quick connect + query
    result = dm.quick_connect_sqlite(':memory:')
    tracker.record("SQLite connect", 'Connected' in result or 'successfully' in result)
    
    # Create a test table and query it
    dm.run_query("CREATE TABLE test_users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    dm.run_query("INSERT INTO test_users VALUES (1, 'Alice', 30)")
    dm.run_query("INSERT INTO test_users VALUES (2, 'Bob', 25)")
    
    result = dm.run_query("SELECT * FROM test_users")
    tracker.record("SQLite query works", result['success'] and result['row_count'] == 2)
    tracker.record("Query returns columns", result['columns'] == ['id', 'name', 'age'])
    
    tables = dm.list_tables()
    tracker.record("List tables works", 'test_users' in tables)
    
    desc = dm.describe_table('test_users')
    tracker.record("Describe table works", 'name' in desc and 'age' in desc)
    
    explore = dm.explore_database()
    tracker.record("Explore database works", 'test_users' in explore)
    
    # Test export
    csv_result = dm.export_to_csv("SELECT * FROM test_users")
    tracker.record("Export CSV works", 'Exported' in csv_result)
    
    json_result = dm.export_to_json("SELECT * FROM test_users")
    tracker.record("Export JSON works", 'Exported' in json_result)
    
    # Test no-connection error handling
    dm.disconnect()
    result = dm.run_query("SELECT 1")
    tracker.record("No-connection handled", not result['success'])
    
    dm.cleanup()
    
except Exception as e:
    tracker.record("Database manager tests", False, str(e)[:100])


# ============================================================
# 12c. API EXPLORER TESTS
# ============================================================
print("\n" + "="*60)
print("12c. API EXPLORER TESTS")
print("="*60)

try:
    from integrations.api_explorer import APIExplorer
    ae = APIExplorer()
    
    tracker.record("APIExplorer init", True)
    tracker.record("APIExplorer.available", ae.available)
    tracker.record("Has add_api", callable(getattr(ae, 'add_api', None)))
    tracker.record("Has get", callable(getattr(ae, 'get', None)))
    tracker.record("Has post", callable(getattr(ae, 'post', None)))
    tracker.record("Has explore_endpoint", callable(getattr(ae, 'explore_endpoint', None)))
    tracker.record("Has explore_api", callable(getattr(ae, 'explore_api', None)))
    tracker.record("Has natural_call", callable(getattr(ae, 'natural_call', None)))
    tracker.record("Has check_api_health", callable(getattr(ae, 'check_api_health', None)))
    
    # Test adding an API
    result = ae.add_api('test', 'https://jsonplaceholder.typicode.com')
    tracker.record("Add API", 'saved' in result.lower())
    tracker.record("API in list", 'test' in ae.apis)
    
    # Test GET (real network call — may fail if offline)
    if ae.available:
        resp = ae.get('https://jsonplaceholder.typicode.com/posts/1')
        tracker.record("GET request works", resp.get('success', False), f"Status: {resp.get('status_code')}")
    
    # Cleanup
    ae.remove_api('test')
    tracker.record("Remove API", 'test' not in ae.apis)
    
except Exception as e:
    tracker.record("API explorer tests", False, str(e)[:100])


# ============================================================
# 13. CONFIG COMPLETENESS TEST
# ============================================================
print("\n" + "="*60)
print("13. CONFIG COMPLETENESS TEST")
print("="*60)

required_flags = [
    'ENABLE_MUSIC_PLAYER', 'ENABLE_SSH_MANAGER', 'ENABLE_SYSTEM_MONITOR',
    'ENABLE_CLIPBOARD_MONITOR', 'ENABLE_SCREEN_CONTROL', 'ENABLE_SELF_SCRIPTING',
    'ENABLE_EMAIL_CHECKER', 'ENABLE_TIMER_SYSTEM', 'ENABLE_DOCUMENT_READER',
    'ENABLE_MODEL_MANAGER', 'ENABLE_DATABASE_MANAGER', 'ENABLE_API_EXPLORER',
    'ENABLE_PROACTIVE_BEHAVIOR', 'ENABLE_CREATIVE_EXPRESSION',
    'ENABLE_CURIOSITY', 'ENABLE_SELF_REFLECTION', 'ENABLE_VISION',
    'ENABLE_V2_SENTIENCE', 'ENABLE_PHASE5', 'ENABLE_AUTONOMOUS_EXECUTION',
]

for flag in required_flags:
    tracker.record(f"Config: {flag}", hasattr(config, flag), getattr(config, flag, 'MISSING'))


# ============================================================
# 14. ENHANCED BOT WIRING TEST
# ============================================================
print("\n" + "="*60)
print("14. ENHANCED BOT WIRING TEST")
print("="*60)

try:
    from core.enhanced_bot import UltimateBotCore
    
    # Check that all handler methods exist on the class
    handlers = [
        '_handle_music_request', '_handle_timer_request', '_handle_ssh_request',
        '_handle_screen_request', '_handle_email_request', '_handle_clipboard_request',
        '_handle_document_request', '_handle_system_monitor_request',
        '_handle_scripting_request', '_handle_model_request',
        '_handle_database_request', '_handle_api_request',
        '_build_capabilities_context', '_try_dynamic_command',
        '_ask_ollama_enhanced',
    ]
    
    for handler in handlers:
        tracker.record(f"Handler: {handler}", hasattr(UltimateBotCore, handler))
    
except Exception as e:
    tracker.record("Enhanced bot wiring tests", False, str(e)[:100])


# ============================================================
# 15. PERSONALITY SYSTEM TESTS
# ============================================================
print("\n" + "="*60)
print("15. PERSONALITY SYSTEM TESTS")
print("="*60)

try:
    from core.personality import PersonalityCore
    from core.memory import MemoryManager
    
    mem = MemoryManager()
    pc = PersonalityCore(mem)
    
    tracker.record("PersonalityCore init", True)
    tracker.record("Has _generate_curiosity_question", callable(getattr(pc, '_generate_curiosity_question', None)))
    tracker.record("Has _share_observation", callable(getattr(pc, '_share_observation', None)))
    tracker.record("Has _express_emotion", callable(getattr(pc, '_express_emotion', None)))
    tracker.record("Has _suggest_activity", callable(getattr(pc, '_suggest_activity', None)))
    tracker.record("Has _reflect_aloud", callable(getattr(pc, '_reflect_aloud', None)))
    tracker.record("Has generate_surprise", callable(getattr(pc, 'generate_surprise', None)))
    tracker.record("Has create_something", callable(getattr(pc, 'create_something', None)))
    
    # Test canned fallbacks work (no Ollama wired)
    q = pc._generate_curiosity_question()
    tracker.record("Curiosity question (fallback)", q is not None and len(q) > 10)
    
    obs = pc._share_observation()
    tracker.record("Observation (fallback)", obs is not None and len(obs) > 10)
    
    act = pc._suggest_activity()
    tracker.record("Activity suggestion (fallback)", act is not None and len(act) > 10)
    
except Exception as e:
    tracker.record("Personality tests", False, str(e)[:100])


# ============================================================
# 16. AUTONOMOUS LIFE TESTS
# ============================================================
print("\n" + "="*60)
print("16. AUTONOMOUS LIFE TESTS")
print("="*60)

try:
    from core.autonomous_life import AutonomousLife
    
    # Use mock bot
    mock_bot = MagicMock()
    mock_bot.phase5 = None
    al = AutonomousLife(mock_bot)
    
    tracker.record("AutonomousLife init", True)
    tracker.record("Has message queue", hasattr(al, '_message_queue'))
    tracker.record("Has queue_message", callable(getattr(al, 'queue_message', None)))
    tracker.record("Has get_pending_message", callable(getattr(al, 'get_pending_message', None)))
    tracker.record("Has has_pending_messages", callable(getattr(al, 'has_pending_messages', None)))
    tracker.record("Has mark_user_interaction", callable(getattr(al, 'mark_user_interaction', None)))
    tracker.record("Has _check_user_presence", callable(getattr(al, '_check_user_presence', None)))
    tracker.record("Has _save_state", callable(getattr(al, '_save_state', None)))
    tracker.record("Has _load_state", callable(getattr(al, '_load_state', None)))
    
    # Test message queue
    al.queue_message("Test message", priority="high")
    tracker.record("Queue message", al.has_pending_messages())
    msg = al.get_pending_message()
    tracker.record("Get message", msg == "Test message")
    tracker.record("Queue empty after get", not al.has_pending_messages())
    
    # Test user presence
    al.mark_user_interaction()
    tracker.record("Mark interaction", not al.user_away)
    
except Exception as e:
    tracker.record("Autonomous life tests", False, str(e)[:100])


# ============================================================
# 17. CROSS-REFERENCE VALIDATION
# ============================================================
print("\n" + "="*60)
print("17. CROSS-REFERENCE VALIDATION")
print("="*60)

# Verify all integration files exist
integration_files = [
    "music_player.py", "ssh_manager.py", "system_monitor.py",
    "clipboard_assistant.py", "screen_control.py", "self_scripting.py",
    "email_checker.py", "timer_system.py", "document_reader.py",
    "ollama_manager.py", "ollama.py", "web_search.py",
    "database_manager.py", "api_explorer.py",
]

integrations_dir = Path(__file__).parent.parent / "integrations"
for f in integration_files:
    exists = (integrations_dir / f).exists()
    tracker.record(f"File: integrations/{f}", exists)

# Verify core files
core_files = [
    "enhanced_bot.py", "autonomous_life.py", "seven_true_autonomy.py",
    "personality.py", "emotions.py", "memory.py", "knowledge_graph.py",
    "emotional_complexity.py", "metacognition.py", "vulnerability.py",
]

core_dir = Path(__file__).parent.parent / "core"
for f in core_files:
    exists = (core_dir / f).exists()
    tracker.record(f"File: core/{f}", exists)


# ============================================================
# FINAL REPORT
# ============================================================
print("\n" + "="*60)
print("SEVEN AI — TEST RESULTS")
print("="*60)

total = tracker.passed + tracker.failed + tracker.skipped
print(f"\n  Total:   {total}")
print(f"  Passed:  {tracker.passed} ✓")
print(f"  Failed:  {tracker.failed} ✗")
print(f"  Skipped: {tracker.skipped} ⊘")
print(f"\n  Score:   {tracker.passed}/{tracker.passed + tracker.failed} ({100*tracker.passed/max(tracker.passed+tracker.failed,1):.0f}%)")

if tracker.failed > 0:
    print(f"\n  FAILURES:")
    for status, name, message in tracker.results:
        if status == "FAIL":
            print(f"    ✗ {name}: {message}")

print("\n" + "="*60)

# Exit code for CI
if tracker.failed > 0:
    print(f"\n{tracker.failed} test(s) FAILED.")
    sys.exit(1)
else:
    print(f"\nAll {tracker.passed} tests PASSED!")
    sys.exit(0)
