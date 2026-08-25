<#
.SYNOPSIS
    Installs a Copilot CLI enterprise managed settings file on Windows.

.DESCRIPTION
    Templates the REPLACE_USERNAME placeholder in the Windows policy files with
    a real profile name, then writes the result to the machine-wide file-based
    location. Requires an elevated PowerShell session.

    File-based deployment is the demo-friendly path. In production use
    server-managed settings in the enterprise .github-private repository, or
    push the same keys through Intune.

.EXAMPLE
    .\Install-ManagedSettings.ps1 -Tier Baseline -WhatIf
    .\Install-ManagedSettings.ps1 -Tier Regulated
    .\Install-ManagedSettings.ps1 -Remove
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('Baseline', 'Regulated')]
    [string]$Tier = 'Baseline',

    [string]$UserName = $env:USERNAME,

    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$targetDir = Join-Path $env:ProgramFiles 'GitHubCopilot'
$targetFile = Join-Path $targetDir 'managed-settings.json'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isElevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

function Assert-Elevated {
    if (-not $isElevated) {
        throw 'This script writes to Program Files and must be run from an elevated PowerShell session. Use -WhatIf to preview without elevation.'
    }
}

if ($Remove) {
    if (Test-Path $targetFile) {
        if ($PSCmdlet.ShouldProcess($targetFile, 'Remove managed settings')) {
            Assert-Elevated
            Remove-Item $targetFile -Force
            Write-Host "Removed $targetFile" -ForegroundColor Green
            Write-Host 'Restart Copilot CLI for the change to take effect.' -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "Nothing to remove at $targetFile" -ForegroundColor Yellow
    }
    return
}

$sourceName = if ($Tier -eq 'Regulated') { 'tier1-regulated-windows.json' } else { 'baseline-windows.json' }
$sourceFile = Join-Path $PSScriptRoot "managed-settings\$sourceName"

if (-not (Test-Path $sourceFile)) {
    throw "Policy file not found: $sourceFile"
}

$content = (Get-Content $sourceFile -Raw).Replace('REPLACE_USERNAME', $UserName)

# Fail fast rather than shipping a policy the client will reject at load time.
try {
    $null = $content | ConvertFrom-Json
}
catch {
    throw "Templated policy is not valid JSON: $_"
}

Write-Host "`nPolicy to install ($Tier tier, user '$UserName'):`n" -ForegroundColor Cyan
Write-Host $content

if ($PSCmdlet.ShouldProcess($targetFile, "Install $Tier managed settings")) {
    Assert-Elevated
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Set-Content -Path $targetFile -Value $content -Encoding UTF8

    Write-Host "`nInstalled to $targetFile" -ForegroundColor Green
    Write-Host 'Restart Copilot CLI, then verify with:' -ForegroundColor Cyan
    Write-Host '  /sandbox status     (should report sandboxing is required)'
    Write-Host '  /sandbox disable    (should be refused)'
    Write-Host '  /sandbox config     (locked values labelled "(managed)")'
}
