"""
Dynamic Command System - Seven's Unrestricted Autonomy
v3.0 - TRUE AUTONOMY

Seven can execute ANY command she decides to run.
No more hardcoded 20-tool limit!

Requirements:
- Log everything Seven does
- Block genuinely dangerous commands (ask user first)
- Allow free API usage
- Track command history for learning
"""

import subprocess
import re
import logging
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from enum import Enum

class CommandSafetyLevel(Enum):
    """Safety classification for commands"""
    SAFE = "safe"                  # Run immediately
    NEEDS_APPROVAL = "needs_approval"  # Ask user first
    PAID_API = "paid_api"         # Costs money, ask user

class CommandResult:
    """Result of command execution"""
    def __init__(self, command: str, stdout: str, stderr: str, 
                 returncode: int, reason: str, timestamp: datetime):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.success = returncode == 0
        self.reason = reason  # Why Seven ran this
        self.timestamp = timestamp
    
    def to_dict(self):
        return {
            'command': self.command,
            'stdout': self.stdout[:500],  # First 500 chars
            'stderr': self.stderr[:500],
            'returncode': self.returncode,
            'success': self.success,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }

class SafetyRules:
    """
    Safety rules for command execution
    
    Philosophy: Block DANGEROUS commands, not restrict to preset list!
    Seven should be able to run most things autonomously.
    """
    
    # Commands that could destroy system/data
    DESTRUCTIVE_PATTERNS = [
        r'rm\s+-rf\s+/',           # Delete root
        r'format\s+[A-Z]:',        # Format drive
        r'del\s+/[fFsS]\s+/[qQ]',  # Force delete all
        r'rd\s+/[sS]\s+/[qQ]',     # Remove directory tree
        r'shutdown',               # Shutdown computer
        r'reboot',                 # Restart
        r'restart-computer',       # PowerShell restart
        r'Stop-Computer',          # PowerShell shutdown
        r'\\\\\.\\PHYSICALDRIVE',  # Direct disk access
        r'diskpart',               # Disk partitioning
        r'bcdedit',                # Boot config
        r'reg\s+delete.*HKLM',     # Delete system registry
    ]
    
    # APIs that cost money
    PAID_API_PATTERNS = [
        r'openai\.com',
        r'api\.anthropic\.com',
        r'cloud\.google\.com',
        r'api\.aws\.amazon\.com',
        r'azure\.microsoft\.com',
        r'stripe\.com',
        r'paypal\.com'
    ]
    
    def classify_command(self, command: str) -> CommandSafetyLevel:
        """
        Classify command safety level
        
        Returns:
            SAFE - Run immediately
            NEEDS_APPROVAL - Dangerous, ask user
            PAID_API - Costs money, ask user
        """
        command_lower = command.lower()
        
        # Check for destructive commands
        for pattern in self.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command_lower):
                return CommandSafetyLevel.NEEDS_APPROVAL
        
        # Check for paid APIs
        for pattern in self.PAID_API_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return CommandSafetyLevel.PAID_API
        
        # Everything else is safe to run
        return CommandSafetyLevel.SAFE

class DynamicCommandSystem:
    """
    Seven's dynamic command execution system
    
    Seven can run ANY command she decides to run!
    No more hardcoded tool library restrictions.
    """
    
    def __init__(self, bot, user_documents_path: str):
        """
        Initialize dynamic command system
        
        Args:
            bot: Reference to main bot instance
            user_documents_path: Path to user documents folder
        """
        self.bot = bot
        self.logger = logging.getLogger("DynamicCommands")
        self.safety_rules = SafetyRules()
        self.user_documents = Path(user_documents_path)
        
        # Command history for learning
        self.command_history: List[CommandResult] = []
        self.history_file = Path("data/command_history.json")
        self.history_file.parent.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'blocked_commands': 0,
            'paid_api_requests': 0
        }
        
        # Load history
        self._load_history()
        
        self.logger.info("✓ Dynamic Command System initialized")
        self.logger.info(f"✓ Seven can now run ANY command she wants!")
        self.logger.info(f"✓ User documents: {self.user_documents}")
    
    def execute_command(self, command: str, reason: str, 
                       timeout: int = 30) -> Optional[CommandResult]:
        """
        Execute a command that Seven decided to run
        
        Args:
            command: Shell command to execute
            reason: Why Seven wants to run this
            timeout: Max execution time (seconds)
        
        Returns:
            CommandResult or None if blocked
        """
        self.stats['total_commands'] += 1
        
        # Classify safety
        safety_level = self.safety_rules.classify_command(command)
        
        # Handle based on safety level
        if safety_level == CommandSafetyLevel.NEEDS_APPROVAL:
            return self._request_approval_for_dangerous(command, reason)
        
        elif safety_level == CommandSafetyLevel.PAID_API:
            return self._request_approval_for_paid_api(command, reason)
        
        # Safe to execute!
        return self._execute_safe_command(command, reason, timeout)
    
    def _execute_safe_command(self, command: str, reason: str, 
                             timeout: int) -> CommandResult:
        """Execute safe command immediately"""
        self.logger.info("="*60)
        self.logger.info(f"[BOT] SEVEN DECIDED TO RUN COMMAND")
        self.logger.info(f"Command: {command}")
        self.logger.info(f"Reason: {reason}")
        self.logger.info("="*60)
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.user_documents)  # Run in user documents
            )
            
            # Create result object
            cmd_result = CommandResult(
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                reason=reason,
                timestamp=datetime.now()
            )
            
            # Log result
            if cmd_result.success:
                self.stats['successful_commands'] += 1
                self.logger.info(f"✓ Command successful!")
                if result.stdout:
                    self.logger.info(f"Output: {result.stdout[:200]}...")
            else:
                self.stats['failed_commands'] += 1
                self.logger.warning(f"✗ Command failed (exit code: {result.returncode})")
                if result.stderr:
                    self.logger.warning(f"Error: {result.stderr[:200]}...")
            
            # Save to history
            self.command_history.append(cmd_result)
            self._save_history()
            
            return cmd_result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s")
            self.stats['failed_commands'] += 1
            return CommandResult(
                command=command,
                stdout="",
                stderr=f"Timeout after {timeout}s",
                returncode=-1,
                reason=reason,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self.stats['failed_commands'] += 1
            return CommandResult(
                command=command,
                stdout="",
                stderr=str(e),
                returncode=-1,
                reason=reason,
                timestamp=datetime.now()
            )
    
    def _request_approval_for_dangerous(self, command: str, 
                                       reason: str) -> Optional[CommandResult]:
        """Request user approval for dangerous command"""
        self.logger.warning("="*60)
        self.logger.warning("[WARNING]  SEVEN WANTS TO RUN DANGEROUS COMMAND")
        self.logger.warning(f"Command: {command}")
        self.logger.warning(f"Reason: {reason}")
        self.logger.warning("[WARNING]  THIS COMMAND COULD BE DESTRUCTIVE!")
        self.logger.warning("="*60)
        
        self.stats['blocked_commands'] += 1
        self.logger.warning("[ERROR] Command blocked - needs user approval")
        
        return None
    
    def _request_approval_for_paid_api(self, command: str, 
                                      reason: str) -> Optional[CommandResult]:
        """Request user approval for paid API"""
        self.logger.warning("="*60)
        self.logger.warning("💰 SEVEN WANTS TO USE PAID API")
        self.logger.warning(f"Command: {command}")
        self.logger.warning(f"Reason: {reason}")
        self.logger.warning("💰 THIS MAY COST YOU MONEY!")
        self.logger.warning("="*60)
        
        self.stats['paid_api_requests'] += 1
        self.logger.warning("[ERROR] Blocked - paid API requires approval")
        
        return None
    
    def get_command_suggestions(self, goal: str) -> List[str]:
        """Suggest commands Seven could run for a goal"""
        suggestions = []
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ['research', 'learn', 'find', 'search']):
            suggestions.extend([
                f'python web_search.py "{goal}"',
                f'curl -s "https://en.wikipedia.org/wiki/{goal.replace(" ", "_")}"'
            ])
        
        if any(word in goal_lower for word in ['organize', 'clean', 'sort']):
            suggestions.extend([
                'python organize_files.py',
                'mkdir organized && mv *.md organized/'
            ])
        
        return suggestions
    
    def learn_from_history(self) -> Dict[str, any]:
        """Analyze command history for patterns"""
        if not self.command_history:
            return {'message': 'No history yet'}
        
        command_counts = {}
        for cmd in self.command_history:
            base_cmd = cmd.command.split()[0]
            command_counts[base_cmd] = command_counts.get(base_cmd, 0) + 1
        
        success_rate = sum(1 for c in self.command_history if c.success) / len(self.command_history) * 100
        
        return {
            'total_commands': len(self.command_history),
            'success_rate': f"{success_rate:.1f}%",
            'most_used_commands': sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'recent_commands': [c.command for c in self.command_history[-5:]]
        }
    
    def _save_history(self):
        """Save command history to file"""
        try:
            history_data = [cmd.to_dict() for cmd in self.command_history[-1000:]]
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
    
    def _load_history(self):
        """Load command history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                
                for item in history_data:
                    cmd = CommandResult(
                        command=item['command'],
                        stdout=item['stdout'],
                        stderr=item['stderr'],
                        returncode=item['returncode'],
                        reason=item['reason'],
                        timestamp=datetime.fromisoformat(item['timestamp'])
                    )
                    self.command_history.append(cmd)
                
                self.logger.info(f"Loaded {len(self.command_history)} commands from history")
        except Exception as e:
            self.logger.error(f"Failed to load history: {e}")
    
    def get_stats(self) -> Dict[str, any]:
        """Get execution statistics"""
        return {
            **self.stats,
            'success_rate': f"{(self.stats['successful_commands'] / max(1, self.stats['total_commands']) * 100):.1f}%",
            'history_size': len(self.command_history)
        }
