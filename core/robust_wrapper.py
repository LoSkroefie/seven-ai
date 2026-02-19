"""
Robust wrapper with comprehensive error handling and fallbacks
Makes the bot production-ready and bulletproof
"""
import functools
import traceback
from typing import Callable, Any, Optional
import time

def safe_execute(fallback_value: Any = None, log_errors: bool = True, max_retries: int = 0):
    """
    Decorator for safe function execution with error handling and retries
    
    Args:
        fallback_value: Value to return on error
        log_errors: Whether to log errors
        max_retries: Number of retry attempts
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if log_errors:
                        print(f"[WARNING]  Error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                        if attempt == max_retries:
                            print(f"[ERROR] Stack trace:\n{traceback.format_exc()}")
                    
                    if attempt < max_retries:
                        time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    else:
                        if log_errors:
                            print(f"[TIP] Returning fallback value: {fallback_value}")
                        return fallback_value
            
            return fallback_value
        
        return wrapper
    return decorator


def validate_input(value: Any, expected_type: type, default: Any = None, min_val: Any = None, max_val: Any = None) -> Any:
    """
    Validate and sanitize input
    
    Args:
        value: Value to validate
        expected_type: Expected type
        default: Default value if validation fails
        min_val: Minimum value (for numbers/strings)
        max_val: Maximum value (for numbers/strings)
        
    Returns:
        Validated value or default
    """
    try:
        # Type check
        if not isinstance(value, expected_type):
            try:
                value = expected_type(value)
            except:
                return default
        
        # Range check for numbers
        if isinstance(value, (int, float)):
            if min_val is not None and value < min_val:
                return default if default is not None else min_val
            if max_val is not None and value > max_val:
                return default if default is not None else max_val
        
        # Length check for strings
        if isinstance(value, str):
            if min_val is not None and len(value) < min_val:
                return default
            if max_val is not None and len(value) > max_val:
                value = value[:max_val]
        
        return value
        
    except Exception as e:
        print(f"[WARNING]  Validation error: {e}")
        return default


class ResourceManager:
    """Context manager for safe resource handling"""
    
    def __init__(self, name: str):
        self.name = name
        self.resources = []
    
    def add_resource(self, resource, cleanup_func: Optional[Callable] = None):
        """Add a resource to manage"""
        self.resources.append((resource, cleanup_func))
        return resource
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all resources"""
        for resource, cleanup_func in reversed(self.resources):
            try:
                if cleanup_func:
                    cleanup_func(resource)
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'stop'):
                    resource.stop()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
            except Exception as e:
                print(f"[WARNING]  Error cleaning up {self.name}: {e}")
        
        return False  # Don't suppress exceptions


class HealthMonitor:
    """Monitor system health and trigger recovery"""
    
    def __init__(self):
        self.checks = {}
        self.failures = {}
        self.max_failures = 3
    
    def register_check(self, name: str, check_func: Callable, recovery_func: Optional[Callable] = None):
        """Register a health check"""
        self.checks[name] = {
            'check': check_func,
            'recovery': recovery_func
        }
        self.failures[name] = 0
    
    def run_checks(self) -> dict:
        """Run all health checks"""
        results = {}
        
        for name, funcs in self.checks.items():
            try:
                is_healthy = funcs['check']()
                results[name] = is_healthy
                
                if is_healthy:
                    self.failures[name] = 0
                else:
                    self.failures[name] += 1
                    
                    # Try recovery if too many failures
                    if self.failures[name] >= self.max_failures and funcs['recovery']:
                        print(f"[CONFIG] Attempting recovery for {name}...")
                        try:
                            funcs['recovery']()
                            self.failures[name] = 0
                        except Exception as e:
                            print(f"[ERROR] Recovery failed for {name}: {e}")
                            
            except Exception as e:
                print(f"[WARNING]  Health check error for {name}: {e}")
                results[name] = False
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        results = self.run_checks()
        return all(results.values())


def safe_file_operation(filepath, mode='r', default=None, encoding='utf-8'):
    """Safely read/write files with error handling"""
    try:
        if 'r' in mode:
            with open(filepath, mode, encoding=encoding) as f:
                return f.read()
        elif 'w' in mode:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            return filepath
    except Exception as e:
        print(f"[WARNING]  File operation error on {filepath}: {e}")
        return default


def timeout_handler(timeout_seconds: int):
    """Decorator to add timeout to functions"""
    import signal
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_function(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
            
            # Set timeout (Unix only)
            try:
                signal.signal(signal.SIGALRM, timeout_function)
                signal.alarm(timeout_seconds)
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            except AttributeError:
                # Windows doesn't have SIGALRM, just run normally
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
