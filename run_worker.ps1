param(
    [string]$Role = "startup-queue",
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

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Pulling GitHub task queue & running Alternating Local LLM Worker (Role: $Role, Primary: rtx5060lp:11434 <-> Secondary: sff7020:1234)..." -ForegroundColor Cyan
python @argsList
