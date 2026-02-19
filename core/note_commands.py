"""
Note command handlers for voice-activated note taking
Mixin for enhanced_bot.py
"""

def _handle_note_commands(self, user_input: str, user_lower: str) -> str:
    """Handle all note-related voice commands"""
    bot_name_lower = self.bot_name.lower()
    
    # Check if bot name is mentioned (required for note commands)
    if bot_name_lower not in user_lower:
        return None
    
    # Take a note (prompt for content)
    if "take a note" in user_lower or "make a note" in user_lower:
        self.pending_note_content = True
        return "What would you like me to note?"
    
    # Note that... (direct note)
    if "note that" in user_lower:
        # Extract content after "note that"
        idx = user_lower.find("note that")
        if idx != -1:
            content = user_input[idx + 9:].strip()
            if content:
                return self._save_note(content)
        return "What would you like me to note?"
    
    # Read notes
    if any(phrase in user_lower for phrase in ["read my notes", "read notes", "what are my notes", "show my notes"]):
        return self._read_notes()
    
    # Search notes
    if "search notes for" in user_lower or "find note about" in user_lower:
        # Extract search query
        for phrase in ["search notes for", "find note about", "find notes about"]:
            if phrase in user_lower:
                idx = user_lower.find(phrase)
                query = user_input[idx + len(phrase):].strip()
                if query:
                    return self._search_notes(query)
        return "What would you like me to search for?"
    
    # Delete notes
    if "delete note" in user_lower:
        if "about" in user_lower:
            idx = user_lower.find("about")
            query = user_input[idx + 5:].strip()
            if query:
                return self._delete_notes(query)
        return "What note would you like me to delete?"
    
    # Count notes
    if "how many notes" in user_lower:
        return self._count_notes()
    
    return None

def _handle_note_content(self, content: str) -> str:
    """Handle note content after 'take a note' prompt"""
    self.pending_note_content = False
    
    if content.lower().strip() in ["cancel", "never mind", "nothing", "skip"]:
        return "Okay, note cancelled."
    
    return self._save_note(content)

def _save_note(self, content: str) -> str:
    """Save a note with auto-categorization"""
    try:
        # Auto-detect category and importance
        category = self.notes.auto_categorize(content)
        importance = self.notes.extract_importance(content)
        
        note_id = self.notes.add_note(content, category=category, importance=importance)
        
        responses = [
            f"Got it. I've noted that down as a {category} item.",
            f"Noted! I've saved that to your {category} notes.",
            f"I've recorded that in your {category} notes.",
            f"Done. That's in your {category} notes now.",
        ]
        
        import random
        return random.choice(responses)
    except Exception as e:
        self.logger.error(f"Failed to save note: {e}")
        return "I had trouble saving that note. Could you try again?"

def _read_notes(self, category: str = None, limit: int = 5) -> str:
    """Read notes aloud"""
    try:
        if category:
            notes = self.notes.get_notes_by_category(category, limit=limit)
        else:
            notes = self.notes.get_all_notes(limit=limit)
        
        return self.notes.format_notes_for_speech(notes, max_notes=limit)
    except Exception as e:
        self.logger.error(f"Failed to read notes: {e}")
        return "I'm having trouble accessing your notes right now."

def _search_notes(self, query: str) -> str:
    """Search and read matching notes"""
    try:
        notes = self.notes.search_notes(query, limit=10)
        
        if not notes:
            return f"I couldn't find any notes about {query}."
        
        return self.notes.format_notes_for_speech(notes, max_notes=5)
    except Exception as e:
        self.logger.error(f"Failed to search notes: {e}")
        return "I had trouble searching your notes."

def _delete_notes(self, query: str) -> str:
    """Delete notes matching query"""
    try:
        # First, find matching notes
        notes = self.notes.search_notes(query, limit=5)
        
        if not notes:
            return f"I couldn't find any notes about {query} to delete."
        
        # Delete them
        deleted_count = self.notes.delete_notes_by_content(query)
        
        if deleted_count == 1:
            return "I've deleted that note."
        else:
            return f"I've deleted {deleted_count} notes matching that."
    except Exception as e:
        self.logger.error(f"Failed to delete notes: {e}")
        return "I had trouble deleting those notes."

def _count_notes(self) -> str:
    """Count and report notes"""
    try:
        total, active = self.notes.get_note_count()
        
        if total == 0:
            return "You don't have any notes yet."
        elif active == total:
            return f"You have {total} note{'s' if total != 1 else ''}."
        else:
            completed = total - active
            return f"You have {active} active note{'s' if active != 1 else ''} and {completed} completed."
    except Exception as e:
        self.logger.error(f"Failed to count notes: {e}")
        return "I'm having trouble counting your notes."

def _summarize_conversation(self) -> str:
    """Summarize recent conversation"""
    try:
        recent = self.memory.get_recent_conversations(limit=10)
        
        if not recent:
            return "We haven't had much of a conversation yet."
        
        # Build summary prompt
        conversation_text = "\n".join([
            f"You: {turn[0]}\nMe: {turn[1]}" for turn in recent
        ])
        
        summary_prompt = f"""Please provide a brief 2-3 sentence summary of this conversation:

{conversation_text}

Summary:"""
        
        summary = self.ollama.generate(
            summary_prompt,
            system_message="You are a helpful assistant that creates concise conversation summaries.",
            temperature=0.5
        )
        
        if summary:
            return f"Here's a summary of our conversation: {summary}"
        else:
            return "I had trouble summarizing our conversation."
    except Exception as e:
        self.logger.error(f"Failed to summarize conversation: {e}")
        return "I couldn't summarize the conversation right now."
