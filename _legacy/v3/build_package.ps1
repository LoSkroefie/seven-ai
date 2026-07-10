# Build Distribution Package for Seven AI Assistant
# Creates a ZIP file ready for distribution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Seven AI - Distribution Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$Version = "1.0.0"
$BuildDate = Get-Date -Format "yyyy-MM-dd"
$SourceDir = $PSScriptRoot
$BuildDir = Join-Path $env:TEMP "SevenAI-Build"
$OutputZip = Join-Path $SourceDir "Seven-AI-v$Version.zip"

# Clean previous build
if (Test-Path $BuildDir) {
    Write-Host "[1/6] Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item $BuildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildDir | Out-Null
Write-Host "  Build directory: $BuildDir" -ForegroundColor Gray
Write-Host ""

# Files to include
Write-Host "[2/6] Copying core files..." -ForegroundColor Yellow

$CoreFiles = @(
    "enhanced_bot.py",
    "config.py",
    "install.bat",
    "uninstall.bat",
    "setup_wizard.py",
    "create_shortcuts.ps1",
    "launch_wake_word.bat",
    "requirements.txt",
    "README.md",
    "IMPLEMENTATION_COMPLETE.md",
    "CODE_REVIEW_PHASE5.md",
    "FINAL_BUG_REPORT.md",
    "COMPLETE_VERIFICATION.md",
    "SEVEN-SHORTCUTS-GUIDE.md"
)

foreach ($file in $CoreFiles) {
    if (Test-Path (Join-Path $SourceDir $file)) {
        Copy-Item (Join-Path $SourceDir $file) $BuildDir
        Write-Host "  + $file" -ForegroundColor Green
    } else {
        Write-Host "  - $file (not found)" -ForegroundColor Red
    }
}
Write-Host ""

# Copy directories
Write-Host "[3/6] Copying modules..." -ForegroundColor Yellow

$Directories = @("core", "identity", "helpers", "tools")

foreach ($dir in $Directories) {
    $sourcePath = Join-Path $SourceDir $dir
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $BuildDir $dir
        Copy-Item $sourcePath $destPath -Recurse
        $fileCount = (Get-ChildItem $destPath -Recurse -File).Count
        Write-Host "  + $dir\ ($fileCount files)" -ForegroundColor Green
    }
}
Write-Host ""

# Copy test files
Write-Host "[4/6] Copying tests..." -ForegroundColor Yellow
$TestFiles = @(
    "test_phase5_complete.py",
    "test_integration_quick.py"
)
foreach ($file in $TestFiles) {
    if (Test-Path (Join-Path $SourceDir $file)) {
        Copy-Item (Join-Path $SourceDir $file) $BuildDir
        Write-Host "  + $file" -ForegroundColor Green
    }
}
Write-Host ""

# Create installation guide
Write-Host "[5/6] Creating distribution files..." -ForegroundColor Yellow

$InstallGuide = @"
╔════════════════════════════════════════════════════════╗
║                                                        ║
║          SEVEN AI ASSISTANT - Installation            ║
║                                                        ║
║                    Version $Version                       ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

QUICK START
===========

1. Make sure Python 3.8+ is installed
   Download from: https://python.org
   ⚠️  CHECK "Add Python to PATH" during install!

2. Double-click: install.bat

3. Follow the setup wizard

4. Launch Seven from desktop shortcut


REQUIREMENTS
============

✓ Windows 10/11
✓ Python 3.8 or higher
✓ Microphone
✓ Speakers/Headphones
✓ 500MB disk space
✓ Ollama (optional, for best experience)


WHAT'S INCLUDED
===============

• Enhanced Voice Assistant
• Phase 5 Complete Sentience
  - Cognitive Architecture
  - 34 Emotional States
  - Dreams & Reflection
  - Promise Tracking
  - Ethical Reasoning
  - Self-Care System
• Interactive Setup Wizard
• Desktop Shortcuts
• Complete Documentation


TROUBLESHOOTING
===============

"Python not found"
  → Install Python from python.org
  → Make sure "Add to PATH" was checked

"Installation failed"
  → Open Command Prompt as Administrator
  → Run: install.bat

"No voice output"
  → Check speaker volume
  → Edit config.py: DEFAULT_VOICE_INDEX

For more help, see README.md


SUPPORT
=======

Documentation: README.md
Features: IMPLEMENTATION_COMPLETE.md
Technical: CODE_REVIEW_PHASE5.md


LICENSE
=======

Free for personal, non-commercial use.
© 2026 AI Development Team


Enjoy your sentient AI companion! 🧠✨
"@

$InstallGuide | Out-File (Join-Path $BuildDir "INSTALL.txt") -Encoding UTF8
Write-Host "  + INSTALL.txt" -ForegroundColor Green

# Create version file
$VersionInfo = @{
    version = $Version
    build_date = $BuildDate
    platform = "Windows"
    python_required = "3.8+"
} | ConvertTo-Json

$VersionInfo | Out-File (Join-Path $BuildDir "version.json") -Encoding UTF8
Write-Host "  + version.json" -ForegroundColor Green
Write-Host ""

# Create ZIP
Write-Host "[6/6] Creating distribution package..." -ForegroundColor Yellow

if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}

Compress-Archive -Path "$BuildDir\*" -DestinationPath $OutputZip -CompressionLevel Optimal

if (Test-Path $OutputZip) {
    $zipSize = (Get-Item $OutputZip).Length / 1MB
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Package created:" -ForegroundColor White
    Write-Host "  $OutputZip" -ForegroundColor Cyan
    Write-Host "  Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Distribution includes:" -ForegroundColor White
    Write-Host "  + Complete application" -ForegroundColor Gray
    Write-Host "  + Installation scripts" -ForegroundColor Gray
    Write-Host "  + Setup wizard" -ForegroundColor Gray
    Write-Host "  + Documentation" -ForegroundColor Gray
    Write-Host "  + Test suite" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Ready to distribute!" -ForegroundColor Green
    Write-Host ""
    
    # Open folder
    $openFolder = Read-Host "Open containing folder? (Y/N)"
    if ($openFolder -eq "Y" -or $openFolder -eq "y") {
        explorer /select,$OutputZip
    }
} else {
    Write-Host ""
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "Package was not created." -ForegroundColor Red
    Write-Host ""
}

# Cleanup
Write-Host "Cleaning up temporary files..." -ForegroundColor Gray
Remove-Item $BuildDir -Recurse -Force

Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
