# Seven AI v2.0 - Distribution Package Creator (Fixed)

$OutputPath = ".\Seven-AI-v2.0-Complete.zip"

Write-Host "Creating Seven AI v2.0 distribution package..." -ForegroundColor Cyan

$SourceDir = Get-Location
$TempDir = Join-Path $env:TEMP "Seven-Build"
$PackageDir = Join-Path $TempDir "Seven-AI-v2.0-Complete"

if (Test-Path $TempDir) {
    Remove-Item -Path $TempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Include these items
$Include = @(
    "config.py", "setup_wizard.py", "install.bat",
    "main_with_gui_and_tray.py", "main_with_gui.py", "main.py",
    "requirements.txt", "requirements-stable.txt",
    "README.md", "CHANGELOG.md", "QUICK_START_GUIDE.md",
    "create_shortcuts.ps1", "uninstall.bat", "seven_icon.ico",
    "core", "gui", "integrations", "utils", "identity"
)

Write-Host "Copying files..." -ForegroundColor Green

foreach ($item in $Include) {
    $src = Join-Path $SourceDir $item
    $dst = Join-Path $PackageDir $item
    
    if (Test-Path $src) {
        if (Test-Path $src -PathType Container) {
            robocopy $src $dst /E /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
        } else {
            Copy-Item $src $dst -Force
        }
    }
}

# Remove test files and dev docs
Get-ChildItem -Path $PackageDir -Recurse -Include "test_*.py","*_test.py","__pycache__","*.pyc" | Remove-Item -Recurse -Force
Get-ChildItem -Path "$PackageDir\core\v2" -Filter "*.md" | Remove-Item -Force

Write-Host "Creating zip archive..." -ForegroundColor Green

if (Test-Path $OutputPath) {
    Remove-Item $OutputPath -Force
}

Compress-Archive -Path "$TempDir\*" -DestinationPath $OutputPath -CompressionLevel Optimal

$size = [math]::Round((Get-Item $OutputPath).Length / 1MB, 2)

Write-Host ""
Write-Host "SUCCESS! Package created: $OutputPath ($size MB)" -ForegroundColor Green

Remove-Item -Path $TempDir -Recurse -Force
