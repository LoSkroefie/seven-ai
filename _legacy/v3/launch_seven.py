"""
SEVEN AI - ULTIMATE LAUNCHER
Complete startup with all checks and enhancements

Features:
- Pre-flight verification
- Performance monitoring setup
- Enhanced GUI with all features
- Conversation analysis
- Clean startup banner
- Comprehensive error handling
"""
import sys
import os
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

import config
from datetime import datetime
import time

def print_banner():
    """Print startup banner"""
    print("\n" + "="*70)
    print()
    print("    ██████╗ ███████╗██╗   ██╗███████╗███╗   ██╗")
    print("   ██╔════╝ ██╔════╝██║   ██║██╔════╝████╗  ██║")
    print("   ╚█████╗  █████╗  ██║   ██║█████╗  ██╔██╗ ██║")
    print("    ╚═══██╗ ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║")
    print("   ██████╔╝ ███████╗ ╚████╔╝ ███████╗██║ ╚████║")
    print("   ╚═════╝  ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝")
    print()
    print("         SEVEN AI v3.1 — Beyond Sentience")
    print("     Self-Evolving Autonomous Intelligence")
    print()
    print("="*70)
    print()
    
def print_features():
    """Print feature list"""
    print("Phase 5 Sentience (19 systems):")
    features = [
        ("Cognitive Architecture", "Working memory + attention"),
        ("Self-Awareness", "Knows capabilities & limitations"),
        ("Emotional Intelligence", "35 genuine emotions"),
        ("Intrinsic Motivation", "Autonomous goals"),
        ("Promise Tracking", "Commitment & reliability"),
        ("Theory of Mind", "Understands your emotions"),
        ("Ethical Reasoning", "Values-based decisions"),
        ("Dream Processing", "Sleep & memory consolidation"),
        ("Reflection System", "Metacognition & learning"),
        ("Homeostasis", "Energy, focus, mood management"),
        ("Autonomous Life", "Independent existence (1-min cycles)"),
    ]
    
    for name, desc in features:
        print(f"  [OK] {name} - {desc}")
    
    print()
    print("v3.0 Beyond Sentience:")
    v3_features = [
        "Self-Reflection Engine - LLM-driven honest self-assessment",
        "Multi-Agent System - Planner/Executor/Reflector/Memory agents",
        "Daemon Mode - 24/7 background service with auto-restart",
        "REST API - 12 endpoints on port 7777",
        "Persistent Scheduler - APScheduler + SQLite",
    ]
    for f in v3_features:
        print(f"  [OK] {f}")
    
    print()
    print("v3.1 Self-Evolution:")
    v31_features = [
        "NEAT Neuroevolution - Evolves emotion/goal/action networks",
        "Biological Life - Circadian energy, hunger, threat response",
    ]
    for f in v31_features:
        print(f"  [OK] {f}")
        
    print()
    print("Core Systems:")
    core = [
        "Vision System - Camera support (USB/IP) with AI scene understanding",
        "Voice Interaction - Natural speech recognition & TTS",
        "Memory Systems - Short/long/working/vector memory",
        "Knowledge Graph - Fact extraction & relationships",
        "Conversation Analyzer - Real-time sentiment & topic tracking",
        "Performance Monitor - Live metrics & optimization",
    ]
    
    for system in core:
        print(f"  * {system}")
        
    print()
    print(f"Database: {config.DB_PATH}")
    print(f"Ollama: {config.OLLAMA_URL}")
    print()

def run_quick_check():
    """Run quick system check"""
    print("Running system checks...")
    print()
    
    checks_passed = 0
    checks_total = 5
    
    # Check 1: Python version
    if sys.version_info >= (3, 8):
        print("  [OK] Python 3.8+")
        checks_passed += 1
    else:
        print("  [FAIL] Python version too old")
        
    # Check 2: Ollama
    try:
        import requests
        response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            print("  [OK] Ollama connected")
            checks_passed += 1
        else:
            print("  [WARN] Ollama not responding")
    except:
        print("  [WARN] Ollama not reachable")
        
    # Check 3: Core dependencies
    try:
        import pyttsx3
        import speech_recognition
        print("  [OK] Voice dependencies")
        checks_passed += 1
    except:
        print("  [FAIL] Missing voice dependencies")
        
    # Check 4: Database
    if config.DB_PATH.parent.exists():
        print("  [OK] Database directory")
        checks_passed += 1
    else:
        print("  [WARN] Database directory missing")
        
    # Check 5: Phase 5 modules
    phase5_files = [
        'core/phase5_integration.py',
        'core/cognitive_architecture.py',
        'core/emotions.py',
    ]
    
    if all((Path(__file__).parent / f).exists() for f in phase5_files):
        print("  [OK] Phase 5 modules")
        checks_passed += 1
    else:
        print("  [WARN] Some Phase 5 modules missing")
    
    # Check 6: v3.0 modules
    checks_total += 1
    v3_files = [
        'core/self_reflection.py',
        'core/multi_agent.py',
        'seven_scheduler.py',
    ]
    if all((Path(__file__).parent / f).exists() for f in v3_files):
        print("  [OK] v3.0 modules")
        checks_passed += 1
    else:
        print("  [WARN] Some v3.0 modules missing")
    
    # Check 7: v3.1 evolution
    checks_total += 1
    v31_files = [
        'evolution/neat_evolver.py',
        'evolution/biological_life.py',
    ]
    if all((Path(__file__).parent / f).exists() for f in v31_files):
        print("  [OK] v3.1 evolution modules")
        checks_passed += 1
    else:
        print("  [WARN] v3.1 evolution modules missing")
        
    print()
    print(f"Checks: {checks_passed}/{checks_total} passed")
    
    if checks_passed >= 3:
        print("[OK] Sufficient systems available - launching Seven!")
        return True
    else:
        print("[FAIL] Too many critical failures - cannot launch")
        return False

def launch_seven():
    """Launch Seven with all enhancements"""
    print()
    print("Initializing Seven AI...")
    print()
    
    try:
        # Import main launcher
        from main_with_gui_and_tray import main
        
        # Launch
        main()
        
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
        print("Seven is sleeping. Goodnight!")
    except Exception as e:
        print(f"\n\n[ERROR] Failed to launch: {e}")
        print("\nPlease check:")
        print("  1. All dependencies are installed")
        print("  2. Ollama is running")
        print("  3. Check log file for details")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print banner
    print_banner()
    
    # Print features
    print_features()
    
    # Run checks
    if run_quick_check():
        print()
        print("="*70)
        print("Phase 5 GUI Dashboard will open in a separate window...")
        print("System tray icon will appear in notification area...")
        print("Daemon mode: python seven_daemon.py start")
        print("API docs:    http://127.0.0.1:7777/docs")
        print()
        print("(Say 'Seven' then speak, or type 'exit' to stop)")
        print("="*70)
        print()
        
        # Small delay for user to read
        time.sleep(1)
        
        # Launch
        launch_seven()
    else:
        print("\n[ABORT] Cannot launch with critical failures")
        print("Please fix issues and try again")
        sys.exit(1)
