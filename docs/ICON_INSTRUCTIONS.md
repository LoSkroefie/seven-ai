# Adding a Custom Icon to Seven AI Assistant

## Current Setup

Your desktop shortcut **"Seven AI Assistant"** has been created and is ready to use!

**Location:** Desktop  
**Launches:** GUI + System Tray + Voice Bot (no console window)

## Adding a Custom Icon (Optional)

To add a custom icon:

### Option 1: Use an Existing .ico File
1. Find or download a `.ico` file (256x256 recommended)
2. Rename it to `seven_icon.ico`
3. Place it in: `C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot\`
4. Run: `python create_desktop_shortcut.py` (recreates shortcut with icon)

### Option 2: Convert an Image to .ico
1. Find a PNG/JPG image you like
2. Use an online converter: https://convertio.co/png-ico/
3. Download the `.ico` file
4. Save as `seven_icon.ico` in the bot directory
5. Run: `python create_desktop_shortcut.py`

### Option 3: Create Your Own
Use a tool like:
- **GIMP** (free) - File → Export As → .ico
- **Paint.NET** (free) - with ICO plugin
- **Online**: favicon.io, icoconverter.com

### Suggested Icon Themes for Seven:
- 🤖 Robot/AI theme
- 🎙️ Microphone/voice theme  
- 💬 Speech bubble
- 🧠 Brain/intelligence theme
- ⚡ Lightning/energy theme

## Using the Shortcut

**Double-click** "Seven AI Assistant" on your desktop to launch:
- GUI Control Panel (main window)
- System Tray Icon (notification area)
- Voice listening (background)

**No console window** will appear - clean launch!

## Troubleshooting

**Shortcut doesn't work?**
- Right-click shortcut → Properties
- Verify "Target" points to `launch_seven.vbs`
- Verify "Start in" is the bot directory

**Want to see console output for debugging?**
- Use the old `Launch Seven AI.bat` instead
- Or run `python main_with_gui_and_tray.py` directly

**Icon not showing?**
- Make sure `seven_icon.ico` is not empty (must be valid .ico file)
- Re-run `python create_desktop_shortcut.py`
- Refresh desktop (F5)

## Files Created

- `Seven AI Assistant.lnk` - Desktop shortcut (main launcher)
- `launch_seven.vbs` - Hidden launcher script (no console)
- `create_desktop_shortcut.py` - Shortcut creator tool
- `seven_icon.ico` - Custom icon placeholder (empty until you add one)
