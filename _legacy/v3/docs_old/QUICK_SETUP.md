# Seven AI v3.1 - Quick Setup

## 🚀 Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Ollama Models
```bash
ollama pull llama3.2           # Core reasoning
ollama pull llama3.2-vision    # Vision (screen/webcam)
```

### 3. Start Seven
```bash
cd enhanced-bot

# Interactive mode (GUI + voice)
python main_with_gui_and_tray.py

# Daemon mode (24/7 background)
python seven_daemon.py start

# API server only
python seven_api.py
# Docs: http://127.0.0.1:7777/docs
```

### 4. Test New Features

**Test Context Cascade:**
```
You: "I love Python programming"
[Seven responds]

You: "It's so powerful for data science"
[Seven should maintain context and emotion]

You: "What were we just talking about?"
[Seven should reference Python naturally]
```

**Test Knowledge Graph:**
```
You: "I use Docker for my projects"
[Seven learns this fact]

You: "I'm learning Kubernetes"
[Seven might connect: Docker → containers → Kubernetes]

You: "What do you know about my interests?"
[Seven should mention Docker, Kubernetes, and connections]
```

---

## 🐛 Troubleshooting

### Issue: Import Error for networkx
```
Solution: pip install networkx==3.2
```

### Issue: Seven seems slow
```
Check: Knowledge graph might be large
Solution: Graph is saved every 5 turns (automatic optimization)
```

### Issue: Facts not being learned
```
Check: config.py has ENABLE_KNOWLEDGE_GRAPH = True
Check: Say clear statements like "I love Python" not "python is cool"
```

### Issue: No context continuity
```
Check: config.py has ENABLE_CONTEXT_CASCADE = True
Check: Have at least 3-4 turn conversation to see cascade effect
```

---

## 📊 Verify Features Working

### Knowledge Graph Stats
After 10 conversations:
```python
# In Python console:
from core.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
print(kg.get_stats())
```

Expected output:
```
{
  'total_nodes': 10-30,
  'total_edges': 15-50,
  'learned_facts': 10-40,
  'inferred_facts': 5-15,
  'avg_connections': 1.5-2.5
}
```

### Check Saved Data
```bash
ls ~/.chatbot/
```

Should see:
- `knowledge_graph.json` (NEW)
- `emotional_state.json` (NEW)
- `memory.db`
- `user_profile.json`

---

## ✅ Feature Checklist

Test each feature:

- [ ] Seven remembers conversation context
- [ ] Emotions don't jump randomly
- [ ] Facts are learned from conversation
- [ ] Seven connects related concepts
- [ ] "We keep coming back to..." callbacks appear
- [ ] Knowledge persists across restarts
- [ ] Emotional state persists across restarts

---

## 🎯 Quick Test Script

Run this conversation to test everything:

```
You: "I love Python programming"
Seven: [should respond positively]

You: "I use it for machine learning projects"
Seven: [should connect Python + ML]

You: "But it's really challenging sometimes"
Seven: [should show empathy, maintain emotional context]

You: "I'm also learning React"
Seven: [might say "We keep coming back to learning new technologies"]

[Exit and restart Seven]

You: "What do you remember about Python?"
Seven: [should recall: likes Python, uses for ML, finds challenging]
```

If all these work → ✅ Everything is functioning perfectly!

---

## 📞 Need Help?

All features are documented in:
- `PHASES_1-3_COMPLETE.md` - Full technical details
- `BUG_FIXES_COMPLETE.md` - Bug fixes applied
- `IMPLEMENTATION_COMPLETE.md` - Phase 1-2 details

Check config.py to enable/disable features:
```python
ENABLE_CONTEXT_CASCADE = True   # Context flow
ENABLE_KNOWLEDGE_GRAPH = True   # Knowledge reasoning
```
