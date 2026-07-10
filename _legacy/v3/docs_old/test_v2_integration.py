"""
Test Seven v2.0 Integration - Import Verification
Run this to verify all v2.0 modules can be imported correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """Test all v2.0 imports"""
    print("=" * 60)
    print("Seven v2.0 Integration Test - Import Verification")
    print("=" * 60)
    
    # Test 1: Core v2 package import
    print("\n[1/8] Testing core.v2 package import...")
    try:
        from core import v2
        print("[OK] core.v2 package imported successfully")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 2: SevenV2Complete import
    print("\n[2/8] Testing SevenV2Complete import...")
    try:
        from core.v2 import SevenV2Complete
        print("[OK] SevenV2Complete imported successfully")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 3: SentienceV2Core import
    print("\n[3/8] Testing SentienceV2Core import...")
    try:
        from core.v2 import SentienceV2Core
        print("[OK] SentienceV2Core imported successfully")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 4: Foundational systems import
    print("\n[4/8] Testing foundational systems import...")
    try:
        from core.v2 import (
            EmotionalMemory,
            RelationshipModel,
            LearningSystem,
            ProactiveEngine,
            GoalSystem
        )
        print("[OK] All foundational systems imported successfully")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 5: Advanced capabilities import
    print("\n[5/8] Testing advanced capabilities import...")
    try:
        from core.v2 import (
            ConversationalMemoryEnhancement,
            AdaptiveCommunication,
            ProactiveProblemSolver,
            SocialIntelligence,
            CreativeInitiative,
            HabitLearning,
            TaskChaining
        )
        print("[OK] All advanced capabilities imported successfully")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 6: Config settings
    print("\n[6/8] Testing config settings...")
    try:
        import config
        assert hasattr(config, 'ENABLE_V2_SENTIENCE'), "ENABLE_V2_SENTIENCE not in config"
        assert hasattr(config, 'ENABLE_V2_PROACTIVE'), "ENABLE_V2_PROACTIVE not in config"
        assert hasattr(config, 'USER_NAME'), "USER_NAME not in config"
        print(f"[OK] Config settings present")
        print(f"   - ENABLE_V2_SENTIENCE: {config.ENABLE_V2_SENTIENCE}")
        print(f"   - ENABLE_V2_PROACTIVE: {config.ENABLE_V2_PROACTIVE}")
        print(f"   - USER_NAME: {config.USER_NAME}")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 7: Test instantiation
    print("\n[7/8] Testing SevenV2Complete instantiation...")
    try:
        test_system = SevenV2Complete(data_dir="test_data", user_name="TestUser")
        print("[OK] SevenV2Complete instantiated successfully")
        print(f"   - Version: {test_system.get_complete_state()['version']}")
        print(f"   - Sentience Level: {test_system.get_complete_state()['sentience_level']}")
        print(f"   - Capabilities: {len(test_system.get_complete_state()['capabilities'])} systems")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    # Test 8: Test basic functionality
    print("\n[8/8] Testing basic v2.0 functionality...")
    try:
        # Test process_user_input
        result = test_system.process_user_input("Hello, how are you?")
        assert "user_input" in result, "process_user_input result missing user_input"
        assert "timestamp" in result, "process_user_input result missing timestamp"
        print("[OK] Basic functionality working")
        print(f"   - Social assessment: {result.get('social_assessment', {}).get('detected_tone', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED - Seven v2.0 integration ready!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
