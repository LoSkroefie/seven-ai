# Create a Desktop shortcut to Seven Real GUI
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $repo "run_seven_gui.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Seven Real.lnk"

$w = New-Object -ComObject WScript.Shell
$s = $w.CreateShortcut($lnkPath)
$s.TargetPath = $bat
$s.WorkingDirectory = $repo
$s.WindowStyle = 1
$s.Description = "Seven Real — local autonomous agent (GUI)"
$s.Save()
Write-Host "Created: $lnkPath"
Write-Host "Target:  $bat"
