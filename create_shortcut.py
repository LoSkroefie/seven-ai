"""
Create desktop shortcut for Enhanced Bot
"""
import os
from pathlib import Path
import subprocess

def create_desktop_shortcut():
    """Create a desktop shortcut for the bot"""
    
    # Get paths
    desktop = Path.home() / "Desktop"
    bot_dir = Path(__file__).parent
    main_script = bot_dir / "main_with_gui.py"
    python_exe = Path(subprocess.run(
        ["where", "python"],
        capture_output=True,
        text=True,
        shell=True
    ).stdout.strip().split('\n')[0])
    
    # PowerShell script to create shortcut
    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\Enhanced Bot.lnk")
$Shortcut.TargetPath = "{python_exe}"
$Shortcut.Arguments = '"{main_script}"'
$Shortcut.WorkingDirectory = "{bot_dir}"
$Shortcut.Description = "Enhanced Voice Assistant Bot with GUI"
$Shortcut.IconLocation = "{python_exe},0"
$Shortcut.Save()
"""
    
    # Execute PowerShell script
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print(f"[OK] Shortcut created on desktop: {desktop}\\Enhanced Bot.lnk")
            print(f"   Target: {main_script}")
            print(f"   Python: {python_exe}")
            print("\nDouble-click 'Enhanced Bot' on your desktop to launch!")
        else:
            print(f"[ERROR] Error creating shortcut: {result.stderr}")
            
    except Exception as e:
        print(f"[ERROR] Failed to create shortcut: {e}")

if __name__ == "__main__":
    create_desktop_shortcut()
