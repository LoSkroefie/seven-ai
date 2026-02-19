"""
Enhanced Command Processor - Run commands and intelligently analyze output
"""
import subprocess
import re
from typing import Dict, Optional, List
from integrations.ollama import OllamaClient

class CommandProcessor:
    """Enhanced command execution with intelligent output analysis"""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama = ollama_client or OllamaClient()
        self.command_history = []
        self.max_output_length = 5000  # Truncate very long output
    
    def execute_command(
        self,
        command: str,
        shell_type: str = "powershell",
        analyze: bool = True,
        cwd: Optional[str] = None
    ) -> Dict:
        """
        Execute command and optionally analyze output with AI
        
        Args:
            command: Command to execute
            shell_type: 'powershell' or 'cmd'
            analyze: Whether to analyze output with Ollama
            cwd: Working directory
            
        Returns:
            Result dictionary with output and analysis
        """
        try:
            # Format command
            if shell_type.lower() == "powershell":
                full_command = ["powershell", "-Command", command]
            elif shell_type.lower() == "cmd":
                full_command = ["cmd", "/c", command]
            else:
                return {
                    'success': False,
                    'error': 'Invalid shell type (use powershell or cmd)'
                }
            
            # Execute
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd
            )
            
            # Get output
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            output = stdout if stdout else stderr
            
            # Truncate if too long
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + "\n... (output truncated)"
            
            # Store in history
            self.command_history.append({
                'command': command,
                'output': output,
                'exit_code': result.returncode
            })
            
            response = {
                'success': result.returncode == 0,
                'command': command,
                'output': output,
                'exit_code': result.returncode,
                'shell': shell_type
            }
            
            # Analyze output with Ollama if requested
            if analyze and output and self.ollama:
                analysis = self._analyze_output(command, output)
                response['analysis'] = analysis
            
            return response
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out after 30 seconds',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to execute command: {str(e)}',
                'command': command
            }
    
    def _analyze_output(self, command: str, output: str) -> str:
        """Use Ollama to analyze command output"""
        try:
            prompt = f"""Analyze this command output and provide a brief, helpful summary.

Command: {command}

Output:
{output}

Provide a concise summary of what the output shows. Be specific and helpful."""
            
            analysis = self.ollama.generate(
                prompt,
                system_message="You are a helpful assistant analyzing command line output. Be concise and clear.",
                temperature=0.5
            )
            
            return analysis if analysis else "Unable to analyze output"
            
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def batch_execute(self, commands: List[str], shell_type: str = "powershell") -> List[Dict]:
        """
        Execute multiple commands in sequence
        
        Args:
            commands: List of commands to execute
            shell_type: Shell type for all commands
            
        Returns:
            List of result dictionaries
        """
        results = []
        for cmd in commands:
            result = self.execute_command(cmd, shell_type, analyze=False)
            results.append(result)
            
            # Stop if command failed
            if not result['success']:
                break
        
        return results
    
    def execute_pipeline(self, commands: List[str]) -> Dict:
        """
        Execute commands as a pipeline (output of one feeds to next)
        
        Args:
            commands: List of commands
            
        Returns:
            Final result dictionary
        """
        try:
            # Join commands with pipe
            pipeline = " | ".join(commands)
            return self.execute_command(pipeline, "powershell", analyze=True)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Pipeline failed: {str(e)}'
            }
    
    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history"""
        return self.command_history[-limit:]
    
    def suggest_next_command(self, goal: str) -> str:
        """
        Use AI to suggest next command for a goal
        
        Args:
            goal: What user wants to achieve
            
        Returns:
            Suggested command
        """
        try:
            # Include recent history
            history_context = ""
            if self.command_history:
                recent = self.command_history[-3:]
                history_context = "\n".join([
                    f"Command: {h['command']}\nOutput: {h['output'][:200]}..."
                    for h in recent
                ])
            
            prompt = f"""Based on the user's goal and recent command history, suggest the next PowerShell command to execute.

User's Goal: {goal}

Recent Commands:
{history_context if history_context else "No recent commands"}

Provide ONLY the PowerShell command, nothing else. Be specific and safe."""
            
            suggestion = self.ollama.generate(
                prompt,
                system_message="You are a PowerShell expert. Suggest safe, effective commands.",
                temperature=0.3
            )
            
            # Clean the suggestion
            if suggestion:
                suggestion = suggestion.strip()
                # Remove markdown code blocks if present
                suggestion = re.sub(r'```.*?\n', '', suggestion)
                suggestion = re.sub(r'```', '', suggestion)
                suggestion = suggestion.strip()
            
            return suggestion if suggestion else "No suggestion available"
            
        except Exception as e:
            return f"Failed to generate suggestion: {str(e)}"
    
    def explain_command(self, command: str) -> str:
        """
        Explain what a command does
        
        Args:
            command: Command to explain
            
        Returns:
            Explanation
        """
        try:
            prompt = f"""Explain this PowerShell/CMD command in simple terms:

Command: {command}

Explain:
1. What it does
2. What the output will be
3. Any risks or side effects

Be concise and clear."""
            
            explanation = self.ollama.generate(
                prompt,
                system_message="You are a helpful assistant explaining command line commands.",
                temperature=0.5
            )
            
            return explanation if explanation else "Unable to explain command"
            
        except Exception as e:
            return f"Explanation failed: {str(e)}"
