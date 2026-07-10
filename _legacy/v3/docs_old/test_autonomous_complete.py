"""
Complete Autonomous System Test
"""

print('='*70)
print('SEVEN AI AUTONOMOUS SYSTEM - COMPLETE TEST')
print('='*70 + '\n')

from core.tool_library import ToolLibrary
from core.autonomous_agent import AutonomousAgent

# Initialize
lib = ToolLibrary()
agent = AutonomousAgent(lib)

# Test queries
test_queries = [
    'How much disk space do I have?',
    "What's my memory usage?",
    'Check my CPU',
    "What's running?",
    'Show me my IP',
    'What time is it?',
    'How much battery?',
    'How long has the system been running?',
    'List all drives',
    'Calculate 15 * 8',
]

print('Testing 10 natural queries...\n')

working = 0
for query in test_queries:
    intent = agent.detect_intent(query)
    tool = agent.select_tool(intent, query)
    
    if tool:
        params = agent.extract_parameters(intent, query)
        safe = agent.can_execute_autonomously(tool)
        
        # Execute if safe
        if safe:
            result = tool.execute(**params)
            print(f'[OK] "{query}"')
            print(f'     Intent: {intent.category}, Tool: {tool.name}')
            print(f'     Result: {result[:60]}...')
            working += 1
        else:
            print(f'[SAFE] "{query}" - requires permission')
    else:
        print(f'[CONV] "{query}" - conversation mode')
    print()

print('='*70)
print(f'AUTONOMOUS TEST COMPLETE: {working}/10 queries auto-executed!')
print(f'Tools available: {lib.get_tool_count()}')
print(f'Safe tools: {len(lib.get_safe_tools())}')
print('='*70)
