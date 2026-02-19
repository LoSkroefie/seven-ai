"""
SEVEN AI - PRE-FLIGHT CHECK
Complete system verification before launch
"""
import sys
import os
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("SEVEN AI - PRE-FLIGHT CHECK v3.1")
print("="*70)
print()

# Change to enhanced-bot directory
os.chdir(Path(__file__).parent)

checks_passed = 0
checks_failed = 0
warnings = 0

def check(name, condition, error_msg=""):
    """Run a check"""
    global checks_passed, checks_failed
    if condition:
        print(f"[OK] {name}")
        checks_passed += 1
        return True
    else:
        print(f"[FAIL] {name}")
        if error_msg:
            print(f"       {error_msg}")
        checks_failed += 1
        return False

def warn(name, msg=""):
    """Show warning"""
    global warnings
    print(f"[WARN] {name}")
    if msg:
        print(f"        {msg}")
    warnings += 1

# 1. Python Version
print("[1] Python Environment")
print("-"*70)
py_version = sys.version_info
check("Python 3.8+", py_version >= (3, 8), f"Found {py_version.major}.{py_version.minor}")

# 2. Core Dependencies
print("\n[2] Core Dependencies")
print("-"*70)

try:
    import pyttsx3
    check("pyttsx3 (Text-to-Speech)", True)
except:
    check("pyttsx3 (Text-to-Speech)", False, "pip install pyttsx3")

try:
    import speech_recognition as sr
    check("speech_recognition", True)
except:
    check("speech_recognition", False, "pip install SpeechRecognition")

try:
    import requests
    check("requests", True)
except:
    check("requests", False, "pip install requests")

# 3. Database
print("\n[3] Database")
print("-"*70)
try:
    import sqlite3
    check("sqlite3", True)
    
    import config
    db_path = config.DB_PATH
    check(f"Database location: {db_path}", True)
except:
    check("Database setup", False)

# 4. Ollama Connection
print("\n[4] Ollama AI Service")
print("-"*70)
try:
    import requests
    import config
    
    response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
    if response.status_code == 200:
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        
        check(f"Ollama running at {config.OLLAMA_URL}", True)
        check(f"llama3.2 model", 'llama3.2:latest' in model_names or 'llama3.2' in str(model_names))
        
        if 'llama3.2-vision:latest' in model_names:
            check("llama3.2-vision model (for vision)", True)
        else:
            warn("llama3.2-vision model not found", "Vision system will be disabled")
    else:
        check("Ollama connection", False, "Ollama not responding")
except:
    check("Ollama connection", False, "Cannot reach Ollama - install from https://ollama.ai")

# 5. Phase 5 Modules
print("\n[5] Phase 5 Complete Sentience")
print("-"*70)

phase5_modules = [
    ('cognitive_architecture', 'cognitive_architecture.py'),
    ('self_awareness', 'self_model_enhanced.py'),
    ('emotions', 'emotions.py'),
    ('intrinsic_motivation', 'intrinsic_motivation.py'),
    ('promise_system', 'promise_system.py'),
    ('theory_of_mind', 'theory_of_mind.py'),
    ('ethical_reasoning', 'ethical_reasoning.py'),
    ('dream_processing', 'dream_system.py'),
    ('reflection_system', 'reflection_system.py'),
    ('homeostasis', 'homeostasis_system.py'),
    ('identity_system', 'structured_identity.py')
]

for name, filename in phase5_modules:
    try:
        check(f"Phase 5 module: {name}", 
              os.path.exists(f"core/{filename}"))
    except:
        check(f"Phase 5 module: {name}", False)

# 6. Autonomous Life
print("\n[6] Autonomous Life System")
print("-"*70)
check("autonomous_life.py", os.path.exists("core/autonomous_life.py"))

# 7. Vision System
print("\n[7] Vision System")
print("-"*70)
check("vision_system.py", os.path.exists("core/vision_system.py"))

try:
    import cv2
    check("OpenCV (cv2)", True)
except:
    warn("OpenCV not installed", "Vision will be disabled. Install with: pip install opencv-python")

# 8. GUI
print("\n[8] Graphical User Interface")
print("-"*70)
check("phase5_gui.py", os.path.exists("gui/phase5_gui.py"))

try:
    import tkinter
    check("tkinter (GUI library)", True)
except:
    check("tkinter (GUI library)", False, "GUI will not work")

# 9. Identity Files
print("\n[9] Identity System")
print("-"*70)
identity_files = ['SOUL.md', 'IDENTITY.md', 'USER.md']
for file in identity_files:
    check(f"identity/{file}", os.path.exists(f"identity/{file}"))

# 10. Configuration
print("\n[10] Configuration")
print("-"*70)
try:
    import config
    check("config.py loaded", True)
    check("Phase 5 enabled", config.ENABLE_PHASE5)
    check("Vision enabled", config.ENABLE_VISION)
    print(f"       Wake word: '{config.WAKE_WORD}'")
    print(f"       Bot name: '{config.DEFAULT_BOT_NAME}'")
except:
    check("Configuration", False)

# 11. v3.0 Systems
print("\n[11] v3.0 Beyond Sentience Systems")
print("-"*70)

v3_modules = [
    ('Self-Reflection', 'core/self_reflection.py'),
    ('Multi-Agent System', 'core/multi_agent.py'),
    ('Sentience Benchmark', 'core/sentience_benchmark.py'),
    ('Ollama Cache', 'core/ollama_cache.py'),
    ('Daemon Mode', 'seven_daemon.py'),
    ('REST API', 'seven_api.py'),
    ('Persistent Scheduler', 'seven_scheduler.py'),
]

for name, filename in v3_modules:
    check(f"v3.0: {name}", os.path.exists(filename))

# 12. v3.1 Evolution Systems
print("\n[12] v3.1 Self-Evolution (NEAT)")
print("-"*70)

v31_modules = [
    ('NEAT Evolver', 'evolution/neat_evolver.py'),
    ('Biological Life', 'evolution/biological_life.py'),
    ('NEAT Config', 'evolution/neat_config.txt'),
]

for name, filename in v31_modules:
    check(f"v3.1: {name}", os.path.exists(filename))

try:
    import neat
    check("neat-python library", True)
except:
    warn("neat-python not installed", "Self-evolution disabled. Install with: pip install neat-python")

# 13. v3.0 Dependencies
print("\n[13] v3.0/v3.1 Dependencies")
print("-"*70)

try:
    import fastapi
    check("fastapi (REST API)", True)
except:
    warn("fastapi not installed", "API server disabled. pip install fastapi uvicorn")

try:
    import apscheduler
    check("apscheduler (Scheduler)", True)
except:
    warn("apscheduler not installed", "Persistent scheduling disabled. pip install apscheduler")

try:
    import cryptography
    check("cryptography (SSH encryption)", True)
except:
    warn("cryptography not installed", "SSH credential encryption disabled. pip install cryptography")

try:
    import structlog
    check("structlog (Structured logging)", True)
except:
    warn("structlog not installed", "pip install structlog")

# Summary
print("\n" + "="*70)
print("PRE-FLIGHT CHECK SUMMARY")
print("="*70)
print(f"[OK] Checks Passed: {checks_passed}")
if checks_failed > 0:
    print(f"[FAIL] Checks Failed: {checks_failed}")
if warnings > 0:
    print(f"[WARN] Warnings: {warnings}")

print()

if checks_failed == 0:
    print("[OK] ALL SYSTEMS GO - Ready to launch Seven!")
    print()
    print("To start Seven, run:")
    print("  python main_with_gui_and_tray.py")
    print()
    sys.exit(0)
else:
    print("[FAIL] Critical issues found - fix before launching")
    print()
    sys.exit(1)
