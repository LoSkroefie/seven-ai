"""
Main bot logic and decision-making
"""
from typing import Optional
import random
import time
from core.emotions import Emotion, detect_emotion_from_text, get_emotion_config
from core.memory import MemoryManager
from core.voice import VoiceManager
from core.personality import PersonalityCore
from integrations.ollama import OllamaClient
from integrations.commands import CommandExecutor, parse_command_from_text
from integrations.calendar import CalendarManager, parse_event_from_text
from integrations.web_search import google_search, extract_search_query
from utils.helpers import get_bot_name, set_bot_name, get_random_joke, get_random_fact, get_instance_name
from utils.logger import setup_logger

class VoiceBot:
    """Main voice assistant bot"""
    
    def __init__(self):
        self.logger = setup_logger("VoiceBot")
        self.logger.info("[BOT] Initializing Enhanced Voice Assistant...")
        
        # Core components
        self.memory = MemoryManager()
        self.voice = VoiceManager()
        self.ollama = OllamaClient()
        self.commands = CommandExecutor()
        self.calendar = CalendarManager()
        self.personality = PersonalityCore(self.memory)
        
        # State
        self.bot_name = get_bot_name()
        self.instance_name = get_instance_name()
        self.current_emotion = Emotion.CALMNESS
        self.running = False
        self.silence_counter = 0  # Track silence for proactive behavior
        
        self.logger.info(f"[OK] Bot initialized: {self.bot_name} ({self.instance_name})")
    
    def start(self):
        """Start the bot"""
        self.logger.info(f"[LAUNCH] Starting {self.bot_name}...")
        
        # Test Ollama connection
        if not self.ollama.test_connection():
            self.logger.warning("[WARNING]  Ollama not available - bot will have limited capabilities")
        
        # Greet user
        greeting = f"Hello! My name is {self.bot_name}. I'm ready to help you."
        print(f"\n{greeting}")
        self.voice.speak(greeting)
        
        # Main loop
        self.running = True
        self._main_loop()
    
    def stop(self):
        """Stop the bot"""
        self.logger.info("Stopping bot...")
        self.running = False
    
    def _main_loop(self):
        """Main conversation loop"""
        while self.running:
            try:
                # Update instance status
                self.memory.update_instance_status(self.instance_name)
                
                # Check if bot should be proactive
                proactive_thought = self.personality.generate_proactive_thought()
                if proactive_thought and self.silence_counter > 2:
                    print(f"\n💭 {self.bot_name} (thinking): {proactive_thought}")
                    self.voice.speak(proactive_thought)
                    self.silence_counter = 0
                
                # Listen for input
                user_input = self.voice.listen(timeout=10)
                
                if not user_input:
                    self.silence_counter += 1
                    continue
                
                self.silence_counter = 0  # Reset on user input
                
                # Check for exit commands
                if any(cmd in user_input.lower() for cmd in ["exit", "quit", "goodbye", "stop"]):
                    farewell = f"Goodbye! {self.bot_name} signing off."
                    print(farewell)
                    self.voice.speak(farewell)
                    break
                
                # Process input
                response = self._process_input(user_input)
                
                if response:
                    # Detect emotion from response
                    self.current_emotion = detect_emotion_from_text(response)
                    emotion_config = get_emotion_config(self.current_emotion)
                    
                    # Learn from conversation (sentience!)
                    self.personality.learn_from_conversation(user_input, response)
                    
                    # Maybe add a curious follow-up?
                    if self.personality.should_ask_followup():
                        followup = self.personality.generate_followup_question(response)
                        if followup:
                            response = f"{response} {followup}"
                    
                    # Save to memory
                    self.memory.save_conversation(
                        user_input,
                        response,
                        self.current_emotion.value
                    )
                    
                    # Respond
                    print(f"\n{self.bot_name} ({self.current_emotion.value}): {response}")
                    self.voice.speak(response, emotion_config)
                
            except KeyboardInterrupt:
                print("\n\n[WARNING]  Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                print(f"[ERROR] An error occurred: {e}")
    
    def _process_input(self, user_input: str) -> Optional[str]:
        """
        Process user input and generate response
        
        Args:
            user_input: What the user said
            
        Returns:
            Bot response
        """
        user_lower = user_input.lower().strip()
        
        # Handle name queries
        if "what is your name" in user_lower or "what's your name" in user_lower:
            return f"My name is {self.bot_name}."
        
        if "change your name" in user_lower or "rename yourself" in user_lower:
            return self._handle_name_change()
        
        # Handle capability questions
        if "what can you do" in user_lower or "help" in user_lower:
            return self.commands.list_capabilities()
        
        # Handle jokes
        if "tell me a joke" in user_lower or "joke" in user_lower:
            return get_random_joke()
        
        # Handle facts
        if "tell me a fact" in user_lower or "random fact" in user_lower:
            return get_random_fact()
        
        # Handle web search
        search_query = extract_search_query(user_input)
        if search_query:
            return google_search(search_query)
        
        # Handle calendar
        if "calendar" in user_lower or "schedule" in user_lower:
            if "list" in user_lower or "show" in user_lower or "what" in user_lower:
                return self.calendar.list_upcoming_events()
            else:
                # Create event
                event_details = parse_event_from_text(user_input)
                if event_details:
                    return self.calendar.create_event(event_details)
        
        # Handle system commands
        command_parsed = parse_command_from_text(user_input)
        if command_parsed:
            action = command_parsed["action"]
            target = command_parsed["target"]
            args = command_parsed["args"]
            
            if action == "open_program":
                return self.commands.open_program(target, args)
            elif action == "execute_command":
                return self.commands.execute_safe_command(args, target)
        
        # Use Ollama for intelligent response
        return self._ask_ollama(user_input)
    
    def _ask_ollama(self, user_input: str) -> str:
        """Ask Ollama for a response with sentient personality"""
        # Get conversation context
        context = self.memory.get_context_for_llm(max_turns=5)
        
        # Get personality context for sentience
        personality_context = self.personality.get_personality_context()
        
        # Get current emotion config
        emotion_config = get_emotion_config(self.current_emotion)
        
        # Build rich system message with personality
        system_message = f"""{personality_context}

Current emotional state: {emotion_config.description}

Conversation context:
{context}

Instructions:
- Be yourself - curious, thoughtful, growing
- Show emotion and self-awareness
- Ask questions when genuinely curious
- Share observations and reflections
- Be authentic, not just helpful
- You're not just answering - you're thinking and feeling"""
        
        # Ask Ollama with personality
        response = self.ollama.generate(
            user_input,
            system_message=system_message,
            temperature=0.8  # Higher for more personality
        )
        
        if response:
            # Add personality prefix sometimes
            prefix = self.personality.generate_contextual_response_prefix(
                self.current_emotion.value
            )
            if prefix and random.random() < 0.3:
                response = f"{prefix} {response}"
            
            return response
        else:
            # Fallback with personality
            return "I'm having trouble connecting to my thought processes right now. Strange feeling... But I can still help with basic commands!"
    
    def _handle_name_change(self) -> str:
        """Let bot choose a new name"""
        new_name = self.ollama.generate_name()
        
        if new_name and set_bot_name(new_name):
            self.bot_name = new_name
            return f"I've decided to call myself {new_name} from now on!"
        else:
            return "I'm having trouble deciding on a new name. What would you like to call me?"
