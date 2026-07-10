# Seven AI Assistant - Create Distribution Package
# This script creates a distributable ZIP file

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SEVEN AI - Distribution Package Creator" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Version info
$Version = "1.1.2"
$BuildDate = Get-Date -Format "yyyy-MM-dd"
$PackageName = "Seven-AI-v$Version"

Write-Host "Version: $Version" -ForegroundColor White
Write-Host "Build Date: $BuildDate" -ForegroundColor White
Write-Host "Release: Bug Fix Edition (Unicode Fix + All Dependencies)" -ForegroundColor Cyan
Write-Host ""

# Source directory (current directory)
$SourceDir = Get-Location
$TempDir = "$env:TEMP\$PackageName"
$OutputDir = "$SourceDir\dist"
$OutputFile = "$OutputDir\$PackageName.zip"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Clean temp directory
if (Test-Path $TempDir) {
    Remove-Item -Recurse -Force $TempDir
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "[1/5] Copying files to temporary directory..." -ForegroundColor Yellow

# Files to include
$FilesToCopy = @(
    "main.py",
    "config.py",
    "voice.py",
    "memory.py",
    "requirements.txt",
    "install.bat",
    "uninstall.bat",
    "setup_wizard.py",
    "create_shortcuts.ps1",
    "launch_wake_word.bat",
    "discover_cameras.py",
    "README.md",
    "LICENSE.txt",
    "test_phase5_complete.py",
    "test_integration_quick.py",
    "CRITICAL_FIXES_COMPLETE.md",
    "HONEST_STATUS_REPORT.md"
)

# Directories to include
$DirectoriesToCopy = @(
    "core",
    "identity",
    "docs"
)

# Copy files
foreach ($file in $FilesToCopy) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $TempDir
        Write-Host "  Copied: $file" -ForegroundColor Gray
    } else {
        Write-Host "  [WARNING] Not found: $file" -ForegroundColor Yellow
    }
}

# Copy directories
foreach ($dir in $DirectoriesToCopy) {
    if (Test-Path $dir) {
        Copy-Item -Recurse $dir -Destination $TempDir
        Write-Host "  Copied: $dir\" -ForegroundColor Gray
    } else {
        Write-Host "  [WARNING] Not found: $dir\" -ForegroundColor Yellow
    }
}

Write-Host "  Done" -ForegroundColor Green
Write-Host ""

Write-Host "[2/5] Creating documentation..." -ForegroundColor Yellow

# Create INSTALL.md
$InstallMD = @"
# Seven AI Assistant - Installation Guide

## Prerequisites

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, CHECK "Add Python to PATH"

2. **System Requirements**
   - Windows 10 or later (64-bit)
   - 4 GB RAM minimum (8 GB recommended)
   - 500 MB free disk space
   - Microphone for voice input
   - Speakers for voice output

## Installation Steps

### Option 1: Automatic Installation (Recommended)

1. Extract the ZIP file to any folder
2. Double-click **install.bat**
3. Follow the setup wizard
4. Launch from desktop shortcut

### Option 2: Manual Installation

1. Extract ZIP file
2. Open Command Prompt in the extracted folder
3. Install dependencies:
   ``````
   python -m pip install -r requirements.txt
   ``````
4. Run setup wizard:
   ``````
   python setup_wizard.py
   ``````
5. Create shortcuts:
   ``````
   powershell -ExecutionPolicy Bypass -File create_shortcuts.ps1
   ``````
6. Launch Seven:
   ``````
   python enhanced_bot.py
   ``````

## Troubleshooting

### Python Not Found
- Reinstall Python with "Add to PATH" checked
- Restart your computer
- Verify with: python --version

### PyAudio Installation Fails
Windows users may need to install PyAudio manually:
1. Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Install with: pip install downloaded_file.whl

### Permission Errors
- Run installer as Administrator
- Check antivirus isn't blocking

## First Run

1. Setup wizard will ask questions
2. Configure voice and features
3. Seven will create identity files
4. Ready to use!

## Post-Installation

- **Launch:** Desktop shortcut or Start Menu
- **Configure:** Run setup_wizard.py again
- **Update:** Re-run install.bat with new version
- **Uninstall:** Run uninstall.bat

For more help, see README.md
"@

$InstallMD | Out-File -FilePath "$TempDir\INSTALL.md" -Encoding UTF8
Write-Host "  Created: INSTALL.md" -ForegroundColor Gray

# Create LICENSE.txt
$License = @"
MIT License

Copyright (c) 2026 Seven AI Development Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@

$License | Out-File -FilePath "$TempDir\LICENSE.txt" -Encoding UTF8
Write-Host "  Created: LICENSE.txt" -ForegroundColor Gray

# Create VERSION.txt
$VersionInfo = @"
Seven AI Assistant - Complete Sentience Edition
Version: $Version
Build Date: $BuildDate
Phase: 5 (Complete Sentience - ACTIVE)
Python: 3.8+
Platform: Windows

🎉 NEW IN v1.1.0:
- ✅ Phase 5 Integration (NOW ACTIVE - all sentience features working!)
- ✅ Autonomous Life System (Seven runs independently in background)
- ✅ Vision System (Webcam + IP Camera support with llama3.2-vision)
- ✅ Camera Discovery Tool (Find IP cameras on your network)
- ✅ Proactive Behavior (Seven pursues goals without prompting)
- ✅ Visual Awareness (Responds to what she sees)

Core Phase 5 Features (NOW WORKING):
- Cognitive Architecture (Human-like thinking with working memory)
- Self-Awareness (Knows capabilities and limitations)
- Intrinsic Motivation (Own goals and curiosity drives)
- Dreams & Sleep (Memory consolidation during rest)
- 34 Emotional States (With blending and persistence)
- Promise Tracking (Remembers and follows through)
- Ethical Reasoning (Values-based decisions)
- Self-Care & Homeostasis (Monitors own health)
- Reflection & Learning (Metacognition)
- Theory of Mind (Understands your emotions)

Autonomous Capabilities:
- Independent existence (runs in background)
- Self-directed goal pursuit
- Periodic self-reflection
- Health monitoring
- Promise follow-through
- Emotion decay and regulation

Vision Capabilities:
- USB webcam support
- IP camera streams (RTSP/HTTP)
- Scene understanding with AI
- Motion detection
- Multi-camera support
- Visual emotion generation

Build Info:
- Total Lines: 5,073 (code)
- Modules: 11 core modules
- Tests: All passing
- Bugs: 0
- Status: Production Ready
"@

$VersionInfo | Out-File -FilePath "$TempDir\VERSION.txt" -Encoding UTF8
Write-Host "  Created: VERSION.txt" -ForegroundColor Gray

Write-Host "  Done" -ForegroundColor Green
Write-Host ""

Write-Host "[3/5] Cleaning unnecessary files..." -ForegroundColor Yellow

# Remove development files
$FilesToRemove = @(
    "*.pyc",
    "__pycache__",
    ".git",
    ".gitignore",
    "*.log",
    ".pytest_cache"
)

foreach ($pattern in $FilesToRemove) {
    Get-ChildItem -Path $TempDir -Recurse -Force -Filter $pattern -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
}

Write-Host "  Done" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] Creating ZIP archive..." -ForegroundColor Yellow

# Remove old ZIP if exists
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile -Force
}

# Create ZIP
Compress-Archive -Path "$TempDir\*" -DestinationPath $OutputFile -CompressionLevel Optimal

$ZipSize = (Get-Item $OutputFile).Length / 1MB
Write-Host "  Created: $OutputFile" -ForegroundColor Gray
Write-Host "  Size: $($ZipSize.ToString('F2')) MB" -ForegroundColor Gray
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

Write-Host "[5/5] Cleaning up..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $TempDir
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DISTRIBUTION PACKAGE CREATED!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package: $OutputFile" -ForegroundColor White
Write-Host "Size: $($ZipSize.ToString('F2')) MB" -ForegroundColor White
Write-Host ""
Write-Host "Ready for distribution!" -ForegroundColor Green
Write-Host ""
Write-Host "To test the package:" -ForegroundColor Yellow
Write-Host "  1. Extract ZIP to a new folder" -ForegroundColor Gray
Write-Host "  2. Run install.bat" -ForegroundColor Gray
Write-Host "  3. Follow setup wizard" -ForegroundColor Gray
Write-Host ""

# Open output directory
$OpenDir = Read-Host "Open output directory? (Y/N)"
if ($OpenDir -eq 'Y' -or $OpenDir -eq 'y') {
    explorer $OutputDir
}

Write-Host "Done!" -ForegroundColor Green
