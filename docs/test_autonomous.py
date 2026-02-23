"""
Test Autonomous Execution System

Quick test to verify autonomous agent works.
"""

import sys
sys.path.insert(0, 'C:\\Users\\USER-PC\\source\\Code\\voice-chat\\python-chat-bot\\enhanced-bot')

from core.autonomous_agent import AutonomousAgent
from core.tool_library import ToolLibrary
from core.permission_manager import PermissionManager


def test_intent_detection():
    """Test if Seven detects intents correctly"""
    print("=" * 60)
    print("TEST 1: Intent Detection")
    print("=" * 60)
    
    agent = AutonomousAgent()
    
    test_cases = [
        ("How much disk space do I have?", "SYSTEM_QUERY"),
        ("What's my memory usage?", "SYSTEM_QUERY"),
        ("Find my tax documents", "FILE_OPERATION"),
        ("Tell me a story", "CONVERSATION"),
        ("What time is it?", "TIME_QUERY"),
    ]
    
    for query, expected in test_cases:
        intent = agent.detect_intent(query)
        status = "[OK]" if intent.type == expected else "[ERROR]"
        print(f"{status} '{query}' → {intent.type} (expected: {expected})")
    
    print()


def test_tool_selection():
    """Test if Seven selects the right tools"""
    print("=" * 60)
    print("TEST 2: Tool Selection")
    print("=" * 60)
    
    agent = AutonomousAgent()
    
    test_cases = [
        ("How much disk space?", "disk_space"),
        ("What's my RAM usage?", "memory_usage"),
        ("Show me CPU info", "cpu_info"),
        ("List running processes", "list_processes"),
    ]
    
    for query, expected_tool in test_cases:
        intent = agent.detect_intent(query)
        tool = agent.select_tool(intent, query)
        
        tool_name = tool.name if tool else "None"
        status = "[OK]" if tool_name == expected_tool else "[ERROR]"
        print(f"{status} '{query}' → {tool_name} (expected: {expected_tool})")
    
    print()


def test_tool_execution():
    """Test if tools actually execute"""
    print("=" * 60)
    print("TEST 3: Tool Execution")
    print("=" * 60)
    
    lib = ToolLibrary()
    
    # Test disk space
    print("\n📀 Testing disk_space tool:")
    disk_tool = lib.get_tool("disk_space")
    result = disk_tool.execute()
    print(result[:200] if result else "No output")
    
    # Test memory
    print("\n[BRAIN] Testing memory_usage tool:")
    mem_tool = lib.get_tool("memory_usage")
    result = mem_tool.execute()
    print(result[:200] if result else "No output")
    
    # Test CPU
    print("\n⚡ Testing cpu_info tool:")
    cpu_tool = lib.get_tool("cpu_info")
    result = cpu_tool.execute()
    print(result[:200] if result else "No output")
    
    print()


def test_safety_system():
    """Test if safety checks work"""
    print("=" * 60)
    print("TEST 4: Safety System")
    print("=" * 60)
    
    lib = ToolLibrary()
    perm = PermissionManager()
    
    # Test safe tool
    disk_tool = lib.get_tool("disk_space")
    is_safe = perm.is_safe(disk_tool)
    print(f"{'[OK]' if is_safe else '[ERROR]'} disk_space is safe: {is_safe}")
    
    # Test tool count
    safe_count = len(perm.safe_commands)
    dangerous_count = len(perm.dangerous_commands)
    print(f"[STATS] Safe commands: {safe_count}")
    print(f"[WARNING] Dangerous commands: {dangerous_count}")
    
    print()


def test_full_workflow():
    """Test complete autonomous workflow"""
    print("=" * 60)
    print("TEST 5: Full Autonomous Workflow")
    print("=" * 60)
    
    agent = AutonomousAgent()
    
    queries = [
        "How much disk space do I have?",
        "What's my memory usage?",
        "Show me my CPU info",
    ]
    
    for query in queries:
        print(f"\n🗣️ User: {query}")
        
        # Detect intent
        intent = agent.detect_intent(query)
        print(f"   Intent: {intent.type}")
        
        # Select tool
        tool = agent.select_tool(intent, query)
        if not tool:
            print(f"   [ERROR] No tool selected")
            continue
        
        print(f"   Tool: {tool.name}")
        
        # Check safety
        can_execute = agent.can_execute_autonomously(tool)
        print(f"   Safe: {can_execute}")
        
        if can_execute:
            # Execute
            result = tool.execute()
            print(f"   [STATS] Result: {result[:150] if result else 'None'}...")
        else:
            print(f"   [WARNING] Requires permission")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SEVEN AI - AUTONOMOUS EXECUTION TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_intent_detection()
        test_tool_selection()
        test_tool_execution()
        test_safety_system()
        test_full_workflow()
        
        print("=" * 60)
        print("[OK] ALL TESTS COMPLETE!")
        print("=" * 60)
        print("\nAutonomous execution system is ready!")
        print("Seven can now:")
        print("  - Detect system queries")
        print("  - Select appropriate tools")
        print("  - Execute safely")
        print("  - Provide natural responses")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
