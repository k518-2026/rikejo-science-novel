param(
    [string]$Role = "auto",
    [int]$Quota = 0,
    [int]$Enqueue = 0,
    [switch]$NoPush
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$argsList = @("-m", "src.task_worker", "--role", $Role)
if ($Quota -gt 0) {
    $argsList += @("--quota", "$Quota")
}
if ($Enqueue -gt 0) {
    $argsList += @("--enqueue", "$Enqueue")
}
if ($NoPush) {
    $argsList += "--no-push"
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Starting Autonomous GitHub-Synced Local LLM Worker (Host: $env:COMPUTERNAME, Role: $Role)..." -ForegroundColor Cyan
python @argsList
