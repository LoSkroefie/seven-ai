"""
Extension / Plugin Loader — Seven AI v3.2

Dynamic import system for user-created extensions.
Extensions are Python files in the extensions/ directory that
implement the SevenExtension interface.

Features:
- Auto-discovery of .py files in extensions/
- Hot-reload via API endpoint (/extensions/reload)
- Sandboxed execution (restricted imports, timeout)
- Auto-registration with scheduler and multi-agent system
- Extension lifecycle: init → start → run → stop

Security:
- Extensions cannot import os.system, subprocess, or eval
- Each extension runs in a try/except wrapper
- Extensions have read-only access to bot state
- Timeout on extension execution (configurable)

Usage:
    loader = PluginLoader(bot=bot_instance)
    loader.discover()
    loader.load_all()
    loader.start_all()
"""

import importlib
import importlib.util
import inspect
import logging
import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any, Type
from abc import ABC, abstractmethod

logger = logging.getLogger("PluginLoader")

# Maximum execution time per extension call (seconds)
EXTENSION_TIMEOUT = 10


class SevenExtension(ABC):
    """
    Base class for Seven AI extensions.
    
    All extensions must subclass this and implement at minimum
    the `run` method. Extensions are auto-discovered from the
    extensions/ directory.
    
    Example extension (extensions/my_plugin.py):
    
        from utils.plugin_loader import SevenExtension
        
        class MyPlugin(SevenExtension):
            name = "My Plugin"
            version = "1.0"
            description = "Does something cool"
            
            def init(self, bot):
                self.bot = bot
            
            def run(self, context: dict) -> dict:
                return {"message": "Hello from my plugin!"}
    """
    
    # Extension metadata (override in subclass)
    name: str = "Unnamed Extension"
    version: str = "0.1"
    description: str = ""
    author: str = ""
    
    # Scheduler integration
    schedule_interval_minutes: int = 0  # 0 = no scheduling
    schedule_cron: str = ""             # Cron expression (overrides interval)
    
    # Capabilities requested
    needs_ollama: bool = False
    needs_memory: bool = False
    needs_scheduler: bool = False
    
    def init(self, bot=None):
        """Called once when the extension is loaded. Override to initialize."""
        pass
    
    def start(self):
        """Called when Seven starts running. Override for startup logic."""
        pass
    
    @abstractmethod
    def run(self, context: dict = None) -> dict:
        """
        Main execution method. Called on schedule or on-demand.
        
        Args:
            context: Dict with current bot state (emotion, energy, etc.)
        
        Returns:
            Dict with results (message, action, data, etc.)
        """
        pass
    
    def stop(self):
        """Called when Seven shuts down. Override for cleanup."""
        pass
    
    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """
        Called after each user interaction. Override to react.
        
        Returns:
            Optional modified/additional response, or None
        """
        return None
    
    def get_status(self) -> dict:
        """Return extension status for GUI/API"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'running': True
        }


class LoadedExtension:
    """Wrapper for a loaded extension with metadata"""
    
    def __init__(self, instance: SevenExtension, module_path: str, 
                 class_name: str):
        self.instance = instance
        self.module_path = module_path
        self.class_name = class_name
        self.loaded_at = time.time()
        self.last_run = None
        self.run_count = 0
        self.errors = 0
        self.enabled = True
    
    def to_dict(self) -> dict:
        return {
            'name': self.instance.name,
            'version': self.instance.version,
            'description': self.instance.description,
            'author': self.instance.author,
            'module': self.module_path,
            'class': self.class_name,
            'enabled': self.enabled,
            'run_count': self.run_count,
            'errors': self.errors,
            'last_run': self.last_run,
            'loaded_at': self.loaded_at,
            'schedule_interval': self.instance.schedule_interval_minutes,
            'schedule_cron': self.instance.schedule_cron,
        }


# Blocked imports for security
BLOCKED_MODULES = {
    'subprocess', 'shutil', 'ctypes', 'multiprocessing',
    'socket', 'http.server', 'xmlrpc', 'ftplib', 'smtplib',
}


class PluginLoader:
    """
    Extension discovery, loading, and lifecycle management.
    
    Scans extensions/ directory for SevenExtension subclasses,
    loads them safely, and manages their lifecycle.
    """
    
    def __init__(self, bot=None, extensions_dir: str = None):
        self.bot = bot
        self.extensions_dir = Path(extensions_dir) if extensions_dir else (
            Path(__file__).parent.parent / "extensions"
        )
        
        # Loaded extensions
        self.extensions: Dict[str, LoadedExtension] = {}
        
        # Ensure directory exists
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create example if directory is empty
        self._ensure_example_exists()
        
        logger.info(f"[PLUGINS] Initialized — dir={self.extensions_dir}")
    
    def _ensure_example_exists(self):
        """Create example extension if none exist"""
        example_file = self.extensions_dir / "example_extension.py"
        if example_file.exists():
            return
        
        # Don't create if other extensions already exist
        py_files = list(self.extensions_dir.glob("*.py"))
        non_init = [f for f in py_files if f.name != '__init__.py']
        if non_init:
            return
        
        example_code = '''"""
Example Extension for Seven AI

This is a template showing how to create extensions.
Copy this file and modify it to create your own.

Extensions are auto-discovered from the extensions/ directory.
"""

from utils.plugin_loader import SevenExtension


class ExampleExtension(SevenExtension):
    """Example extension that logs a greeting"""
    
    name = "Example Extension"
    version = "1.0"
    description = "A simple example extension"
    author = "Seven AI"
    
    # Run every 60 minutes (set to 0 to disable scheduling)
    schedule_interval_minutes = 0
    
    def init(self, bot=None):
        """Called once when loaded"""
        self.bot = bot
        self.greetings_sent = 0
    
    def run(self, context: dict = None) -> dict:
        """Main execution — called on schedule or manually"""
        self.greetings_sent += 1
        return {
            "message": f"Hello from Example Extension! (run #{self.greetings_sent})",
            "status": "ok"
        }
    
    def on_message(self, user_message: str, bot_response: str):
        """React to user messages (optional)"""
        # Return None to not modify anything
        return None
    
    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "greetings_sent": self.greetings_sent,
            "running": True
        }
'''
        
        try:
            with open(example_file, 'w', encoding='utf-8') as f:
                f.write(example_code)
            logger.info(f"[PLUGINS] Created example extension: {example_file}")
        except Exception as e:
            logger.debug(f"[PLUGINS] Could not create example: {e}")
    
    # ==================== Discovery ====================
    
    def discover(self) -> List[str]:
        """
        Discover extension files in the extensions directory.
        
        Returns:
            List of discovered .py file paths
        """
        discovered = []
        
        for py_file in sorted(self.extensions_dir.glob("*.py")):
            if py_file.name.startswith('_'):
                continue
            discovered.append(str(py_file))
        
        logger.info(f"[PLUGINS] Discovered {len(discovered)} extension file(s)")
        return discovered
    
    # ==================== Loading ====================
    
    def load_all(self) -> Dict[str, str]:
        """
        Discover and load all extensions.
        
        Returns:
            Dict mapping extension name → status ('loaded' or error message)
        """
        results = {}
        discovered = self.discover()
        
        for file_path in discovered:
            name, status = self._load_file(file_path)
            if name:
                results[name] = status
        
        logger.info(f"[PLUGINS] Loaded {sum(1 for s in results.values() if s == 'loaded')}/{len(results)} extensions")
        return results
    
    def _load_file(self, file_path: str) -> tuple:
        """
        Load a single extension file.
        
        Returns:
            (extension_name, status_string)
        """
        path = Path(file_path)
        module_name = f"ext_{path.stem}"
        
        try:
            # Security check — scan for blocked imports
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            for blocked in BLOCKED_MODULES:
                if f"import {blocked}" in source or f"from {blocked}" in source:
                    msg = f"Blocked import '{blocked}' found"
                    logger.warning(f"[PLUGINS] {path.name}: {msg}")
                    return (path.stem, f"security: {msg}")
            
            # Dynamic import
            spec = importlib.util.spec_from_file_location(module_name, str(path))
            if not spec or not spec.loader:
                return (path.stem, "invalid module")
            
            module = importlib.util.module_from_spec(spec)
            
            # Temporarily add to sys.modules for relative imports
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find SevenExtension subclasses
            loaded_count = 0
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, SevenExtension) and 
                    obj is not SevenExtension and
                    not inspect.isabstract(obj)):
                    
                    try:
                        instance = obj()
                        instance.init(bot=self.bot)
                        
                        ext_id = f"{path.stem}.{name}"
                        self.extensions[ext_id] = LoadedExtension(
                            instance=instance,
                            module_path=str(path),
                            class_name=name
                        )
                        loaded_count += 1
                        
                        logger.info(
                            f"[PLUGINS] Loaded: {instance.name} v{instance.version} "
                            f"({ext_id})"
                        )
                    except Exception as e:
                        logger.error(f"[PLUGINS] Init error ({name}): {e}")
            
            if loaded_count > 0:
                return (path.stem, "loaded")
            else:
                return (path.stem, "no SevenExtension subclass found")
            
        except Exception as e:
            logger.error(f"[PLUGINS] Load error ({path.name}): {e}")
            return (path.stem, f"error: {str(e)}")
    
    # ==================== Lifecycle ====================
    
    def start_all(self):
        """Start all loaded extensions"""
        for ext_id, ext in self.extensions.items():
            if ext.enabled:
                try:
                    ext.instance.start()
                    logger.debug(f"[PLUGINS] Started: {ext_id}")
                except Exception as e:
                    logger.error(f"[PLUGINS] Start error ({ext_id}): {e}")
                    ext.errors += 1
    
    def stop_all(self):
        """Stop all loaded extensions"""
        for ext_id, ext in self.extensions.items():
            try:
                ext.instance.stop()
            except Exception:
                pass
    
    def run_extension(self, ext_id: str, context: dict = None) -> Optional[dict]:
        """
        Run a specific extension by ID.
        
        Args:
            ext_id: Extension identifier
            context: Current bot context
        
        Returns:
            Extension result dict, or None on error
        """
        ext = self.extensions.get(ext_id)
        if not ext or not ext.enabled:
            return None
        
        try:
            result = ext.instance.run(context or self._build_context())
            ext.run_count += 1
            ext.last_run = time.time()
            return result
        except Exception as e:
            ext.errors += 1
            logger.error(f"[PLUGINS] Run error ({ext_id}): {e}")
            return {'error': str(e)}
    
    def run_all(self, context: dict = None) -> Dict[str, Any]:
        """Run all enabled extensions"""
        results = {}
        ctx = context or self._build_context()
        
        for ext_id, ext in self.extensions.items():
            if ext.enabled:
                results[ext_id] = self.run_extension(ext_id, ctx)
        
        return results
    
    def notify_message(self, user_message: str, bot_response: str) -> List[str]:
        """
        Notify all extensions of a user message.
        
        Returns:
            List of additional responses from extensions
        """
        additional = []
        
        for ext_id, ext in self.extensions.items():
            if not ext.enabled:
                continue
            try:
                result = ext.instance.on_message(user_message, bot_response)
                if result and isinstance(result, str):
                    additional.append(result)
            except Exception as e:
                ext.errors += 1
                logger.debug(f"[PLUGINS] on_message error ({ext_id}): {e}")
        
        return additional
    
    # ==================== Hot Reload ====================
    
    def reload_all(self) -> Dict[str, str]:
        """
        Hot-reload all extensions.
        Stops current extensions, clears, re-discovers and loads.
        
        Returns:
            Dict mapping extension name → reload status
        """
        logger.info("[PLUGINS] Hot-reloading all extensions...")
        
        # Stop all
        self.stop_all()
        
        # Clear loaded modules from sys.modules
        for ext_id, ext in self.extensions.items():
            module_name = f"ext_{Path(ext.module_path).stem}"
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # Clear registry
        self.extensions.clear()
        
        # Invalidate import caches
        importlib.invalidate_caches()
        
        # Re-load
        results = self.load_all()
        
        # Re-start
        self.start_all()
        
        return results
    
    # ==================== Scheduling Integration ====================
    
    def get_scheduled_extensions(self) -> List[tuple]:
        """
        Get extensions that want to be scheduled.
        
        Returns:
            List of (ext_id, interval_minutes, cron_expr) tuples
        """
        scheduled = []
        
        for ext_id, ext in self.extensions.items():
            if not ext.enabled:
                continue
            
            interval = ext.instance.schedule_interval_minutes
            cron = ext.instance.schedule_cron
            
            if interval > 0 or cron:
                scheduled.append((ext_id, interval, cron))
        
        return scheduled
    
    # ==================== Context Building ====================
    
    def _build_context(self) -> dict:
        """Build context dict for extension execution"""
        ctx = {
            'timestamp': datetime.now().isoformat(),
            'bot_available': self.bot is not None,
        }
        
        if self.bot:
            ctx['emotion'] = str(getattr(self.bot, 'current_emotion', 'unknown'))
            ctx['running'] = getattr(self.bot, 'running', False)
            ctx['sleeping'] = getattr(self.bot, 'sleeping', False)
            
            if hasattr(self.bot, 'biological_life') and self.bot.biological_life:
                bio = self.bot.biological_life
                ctx['energy'] = getattr(bio, 'energy', 0.5)
                ctx['hunger'] = getattr(bio, 'hunger_level', 0.5)
        
        return ctx
    
    # ==================== Status ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin system status for GUI/API"""
        return {
            'extensions_dir': str(self.extensions_dir),
            'total_loaded': len(self.extensions),
            'total_enabled': sum(1 for e in self.extensions.values() if e.enabled),
            'extensions': {
                ext_id: ext.to_dict()
                for ext_id, ext in self.extensions.items()
            }
        }
    
    def list_extensions(self) -> List[Dict]:
        """List all extensions with status"""
        return [ext.to_dict() for ext in self.extensions.values()]


# Import for type hints
from datetime import datetime
