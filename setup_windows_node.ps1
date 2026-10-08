<#
.SYNOPSIS
    One-click autonomous worker setup for Windows Local LLM nodes (rtx5060lp / sff7020 / MINISFORUM64GB).
    Enables this PC to pull queued tasks from GitHub (data/tasks.json), execute its assigned episodes
    (or failover if the peer is off), and push results to GitHub even when MINISFORUM64GB is powered off.
#>
param(
    [string]$InstallDir = "$HOME\rikejo-science-novel",
    [string]$Role = "auto"
)

$ErrorActionPreference = "Continue"
$RepoUrl = "https://github.com/k518-2026/rikejo-science-novel.git"

# 1. If executed from inside an existing clone, use that directory; otherwise clone/pull in $InstallDir
if (Test-Path (Join-Path $PSScriptRoot "src\task_worker.py")) {
    $WorkDir = $PSScriptRoot
} else {
    $WorkDir = $InstallDir
    if (-not (Test-Path (Join-Path $WorkDir ".git"))) {
        Write-Host "[1/3] Cloning repository to $WorkDir..." -ForegroundColor Cyan
        git clone $RepoUrl $WorkDir
    } else {
        Write-Host "[1/3] Updating repository in $WorkDir..." -ForegroundColor Cyan
        Push-Location $WorkDir
        git pull --rebase --autostash origin main
        Pop-Location
    }
}

Write-Host "Using workspace: $WorkDir (Host: $env:COMPUTERNAME, Role: $Role)" -ForegroundColor Green

# 2. Register Windows Startup folder launcher (runs automatically at every PC boot/logon without Admin rights)
$StartupDir = [Environment]::GetFolderPath("Startup")
$StartupCmd = Join-Path $StartupDir "RikejoScienceNovel_GitHubQueue.cmd"
$CmdContent = @"
@echo off
cd /d "$WorkDir"
powershell -NoProfile -WindowStyle Minimized -ExecutionPolicy Bypass -File "$WorkDir\run_worker.ps1" -Role $Role
"@
Set-Content -Path $StartupCmd -Value $CmdContent -Encoding ASCII
Write-Host "[2/3] Installed PC Startup launcher: $StartupCmd" -ForegroundColor Green

# 3. Register periodic Windows Scheduled Task (runs every 3 hours + StartWhenAvailable while PC is on)
$PyPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PyPath) { $PyPath = "python.exe" }

try {
    $Action = New-ScheduledTaskAction -Execute $PyPath -Argument "-m src.task_worker --role $Role" -WorkingDirectory $WorkDir
    $TrigDaily = New-ScheduledTaskTrigger -Daily -At "09:00"
    $Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 6)
    Register-ScheduledTask -TaskName "RikejoScienceNovel_NodeWorker" -Action $Action -Trigger $TrigDaily -Settings $Settings -Description "Autonomous GitHub Task Queue Worker ($env:COMPUTERNAME)" -Force | Out-Null
    Write-Host "[3/3] Registered Scheduled Task: RikejoScienceNovel_NodeWorker (Daily 09:00 + StartWhenAvailable)" -ForegroundColor Green
} catch {
    Write-Host "[3/3] Note: Startup launcher in $StartupCmd is active (Scheduled Task skipped: $($_.Exception.Message))" -ForegroundColor Yellow
}

Write-Host "`nSetup complete! Running initial GitHub sync & autonomous task check now..." -ForegroundColor Cyan
Push-Location $WorkDir
python -m src.task_worker --role $Role
Pop-Location
