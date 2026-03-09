$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent
$ironclawBin = Join-Path $workspaceRoot "repos\ironclaw\target\release\ironclaw.exe"

if (-not (Test-Path $ironclawBin)) {
  throw "Missing IronClaw binary at: $ironclawBin"
}

Write-Host "Running IronClaw version check..."
& $ironclawBin --version

Write-Host "Running IronClaw status check..."
& $ironclawBin status --no-db --no-onboard --cli-only

