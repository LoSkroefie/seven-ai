param(
    [switch]$DryRun,
    [switch]$NonInteractive,
    [switch]$InstallOllama,
    [switch]$PullModels
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$installRoot = Join-Path $env:LOCALAPPDATA "Programs\SevenAI"
$venv = Join-Path $installRoot "venv"

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

$setupArgs = @("--setup")
if ($DryRun) { $setupArgs += "--setup-dry-run" }
if ($NonInteractive) { $setupArgs += "--setup-noninteractive" }
if ($InstallOllama) { $setupArgs += "--setup-install-ollama" }
if ($PullModels) { $setupArgs += "--setup-pull-models" }

if ($DryRun) {
    Write-Host "DRY RUN: would create isolated environment at $venv"
    Write-Host "DRY RUN: would install ${repo}[voice,tray]"
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
if (-not (Test-Path $venv)) {
    & $pythonExe @pythonArgs -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create Seven virtual environment." }
}

$venvPython = Join-Path $venv "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip in Seven's isolated environment." }
& $venvPython -m pip install --upgrade "${repo}[voice,tray]"
if ($LASTEXITCODE -ne 0) { throw "Could not install Seven. Existing user data was preserved." }
& $venvPython -m seven @setupArgs
exit $LASTEXITCODE
