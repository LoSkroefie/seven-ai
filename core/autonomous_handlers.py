"""
Handlers for autonomous capabilities (file management, code execution, command processing)
"""
from typing import Optional
import re

class AutonomousHandlers:
    """Mixin class providing handlers for autonomous operations"""
    
    def _list_all_capabilities(self) -> str:
        """List all bot capabilities including autonomous features"""
        capabilities = []
        
        capabilities.append("[TARGET] **Core Capabilities:**")
        capabilities.append("- Voice conversation with emotions")
        capabilities.append("- Proactive behaviors and personality")
        capabilities.append("- Learning from corrections")
        capabilities.append("- Google Calendar integration")
        capabilities.append("- Web search")
        capabilities.append("")
        
        capabilities.append("[BOT] **Autonomous Capabilities:**")
        if hasattr(self, 'file_manager') and self.file_manager:
            capabilities.append("[FOLDER] File operations (create, read, search files)")
        if hasattr(self, 'code_executor') and self.code_executor:
            capabilities.append("💻 Code execution in safe sandbox")
        if hasattr(self, 'notes') and self.notes:
            capabilities.append("[NOTE] Voice-activated notes (say 'Seven, take a note')")
            capabilities.append("   - Take notes, read notes, search notes, count notes")
        if hasattr(self, 'tasks') and self.tasks:
            capabilities.append("[OK] Task and reminder management")
            capabilities.append("   - Add tasks, set reminders, list tasks, complete tasks")
        if hasattr(self, 'projects') and self.projects:
            capabilities.append("[STATS] Multi-session project tracking")
            capabilities.append("   - Start projects, track progress, log work sessions")
        if hasattr(self, 'storyteller') and self.storyteller:
            capabilities.append("📖 Interactive storytelling")
            capabilities.append("   - Tell stories, continue stories, personalized narratives")
        if hasattr(self, 'diary') and self.diary:
            capabilities.append("📔 Personal diary with insights")
            capabilities.append("   - Weekly summaries, mood tracking, conversation analysis")
        if hasattr(self, 'special_dates') and self.special_dates:
            capabilities.append("🎂 Birthday and anniversary tracking")
            capabilities.append("   - Track special dates, get reminders")
        if hasattr(self, 'message_drafter') and self.message_drafter:
            capabilities.append("✉️ Email and message drafting assistant")
            capabilities.append("   - Draft emails, refine messages, adjust tone")
        if hasattr(self, 'cmd_processor') and self.cmd_processor:
            capabilities.append("[CONFIG] Command processing (analyze and execute)")
        
        return "\n".join(capabilities)
    
    def _handle_file_operations(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle file operation requests"""
        if not self.file_manager:
            return None
        
        # Create file
        if "create file" in user_lower or "make a file" in user_lower:
            return self._handle_create_file(user_input)
        
        # Read file
        if "read file" in user_lower or "show file" in user_lower or "open file" in user_lower:
            return self._handle_read_file(user_input)
        
        # Edit file
        if "edit file" in user_lower or "modify file" in user_lower or "change file" in user_lower:
            return self._handle_edit_file(user_input)
        
        # List files
        if "list files" in user_lower or "show files" in user_lower:
            return self._handle_list_files(user_input)
        
        # Delete file
        if "delete file" in user_lower or "remove file" in user_lower:
            return self._handle_delete_file(user_input)
        
        return None
    
    def _handle_create_file(self, user_input: str) -> str:
        """Handle file creation request"""
        # Use Ollama to extract filename and content
        prompt = f"""Extract the filename and initial content from this request:
"{user_input}"

Respond in this exact format:
FILENAME: <filename>
CONTENT: <content or leave empty>"""
        
        try:
            response = self.ollama.generate(prompt, temperature=0.3)
            if response:
                lines = response.split('\n')
                filename = ""
                content = ""
                
                for line in lines:
                    if line.startswith("FILENAME:"):
                        filename = line.replace("FILENAME:", "").strip()
                    elif line.startswith("CONTENT:"):
                        content = line.replace("CONTENT:", "").strip()
                
                if filename:
                    result = self.file_manager.create_file(filename, content)
                    if result['success']:
                        return f"[OK] File created: {filename}"
                    else:
                        return f"[ERROR] Failed to create file: {result['error']}"
        except:
            pass
        
        return "I need more information. Please specify: create file <filename> with content <content>"
    
    def _handle_read_file(self, user_input: str) -> str:
        """Handle file reading request"""
        # Extract filename
        match = re.search(r'read file ([^\s]+)', user_input, re.IGNORECASE)
        if not match:
            match = re.search(r'show file ([^\s]+)', user_input, re.IGNORECASE)
        
        if match:
            filename = match.group(1)
            result = self.file_manager.read_file(filename, max_lines=50)
            
            if result['success']:
                return f"[FILE] Contents of {filename}:\n\n{result['content']}"
            else:
                return f"[ERROR] {result['error']}"
        
        return "Please specify which file to read"
    
    def _handle_edit_file(self, user_input: str) -> str:
        """Handle file editing request"""
        return "To edit a file, please say: edit file <filename> replace <old_text> with <new_text>"
    
    def _handle_list_files(self, user_input: str) -> str:
        """Handle file listing request"""
        result = self.file_manager.list_files()
        
        if result['success']:
            if result['count'] == 0:
                return "[FOLDER] No files in current directory"
            
            files_list = []
            for file in result['files'][:20]:  # Limit to 20
                size_kb = file['size'] / 1024
                files_list.append(f"- {file['name']} ({size_kb:.1f} KB)")
            
            return f"[FOLDER] Files in {result['directory']}:\n" + "\n".join(files_list)
        else:
            return f"[ERROR] {result['error']}"
    
    def _handle_delete_file(self, user_input: str) -> str:
        """Handle file deletion request"""
        return "[WARNING]  File deletion requires explicit confirmation. Please confirm you want to delete the file."
    
    def _handle_code_execution(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle code execution requests"""
        if not self.code_executor:
            return None
        
        # Detect code execution requests
        if any(phrase in user_lower for phrase in ["run code", "execute code", "run python", "calculate"]):
            return self._execute_python_code(user_input)
        
        return None
    
    def _execute_python_code(self, user_input: str) -> str:
        """Execute Python code from user request"""
        # Extract code using Ollama
        prompt = f"""Extract the Python code to execute from this request:
"{user_input}"

Provide ONLY the Python code, no explanations."""
        
        try:
            code = self.ollama.generate(prompt, temperature=0.3)
            if code:
                # Clean code
                code = code.strip()
                code = re.sub(r'```python\n?', '', code)
                code = re.sub(r'```\n?', '', code)
                
                # Execute
                result = self.code_executor.execute_code(code)
                
                if result['success']:
                    output = result['output'] if result['output'] else "(no output)"
                    return f"[OK] Code executed in {result['execution_time']}s:\n{output}"
                else:
                    return f"[ERROR] Execution failed: {result['error']}"
        except:
            pass
        
        return "I couldn't extract valid Python code from your request"
    
    def _handle_enhanced_commands(self, user_input: str, user_lower: str) -> Optional[str]:
        """Handle enhanced command processing"""
        if not self.cmd_processor:
            return None
        
        # Detect command execution with analysis
        if "analyze command" in user_lower or "run and analyze" in user_lower:
            return self._run_and_analyze_command(user_input)
        
        # Command suggestion
        if "suggest command" in user_lower or "how do i" in user_lower:
            return self._suggest_command(user_input)
        
        # Explain command
        if "explain command" in user_lower or "what does" in user_lower:
            return self._explain_command(user_input)
        
        return None
    
    def _run_and_analyze_command(self, user_input: str) -> str:
        """Run command with AI analysis"""
        # Extract command
        prompt = f"""Extract the command to run from this request:
"{user_input}"

Provide ONLY the command, no explanations."""
        
        try:
            command = self.ollama.generate(prompt, temperature=0.3)
            if command:
                command = command.strip()
                result = self.cmd_processor.execute_command(command, analyze=True)
                
                if result['success']:
                    response = f"[OK] Command executed:\n{result['output']}\n\n"
                    if 'analysis' in result:
                        response += f"[STATS] Analysis: {result['analysis']}"
                    return response
                else:
                    return f"[ERROR] {result.get('error', 'Command failed')}"
        except:
            pass
        
        return "I couldn't extract a valid command from your request"
    
    def _suggest_command(self, user_input: str) -> str:
        """Suggest command for user's goal"""
        suggestion = self.cmd_processor.suggest_next_command(user_input)
        return f"[TIP] Suggested command:\n{suggestion}\n\nWould you like me to run this?"
    
    def _explain_command(self, user_input: str) -> str:
        """Explain a command"""
        # Extract command to explain
        match = re.search(r'command[:\s]+(.+)', user_input, re.IGNORECASE)
        if match:
            command = match.group(1).strip()
            explanation = self.cmd_processor.explain_command(command)
            return f"📖 Explanation:\n{explanation}"
        
        return "Please specify which command you'd like me to explain"
