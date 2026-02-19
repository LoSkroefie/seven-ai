"""
Safe Code Execution Sandbox
Allows bot to write and run Python code safely
"""
import sys
import io
import contextlib
import ast
import time
from typing import Dict, Optional, List
import multiprocessing
import signal

class CodeExecutor:
    """Safe Python code execution with hardened sandboxing"""
    
    def __init__(self):
        self.timeout_seconds = 10
        self.max_output_length = 5000
        self.max_code_length = 10000  # Max chars of code to accept
        self.forbidden_imports = [
            'os', 'subprocess', 'sys', 'importlib', '__import__',
            'eval', 'exec', 'compile', 'open', 'file',
            'shutil', 'pathlib', 'socket', 'http', 'urllib',
            'ctypes', 'multiprocessing', 'threading', 'signal',
            'pickle', 'shelve', 'tempfile', 'glob', 'fnmatch',
            'code', 'codeop', 'pty', 'pipes', 'resource',
        ]
        self.allowed_imports = [
            'math', 'random', 'datetime', 'json', 'collections',
            'itertools', 're', 'string', 'statistics', 'functools',
            'decimal', 'fractions', 'textwrap', 'difflib',
        ]
        self.execution_count = 0
        self.max_executions_per_minute = 10
        self._execution_times = []
    
    def is_safe_code(self, code: str) -> Dict:
        """
        Check if code is safe to execute
        
        Args:
            code: Python code to check
            
        Returns:
            Dictionary with safety result
        """
        try:
            # Parse code to AST
            tree = ast.parse(code)
            
            # Check for forbidden operations
            forbidden_found = []
            
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_module = alias.name.split('.')[0]
                        if base_module in self.forbidden_imports:
                            forbidden_found.append(f"Forbidden import: {alias.name}")
                        elif base_module not in self.allowed_imports:
                            forbidden_found.append(f"Unapproved import: {alias.name} (allowed: {', '.join(self.allowed_imports)})")
                
                if isinstance(node, ast.ImportFrom):
                    base_module = (node.module or '').split('.')[0]
                    if base_module in self.forbidden_imports:
                        forbidden_found.append(f"Forbidden import: {node.module}")
                    elif base_module not in self.allowed_imports:
                        forbidden_found.append(f"Unapproved import: {node.module}")
                
                # Check dangerous functions
                if isinstance(node, ast.Name):
                    if node.id in self.forbidden_imports:
                        forbidden_found.append(f"Dangerous function: {node.id}")
                    if node.id in ('__import__', 'globals', 'locals', 'vars', 'dir',
                                   'getattr', 'setattr', 'delattr', 'hasattr'):
                        forbidden_found.append(f"Restricted builtin: {node.id}")
                
                # Block dunder attribute access (e.g. obj.__class__.__bases__)
                if isinstance(node, ast.Attribute):
                    if node.attr.startswith('__') and node.attr.endswith('__'):
                        forbidden_found.append(f"Dunder access blocked: {node.attr}")
                
                # Block starred imports
                if isinstance(node, ast.ImportFrom):
                    if any(alias.name == '*' for alias in node.names):
                        forbidden_found.append("Wildcard import blocked")
            
            if forbidden_found:
                return {
                    'safe': False,
                    'errors': forbidden_found
                }
            
            return {
                'safe': True,
                'message': 'Code passed safety checks'
            }
            
        except SyntaxError as e:
            return {
                'safe': False,
                'errors': [f'Syntax error: {str(e)}']
            }
        except Exception as e:
            return {
                'safe': False,
                'errors': [f'Parse error: {str(e)}']
            }
    
    def execute_code(self, code: str, timeout: Optional[int] = None) -> Dict:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds (default: self.timeout_seconds)
            
        Returns:
            Result dictionary with output and errors
        """
        # Check safety first
        safety_check = self.is_safe_code(code)
        if not safety_check['safe']:
            return {
                'success': False,
                'error': 'Code failed safety checks',
                'details': safety_check['errors']
            }
        
        timeout = timeout or self.timeout_seconds
        
        # Rate limit check
        now = time.time()
        self._execution_times = [t for t in self._execution_times if now - t < 60]
        if len(self._execution_times) >= self.max_executions_per_minute:
            return {
                'success': False,
                'error': f'Rate limit: max {self.max_executions_per_minute} executions per minute'
            }
        self._execution_times.append(now)
        
        # Code length check
        if len(code) > self.max_code_length:
            return {
                'success': False,
                'error': f'Code too long ({len(code)} chars, max {self.max_code_length})'
            }
        
        # Execute in a subprocess for real isolation + hard timeout
        start_time = time.time()
        
        try:
            result = self._execute_in_subprocess(code, timeout)
            execution_time = time.time() - start_time
            self.execution_count += 1
            
            if result.get('timed_out'):
                return {
                    'success': False,
                    'error': f'Execution timed out after {timeout} seconds (hard kill)'
                }
            
            if result.get('error'):
                return {
                    'success': False,
                    'error': f'Runtime error: {result["error"]}',
                    'type': 'RuntimeError'
                }
            
            stdout = result.get('output', '')
            stderr = result.get('stderr', '')
            
            # Truncate if too long
            if len(stdout) > self.max_output_length:
                stdout = stdout[:self.max_output_length] + "\n... (output truncated)"
            
            return {
                'success': True,
                'output': stdout,
                'errors': stderr if stderr else None,
                'execution_time': round(execution_time, 3)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution failed: {str(e)}'
            }
    
    @staticmethod
    def _subprocess_worker(code, result_dict):
        """Worker function that runs in a separate process"""
        import io, contextlib
        restricted_globals = {
            '__builtins__': {
                'print': print, 'len': len, 'range': range,
                'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
                'abs': abs, 'sum': sum, 'min': min, 'max': max,
                'round': round, 'sorted': sorted, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'isinstance': isinstance, 'type': type, 'repr': repr,
                'True': True, 'False': False, 'None': None,
            }
        }
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                compiled = compile(code, '<sandbox>', 'exec')
                exec(compiled, restricted_globals)
            result_dict['output'] = stdout_buf.getvalue()
            result_dict['stderr'] = stderr_buf.getvalue()
        except Exception as e:
            result_dict['error'] = f'{type(e).__name__}: {str(e)}'
            result_dict['output'] = stdout_buf.getvalue()
            result_dict['stderr'] = stderr_buf.getvalue()
    
    def _execute_in_subprocess(self, code: str, timeout: int) -> Dict:
        """Execute code in an isolated subprocess with hard timeout"""
        try:
            multiprocessing.freeze_support()
            manager = multiprocessing.Manager()
            result_dict = manager.dict()
            
            proc = multiprocessing.Process(
                target=self._subprocess_worker,
                args=(code, result_dict)
            )
            proc.start()
            proc.join(timeout=timeout)
            
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=2)
                if proc.is_alive():
                    proc.kill()
                return {'timed_out': True, 'output': '', 'stderr': ''}
            
            return dict(result_dict)
        except RuntimeError:
            # Fallback: in-process execution with restricted globals (Windows spawn issue)
            return self._execute_in_process(code, timeout)
    
    def _execute_in_process(self, code: str, timeout: int) -> Dict:
        """Fallback in-process execution with restricted globals"""
        import io as _io, contextlib as _ctx
        restricted_globals = {
            '__builtins__': {
                'print': print, 'len': len, 'range': range,
                'str': str, 'int': int, 'float': float, 'bool': bool,
                'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
                'abs': abs, 'sum': sum, 'min': min, 'max': max,
                'round': round, 'sorted': sorted, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'isinstance': isinstance, 'type': type, 'repr': repr,
                'True': True, 'False': False, 'None': None,
            }
        }
        stdout_buf = _io.StringIO()
        stderr_buf = _io.StringIO()
        try:
            with _ctx.redirect_stdout(stdout_buf), _ctx.redirect_stderr(stderr_buf):
                compiled = compile(code, '<sandbox>', 'exec')
                exec(compiled, restricted_globals)
            return {'output': stdout_buf.getvalue(), 'stderr': stderr_buf.getvalue()}
        except Exception as e:
            return {'error': f'{type(e).__name__}: {str(e)}', 'output': stdout_buf.getvalue(), 'stderr': stderr_buf.getvalue()}
    
    def execute_code_with_result(self, code: str) -> Dict:
        """
        Execute code and return the last expression's value
        
        Args:
            code: Python code
            
        Returns:
            Result with output and return value
        """
        # Check if last line is an expression
        lines = code.strip().split('\n')
        if not lines:
            return {'success': False, 'error': 'Empty code'}
        
        # Try to evaluate last line as expression
        try:
            *statements, last_line = lines
            statements_code = '\n'.join(statements)
            
            # Execute statements first
            if statements_code:
                result = self.execute_code(statements_code)
                if not result['success']:
                    return result
            
            # Try to evaluate last line
            try:
                # Check safety
                safety = self.is_safe_code(last_line)
                if not safety['safe']:
                    return {
                        'success': False,
                        'error': 'Last expression failed safety check'
                    }
                
                # Evaluate
                result_value = eval(last_line, {"__builtins__": {}})
                
                return {
                    'success': True,
                    'output': str(result_value),
                    'return_value': result_value
                }
                
            except Exception:
                # If eval fails, execute normally
                return self.execute_code(code)
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to execute: {str(e)}'
            }
    
    def validate_syntax(self, code: str) -> Dict:
        """
        Check if code has valid Python syntax
        
        Args:
            code: Python code
            
        Returns:
            Validation result
        """
        try:
            ast.parse(code)
            return {
                'valid': True,
                'message': 'Syntax is valid'
            }
        except SyntaxError as e:
            return {
                'valid': False,
                'error': str(e),
                'line': e.lineno,
                'offset': e.offset
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_help(self) -> str:
        """Get help about code execution capabilities"""
        return """Code Execution Sandbox

Allowed:
- Basic Python operations (math, strings, lists, etc.)
- Allowed imports: math, random, datetime, json, collections, itertools, re, string, statistics
- Print statements
- Variables and functions
- Loops and conditionals

Not Allowed:
- File operations (open, read, write)
- System operations (os, subprocess, sys)
- Network operations
- Import of dangerous modules
- eval/exec/compile

Examples:
- "Calculate 2 + 2"
- "Generate 10 random numbers"
- "Sort this list: [3,1,4,1,5,9,2,6]"

Timeout: {timeout} seconds
Max output: {max_output} characters
"""
