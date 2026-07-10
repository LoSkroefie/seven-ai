# Clawdbot Integration for Seven

Seven now has full integration with Clawdbot, giving her access to advanced skills and capabilities through voice commands.

## What This Integration Does

Seven can now:
- **Automatically detect** when a task needs Clawdbot's advanced features
- **Route complex tasks** to Clawdbot gateway for processing
- **Execute Clawdbot CLI commands** directly
- **Access all Clawdbot skills** (GitHub, WhatsApp, file ops, etc.)
- **Respond via voice** with results from Clawdbot

## Architecture

```
You (Voice) → Seven (Voice Recognition) → Detect Intent
                                             ↓
                                    [Clawdbot Task?]
                                        ↙        ↘
                                   Yes             No
                                    ↓               ↓
                        Clawdbot Gateway      Seven's Ollama
                        (ws://127.0.0.1:18789)     ↓
                                    ↓           Local LLM
                              Clawdbot Skills      ↓
                              (50+ tools)      Response
                                    ↓               ↓
                                Response ←─────────┘
                                    ↓
                        Seven speaks result back to you
```

## Setup

### 1. Install Dependencies

```bash
cd C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot
pip install websockets
```

### 2. Ensure Clawdbot Gateway is Running

Before starting Seven, make sure Clawdbot gateway is active:

```powershell
# In a separate terminal
cd C:\Users\USER-PC\Desktop\clawd
.\clawdbot-local.cmd gateway --port 18789
```

You should see:
```
[gateway] listening on ws://127.0.0.1:18789
[whatsapp] Listening for personal WhatsApp inbound messages.
```

### 3. Start Seven

```bash
cd C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot
python main_with_gui_and_tray.py
```

Seven will automatically initialize Clawdbot connection at startup.

## Usage Examples

### Voice Commands That Use Clawdbot

Seven automatically detects these types of requests and routes them to Clawdbot:

**WhatsApp & Messaging:**
- "Send a WhatsApp message"
- "Check my WhatsApp messages"

**GitHub & Code:**
- "Search my GitHub repositories"
- "Create a GitHub issue"
- "Analyze this codebase"

**File Operations:**
- "Search all my files for invoice.pdf"
- "Organize my downloads folder"

**Advanced Tasks:**
- "Deploy this project"
- "Run complex task: [description]"

**Notion & Productivity:**
- "Create a Notion page"
- "Update my Notion database"

**Slack:**
- "Send a Slack message"
- "Check Slack notifications"

### Manual Clawdbot Invocation

You can also explicitly ask Seven to use Clawdbot:

- "Use Clawdbot to check my system status"
- "Ask Clawdbot what skills are available"

## Configuration

Edit `config.py` to customize:

```python
# Clawdbot Integration
ENABLE_CLAWDBOT = True  # Enable/disable integration
CLAWDBOT_GATEWAY_URL = "ws://127.0.0.1:18789"  # Gateway URL
CLAWDBOT_TIMEOUT = 30  # Response timeout in seconds
CLAWDBOT_AUTO_DETECT = True  # Auto-detect Clawdbot tasks
```

### Disable Auto-Detection

If you want Seven to only use Clawdbot when explicitly asked:

```python
CLAWDBOT_AUTO_DETECT = False
```

Then say: "Use Clawdbot to [task]" or "Ask Clawdbot [question]"

## Testing the Integration

### Quick Test

1. Start Clawdbot gateway
2. Start Seven
3. Say to Seven: "What Clawdbot skills are available?"

Seven should query Clawdbot and speak the list of skills.

### Advanced Test

1. Make sure WhatsApp is connected to Clawdbot
2. Say to Seven: "Check my WhatsApp messages"
3. Seven will route this to Clawdbot, get the result, and speak it back

## Troubleshooting

### "Clawdbot gateway not accessible"

**Problem:** Seven can't connect to Clawdbot gateway

**Solutions:**
1. Check gateway is running: `clawdbot doctor`
2. Verify port 18789 is not blocked
3. Check gateway URL in `config.py` is correct
4. Restart gateway: `clawdbot gateway --port 18789`

### "Tried to process through Clawdbot but didn't get response"

**Problem:** Gateway connected but no response

**Solutions:**
1. Check gateway logs for errors
2. Increase `CLAWDBOT_TIMEOUT` in config.py
3. Test gateway directly: `clawdbot run "test command"`

### "Clawdbot not initializing"

**Problem:** Seven starts but Clawdbot isn't loaded

**Solutions:**
1. Check `ENABLE_CLAWDBOT = True` in config.py
2. Verify websockets installed: `pip install websockets`
3. Check Seven's log file: `~/.chatbot/bot.log`

## Technical Details

### Files Added

- `integrations/clawdbot.py` - Main integration module
- `CLAWDBOT_INTEGRATION.md` - This documentation

### Files Modified

- `config.py` - Added Clawdbot configuration options
- `core/enhanced_bot.py` - Added Clawdbot client and intent detection
- `requirements.txt` - Added websockets dependency

### Intent Detection

Seven uses keyword detection to route tasks to Clawdbot:

```python
clawdbot_keywords = [
    "whatsapp", "send message", "check messages",
    "github", "git", "repository",
    "complex task", "advanced task",
    "code review", "analyze code",
    "deploy", "deployment",
    "search codebase", "find in code",
    "notion", "slack",
    "file system", "organize files",
    "run command", "execute",
]
```

You can modify this list in `integrations/clawdbot.py`.

## Integration Benefits

### Before Integration

Seven could:
- ✅ Listen to voice
- ✅ Local Ollama responses
- ✅ Basic system commands
- ✅ Calendar, notes, tasks
- ❌ No WhatsApp control
- ❌ No GitHub operations
- ❌ Limited file operations
- ❌ No deployment tools

### After Integration

Seven can now:
- ✅ Everything from before
- ✅ **Control WhatsApp** (read, send, manage)
- ✅ **GitHub operations** (repos, issues, PRs)
- ✅ **Advanced file operations** (semantic search, organization)
- ✅ **Deploy applications**
- ✅ **50+ Clawdbot skills**
- ✅ **Unified voice interface** for everything

## Voice → WhatsApp Example Flow

1. **You say:** "Send a WhatsApp message to John saying I'll be late"
2. **Seven hears:** Converts speech to text
3. **Seven detects:** "whatsapp" keyword → route to Clawdbot
4. **Seven sends:** Message to Clawdbot gateway (ws://127.0.0.1:18789)
5. **Clawdbot processes:** Uses WhatsApp channel, sends message
6. **Clawdbot responds:** "Message sent to John"
7. **Seven receives:** Response from gateway
8. **Seven speaks:** "Message sent to John"
9. **You hear:** Confirmation via voice

## Future Enhancements

Potential improvements:
- Stream responses from Clawdbot for real-time feedback
- Add more intent keywords for better routing
- Visual feedback in Seven's GUI when using Clawdbot
- Clawdbot skill suggestions based on context
- Fallback to Seven's Ollama if Clawdbot is unavailable

## Support

If you encounter issues:
1. Check `~/.chatbot/bot.log` for Seven's logs
2. Check `\tmp\clawdbot\clawdbot-[date].log` for Clawdbot logs
3. Run `clawdbot doctor` to check Clawdbot health
4. Verify both Seven and Clawdbot gateway are running

---

**You now have a fully voice-controlled AI assistant with enterprise-level capabilities!** 🎙️💫🦞
