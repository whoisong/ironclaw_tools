$ErrorActionPreference = "Stop"

$toolRoot = "C:\Users\nutty\Documents\workspace\AI\ironclaw_tool"
$ironclawRoot = "C:\Users\nutty\Documents\workspace\AI\repos\ironclaw"
$testDir = Join-Path $toolRoot "test"
$uvicornPidFile = Join-Path $testDir "uvicorn_pid.txt"
$ironclawPidFile = Join-Path $testDir "ironclaw_run_pid.txt"

New-Item -ItemType Directory -Force -Path $testDir | Out-Null

function Stop-ByPidFile {
    param([string]$PidFile)
    if (Test-Path $PidFile) {
        try {
            $targetPid = [int](Get-Content $PidFile)
            Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
        } catch {
        }
    }
}

function Stop-ListeningPort {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        $connections | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Stopping old processes..."
Stop-ByPidFile -PidFile $uvicornPidFile
Stop-ByPidFile -PidFile $ironclawPidFile
Stop-ListeningPort -Port 8000
Stop-ListeningPort -Port 3000

Write-Host "Starting ironclaw_tool MCP backend on 127.0.0.1:8000..."
$uvicornOut = Join-Path $testDir "uvicorn_stdout.log"
$uvicornErr = Join-Path $testDir "uvicorn_stderr.log"
$uvicornProc = Start-Process -FilePath "python" `
    -ArgumentList "-m uvicorn agent_service.main:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory $toolRoot `
    -RedirectStandardOutput $uvicornOut `
    -RedirectStandardError $uvicornErr `
    -PassThru
Set-Content -Path $uvicornPidFile -Value $uvicornProc.Id

Start-Sleep -Seconds 2

Write-Host "Starting ironclaw run..."
$ironclawExe = Join-Path $ironclawRoot "target\release\ironclaw.exe"
$ironclawProc = Start-Process -FilePath $ironclawExe `
    -ArgumentList "run" `
    -WorkingDirectory $ironclawRoot `
    -PassThru
Set-Content -Path $ironclawPidFile -Value $ironclawProc.Id

Start-Sleep -Seconds 3

Write-Host "Checking ports..."
$toolListen = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$ironclawListen = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $toolListen) {
    throw "ironclaw_tool backend did not bind port 8000"
}
if (-not $ironclawListen) {
    throw "ironclaw did not bind port 3000"
}

Write-Host "Ensuring MCP server registration..."
& $ironclawExe mcp add ironclaw_tool http://127.0.0.1:8000/mcp 2>$null | Out-Null
& $ironclawExe mcp test ironclaw_tool

Write-Host ""
Write-Host "Stack is up."
Write-Host "ironclaw_tool PID: $($uvicornProc.Id)"
Write-Host "ironclaw PID:      $($ironclawProc.Id)"
Write-Host "Open gateway:"
Write-Host "http://127.0.0.1:3000/"
