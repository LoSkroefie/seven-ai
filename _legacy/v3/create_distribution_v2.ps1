# Seven AI v2.0 - Distribution Package Creator
# Creates clean distribution zip ready for public release

param(
    [string]$OutputPath = ".\Seven-AI-v2.0-Complete.zip"
)

Write-Host "========================================"
Write-Host "  Seven AI v2.0 - Package Creator"
Write-Host "========================================"
Write-Host ""

# Define directories
$SourceDir = Get-Location
$TempDir = Join-Path $env:TEMP "Seven-AI-v2.0-Build"
$PackageDir = Join-Path $TempDir "Seven-AI-v2.0-Complete"

# Clean up existing temp
if (Test-Path $TempDir) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item -Path $TempDir -Recurse -Force
}

# Create package directory
Write-Host "Creating package directory..." -ForegroundColor Green
New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null

# Files to include
$IncludeItems = @(
    "config.py",
    "setup_wizard.py",
    "install.bat",
    "main_with_gui_and_tray.py",
    "main_with_gui.py",
    "main.py",
    "requirements.txt",
    "requirements-stable.txt",
    "README.md",
    "CHANGELOG.md",
    "QUICK_START_GUIDE.md",
    "LICENSE",
    "create_shortcuts.ps1",
    "uninstall.bat",
    "seven_icon.ico",
    "core",
    "gui",
    "integrations",
    "utils",
    "identity"
)

# Patterns to exclude
$ExcludePatterns = @(
    "*.pyc",
    "__pycache__",
    "test_*.py",
    "*_test.py",
    "test_data",
    ".git",
    "dist",
    "build"
)

Write-Host "Copying files..." -ForegroundColor Green

# Copy each item
foreach ($item in $IncludeItems) {
    $sourcePath = Join-Path $SourceDir $item
    $destPath = Join-Path $PackageDir $item
    
    if (Test-Path $sourcePath) {
        if (Test-Path $sourcePath -PathType Container) {
            Write-Host "  Copying directory: $item" -ForegroundColor Gray
            
            # Copy directory with exclusions
            Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
            
            # Remove excluded patterns
            foreach ($pattern in $ExcludePatterns) {
                Get-ChildItem -Path $destPath -Include $pattern -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host "  Copying file: $item" -ForegroundColor Gray
            $targetDir = Split-Path $destPath -Parent
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item -Path $sourcePath -Destination $destPath -Force
        }
    } else {
        Write-Host "  Warning: $item not found" -ForegroundColor Yellow
    }
}

# Remove markdown files from core/v2
$v2Path = Join-Path $PackageDir "core\v2"
if (Test-Path $v2Path) {
    Write-Host "  Cleaning v2 docs..." -ForegroundColor Gray
    Get-ChildItem -Path $v2Path -Filter "*.md" | Remove-Item -Force -ErrorAction SilentlyContinue
}

# Verify critical files
Write-Host ""
Write-Host "Verifying package..." -ForegroundColor Green

$CriticalFiles = @(
    "README.md",
    "CHANGELOG.md",
    "config.py",
    "setup_wizard.py",
    "install.bat",
    "main_with_gui_and_tray.py",
    "core\enhanced_bot.py",
    "core\v2\seven_v2_complete.py",
    "gui\phase5_gui.py"
)

$allPresent = $true
foreach ($file in $CriticalFiles) {
    $filePath = Join-Path $PackageDir $file
    if (Test-Path $filePath) {
        Write-Host "  OK: $file" -ForegroundColor DarkGreen
    } else {
        Write-Host "  MISSING: $file" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host ""
    Write-Host "ERROR: Critical files missing!" -ForegroundColor Red
    exit 1
}

# Create zip
Write-Host ""
Write-Host "Creating archive..." -ForegroundColor Green

if (Test-Path $OutputPath) {
    Remove-Item -Path $OutputPath -Force
}

# FIX: Zip contents directly, not the folder itself (prevents double-nesting)
$zipSource = Join-Path $PackageDir "*"
Compress-Archive -Path $zipSource -DestinationPath $OutputPath -CompressionLevel Optimal

# Verify zip created
if (Test-Path $OutputPath) {
    $zipSize = (Get-Item $OutputPath).Length
    $zipSizeMB = [math]::Round($zipSize / 1MB, 2)
    
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  SUCCESS! Package Created"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Output: $OutputPath" -ForegroundColor Cyan
    Write-Host "Size: $zipSizeMB MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Package includes:" -ForegroundColor Yellow
    Write-Host "  * v2.0 documentation"
    Write-Host "  * 8 v2.0 sentience modules"
    Write-Host "  * Core modules and GUI"
    Write-Host "  * 20 autonomous tools"
    Write-Host "  * Setup wizard"
    Write-Host ""
    Write-Host "Next: Test installation!" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to create zip!" -ForegroundColor Red
    exit 1
}

# Cleanup
Write-Host "Cleaning up..." -ForegroundColor Gray
Remove-Item -Path $TempDir -Recurse -Force

Write-Host "Done! Ready for distribution." -ForegroundColor Green
Write-Host ""
