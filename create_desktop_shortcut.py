# Create desktop shortcut for Seven AI Assistant
import os
import sys
from pathlib import Path

def create_shortcut():
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        print("Installing required packages...")
        os.system("pip install pywin32 winshell")
        import winshell
        from win32com.client import Dispatch
    
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "Seven AI Assistant.lnk")
    
    bot_dir = Path(__file__).parent.absolute()
    vbs_launcher = bot_dir / "launch_seven.vbs"
    icon_path = bot_dir / "seven_icon.ico"
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = str(vbs_launcher)
    shortcut.WorkingDirectory = str(bot_dir)
    shortcut.Description = "Seven AI Assistant - Enhanced Voice Bot with GUI"
    
    if icon_path.exists() and icon_path.stat().st_size > 0:
        shortcut.IconLocation = str(icon_path)
    
    shortcut.save()
    
    print("SUCCESS: Desktop shortcut created")
    print("Location:", shortcut_path)
    print("Target:", vbs_launcher)
    print("\nDouble-click 'Seven AI Assistant' on your desktop to launch!")

if __name__ == "__main__":
    try:
        create_shortcut()
    except Exception as e:
        print("ERROR:", str(e))
        sys.exit(1)
