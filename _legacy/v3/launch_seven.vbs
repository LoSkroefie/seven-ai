' Launch Seven AI Assistant (no console window)
Set objShell = CreateObject("Wscript.Shell")
botPath = "C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot"
objShell.CurrentDirectory = botPath
objShell.Run "python main_with_gui_and_tray.py", 0, False
