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
    """Safe Python code execution with sandboxing"""
    
    def __init__(self):
        self.timeout_seconds = 10
        self.max_output_length = 5000
        self.forbidden_imports = [
            'os', 'subprocess', 'sys', 'importlib', '__import__',
            'eval', 'exec', 'compile', 'open', 'file'
        ]
        self.allowed_imports = [
            'math', 'random', 'datetime', 'json', 'collections',
            'itertools', 're', 'string', 'statistics'
        ]
    
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
                        if alias.name in self.forbidden_imports:
                            forbidden_found.append(f"Forbidden import: {alias.name}")
                
                if isinstance(node, ast.ImportFrom):
                    if node.module in self.forbidden_imports:
                        forbidden_found.append(f"Forbidden import: {node.module}")
                
                # Check dangerous functions
                if isinstance(node, ast.Name):
                    if node.id in self.forbidden_imports:
                        forbidden_found.append(f"Dangerous function: {node.id}")
            
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
        
        try:
            # Capture output
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            # Create restricted globals
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'abs': abs,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'round': round,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                }
            }
            
            # Execute with timeout and captured output
            start_time = time.time()
            
            with contextlib.redirect_stdout(output_buffer), \
                 contextlib.redirect_stderr(error_buffer):
                try:
                    # Compile and execute
                    compiled_code = compile(code, '<string>', 'exec')
                    exec(compiled_code, restricted_globals)
                    
                    execution_time = time.time() - start_time
                    
                    # Check timeout
                    if execution_time > timeout:
                        return {
                            'success': False,
                            'error': f'Execution timed out after {timeout} seconds'
                        }
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Runtime error: {str(e)}',
                        'type': type(e).__name__
                    }
            
            # Get output
            stdout = output_buffer.getvalue()
            stderr = error_buffer.getvalue()
            
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
