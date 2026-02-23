"""
Test Script - Verify All Fixes Are Working

This script tests:
1. Phase 5 integration
2. Autonomous life system
3. Vision system (basic)
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all new modules can be imported"""
    print("Testing imports...")
    
    try:
        from core.phase5_integration import Phase5Integration
        print("  [OK] Phase5Integration")
    except Exception as e:
        print(f"  [FAIL] Phase5Integration: {e}")
        return False
    
    try:
        from core.autonomous_life import AutonomousLife
        print("  [OK] AutonomousLife")
    except Exception as e:
        print(f"  [FAIL] AutonomousLife: {e}")
        return False
    
    try:
        from core.vision_system import VisionSystem
        print("  [OK] VisionSystem")
    except Exception as e:
        print(f"  [FAIL] VisionSystem: {e}")
        return False
    
    return True

def test_config():
    """Test that config has new settings"""
    print("\nTesting config...")
    
    import config
    
    checks = [
        ('ENABLE_PHASE5', True),
        ('ENABLE_VISION', True),
        ('VISION_CAMERAS', list),
        ('VISION_WEBCAM_INDEX', int),
    ]
    
    for setting, expected_type in checks:
        if hasattr(config, setting):
            value = getattr(config, setting)
            if expected_type == type(value) or (expected_type == True and value == True):
                print(f"  ✓ {setting} = {value}")
            else:
                print(f"  ✗ {setting} has wrong type")
                return False
        else:
            print(f"  ✗ {setting} not found")
            return False
    
    return True

def test_phase5():
    """Test Phase 5 integration"""
    print("\nTesting Phase 5 integration...")
    
    try:
        from core.phase5_integration import Phase5Integration
        from core.identity_manager import IdentityManager
        from core.memory import MemoryManager
        from core.knowledge_graph import KnowledgeGraph
        
        # Create minimal instances
        identity_mgr = IdentityManager()
        memory_mgr = MemoryManager()
        knowledge_graph = KnowledgeGraph()
        
        # Try to create Phase5
        phase5 = Phase5Integration(
            identity_manager=identity_mgr,
            memory_manager=memory_mgr,
            knowledge_graph=knowledge_graph
        )
        
        print("  ✓ Phase5Integration created successfully")
        
        # Test basic functionality
        result = phase5.process_user_input("Hello!")
        print(f"  ✓ process_user_input works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Phase 5 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_autonomous_life():
    """Test autonomous life system"""
    print("\nTesting Autonomous Life...")
    
    try:
        from core.autonomous_life import AutonomousLife
        
        # Create mock bot
        class MockBot:
            def __init__(self):
                self.phase5 = None
                self.logger = None
                
                # Setup logger
                from utils.logger import setup_logger
                self.logger = setup_logger("MockBot")
        
        bot = MockBot()
        
        # Create autonomous life
        auto_life = AutonomousLife(bot)
        print("  ✓ AutonomousLife created")
        
        # Start it
        auto_life.start()
        print("  ✓ AutonomousLife started")
        
        # Let it run for 3 seconds
        time.sleep(3)
        
        # Check status
        status = auto_life.get_status()
        print(f"  ✓ Status: {status['running']}, cycles: {status['cycles_completed']}")
        
        # Stop it
        auto_life.stop()
        print("  ✓ AutonomousLife stopped")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Autonomous life test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision_system():
    """Test vision system (without camera)"""
    print("\nTesting Vision System...")
    
    try:
        from core.vision_system import VisionSystem
        
        # Create mock bot
        class MockBot:
            def __init__(self):
                self.phase5 = None
                self.ollama = None
                self.logger = None
                
                # Setup logger
                from utils.logger import setup_logger
                self.logger = setup_logger("MockBot")
        
        bot = MockBot()
        
        # Create vision system (disabled)
        vision_config = {
            'enabled_cameras': [],  # No cameras for test
            'analysis_interval': 30
        }
        
        vision = VisionSystem(bot, vision_config)
        print("  ✓ VisionSystem created")
        
        # Test get_status
        status = vision.get_status()
        print(f"  ✓ Status: running={status['running']}, cameras={status['cameras']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Vision system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING ALL CRITICAL FIXES")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Config", test_config),
        ("Phase 5", test_phase5),
        ("Autonomous Life", test_autonomous_life),
        ("Vision System", test_vision_system),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{name} test crashed: {e}")
            results.append((name, False))
        
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Seven is ready to be alive!")
        print()
        print("Next steps:")
        print("  1. Find nanny cam: python find_cameras.py")
        print("  2. Configure cameras in config.py")
        print("  3. Launch Seven: python main.py")
        return 0
    else:
        print("[WARNING]  SOME TESTS FAILED")
        print()
        print("Check error messages above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print()
    input("Press Enter to exit...")
    sys.exit(exit_code)

