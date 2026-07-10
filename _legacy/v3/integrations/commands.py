"""
Safe system command execution
"""
import subprocess
import shlex
import psutil
from typing import Optional, Dict, List
import config

class CommandExecutor:
    """Safely execute system commands"""
    
    def __init__(self):
        self.allowed_programs = config.ALLOWED_PROGRAMS
        self.process_map = {}  # Track opened processes
    
    def open_program(self, program_name: str, args: str = "") -> str:
        """
        Open a program safely
        
        Args:
            program_name: Name of program (from whitelist)
            args: Optional arguments
            
        Returns:
            Status message
        """
        program_lower = program_name.lower().strip()
        
        # Check whitelist
        if program_lower not in self.allowed_programs:
            available = ", ".join(self.allowed_programs.keys())
            return f"[ERROR] Program '{program_name}' not in whitelist. Available: {available}"
        
        executable = self.allowed_programs[program_lower]
        
        try:
            # Build command
            if args:
                cmd = f"{executable} {args}"
            else:
                cmd = executable
            
            # Execute and track
            process = subprocess.Popen(cmd, shell=True)
            self.process_map[program_lower] = process
            return f"[OK] Opened {program_name}"
            
        except FileNotFoundError:
            return f"[ERROR] Program '{program_name}' not found on system"
        except Exception as e:
            return f"[ERROR] Error opening {program_name}: {str(e)}"
    
    def close_program(self, program_name: str) -> str:
        """Close a running program by name"""
        program_lower = program_name.lower().strip()
        
        try:
            # Map common names to process names
            process_names = {
                'calculator': ['calc.exe', 'CalculatorApp.exe'],
                'calc': ['calc.exe', 'CalculatorApp.exe'],
                'notepad': ['notepad.exe'],
                'paint': ['mspaint.exe'],
                'wordpad': ['write.exe', 'wordpad.exe'],
                'chrome': ['chrome.exe'],
                'firefox': ['firefox.exe'],
            }
            
            # Get process names to kill
            targets = process_names.get(program_lower, [f"{program_lower}.exe"])
            
            killed_count = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in [t.lower() for t in targets]:
                        proc.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                return f"[OK] Closed {killed_count} instance(s) of {program_name}"
            else:
                return f"[INFO] {program_name} is not running"
                
        except Exception as e:
            return f"[ERROR] Error closing {program_name}: {str(e)}"
    
    def kill_program(self, program_name: str) -> str:
        """Force kill a program (stronger than close)"""
        program_lower = program_name.lower().strip()
        
        try:
            process_names = {
                'calculator': ['calc.exe', 'CalculatorApp.exe'],
                'calc': ['calc.exe', 'CalculatorApp.exe'],
                'notepad': ['notepad.exe'],
                'paint': ['mspaint.exe'],
                'wordpad': ['write.exe', 'wordpad.exe'],
                'chrome': ['chrome.exe'],
                'firefox': ['firefox.exe'],
            }
            
            targets = process_names.get(program_lower, [f"{program_lower}.exe"])
            
            killed_count = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in [t.lower() for t in targets]:
                        proc.kill()  # Force kill
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                return f"[OK] Force killed {killed_count} instance(s) of {program_name}"
            else:
                return f"[INFO] {program_name} is not running"
                
        except Exception as e:
            return f"[ERROR] Error killing {program_name}: {str(e)}"
    
    def list_running_programs(self) -> List[str]:
        """List common running programs"""
        common_programs = ['calc', 'notepad', 'chrome', 'firefox', 'paint', 'wordpad']
        running = []
        
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                for prog in common_programs:
                    if prog in name:
                        running.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return list(set(running))
    
    def execute_safe_command(self, command: str, shell_type: str = "cmd") -> str:
        """
        Execute a system command (CMD or PowerShell)
        
        Args:
            command: Command to execute
            shell_type: 'cmd' or 'powershell'
            
        Returns:
            Command output or error message
        """
        # Warning: This is inherently risky. Only use with trusted input.
        print(f"[WARNING]  Executing {shell_type} command: {command}")
        
        try:
            if shell_type.lower() == "powershell":
                full_cmd = f'powershell -Command "{command}"'
            else:
                full_cmd = command
            
            # Execute with timeout
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Get output
            output = result.stdout.strip() or result.stderr.strip()
            
            if result.returncode == 0:
                return f"[OK] Command executed:\n{output if output else '(no output)'}"
            else:
                return f"[WARNING] Command completed with errors:\n{output}"
                
        except subprocess.TimeoutExpired:
            return "[TIMEOUT] Command timed out (30s limit)"
        except Exception as e:
            return f"[ERROR] Error executing command: {str(e)}"
    
    def list_capabilities(self) -> str:
        """List available commands"""
        caps = [
            "[PROGRAMS] Open/Close Programs:",
            *[f"  - {name}" for name in self.allowed_programs.keys()],
            "",
            "[COMMANDS] System Commands:",
            "  - Run CMD commands (use with caution)",
            "  - Run PowerShell commands (use with caution)",
            "",
            "[OTHER] Other Capabilities:",
            "  - Google search",
            "  - Set reminders",
            "  - Calendar events",
            "  - Tell jokes/facts",
        ]
        return "\n".join(caps)

def parse_command_from_text(text: str) -> Optional[Dict[str, str]]:
    """
    Parse command intent from natural language
    
    Returns:
        Dict with 'action', 'target', 'args' or None
    """
    text_lower = text.lower().strip()
    
    # Close/kill program - PRIORITY (check before open)
    if any(keyword in text_lower for keyword in ["close", "kill", "stop", "exit", "quit"]):
        # Don't trigger on "exit bot" or "quit bot"
        if not any(word in text_lower for word in ["bot", "assistant", "program"]):
            for program in ["calculator", "calc", "notepad", "paint", "chrome", "firefox", "wordpad"]:
                if program in text_lower:
                    action = "kill_program" if "kill" in text_lower or "force" in text_lower else "close_program"
                    return {
                        "action": action,
                        "target": program,
                        "args": ""
                    }
    
    # Open program
    if "open" in text_lower or "start" in text_lower or "launch" in text_lower:
        for program in config.ALLOWED_PROGRAMS.keys():
            if program in text_lower:
                return {
                    "action": "open_program",
                    "target": program,
                    "args": ""
                }
    
    # List running programs
    if "what" in text_lower and ("running" in text_lower or "open" in text_lower):
        if "program" in text_lower or "app" in text_lower:
            return {
                "action": "list_programs",
                "target": "",
                "args": ""
            }
    
    # CMD command
    if "run cmd" in text_lower or "execute cmd" in text_lower:
        cmd = text_lower.split("cmd", 1)[-1].strip()
        return {
            "action": "execute_command",
            "target": "cmd",
            "args": cmd
        }
    
    # PowerShell command
    if "run powershell" in text_lower or "execute powershell" in text_lower:
        cmd = text_lower.split("powershell", 1)[-1].strip()
        return {
            "action": "execute_command",
            "target": "powershell",
            "args": cmd
        }
    
    return None
