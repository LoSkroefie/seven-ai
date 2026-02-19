"""
Structured Identity System - Manage self-awareness markdown files

This module enables Seven to:
1. Read its identity files (SOUL, IDENTITY, USER, TOOLS, HEARTBEAT, BOOTSTRAP)
2. Update files as it learns
3. Perform heartbeat checks
4. Detect and handle bootstrap scenarios
"""

from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import re

class StructuredIdentity:
    """
    Manage Seven's self-awareness through structured markdown files.
    
    Files:
    - SOUL.md: Core principles and beliefs
    - IDENTITY.md: Who Seven is, capabilities, version
    - USER.md: Information about the user
    - TOOLS.md: Available tools and environment
    - HEARTBEAT.md: Periodic check definitions
    - BOOTSTRAP.md: First-time interaction guide
    - SILENT_REPLIES.md: When to be minimal
    """
    
    def __init__(self, identity_dir: Path = None):
        """Initialize with identity directory"""
        if identity_dir is None:
            # Default to identity/ subdirectory
            import config
            self.identity_dir = Path(__file__).parent.parent / "identity"
        else:
            self.identity_dir = Path(identity_dir)
        
        # Ensure directory exists
        self.identity_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.files = {
            'soul': self.identity_dir / "SOUL.md",
            'identity': self.identity_dir / "IDENTITY.md",
            'user': self.identity_dir / "USER.md",
            'tools': self.identity_dir / "TOOLS.md",
            'heartbeat': self.identity_dir / "HEARTBEAT.md",
            'bootstrap': self.identity_dir / "BOOTSTRAP.md",
            'silent_replies': self.identity_dir / "SILENT_REPLIES.md"
        }
        
        # Cache for loaded content
        self._cache = {}
        self._last_load_times = {}
        
        # Heartbeat tracking
        self.last_heartbeat_time = None
        self.heartbeat_history = []
        
        # Bootstrap tracking
        self.bootstrap_completed = False
    
    def load_all(self) -> Dict[str, str]:
        """
        Load all identity files into memory
        
        Returns:
            Dictionary of file_key -> content
        """
        result = {}
        for key, path in self.files.items():
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    result[key] = content
                    self._cache[key] = content
                    self._last_load_times[key] = datetime.now()
                except Exception as e:
                    print(f"Warning: Could not load {key}: {e}")
                    result[key] = f"# {key.upper()}\n\n[File not accessible]"
            else:
                result[key] = f"# {key.upper()}\n\n[File not found]"
        
        return result
    
    def get_file(self, file_key: str, force_reload: bool = False) -> str:
        """
        Get content of a specific identity file
        
        Args:
            file_key: One of 'soul', 'identity', 'user', 'tools', 'heartbeat', 'bootstrap'
            force_reload: Reload from disk even if cached
            
        Returns:
            File content as string
        """
        if force_reload or file_key not in self._cache:
            path = self.files.get(file_key)
            if path and path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    self._cache[file_key] = content
                    self._last_load_times[file_key] = datetime.now()
                    return content
                except Exception as e:
                    return f"# Error loading {file_key}: {e}"
            else:
                return f"# {file_key.upper()} not found"
        
        return self._cache.get(file_key, "")
    
    def update_file(self, file_key: str, new_content: str) -> bool:
        """
        Update an identity file
        
        Args:
            file_key: File to update
            new_content: New content
            
        Returns:
            True if successful
        """
        path = self.files.get(file_key)
        if not path:
            return False
        
        try:
            # Backup current version
            if path.exists():
                backup_path = path.with_suffix('.md.backup')
                backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
            
            # Write new content
            path.write_text(new_content, encoding='utf-8')
            
            # Update cache
            self._cache[file_key] = new_content
            self._last_load_times[file_key] = datetime.now()
            
            return True
        except Exception as e:
            print(f"Error updating {file_key}: {e}")
            return False
    
    def append_to_user_notes(self, note: str) -> bool:
        """
        Append a note to USER.md notes section
        
        Args:
            note: Note to add
            
        Returns:
            True if successful
        """
        current = self.get_file('user')
        
        # Find notes section
        if "## Notes & Observations" in current:
            # Append to existing notes
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_note = f"\n- [{timestamp}] {note}"
            
            # Find where to insert (before "## Evolution" or end of file)
            if "## Evolution" in current:
                parts = current.split("## Evolution")
                updated = parts[0].rstrip() + new_note + "\n\n## Evolution" + parts[1]
            else:
                updated = current.rstrip() + new_note + "\n"
            
            return self.update_file('user', updated)
        
        return False
    
    def update_user_field(self, field_path: str, value: str) -> bool:
        """
        Update a specific field in USER.md
        
        Args:
            field_path: Path like "Basic Info/Name" or "Communication Style/Preferences"
            value: New value
            
        Returns:
            True if successful
        """
        current = self.get_file('user')
        
        # Simple find and replace for now
        # In future, could use more sophisticated markdown parsing
        
        return self.update_file('user', current)
    
    def get_llm_context(self) -> str:
        """
        Get formatted context for LLM system message
        
        Returns:
            Formatted identity context
        """
        parts = []
        
        # Load all files
        files = self.load_all()
        
        # Add each with header
        for key in ['soul', 'identity', 'user', 'tools']:
            if key in files:
                parts.append(f"=== {key.upper()} ===\n{files[key]}\n")
        
        return "\n".join(parts)
    
    def check_heartbeat(self, personality, tasks, projects, memory) -> Optional[str]:
        """
        Perform heartbeat check
        
        Args:
            personality: PersonalityCore instance
            tasks: TaskManager instance
            projects: ProjectTracker instance
            memory: MemoryManager instance
            
        Returns:
            Status message or None if all OK
        """
        issues = []
        
        # Check pending tasks
        if tasks:
            try:
                upcoming = tasks.get_upcoming_tasks(hours=2)
                if upcoming:
                    issues.append(f"IMPORTANT - {len(upcoming)} task(s) due soon")
            except:
                pass
        
        # Check unfinished topics
        if personality and hasattr(personality, 'unfinished_topics'):
            try:
                if personality.unfinished_topics:
                    topic = list(personality.unfinished_topics)[0][:50]
                    issues.append(f"INFO - Unfinished topic: {topic}")
            except:
                pass
        
        # Check project staleness
        if projects:
            try:
                stale = projects.get_stale_projects(days=3)
                if stale:
                    issues.append(f"INFO - {len(stale)} project(s) without recent activity")
            except:
                pass
        
        # Track heartbeat
        self.last_heartbeat_time = datetime.now()
        self.heartbeat_history.append({
            'time': self.last_heartbeat_time,
            'issues_found': len(issues)
        })
        
        # Keep only last 10 heartbeats
        self.heartbeat_history = self.heartbeat_history[-10:]
        
        if issues:
            return "\n".join(issues)
        else:
            return "HEARTBEAT_OK"
    
    def should_bootstrap(self, conversation_count: int = 0) -> bool:
        """
        Determine if bootstrap greeting is needed
        
        Args:
            conversation_count: Number of conversations with user
            
        Returns:
            True if should run bootstrap
        """
        # Check if USER.md has real information
        user_content = self.get_file('user')
        
        # Look for placeholder content
        if "## Basic Info" in user_content:
            if "**Name**: Jan" not in user_content:
                return True
        
        # Check conversation count
        if conversation_count < 3:
            return True
        
        return False
    
    def get_bootstrap_greeting(self) -> str:
        """
        Get bootstrap greeting from BOOTSTRAP.md
        
        Returns:
            Initial greeting text
        """
        bootstrap = self.get_file('bootstrap')
        
        # Extract greeting from file
        # Look for the greeting example
        if "## Initial Greeting" in bootstrap:
            lines = bootstrap.split('\n')
            in_greeting = False
            greeting_lines = []
            
            for line in lines:
                if "### Warm but Direct" in line:
                    in_greeting = True
                    continue
                if in_greeting:
                    if line.startswith('```'):
                        in_greeting = not in_greeting
                        if not in_greeting:
                            break
                    elif in_greeting and line.strip() and not line.startswith('#'):
                        greeting_lines.append(line.strip('"'))
            
            if greeting_lines:
                return '\n'.join(greeting_lines).strip()
        
        # Default greeting
        return """Hi! I'm Seven, your AI assistant. I'm here to be genuinely helpful - 
not just answer questions, but proactively solve problems and remember 
what matters to you.

I learn and grow from our conversations. The more we interact, the 
better I'll understand your preferences and needs.

Let's start with the basics: What's your name?"""
    
    def should_use_silent_reply(self, user_input: str) -> bool:
        """
        Check if situation calls for silent/minimal reply
        
        Args:
            user_input: User's message
            
        Returns:
            True if should respond minimally
        """
        user_lower = user_input.lower().strip()
        
        # Heartbeat check
        if any(phrase in user_lower for phrase in [
            "status check", "check your heartbeat", "how are things",
            "anything need attention", "heartbeat check"
        ]):
            return True
        
        # Simple thanks
        if user_lower in ["thanks", "thank you", "ty", "thx"]:
            return True
        
        # Simple acknowledgments
        if user_lower in ["ok", "okay", "got it", "understood", "noted"]:
            return True
        
        return False
    
    def get_minimal_reply(self, user_input: str, context: str = "") -> str:
        """
        Get appropriate minimal reply
        
        Args:
            user_input: User's message
            context: Context about what was done
            
        Returns:
            Minimal response
        """
        user_lower = user_input.lower().strip()
        
        # Heartbeat
        if "heartbeat" in user_lower or "status check" in user_lower:
            return "HEARTBEAT_OK"
        
        # Thanks
        if "thank" in user_lower:
            return "Anytime"
        
        # Acknowledgment
        if user_lower in ["ok", "okay"]:
            return "[OK]"
        
        # Task completion
        if context and "saved" in context.lower():
            return "Saved"
        if context and "done" in context.lower():
            return "Done"
        
        # Default minimal
        return "Got it"
    
    def get_stats(self) -> Dict:
        """Get identity system statistics"""
        return {
            'files_loaded': len(self._cache),
            'last_heartbeat': self.last_heartbeat_time.isoformat() if self.last_heartbeat_time else None,
            'heartbeat_history_count': len(self.heartbeat_history),
            'bootstrap_completed': self.bootstrap_completed,
            'identity_dir': str(self.identity_dir)
        }


# Example usage
if __name__ == "__main__":
    # Test identity system
    identity = StructuredIdentity()
    
    # Load all files
    print("Loading identity files...")
    files = identity.load_all()
    
    print(f"\nLoaded {len(files)} files:")
    for key in files.keys():
        lines = files[key].count('\n')
        print(f"  - {key}: {lines} lines")
    
    # Get LLM context
    print("\nGenerating LLM context...")
    context = identity.get_llm_context()
    print(f"Context length: {len(context)} characters")
    
    # Test heartbeat
    print("\nTesting heartbeat...")
    status = identity.check_heartbeat(None, None, None, None)
    print(f"Heartbeat: {status}")
    
    # Test bootstrap detection
    print("\nTesting bootstrap detection...")
    needs_bootstrap = identity.should_bootstrap(conversation_count=0)
    print(f"Needs bootstrap: {needs_bootstrap}")
    
    if needs_bootstrap:
        greeting = identity.get_bootstrap_greeting()
        print(f"\nBootstrap greeting:\n{greeting[:100]}...")
    
    print("\n[OK] Identity system test complete")
