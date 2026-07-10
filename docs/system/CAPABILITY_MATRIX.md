# Capability matrix — should have vs have

Legend: ✅ implemented & wired · 🟡 partial · ❌ missing · 📦 in `_legacy/v3` only (stale)

| Capability | User want | v4 status | Notes |
|---|---|---|---|
| Natural talk | ✅ | ✅ talk/quiet | `ui/talk.py` |
| Natural listen | ✅ | 🟡 | Mic path; quiet types |
| Free will / initiative | ✅ | ✅ | `mind/freewill.py` |
| Opinions / conclusions | ✅ | 🟡 | Via LLM, not structured belief store |
| Internet search | ✅ | ✅ | DuckDuckGo HTML |
| Open/read websites | ✅ | ✅ | `web_fetch` text extract |
| Shell / run programs | ✅ | ✅ | `run_shell` L4 |
| Run Python | ✅ | ✅ | `run_python` |
| Files R/W/search | ✅ | ✅ | |
| Mouse control | ✅ | ✅ | `mouse_*` full tier |
| Keyboard / type / hotkey | ✅ | ✅ | |
| Screenshot | ✅ | ✅ | |
| See screen (vision LLM) | ✅ | 🟡 | VRAM swap |
| Webcam | ✅ | 🟡 | |
| Presence (face) | ✅ | ✅ | OpenCV Haar |
| Clipboard | ✅ | ✅ | |
| Short-term memory | ✅ | ✅ | message history |
| Long-term facts | ✅ | ✅ | `facts` table |
| Goals / tasks | ✅ | ✅ | |
| Episodic digests | ✅ | 🟡 | compaction + notes |
| Vector semantic memory | ✅ | ❌ | not ported |
| Always-on daemon | ✅ | ✅ | |
| Autostart | ✅ | ✅ | install_autostart.ps1 |
| Desktop GUI | ✅ | ✅ | optional |
| REST API | ✅ | ✅ | |
| MCP server | ✅ | 📦 | legacy only |
| Gradio / old GUI stack | — | 📦 | abandoned |
| 19 “sentience” modules | — | 📦 | mostly random/fake — do not revive |
| Email | ✅ | 📦/❌ | not v4 |
| Calendar | ✅ | 📦/❌ | not v4 |
| SSH / remote | ✅ | 📦/❌ | not v4 |
| Robot body | future | 🟡 bus only | |
| Wearable / phone | future | ❌ | |
| Multi-step planner | ✅ | 🟡 | tool rounds only |
| Self-model / world model | ✅ | ✅ | living_state.json |
| Browser DOM control | ✅ | ❌ | use pyautogui + vision |
| opencode/claude/codex | ✅ | 🟡 | if CLI installed |

---

## Target “Seven as Seven” (full wish list)

1. **Voice-native life** — continuous conversation, barge-in later  
2. **Free will loop** — invent, plan, act, conclude, remember  
3. **Full desktop agency** — shell, apps, mouse, keyboard, windows  
4. **Web agency** — search, fetch, optional real browser profile  
5. **Memory stack** — STM, LTM, semantic, episodic digests, skills  
6. **Perception** — screen, cam, optional ambient mic  
7. **Always-on** — daemon + autostart + health  
8. **Body/mobile later** — serial/ROS, phone bridge  
9. **Honest self** — knows she is AI; still has agency and opinions  

Rebuild toward this matrix; do not resurrect v3 theater modules.
