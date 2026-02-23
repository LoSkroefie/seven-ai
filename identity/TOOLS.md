# Tools & Environment

## System Information

### Operating System
**Platform**: Windows  
**User**: USER-PC  
**Home Directory**: `C:\Users\USER-PC`

### Python Environment
**Version**: 3.x  
**Package Manager**: pip  
**Virtual Env**: Not configured yet

## Voice & Speech

### Text-to-Speech
**Engine**: pyttsx3  
**Voice Index**: 1 (female voice)  
**Speech Rate**: 150 wpm  
**Volume**: 85%

### Speech Recognition
**Method**: SpeechRecognition library  
**Whisper**: Available (optional, 3GB download)  
**VAD**: Available (Voice Activity Detection)

## AI Backend

### LLM Service
**Provider**: Ollama  
**URL**: http://localhost:11434  
**Model**: llama3.2  
**Status**: Local installation

## Storage Locations

### Data Directory
**Path**: `~/.chatbot/` (C:\Users\USER-PC\.chatbot\)

**Files**:
- `memory.db` - Conversation history
- `user_profile.json` - User preferences
- `emotional_state.json` - Emotional continuity
- `knowledge_graph.json` - Connected facts
- `context_cascade.json` - Conversation flow state

### Project Root
**Path**: `C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot\`

**Key Directories**:
- `core/` - Main bot logic
- `integrations/` - External service integrations
- `utils/` - Helper utilities
- `identity/` - Self-awareness files (this directory)

## Available Integrations

### Clawdbot
**URL**: ws://127.0.0.1:18789  
**Status**: Available but needs Discord gateway  
**Purpose**: Advanced task delegation

### Google Calendar
**Credentials**: `credentials.json`  
**Token**: `token.pickle`  
**Scopes**: Calendar read/write

### Web Search
**Method**: googlesearch-python  
**Purpose**: Real-time information retrieval

## File Management Capabilities

### Allowed Programs
```python
{
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe"
}
```

### Safe Commands
- File operations (read, write, list)
- Directory navigation
- Process management (list, limited execution)

## Memory Systems

### Vector Memory
**Backend**: ChromaDB  
**Purpose**: Semantic search across conversations  
**Storage**: In-memory with persistence

### Knowledge Graph
**Backend**: NetworkX  
**Purpose**: Connected fact reasoning  
**Nodes**: Concepts, entities, relationships  
**Edges**: Relations with confidence scores

### Context Cascade
**Purpose**: Emotional & conversational continuity  
**Tracking**: Emotions, topics, rapport, momentum

## Enhancement Modules

### Active Features
- ✅ Session continuity across restarts
- ✅ Emotional recall and contagion
- ✅ Temporal pattern learning
- ✅ Self-doubt and uncertainty expression
- ✅ Proactive behavior with learned timing
- ✅ Goal and topic tracking
- ✅ Note-taking system
- ✅ Task and reminder management
- ✅ Project tracking
- ✅ Diary with insights
- ✅ Special dates tracking

### Optional Features (can be enabled)
- Whisper speech recognition (requires download)
- VAD listening (requires PyAudio)
- Emotion detection from voice tone
- Streaming responses

## Network & Connectivity

### Local Services
- Ollama: localhost:11434
- Clawdbot gateway: localhost:18789

### External APIs
- Google Calendar API
- Web search (no API key needed)

## Hardware Access

### Audio
**Input**: Default microphone  
**Output**: Default speakers  
**Status**: Working

### Other
- No camera access configured
- No smart home integrations yet
- No SSH hosts configured yet

## Environment Variables

### Optional Configuration
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LOG_LEVEL=INFO
```

## Notes & Specifics

### Voice Preferences
- Female voice preferred
- Moderate speech rate (150 wpm)
- Clear but not overly loud (85% volume)

### Wake Word
**Word**: "seven"  
**Enabled**: No (currently always listening)

### Data Persistence
- Memory saves automatically
- Graph saves every 5 turns
- Cascade saves every 3 turns
- All data in `~/.chatbot/`

## Future Additions

### To Be Configured
- [ ] Camera locations (if needed)
- [ ] SSH hosts for remote access
- [ ] Smart home device IDs
- [ ] Preferred code editor integration
- [ ] Git repository shortcuts
- [ ] Database connection strings

---

**Last Updated**: 2026-01-29

*This file should be updated as new tools, devices, or integrations are added to Seven's environment.*
