# How to Interrupt the Bot

The bot now has **interrupt functionality enabled**! Here's how to use it:

## Method 1: Voice Commands (NEW!)
Say any of these while the bot is speaking:
- **"STOP"**
- **"SHUT UP"**
- **"BE QUIET"**
- **"QUIET"**
- **"ENOUGH"**
- **"PAUSE"**

The bot will stop speaking immediately when it hears these!

## Method 2: Ctrl+C
Press **Ctrl+C** on your keyboard and the bot stops instantly

## What's Enabled
- `USE_INTERRUPTS = True` in config.py
- Interruptible TTS splits speech into sentences
- Each sentence checks for interrupt signals
- Bot stops mid-speech when interrupted

## How It Works
1. Bot starts speaking a response
2. Speech is split into sentences
3. Between each sentence, bot checks if interrupted
4. If interrupted, remaining speech is cancelled
5. Bot immediately returns to listening

## Current Limitations
- Keyboard interrupts work (Ctrl+C)
- Voice-based interrupts require additional voice detection setup
- Currently interrupts at sentence boundaries (not mid-word)

## Advanced: Voice Interrupts
To enable voice-based interrupts (detect when you start speaking):
1. Install PyAudio: `pip install pyaudio`
2. Set `USE_VAD = True` in config.py
3. Bot will detect when you start speaking and interrupt itself

## Testing
1. Run the bot: `python main_with_gui.py`
2. Ask it a long question: "Tell me everything about Python"
3. While it's speaking, say **"STOP"** or press **Ctrl+C**
4. Bot should stop immediately

## Voice Interrupt Examples
- Bot rambling too long? → Say **"STOP"**
- Bot going off-topic? → Say **"SHUT UP"**
- Need to correct something? → Say **"PAUSE"**
- Bot being too chatty? → Say **"ENOUGH"**

## Notes
- Interrupt handler is thread-safe
- Works with both GUI and console modes
- Preserves conversation context after interruption
