"""
Permission Manager - Safety System for Autonomous Execution

Determines which commands are safe to auto-execute and which require permission.
"""

import re
from typing import List, Set
import logging


class PermissionManager:
    """
    Manages permissions for autonomous command execution
    
    Safety Levels:
    - SAFE: Auto-execute (read-only operations)
    - ASK: Require user confirmation (write operations)
    - DANGEROUS: Always require explicit permission (destructive)
    """
    
    def __init__(self):
        """Initialize permission manager"""
        
        # Safe commands (read-only, auto-execute)
        self.safe_commands: Set[str] = {
            "wmic",
            "tasklist",
            "ipconfig",
            "dir",
            "where",
            "echo",
            "time",
            "date",
            "ping",
            "systeminfo",
            "hostname",
            "whoami",
            "ver",
            "type",  # Read file content
            "find",  # Search in files
            "findstr",  # Search in files
        }
        
        # Commands that require permission (write operations)
        self.require_permission: Set[str] = {
            "copy",
            "xcopy",
            "move",
            "rename",
            "ren",
            "mkdir",
            "md",
            "echo >",  # Writing to file
        }
        
        # Dangerous commands (always ask, never auto-execute)
        self.dangerous_commands: Set[str] = {
            "del",
            "delete",
            "rm",
            "rmdir",
            "rd",
            "format",
            "shutdown",
            "restart",
            "reg",  # Registry
            "regedit",
            "netsh",  # Network config
            "sc",  # Service control
            "taskkill",
            "powercfg",
        }
        
        # Audit log
        self.audit_log: List[dict] = []
        self.max_audit_size = 1000
    
    def is_safe(self, tool) -> bool:
        """
        Check if a tool is safe to auto-execute
        
        Args:
            tool: Tool object to check
            
        Returns:
            True if safe to auto-execute
        """
        if not tool:
            return False
        
        # Check safety level
        if tool.safety_level != "safe":
            return False
        
        # Double-check command
        command_lower = tool.command.lower()
        
        # Check for dangerous commands
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return False
        
        # Check if starts with safe command
        for safe_cmd in self.safe_commands:
            if command_lower.startswith(safe_cmd):
                return True
        
        # Default: not safe
        return False
    
    def requires_permission(self, tool) -> bool:
        """
        Check if tool requires user permission
        
        Args:
            tool: Tool object to check
            
        Returns:
            True if permission required
        """
        if not tool:
            return True
        
        # Always require permission for non-safe tools
        if not self.is_safe(tool):
            return True
        
        command_lower = tool.command.lower()
        
        # Check require_permission list
        for cmd in self.require_permission:
            if cmd in command_lower:
                return True
        
        return False
    
    def is_dangerous(self, tool) -> bool:
        """
        Check if tool is dangerous
        
        Args:
            tool: Tool object to check
            
        Returns:
            True if dangerous
        """
        if not tool:
            return False
        
        command_lower = tool.command.lower()
        
        # Check dangerous commands
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return True
        
        return False
    
    def log_execution(self, tool, user_input: str, result: str, auto_executed: bool = True):
        """
        Log command execution for audit trail
        
        Args:
            tool: Tool that was executed
            user_input: Original user input
            result: Execution result
            auto_executed: Whether it was auto-executed or user-approved
        """
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool.name if tool else "unknown",
            "command": tool.command if tool else "unknown",
            "user_input": user_input,
            "result_preview": result[:100] if result else "no output",
            "auto_executed": auto_executed,
            "safety_level": tool.safety_level if tool else "unknown"
        }
        
        self.audit_log.append(log_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > self.max_audit_size:
            self.audit_log = self.audit_log[-self.max_audit_size:]
    
    def get_audit_log(self, last_n: int = 10) -> List[dict]:
        """
        Get recent audit log entries
        
        Args:
            last_n: Number of recent entries to return
            
        Returns:
            List of log entries
        """
        return self.audit_log[-last_n:] if self.audit_log else []
    
    def get_safety_report(self) -> dict:
        """
        Get safety statistics
        
        Returns:
            Dictionary with safety stats
        """
        total_executions = len(self.audit_log)
        auto_executed = sum(1 for entry in self.audit_log if entry.get("auto_executed", False))
        
        return {
            "total_executions": total_executions,
            "auto_executed": auto_executed,
            "user_approved": total_executions - auto_executed,
            "safe_commands": len(self.safe_commands),
            "dangerous_commands": len(self.dangerous_commands)
        }
    
    def clear_audit_log(self):
        """Clear the audit log"""
        self.audit_log = []
