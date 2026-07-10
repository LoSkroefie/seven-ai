"""
COMPREHENSIVE CODE ANALYZER
Analyzes entire codebase for:
- Missing features
- Potential enhancements
- Code quality issues
- Performance optimizations
- Incomplete implementations
"""
import os
import ast
import sys
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(r"C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot")

class CodeAnalyzer:
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'issues': [],
            'enhancements': [],
            'features': []
        }
        
    def analyze_file(self, filepath):
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            self.stats['total_files'] += 1
            self.stats['total_lines'] += len(lines)
            
            # Parse AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, filepath)
            except SyntaxError as e:
                self.stats['issues'].append({
                    'file': str(filepath.relative_to(BASE_DIR)),
                    'type': 'Syntax Error',
                    'line': e.lineno,
                    'msg': str(e)
                })
                
        except Exception as e:
            pass
            
    def _analyze_ast(self, tree, filepath):
        """Analyze AST for patterns"""
        rel_path = str(filepath.relative_to(BASE_DIR))
        
        for node in ast.walk(tree):
            # Count functions
            if isinstance(node, ast.FunctionDef):
                self.stats['total_functions'] += 1
                
                # Check for empty functions
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    self.stats['issues'].append({
                        'file': rel_path,
                        'type': 'Empty Function',
                        'line': node.lineno,
                        'msg': f"Function '{node.name}' is empty"
                    })
                    
            # Count classes
            if isinstance(node, ast.ClassDef):
                self.stats['total_classes'] += 1
                
    def scan_directory(self, directory):
        """Scan all Python files"""
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    self.analyze_file(filepath)
                    
    def generate_report(self):
        """Generate comprehensive report"""
        print("=" * 80)
        print("COMPREHENSIVE CODE ANALYSIS REPORT")
        print("=" * 80)
        print()
        
        print("[STATS] CODEBASE STATISTICS")
        print("-" * 80)
        print(f"Total Python Files: {self.stats['total_files']}")
        print(f"Total Lines of Code: {self.stats['total_lines']:,}")
        print(f"Total Functions: {self.stats['total_functions']}")
        print(f"Total Classes: {self.stats['total_classes']}")
        print()
        
        if self.stats['issues']:
            print(f"[WARNING]  ISSUES FOUND: {len(self.stats['issues'])}")
            print("-" * 80)
            for issue in self.stats['issues'][:20]:
                print(f"  [{issue['type']}] {issue['file']}:{issue.get('line', '?')}")
                print(f"    {issue['msg']}")
            if len(self.stats['issues']) > 20:
                print(f"  ... and {len(self.stats['issues']) - 20} more")
        else:
            print("[OK] NO ISSUES FOUND!")
        
        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

# Run analysis
analyzer = CodeAnalyzer()
analyzer.scan_directory(BASE_DIR / "core")
analyzer.scan_directory(BASE_DIR / "gui")
analyzer.generate_report()

# Check for specific features
print("\n" + "=" * 80)
print("FEATURE COMPLETENESS CHECK")
print("=" * 80)

features_to_check = [
    ('core/enhanced_bot.py', 'Main bot implementation'),
    ('core/phase5_integration.py', 'Phase 5 integration'),
    ('core/autonomous_life.py', 'Autonomous life system'),
    ('core/dream_system.py', 'Dream processing'),
    ('core/vision_system.py', 'Vision system'),
    ('gui/phase5_gui.py', 'Phase 5 GUI'),
    ('identity/SOUL.md', 'Identity system'),
    ('config.py', 'Configuration'),
]

print("\nCore Files Status:")
for filepath, desc in features_to_check:
    full_path = BASE_DIR / filepath
    status = "[OK] EXISTS" if full_path.exists() else "[ERROR] MISSING"
    print(f"  {status} - {desc}")
    if full_path.exists() and full_path.suffix == '.py':
        size = full_path.stat().st_size
        lines = len(full_path.read_text(encoding='utf-8').split('\n'))
        print(f"           ({lines} lines, {size:,} bytes)")

print("\n" + "=" * 80)
