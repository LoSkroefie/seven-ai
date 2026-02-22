# Seven AI - Create Desktop & Start Menu Shortcuts
$installDir = "$env:LOCALAPPDATA\SevenAI"
$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"

# Desktop shortcut — "Seven AI"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("$desktop\Seven AI.lnk")
$sc.TargetPath = "$installDir\start.bat"
$sc.WorkingDirectory = $installDir
$sc.Description = "Launch Seven AI"
$sc.WindowStyle = 7  # Minimized
$sc.Save()

# Start Menu shortcut
if (!(Test-Path "$startMenu\Seven AI")) { New-Item -ItemType Directory -Path "$startMenu\Seven AI" | Out-Null }
$sc2 = $ws.CreateShortcut("$startMenu\Seven AI\Seven AI.lnk")
$sc2.TargetPath = "$installDir\start.bat"
$sc2.WorkingDirectory = $installDir
$sc2.Description = "Launch Seven AI"
$sc2.WindowStyle = 7
$sc2.Save()

Write-Host "[OK] Desktop shortcut created: Seven AI"
Write-Host "[OK] Start Menu shortcut created: Seven AI"
