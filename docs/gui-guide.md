# GUI Guide

Seven includes a full desktop GUI built with Tkinter, featuring a chat interface, emotion dashboard, and system status panel.

---

## Launching the GUI

```bash
# Standard GUI
python main_with_gui.py

# GUI with system tray icon
python main_with_gui_and_tray.py
```

## Interface Overview

### Chat Panel
- Message input field at the bottom
- Conversation history with timestamps
- Seven's responses styled differently from user input
- Typing indicator when Seven is processing

### Emotion Dashboard
- Real-time display of Seven's current emotional state
- Color-coded emotion bars showing intensity (0.0 – 1.0)
- Primary emotions prominently displayed
- Complex emotions shown when active

### System Status
- All 19 sentience systems with active/idle indicators
- Ollama connection status
- Voice recognition status (listening/processing)
- Vision feed status (if camera connected)
- Memory usage and session duration

### System Tray
When using `main_with_gui_and_tray.py`:
- Minimizes to system tray
- Status icon changes based on Seven's state
- Right-click menu for quick actions
- Double-click to restore window

## GUI Modules

| Module | Purpose |
|--------|---------|
| `gui/phase5_gui.py` | Full sentience dashboard (81KB) |
| `gui/bot_gui.py` | Core chat interface |
| `gui/bot_gui_notes_tasks.py` | Notes and task management panel |
| `gui/system_tray.py` | System tray integration |

## Customization

The GUI uses Tkinter's theming system. Colors and layout are defined within the GUI modules. To modify the appearance, edit the style constants at the top of `gui/phase5_gui.py`.
