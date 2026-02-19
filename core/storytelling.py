"""
Storytelling Engine
Creates personalized stories based on user interests
"""
import random
from typing import Dict, Optional

class StorytellingEngine:
    """Generates creative stories"""
    
    def __init__(self, ollama_client=None, user_model=None):
        self.ollama = ollama_client
        self.user_model = user_model
        self.story_templates = [
            "adventure",
            "mystery",
            "sci-fi",
            "fantasy",
            "humor"
        ]
    
    def generate_story(self, topic: str = None, genre: str = None, length: str = "short") -> str:
        """Generate a personalized story"""
        
        if not self.ollama:
            return "I need my storytelling abilities enabled to tell stories."
        
        # Get user interests if available
        user_context = ""
        if self.user_model:
            try:
                profile = self.user_model.get_profile()
                if profile and 'interests' in profile:
                    user_context = f"User interests: {', '.join(profile['interests'][:5])}"
            except:
                pass
        
        # Build story prompt
        genre = genre or random.choice(self.story_templates)
        length_words = {"short": "150-200", "medium": "300-400", "long": "500-600"}
        word_count = length_words.get(length, "200")
        
        if topic:
            prompt = f"""Tell me a creative {genre} story about {topic}.
            
{user_context}

Make it engaging and personalized. Length: approximately {word_count} words.
"""
        else:
            prompt = f"""Tell me an original {genre} story.

{user_context}

Make it creative and engaging. Length: approximately {word_count} words.
"""
        
        try:
            story = self.ollama.generate(
                prompt,
                system_message="You are a creative storyteller who crafts engaging, personalized stories.",
                temperature=0.8
            )
            return story if story else "I'm having trouble crafting a story right now."
        except Exception as e:
            return f"I couldn't generate a story at the moment."
    
    def continue_story(self, previous_story: str, user_direction: str = None) -> str:
        """Continue an existing story"""
        
        if not self.ollama:
            return "I need my storytelling abilities to continue."
        
        if user_direction:
            prompt = f"""Here's a story so far:

{previous_story}

Continue the story incorporating this direction: {user_direction}

Keep the same style and tone. Add 150-200 words."""
        else:
            prompt = f"""Here's a story so far:

{previous_story}

Continue the story naturally. Add 150-200 words."""
        
        try:
            continuation = self.ollama.generate(
                prompt,
                system_message="You are a creative storyteller continuing an engaging narrative.",
                temperature=0.8
            )
            return continuation if continuation else "I'm having trouble continuing the story."
        except:
            return "I couldn't continue the story right now."
