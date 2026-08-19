<#
.SYNOPSIS
    Drives the Copilot CLI sandboxing demo on Windows.

.DESCRIPTION
    Wraps the Python demo scripts so the whole demo can be run from PowerShell
    without remembering paths or juggling terminals. The simulated internal
    service is started as a background process and tracked by PID.

.EXAMPLE
    .\Invoke-SandboxDemo.ps1 -Action Check
    .\Invoke-SandboxDemo.ps1 -Action Setup
    .\Invoke-SandboxDemo.ps1 -Action Probe -Evidence before.json
    .\Invoke-SandboxDemo.ps1 -Action Teardown
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Check', 'Setup', 'StartService', 'Probe', 'StopService', 'Teardown')]
    [string]$Action,

    [string]$Evidence
)

$ErrorActionPreference = 'Stop'
$demoRoot = $PSScriptRoot
$pidFile = Join-Path $env:TEMP 'wbc-sandbox-demo-service.pid'

function Resolve-Python {
    foreach ($candidate in 'python', 'py') {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw 'Python was not found on PATH. Install Python 3.10 or later.'
}

function Invoke-Check {
    Write-Host "`n=== Demo readiness check ===`n" -ForegroundColor Cyan

    $python = Resolve-Python
    Write-Host ("  Python              : {0}" -f (& $python --version 2>&1)) -ForegroundColor Green

    $build = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild
    Write-Host ("  Windows build       : {0}" -f $build)

    # Local sandbox enforcement on Windows currently ships only in Insider builds.
    if ($build -ge 27000) {
        Write-Host '  Sandbox enforcement : likely available (Insider build)' -ForegroundColor Green
    }
    else {
        Write-Host '  Sandbox enforcement : NOT available on this retail build' -ForegroundColor Yellow
        Write-Host '                        Acts 1, 3 and 4 still run natively.' -ForegroundColor Yellow
        Write-Host '                        Run Act 2 from WSL2 Ubuntu with bubblewrap.' -ForegroundColor Yellow
    }

    $copilot = Get-Command copilot -ErrorAction SilentlyContinue
    if ($copilot) {
        Write-Host '  Copilot CLI         : found' -ForegroundColor Green
    }
    else {
        Write-Host '  Copilot CLI         : not found on PATH' -ForegroundColor Yellow
    }

    $wsl = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wsl) {
        $bwrap = (wsl -e bash -lc 'command -v bwrap' 2>$null)
        if ($bwrap) {
            Write-Host '  WSL bubblewrap      : installed (Act 2 fallback ready)' -ForegroundColor Green
        }
        else {
            Write-Host '  WSL bubblewrap      : missing' -ForegroundColor Yellow
            Write-Host '                        wsl -e sudo apt-get install -y bubblewrap' -ForegroundColor Yellow
        }
    }

    Write-Host ''
}

function Start-InternalService {
    if (Test-Path $pidFile) {
        $existing = Get-Content $pidFile
        if (Get-Process -Id $existing -ErrorAction SilentlyContinue) {
            Write-Host "Internal service already running (PID $existing)." -ForegroundColor Yellow
            return
        }
    }

    $python = Resolve-Python
    $script = Join-Path $demoRoot 'internal_payments_api.py'
    $proc = Start-Process -FilePath $python -ArgumentList $script -PassThru -WindowStyle Hidden
    $proc.Id | Set-Content $pidFile

    Start-Sleep -Seconds 2
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:9443/health' -TimeoutSec 5
        Write-Host ("Internal service running (PID {0}): {1}" -f $proc.Id, $health.service) -ForegroundColor Green
    }
    catch {
        throw "Internal service failed to start on 127.0.0.1:9443. $_"
    }
}

function Stop-InternalService {
    if (-not (Test-Path $pidFile)) {
        Write-Host 'No tracked internal service to stop.' -ForegroundColor Yellow
        return
    }

    $servicePid = Get-Content $pidFile
    if (Get-Process -Id $servicePid -ErrorAction SilentlyContinue) {
        Stop-Process -Id $servicePid -Force
        Write-Host "Stopped internal service (PID $servicePid)." -ForegroundColor Green
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

switch ($Action) {
    'Check' { Invoke-Check }

    'Setup' {
        & (Resolve-Python) (Join-Path $demoRoot 'setup_demo.py')
        Start-InternalService
    }

    'StartService' { Start-InternalService }

    'Probe' {
        $probeArgs = @((Join-Path $demoRoot 'blast_radius_probe.py'))
        if ($Evidence) { $probeArgs += @('--json', $Evidence) }
        & (Resolve-Python) @probeArgs
    }

    'StopService' { Stop-InternalService }

    'Teardown' {
        Stop-InternalService
        & (Resolve-Python) (Join-Path $demoRoot 'teardown_demo.py')
    }
}
