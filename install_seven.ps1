param(
    [switch]$DryRun,
    [switch]$NonInteractive,
    [switch]$InstallOllama,
    [switch]$PullModels,
    [switch]$InstallBrowser,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "Programs\SevenAI"),
    [string]$DataDir = (Join-Path $env:USERPROFILE ".seven"),
    [string]$Workspace = "",
    [string]$AssistantName = "Seven",
    [string]$UserName = $env:USERNAME,
    [string]$TextModel = "qwen2.5:7b",
    [string]$VisionModel = "llama3.2-vision",
    [ValidateSet("auto", "edge", "pyttsx3", "none")]
    [string]$Voice = "edge",
    [ValidateSet("off", "webcam", "screen", "both")]
    [string]$Camera = "both",
    [ValidateSet("unchanged", "talk", "quiet", "none")]
    [string]$Startup = "unchanged",
    [ValidateSet("lean", "core", "full")]
    [string]$ToolTier = "full",
    [ValidateSet("native", "dispatcher")]
    [string]$ToolSchemaMode = "dispatcher",
    [ValidateRange(1, 65535)]
    [int]$ApiPort = 8765,
    [string]$Extras = "all",
    [string]$ProjectRoots = ""
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$installRoot = [IO.Path]::GetFullPath($InstallRoot)
$dataDir = [IO.Path]::GetFullPath($DataDir)
if (-not $Workspace) {
    $Workspace = Join-Path $dataDir "workspace"
}
$workspace = [IO.Path]::GetFullPath($Workspace)
$venv = Join-Path $installRoot "venv"
$temporary = Join-Path $installRoot "tmp"
$browserPath = Join-Path $installRoot "ms-playwright"

foreach ($value in @($installRoot, $dataDir, $workspace, $ProjectRoots)) {
    if ($value -match "[`r`n`0]") {
        throw "Install, data, and workspace paths cannot contain control characters."
    }
}

$pythonExe = $null
$pythonArgs = @()
foreach ($candidate in @(
    @{ Exe = "py"; Args = @("-3.13") },
    @{ Exe = "py"; Args = @("-3.12") },
    @{ Exe = "py"; Args = @("-3.11") },
    @{ Exe = "python"; Args = @() }
)) {
    try {
        $command = Get-Command $candidate.Exe -ErrorAction Stop
        & $command.Source @($candidate.Args) -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = $command.Source
            $pythonArgs = @($candidate.Args)
            break
        }
    } catch {
        continue
    }
}
if (-not $pythonExe) {
    throw "Python 3.11 or newer is required. Install it from https://www.python.org/downloads/"
}

$setupArgs = @(
    "--setup",
    "--setup-name", $AssistantName,
    "--setup-user-name", $UserName,
    "--setup-workspace", $workspace,
    "--setup-text-model", $TextModel,
    "--setup-vision-model", $VisionModel,
    "--setup-voice", $Voice,
    "--setup-camera", $Camera,
    "--setup-startup", $Startup
)
if ($DryRun) { $setupArgs += "--setup-dry-run" }
if ($NonInteractive) { $setupArgs += "--setup-noninteractive" }
if ($InstallOllama) { $setupArgs += "--setup-install-ollama" }
if ($PullModels) { $setupArgs += "--setup-pull-models" }

$env:SEVEN_DATA_DIR = $dataDir
$env:SEVEN_WORKSPACE = $workspace
$env:SEVEN_TOOL_TIER = $ToolTier
$env:SEVEN_TOOL_SCHEMA_MODE = $ToolSchemaMode
$env:SEVEN_API_HOST = "127.0.0.1"
$env:SEVEN_API_PORT = [string]$ApiPort
$env:SEVEN_BROWSER_PROFILE = Join-Path $dataDir "browser_profile"
$env:PLAYWRIGHT_BROWSERS_PATH = $browserPath
if ($ProjectRoots) {
    $env:SEVEN_PROJECT_ROOTS = $ProjectRoots
}

if ($DryRun) {
    Write-Host "DRY RUN: would create isolated environment at $venv"
    Write-Host "DRY RUN: would install ${repo}[$Extras]"
    Write-Host "DRY RUN: data=$dataDir workspace=$workspace tier=$ToolTier"
    if ($InstallBrowser) {
        Write-Host "DRY RUN: would install isolated Chromium at $browserPath"
    }
    Push-Location $repo
    try {
        & $pythonExe @pythonArgs -m seven @setupArgs
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    exit $exitCode
}

if ((Test-Path $venv) -and -not (Test-Path (Join-Path $venv "pyvenv.cfg"))) {
    throw "Refusing to reuse non-venv path: $venv"
}
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
New-Item -ItemType Directory -Force -Path $temporary | Out-Null
$env:TEMP = $temporary
$env:TMP = $temporary
if (-not (Test-Path $venv)) {
    & $pythonExe @pythonArgs -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create Seven virtual environment." }
}

$venvPython = Join-Path $venv "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip in Seven's isolated environment." }
& $venvPython -m pip install --no-cache-dir --upgrade "${repo}[$Extras]"
if ($LASTEXITCODE -ne 0) { throw "Could not install Seven. Existing user data was preserved." }
if ($InstallBrowser) {
    & $venvPython -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        throw "Seven installed, but isolated Chromium installation failed."
    }
}
& $venvPython -m seven @setupArgs
$setupExit = $LASTEXITCODE
if ($setupExit -ne 0) { exit $setupExit }

function ConvertTo-CmdValue([string]$Value) {
    return $Value.Replace("%", "%%").Replace('"', '""')
}

$launchers = @{
    "Start-Seven.cmd" = "--talk"
    "Start-Seven-Quiet.cmd" = "--quiet"
    "Start-Seven-API.cmd" = "--api-only"
    "Seven-Status.cmd" = "--status"
}
foreach ($entry in $launchers.GetEnumerator()) {
    $content = @(
        "@echo off",
        ('set "SEVEN_DATA_DIR=' + (ConvertTo-CmdValue $dataDir) + '"'),
        ('set "SEVEN_WORKSPACE=' + (ConvertTo-CmdValue $workspace) + '"'),
        ('set "SEVEN_TOOL_TIER=' + (ConvertTo-CmdValue $ToolTier) + '"'),
        ('set "SEVEN_TOOL_SCHEMA_MODE=' + (ConvertTo-CmdValue $ToolSchemaMode) + '"'),
        'set "SEVEN_API_HOST=127.0.0.1"',
        ('set "SEVEN_API_PORT=' + $ApiPort + '"'),
        ('set "SEVEN_BROWSER_PROFILE=' + (ConvertTo-CmdValue (Join-Path $dataDir "browser_profile")) + '"'),
        ('set "PLAYWRIGHT_BROWSERS_PATH=' + (ConvertTo-CmdValue $browserPath) + '"'),
        $(if ($ProjectRoots) { 'set "SEVEN_PROJECT_ROOTS=' + (ConvertTo-CmdValue $ProjectRoots) + '"' }),
        ('"' + $venvPython + '" -m seven ' + $entry.Value + ' %*')
    ) | Where-Object { $_ }
    $content = $content -join "`r`n"
    [IO.File]::WriteAllText((Join-Path $installRoot $entry.Key), $content + "`r`n")
}

$commit = (& git -C $repo rev-parse HEAD 2>$null)
$manifest = [ordered]@{
    installed_at = [DateTime]::UtcNow.ToString("o")
    source = $repo
    source_commit = if ($LASTEXITCODE -eq 0) { $commit } else { $null }
    assistant_name = $AssistantName
    user_name = $UserName
    install_root = $installRoot
    data_dir = $dataDir
    workspace = $workspace
    python = $venvPython
    text_model = $TextModel
    vision_model = $VisionModel
    voice = $Voice
    camera = $Camera
    startup = $Startup
    tool_tier = $ToolTier
    tool_schema_mode = $ToolSchemaMode
    api_host = "127.0.0.1"
    api_port = $ApiPort
    extras = $Extras
    project_roots = if ($ProjectRoots) { @($ProjectRoots -split [IO.Path]::PathSeparator) } else { @() }
    browser_path = if ($InstallBrowser) { $browserPath } else { $null }
}
[IO.File]::WriteAllText(
    (Join-Path $installRoot "install-manifest.json"),
    ($manifest | ConvertTo-Json -Depth 4) + "`n"
)

& $venvPython -c "from seven.memory.store import Memory; Memory()"
if ($LASTEXITCODE -ne 0) { throw "Seven installed, but its memory database could not be initialized." }
& $venvPython -m seven --memory-check
if ($LASTEXITCODE -ne 0) { throw "Seven installed, but its memory integrity check failed." }
& $venvPython -m seven --status
if ($LASTEXITCODE -ne 0) { throw "Seven installed, but its runtime status check failed." }

Write-Host "Seven installed and validated at $installRoot"
Write-Host "Data: $dataDir"
Write-Host "Workspace: $workspace"
exit 0
