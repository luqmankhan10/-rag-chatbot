# run.ps1 — launch the Docs RAG Streamlit chat UI.
#
# Usage:
#   .\run.ps1              # start the UI (uses port from .streamlit/config.toml)
#   .\run.ps1 -Port 8601   # start on a different port
#   .\run.ps1 -Stop        # stop a running instance
#   .\run.ps1 -Status      # show whether it is running and where
#   .\run.ps1 -Cli "how many days of annual leave do employees get?"
#                          # ask a one-off question on the command line instead
#
# If PowerShell refuses to run this file, use .\run.cmd instead, or run:
#   powershell -ExecutionPolicy Bypass -File .\run.ps1

[CmdletBinding()]
param(
    [int]$Port,
    [switch]$Stop,
    [switch]$Status,
    [string]$Cli
)

$ErrorActionPreference = 'Stop'

# --- Paths ------------------------------------------------------------------
$ProjectRoot = $PSScriptRoot
$ConfigPath  = Join-Path $ProjectRoot '.streamlit\config.toml'
$AppFile     = Join-Path $ProjectRoot 'streamlit_app.py'

# The interpreter lives outside the project, so it is resolved at run time and
# every known location is tried before giving up.
function Resolve-Python {
    $candidates = @(
        'C:\Users\hp\fileDownload\Desktop\RAG_Project\.venv\Scripts\python.exe'
    )

    # Also accept a venv inside the project, if one is ever added.
    $local = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    if (Test-Path $local) { $candidates = @($local) + $candidates }

    # And fall back to whatever is on PATH.
    $onPath = Get-Command python -ErrorAction SilentlyContinue
    if ($onPath) { $candidates += $onPath.Source }

    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }

    throw ("No Python interpreter found. Tried:`n  " + ($candidates -join "`n  ") +
           "`nSet one up, or edit the candidates list in run.ps1.")
}

# The port is read from the Streamlit config so the two never disagree.
function Get-ConfiguredPort {
    if (Test-Path $ConfigPath) {
        $match = Select-String -Path $ConfigPath -Pattern '^\s*port\s*=\s*(\d+)' |
                 Select-Object -First 1
        if ($match) { return [int]$match.Matches[0].Groups[1].Value }
    }
    return 8600
}

function Get-ListeningProcess {
    param([int]$ListenPort)
    Get-NetTCPConnection -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

$resolvedPort = if ($PSBoundParameters.ContainsKey('Port')) { $Port } else { Get-ConfiguredPort }
$url          = "http://localhost:$resolvedPort"
$healthUrl    = "$url/_stcore/health"

# --- -Status ----------------------------------------------------------------
if ($Status) {
    $listener = Get-ListeningProcess -ListenPort $resolvedPort
    if ($listener) {
        $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "Running on port $resolvedPort (PID $($listener.OwningProcess), $($proc.ProcessName))." -ForegroundColor Green
        Write-Host "Open: $url"
    }
    else {
        Write-Host "Not running on port $resolvedPort." -ForegroundColor Yellow
    }
    exit 0
}

# --- -Stop ------------------------------------------------------------------
if ($Stop) {
    $listener = Get-ListeningProcess -ListenPort $resolvedPort
    if (-not $listener) {
        Write-Host "Nothing is listening on port $resolvedPort; nothing to stop." -ForegroundColor Yellow
        exit 0
    }

    $rootPid = $listener.OwningProcess
    # Streamlit spawns a child, so walk up to the parent launcher and stop that
    # too — otherwise the parent can respawn or linger holding resources.
    $parent = (Get-CimInstance Win32_Process -Filter "ProcessId=$rootPid" -ErrorAction SilentlyContinue).ParentProcessId
    if ($parent) {
        $parentCmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$parent" -ErrorAction SilentlyContinue).CommandLine
        if ($parentCmd -and $parentCmd -match 'streamlit') {
            Stop-Process -Id $parent -Force -ErrorAction SilentlyContinue
        }
    }
    Stop-Process -Id $rootPid -Force -ErrorAction SilentlyContinue

    Start-Sleep -Seconds 2
    if (Get-ListeningProcess -ListenPort $resolvedPort) {
        Write-Host "Port $resolvedPort is still held. Check it manually:" -ForegroundColor Red
        Write-Host "  Get-NetTCPConnection -LocalPort $resolvedPort -State Listen"
        exit 1
    }
    Write-Host "Stopped the app on port $resolvedPort." -ForegroundColor Green
    exit 0
}

# --- -Cli -------------------------------------------------------------------
if ($PSBoundParameters.ContainsKey('Cli')) {
    $python = Resolve-Python
    Set-Location $ProjectRoot
    & $python (Join-Path $ProjectRoot 'ask.py') $Cli
    exit $LASTEXITCODE
}

# --- Default: start the UI --------------------------------------------------
if (-not (Test-Path $AppFile)) {
    Write-Host "Cannot find streamlit_app.py in $ProjectRoot" -ForegroundColor Red
    exit 1
}

$python = Resolve-Python

# Refuse to start a second copy; a silent port clash is the most confusing
# failure mode this project has had.
$existing = Get-ListeningProcess -ListenPort $resolvedPort
if ($existing) {
    Write-Host "Port $resolvedPort is already in use (PID $($existing.OwningProcess))." -ForegroundColor Yellow
    Write-Host "It may already be this app. Check:  .\run.ps1 -Status"
    Write-Host "To restart it:  .\run.ps1 -Stop   then run .\run.ps1 again"
    Write-Host "Or pick another port:  .\run.ps1 -Port 8601"
    exit 1
}

Write-Host "Chat model: reading from .env / src\rag\config.py" -ForegroundColor DarkGray
Write-Host "Starting Docs RAG Chat on $url ..." -ForegroundColor Cyan

Set-Location $ProjectRoot
$args = @('-m', 'streamlit', 'run', 'streamlit_app.py', '--server.port', "$resolvedPort")

if ($Port) {
    # An explicit port overrides the config file for this launch only.
    Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $ProjectRoot | Out-Null
}
else {
    Start-Process -FilePath $python -ArgumentList @('-m','streamlit','run','streamlit_app.py') -WorkingDirectory $ProjectRoot | Out-Null
}

# Poll the health endpoint instead of guessing how long startup takes.
$ready = $false
foreach ($attempt in 1..30) {
    Start-Sleep -Milliseconds 700
    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    }
    catch { }
}

if ($ready) {
    Write-Host "Ready. Opening $url" -ForegroundColor Green
    Start-Process $url
}
else {
    Write-Host "Started, but the health check did not pass within ~20s." -ForegroundColor Yellow
    Write-Host "Try opening $url in your browser, or check the log: .\run.ps1 -Status"
}
