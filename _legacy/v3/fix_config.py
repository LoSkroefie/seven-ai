"""Remove duplicate VISION config"""
import re

filepath = r"C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot\config.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the duplicate section (starts with the separator comment)
pattern = r'# ========================================\n# VISION SYSTEM - Seven\'s Eyes\n# ========================================.*?VISION_SAVE_INTERESTING_FRAMES = False  # Save frames when interesting events detected'

content = re.sub(pattern, '', content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Removed duplicate VISION configuration")
