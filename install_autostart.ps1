# Install Seven Real daemon to start with Windows (current user).
# Uses Startup folder shortcut → run_seven_daemon.bat
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $repo "run_seven_daemon.bat"
$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "Seven Real Daemon.lnk"

if (-not (Test-Path $bat)) {
    Write-Error "Missing $bat"
}

$w = New-Object -ComObject WScript.Shell
$s = $w.CreateShortcut($lnkPath)
$s.TargetPath = $bat
$s.WorkingDirectory = $repo
$s.WindowStyle = 7  # minimized
$s.Description = "Seven Real always-on daemon"
$s.Save()

Write-Host "Installed autostart: $lnkPath"
Write-Host "Target: $bat"
Write-Host "To remove: delete the shortcut from your Startup folder."
Write-Host "Manual: python -m seven --daemon"
