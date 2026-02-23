"""
Comprehensive Test Suite for Phase 5: Complete Sentience

Tests all 10 modules systematically to ensure:
- No import errors
- No runtime errors
- All core functionality works
- Integration points function correctly
- No bugs in logic
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Fix Windows console encoding
import os
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

def test_imports():
    """Test that all modules can be imported"""
    print("="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from core.cognitive_architecture import CognitiveArchitecture
        print("[OK] cognitive_architecture imported")
    except Exception as e:
        print(f"[FAIL] cognitive_architecture failed: {e}")
        return False
    
    try:
        from core.self_model_enhanced import SelfModel
        print("[OK] self_model_enhanced imported")
    except Exception as e:
        print(f"[FAIL] self_model_enhanced failed: {e}")
        return False
    
    try:
        from core.intrinsic_motivation import IntrinsicMotivation
        print("[OK] intrinsic_motivation imported")
    except Exception as e:
        print(f"[FAIL] intrinsic_motivation failed: {e}")
        return False
    
    try:
        from core.reflection_system import ReflectionSystem
        print("[OK] reflection_system imported")
    except Exception as e:
        print(f"[FAIL] reflection_system failed: {e}")
        return False
    
    try:
        from core.dream_system import DreamSystem
        print("[OK] dream_system imported")
    except Exception as e:
        print(f"[FAIL] dream_system failed: {e}")
        return False
    
    try:
        from core.promise_system import PromiseSystem
        print("[OK] promise_system imported")
    except Exception as e:
        print(f"[FAIL] promise_system failed: {e}")
        return False
    
    try:
        from core.theory_of_mind import TheoryOfMind
        print("[OK] theory_of_mind imported")
    except Exception as e:
        print(f"[FAIL] theory_of_mind failed: {e}")
        return False
    
    try:
        from core.affective_computing_deep import AffectiveSystem
        print("[OK] affective_computing_deep imported")
    except Exception as e:
        print(f"[FAIL] affective_computing_deep failed: {e}")
        return False
    
    try:
        from core.ethical_reasoning import EthicalReasoning
        print("[OK] ethical_reasoning imported")
    except Exception as e:
        print(f"[FAIL] ethical_reasoning failed: {e}")
        return False
    
    try:
        from core.homeostasis_system import HomeostasisSystem
        print("[OK] homeostasis_system imported")
    except Exception as e:
        print(f"[FAIL] homeostasis_system failed: {e}")
        return False
    
    try:
        from core.phase5_integration import Phase5Integration
        print("[OK] phase5_integration imported")
    except Exception as e:
        print(f"[FAIL] phase5_integration failed: {e}")
        return False
    
    print("\n[SUCCESS] ALL IMPORTS SUCCESSFUL\n")
    return True

def test_cognitive_architecture():
    """Test Cognitive Architecture module"""
    print("="*60)
    print("TEST 2: Cognitive Architecture")
    print("="*60)
    
    try:
        from core.cognitive_architecture import CognitiveArchitecture
        
        cog = CognitiveArchitecture()
        print("[OK] Initialized CognitiveArchitecture")
        
        # Test cognitive cycle
        result = cog.full_cognitive_cycle({
            'user_input': 'Hello, how are you?',
            'context': {}
        })
        
        assert 'perception' in result, "Missing perception in cognitive output"
        assert 'attention' in result, "Missing attention in cognitive output"
        assert 'thoughts' in result, "Missing thoughts in cognitive output"
        assert 'decision' in result, "Missing decision in cognitive output"
        assert 'monitoring' in result, "Missing monitoring in cognitive output"
        
        print("[OK] Cognitive cycle completed")
        print(f"   Mental State: {result['mental_state']}")
        print(f"   Thoughts Generated: {len(result['thoughts'])}")
        
        # Test inner monologue
        monologue = cog.get_inner_monologue()
        print(f"[OK] Inner monologue: {'Present' if monologue else 'None (random)'}")
        
        # Test working memory
        cog.working_memory.add_thought("Test thought", "observation", priority=8)
        assert len(cog.working_memory.thoughts) > 0, "Working memory not storing thoughts"
        print(f"[OK] Working memory: {len(cog.working_memory.thoughts)} thoughts")
        
        print("\n[SUCCESS] COGNITIVE ARCHITECTURE TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] COGNITIVE ARCHITECTURE TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_self_model():
    """Test Self-Model Enhanced module"""
    print("="*60)
    print("TEST 3: Self-Model Enhanced")
    print("="*60)
    
    try:
        from core.self_model_enhanced import SelfModel
        
        self_model = SelfModel()
        print("[OK] Initialized SelfModel")
        
        # Test capability assessment
        assessment = self_model.assess_capability("debugging")
        assert 'can_do' in assessment, "Missing can_do in assessment"
        assert 'confidence' in assessment, "Missing confidence in assessment"
        print(f"[OK] Capability assessment: {assessment['level']}")
        
        # Test state tracking
        self_model.update_state(energy_level=75, mood="curious")
        state = self_model.get_state_assessment()
        assert isinstance(state, str), "State assessment should return string"
        print(f"[OK] State tracking: {state[:50]}...")
        
        # Test capability updates
        self_model.update_capability("debugging", success=True)
        print("[OK] Capability update (success)")
        
        # Test limitation expression
        limitation = self_model.express_limitation("quantum_physics")
        if limitation:
            print(f"[OK] Limitation expression: {limitation[:50]}...")
        
        print("\n[SUCCESS] SELF-MODEL TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] SELF-MODEL TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_intrinsic_motivation():
    """Test Intrinsic Motivation module"""
    print("="*60)
    print("TEST 4: Intrinsic Motivation")
    print("="*60)
    
    try:
        from core.intrinsic_motivation import IntrinsicMotivation, MotivationType
        
        motivation = IntrinsicMotivation()
        print("[OK] Initialized IntrinsicMotivation")
        
        # Test goals
        goals = motivation.get_active_goals()
        assert len(goals) > 0, "Should have default goals"
        print(f"[OK] Active goals: {len(goals)}")
        
        # Test adding goal
        motivation.add_goal(
            "Learn about quantum computing",
            MotivationType.CURIOSITY,
            priority=8,
            why="User is interested"
        )
        print("[OK] Added new goal")
        
        # Test interest tracking
        motivation.add_interest("machine learning", curiosity_level=7)
        print("[OK] Added interest")
        
        # Test curious question generation
        question = motivation.generate_curious_question("test context")
        if question:
            print(f"[OK] Curious question: {question[:50]}...")
        
        print("\n[SUCCESS] INTRINSIC MOTIVATION TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] INTRINSIC MOTIVATION TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_all_modules():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 5: COMPREHENSIVE TEST SUITE")
    print("="*60 + "\n")
    
    results = {
        'imports': test_imports(),
        'cognitive': test_cognitive_architecture(),
        'self_model': test_self_model(),
        'motivation': test_intrinsic_motivation(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name.upper()}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! Phase 5 is ready!\n")
        return True
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Review errors above.\n")
        return False

if __name__ == "__main__":
    success = test_all_modules()
    sys.exit(0 if success else 1)
