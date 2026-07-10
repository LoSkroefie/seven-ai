"""
Code Review Scanner - Find all TODOs, FIXMEs, placeholders, and potential bugs
"""
import os
import sys
from pathlib import Path
import re

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(r"C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot")

# Patterns to search for (excluding NOTE which is too common)
PATTERNS = [
    (r'\bTODO\b', 'TODO'),
    (r'\bFIXME\b', 'FIXME'),
    (r'\bXXX\b', 'XXX'),
    (r'\bHACK\b', 'HACK'),
    (r'placeholder', 'Placeholder'),
    (r'pass\s*#', 'Empty pass'),
    (r'raise NotImplementedError', 'Not Implemented'),
]

def scan_file(filepath):
    """Scan a file for issues"""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern, issue_type in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Remove non-ASCII chars to avoid console errors
                    content = line.strip()[:100].encode('ascii', 'ignore').decode('ascii')
                    findings.append({
                        'file': str(filepath.relative_to(BASE_DIR)),
                        'line': line_num,
                        'type': issue_type,
                        'content': content
                    })
    except Exception as e:
        pass
    
    return findings

def scan_directory(directory):
    """Scan all Python files in directory"""
    all_findings = []
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                findings = scan_file(filepath)
                all_findings.extend(findings)
    
    return all_findings

# Scan the enhanced-bot directory
print("=" * 70)
print("CODE REVIEW SCANNER - Finding Issues")
print("=" * 70)
print()

findings = scan_directory(BASE_DIR)

if not findings:
    print("[OK] No TODOs, FIXMEs, or placeholders found!")
else:
    print(f"Found {len(findings)} potential issues:\n")
    
    # Group by type
    by_type = {}
    for f in findings:
        issue_type = f['type']
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(f)
    
    for issue_type, issues in by_type.items():
        print(f"\n{issue_type} ({len(issues)} found):")
        print("-" * 70)
        for issue in issues[:10]:  # Show first 10 of each type
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['content']}")
        
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

print("\n" + "=" * 70)
print("Scan complete!")
print("=" * 70)
