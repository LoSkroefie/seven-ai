"""
Helper utilities
"""
import random
from pathlib import Path
import uuid
import config

def get_bot_name() -> str:
    """Get or generate bot name"""
    try:
        if config.BOT_NAME_FILE.exists():
            return config.BOT_NAME_FILE.read_text().strip()
        else:
            # Use default
            config.BOT_NAME_FILE.write_text(config.DEFAULT_BOT_NAME)
            return config.DEFAULT_BOT_NAME
    except Exception as e:
        print(f"[WARNING]  Error reading bot name: {e}")
        return config.DEFAULT_BOT_NAME

def set_bot_name(name: str) -> bool:
    """Set bot name"""
    try:
        config.BOT_NAME_FILE.write_text(name.strip())
        return True
    except Exception as e:
        print(f"[ERROR] Error saving bot name: {e}")
        return False

def get_instance_name() -> str:
    """Get or generate unique instance name"""
    try:
        if config.INSTANCE_NAME_FILE.exists():
            return config.INSTANCE_NAME_FILE.read_text().strip()
        else:
            # Generate unique instance name
            bot_name = get_bot_name()
            instance_name = f"{bot_name}_{uuid.uuid4().hex[:6]}"
            config.INSTANCE_NAME_FILE.write_text(instance_name)
            return instance_name
    except Exception as e:
        print(f"[WARNING]  Error with instance name: {e}")
        return f"{config.DEFAULT_BOT_NAME}_{random.randint(1000, 9999)}"

def get_random_joke() -> str:
    """Get a random joke"""
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why don't eggs tell jokes? They'd crack up!",
        "What did the ocean say to the beach? Nothing, it just waved!",
    ]
    return random.choice(jokes)

def get_random_fact() -> str:
    """Get a random fact"""
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old!",
        "Octopuses have three hearts and blue blood.",
        "Bananas are berries, but strawberries aren't.",
        "A group of flamingos is called a 'flamboyance'.",
        "The shortest war in history was between Britain and Zanzibar in 1896. It lasted 38 minutes.",
    ]
    return random.choice(facts)
