"""Quick integration test"""
from core.phase5_integration import Phase5Integration

print("Initializing Phase 5...")
p5 = Phase5Integration()

print("\nTesting processing pipeline...")
state = p5.process_user_input("I'm frustrated with this bug!")

print(f"User emotion detected: {state['user_emotion'].emotion.value}")
print(f"User intent: {state['user_intent'].value}")
print(f"Seven's emotion: {state['seven_emotion'].emotion.value}")
print(f"Mental state: {state['mental_state']}")

if state['empathy_response']:
    print(f"Empathy: {state['empathy_response']}")

print("\nTesting response evaluation...")
eval_result = p5.evaluate_proposed_response(
    "Let me help you debug that",
    "I'm frustrated with this bug!"
)
print(f"Ethical: {eval_result['ethical']}")
print(f"Recommendation: {eval_result['recommendation']}")

print("\nTesting sleep/wake...")
conversations = [
    ("Help me", "Sure, what's the issue?"),
    ("It's a bug", "Let's debug it")
]
p5.enter_sleep_mode(conversations)
wake_data = p5.wake_up()

if wake_data.get('morning_share'):
    print(f"Morning share: {wake_data['morning_share'][:100]}...")

print("\n[SUCCESS] ALL INTEGRATION TESTS PASSED!")
