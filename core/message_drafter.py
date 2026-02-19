"""
Email and Message Drafting Assistant
Helps compose emails and messages with AI assistance
"""

class MessageDrafter:
    """Assists with drafting emails and messages"""
    
    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        self.draft_history = []
        self.current_draft = None
    
    def draft_email(self, recipient: str, purpose: str, tone: str = "professional") -> str:
        """Draft an email"""
        
        if not self.ollama:
            return "I need my drafting abilities to create emails."
        
        tone_instructions = {
            "professional": "Use professional, formal language",
            "casual": "Use friendly, casual language",
            "formal": "Use very formal, business language",
            "friendly": "Use warm, friendly language"
        }
        
        tone_instruction = tone_instructions.get(tone.lower(), tone_instructions["professional"])
        
        prompt = f"""Draft an email to {recipient} about: {purpose}

Tone: {tone_instruction}

Provide subject line and email body. Make it clear, concise, and well-structured."""
        
        try:
            draft = self.ollama.generate(
                prompt,
                system_message="You are a professional email writing assistant.",
                temperature=0.7
            )
            
            if draft:
                self.current_draft = {
                    'type': 'email',
                    'recipient': recipient,
                    'purpose': purpose,
                    'content': draft
                }
                self.draft_history.append(self.current_draft)
                return draft
            return "I had trouble drafting the email."
        except:
            return "I couldn't draft the email right now."
    
    def refine_draft(self, instruction: str) -> str:
        """Refine the current draft based on instruction"""
        
        if not self.current_draft:
            return "There's no current draft to refine."
        
        if not self.ollama:
            return "I need my drafting abilities to refine."
        
        prompt = f"""Here's the current draft:

{self.current_draft['content']}

Please modify it according to this instruction: {instruction}

Provide the complete revised version."""
        
        try:
            refined = self.ollama.generate(
                prompt,
                system_message="You are a professional editor refining written content.",
                temperature=0.6
            )
            
            if refined:
                self.current_draft['content'] = refined
                return refined
            return "I had trouble refining the draft."
        except:
            return "I couldn't refine the draft right now."
    
    def make_more_professional(self) -> str:
        """Make current draft more professional"""
        return self.refine_draft("Make this more professional and formal")
    
    def make_shorter(self) -> str:
        """Make current draft shorter"""
        return self.refine_draft("Make this more concise, removing unnecessary words")
    
    def make_friendlier(self) -> str:
        """Make current draft friendlier"""
        return self.refine_draft("Make this sound more friendly and warm")
