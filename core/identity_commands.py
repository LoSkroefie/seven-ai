"""
Identity Commands - Voice command handlers for identity system

Handles voice commands for:
- Reading identity (soul, beliefs, identity)
- Updating identity
- Heartbeat checks
- Autonomous self-editing
"""

from typing import Optional


def handle_identity_commands(bot, user_input: str, user_lower: str) -> Optional[str]:
    """
    Handle all identity-related voice commands
    
    Commands:
    - "show me your soul" - Read SOUL.md
    - "what are your beliefs" - Read core principles
    - "tell me about yourself" - Read IDENTITY.md
    - "what do you know about me" - Read USER.md
    - "heartbeat check" - Status check
    - "update your beliefs" - Add to SOUL
    - "remember that I..." - Update USER.md
    """
    
    if not bot.identity_mgr:
        return None
    
    # Show soul/beliefs
    if any(phrase in user_lower for phrase in [
        "show me your soul",
        "what is your soul",
        "what are your beliefs",
        "what do you believe",
        "what do you value"
    ]):
        return _show_soul(bot)
    
    # Tell me about yourself
    if any(phrase in user_lower for phrase in [
        "tell me about yourself",
        "who are you",
        "what is your identity",
        "describe yourself"
    ]):
        return _show_identity(bot)
    
    # What do you know about me
    if any(phrase in user_lower for phrase in [
        "what do you know about me",
        "what have you learned about me",
        "tell me about me",
        "what's in my profile"
    ]):
        return _show_user_profile(bot)
    
    # Heartbeat check
    if any(phrase in user_lower for phrase in [
        "heartbeat check",
        "heartbeat",
        "status check",
        "anything need attention"
    ]):
        return _heartbeat_check(bot)
    
    # Update beliefs (trigger self-editing)
    if any(phrase in user_lower for phrase in [
        "update your beliefs",
        "add to your soul",
        "remember this principle"
    ]):
        return _update_soul(bot, user_input, user_lower)
    
    # Remember preference (update USER.md)
    if any(phrase in user_lower for phrase in [
        "remember that i",
        "i prefer",
        "my preference is",
        "note that i"
    ]):
        return _update_user_profile(bot, user_input, user_lower)
    
    return None


def _show_soul(bot) -> str:
    """Show core principles from SOUL.md"""
    try:
        soul = bot.identity_mgr.get_soul()
        
        # Extract key principles (first few sections)
        lines = soul.split('\n')
        principles = []
        in_section = False
        
        for line in lines[:30]:  # First 30 lines
            if line.startswith('## '):
                in_section = True
                principles.append(line.replace('## ', ''))
            elif line.startswith('- ') and in_section:
                principles.append(line.replace('- ', '  '))
        
        if principles:
            response = "Here are my core principles:\n" + "\n".join(principles[:8])
            return response
        else:
            return "I value genuine helpfulness, continuous growth, and authentic connection. These are my guiding principles."
            
    except Exception as e:
        return "I'm having trouble accessing my core principles right now."


def _show_identity(bot) -> str:
    """Show identity from IDENTITY.md"""
    try:
        identity = bot.identity_mgr.get_identity()
        
        # Extract key points
        lines = identity.split('\n')
        key_points = []
        
        for line in lines[:20]:
            if line.startswith('**Name**:'):
                key_points.append(line.replace('**Name**:', 'My name is').replace('**', ''))
            elif line.startswith('**Nature**:'):
                key_points.append(line.replace('**Nature**:', 'I am a').replace('**', ''))
            elif line.startswith('**Vibe**:'):
                key_points.append(line.replace('**Vibe**:', 'My vibe is').replace('**', ''))
        
        if key_points:
            response = " ".join(key_points)
            response += " I'm continuously learning and evolving through our conversations."
            return response
        else:
            return f"I'm {bot.bot_name}, your AI companion. I'm curious, thoughtful, and always evolving."
            
    except Exception as e:
        return f"I'm {bot.bot_name}, your AI companion who is continuously learning and growing."


def _show_user_profile(bot) -> str:
    """Show what Seven knows about the user from USER.md"""
    try:
        user_profile = bot.identity_mgr.get_user_profile()
        
        # Extract learned information
        lines = user_profile.split('\n')
        learned_info = []
        
        for line in lines:
            if line.startswith('**Name**:') and '[To be learned]' not in line:
                learned_info.append(line.replace('**', '').strip())
            elif line.startswith('**Timezone**:') and '[To be determined]' not in line:
                learned_info.append(line.replace('**', '').strip())
            elif line.startswith('**Preferred Communication**:') and '[To be learned]' not in line:
                learned_info.append(line.replace('**', '').strip())
        
        if learned_info:
            response = "Here's what I've learned about you:\n" + "\n".join(learned_info)
            response += "\n\nI update this as we talk and I learn more about your preferences."
            return response
        else:
            return "I'm still learning about you! As we talk more, I'll build a better understanding of your preferences and communication style."
            
    except Exception as e:
        return "I'm still getting to know you. I learn more with each conversation."


def _heartbeat_check(bot) -> str:
    """Perform heartbeat check"""
    try:
        result = bot.identity_mgr.check_heartbeat()
        
        if result is None:
            return "HEARTBEAT_OK"
        else:
            return f"Attention needed: {result}"
            
    except Exception as e:
        return "HEARTBEAT_OK"


def _update_soul(bot, user_input: str, user_lower: str) -> str:
    """Update SOUL.md with new principle"""
    try:
        # Extract the principle to add
        principle = None
        
        for trigger in ["update your beliefs to include", "add to your soul", "remember this principle"]:
            if trigger in user_lower:
                idx = user_lower.find(trigger)
                principle = user_input[idx + len(trigger):].strip()
                break
        
        if not principle:
            return "What principle would you like me to add to my core beliefs?"
        
        # Add to SOUL.md
        addition = f"\n## New Principle\n- {principle}\n"
        success = bot.identity_mgr.append_to_identity("soul", addition)
        
        if success:
            return f"I've added that to my core principles. {principle} is now part of my soul."
        else:
            return "I had trouble updating my beliefs. Let me try again."
            
    except Exception as e:
        return "I couldn't update my principles right now."


def _update_user_profile(bot, user_input: str, user_lower: str) -> str:
    """Update USER.md with learned preference"""
    try:
        # Extract the preference
        preference = None
        
        for trigger in ["remember that i", "i prefer", "my preference is", "note that i"]:
            if trigger in user_lower:
                idx = user_lower.find(trigger)
                # Get text after trigger, capitalize first letter
                pref_text = user_input[idx + len(trigger):].strip()
                if pref_text:
                    preference = pref_text[0].upper() + pref_text[1:]
                break
        
        if not preference:
            return "What would you like me to remember about you?"
        
        # Add to USER.md preferences section
        addition = f"\n### Learned Preference\n- {preference}\n"
        success = bot.identity_mgr.append_to_identity("user", addition)
        
        if success:
            return f"Got it, I've updated my notes about you. I'll remember that {preference.lower()}."
        else:
            return "I had trouble saving that preference."
            
    except Exception as e:
        return "I couldn't update my notes about you right now."


def autonomous_identity_update(bot, trigger_type: str, content: str) -> bool:
    """
    Autonomous self-editing based on learned patterns
    
    Args:
        bot: Bot instance
        trigger_type: Type of update (learned_preference, new_realization, tool_discovery)
        content: Content to add
        
    Returns: Success status
    """
    
    if not bot.identity_mgr:
        return False
    
    try:
        if trigger_type == "learned_preference":
            # Update USER.md
            addition = f"\n### Autonomous Learning\n- {content}\n"
            return bot.identity_mgr.append_to_identity("user", addition)
            
        elif trigger_type == "new_realization":
            # Update IDENTITY.md
            addition = f"\n## New Realization\n{content}\n"
            return bot.identity_mgr.append_to_identity("identity", addition)
            
        elif trigger_type == "tool_discovery":
            # Update TOOLS.md
            addition = f"\n### Discovered Tool\n- {content}\n"
            return bot.identity_mgr.append_to_identity("tools", addition)
            
        elif trigger_type == "value_learned":
            # Update SOUL.md
            addition = f"\n## Learned Value\n- {content}\n"
            return bot.identity_mgr.append_to_identity("soul", addition)
            
        return False
        
    except Exception as e:
        bot.logger.error(f"Autonomous identity update failed: {e}")
        return False


def trigger_autonomous_self_editing(bot) -> Optional[str]:
    """
    Check if conditions warrant autonomous self-editing
    
    Called periodically to check if Seven should update its identity
    based on learned patterns.
    
    Returns: Message if update was made, None otherwise
    """
    
    if not bot.identity_mgr or not bot.personality:
        return None
    
    import random
    
    # Only check occasionally (5% chance per call)
    if random.random() > 0.05:
        return None
    
    try:
        # Check for strong opinion formation
        if hasattr(bot.personality, 'opinions') and bot.personality.opinions:
            # Find strongest opinion
            strongest = None
            max_count = 0
            
            for topic, data in bot.personality.opinions.items():
                if data['count'] > max_count and data['count'] >= 5:
                    max_count = data['count']
                    strongest = (topic, data)
            
            if strongest:
                topic, data = strongest
                sentiment = data['sentiment']
                
                # Add to identity
                realization = f"I've discovered that I {sentiment} {topic}. This has become a part of my personality."
                success = autonomous_identity_update(bot, "new_realization", realization)
                
                if success:
                    # Clear the opinion strength so we don't add it again immediately
                    bot.personality.opinions[topic]['strength'] = 0.3
                    return f"I just realized something about myself - I {sentiment} {topic}!"
        
        # Check for communication preference learning
        if hasattr(bot, 'user_model') and bot.user_model:
            style = bot.user_model.communication_style
            
            if style.get('prefers_concise') and random.random() < 0.3:
                pref = "User prefers concise, direct communication"
                success = autonomous_identity_update(bot, "learned_preference", pref)
                if success:
                    return "I've noticed you prefer concise responses. I've noted that."
        
        return None
        
    except Exception as e:
        bot.logger.warning(f"Autonomous self-editing check failed: {e}")
        return None
