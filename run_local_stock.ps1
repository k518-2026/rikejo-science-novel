param(
    [int]$Count = 2,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$argsList = @("-m", "src.main", "--stock-count", "$Count")
if (-not $NoPush) {
    $argsList += "--push"
}

Write-Host "Running Dual-LLM (Qwen 2.5 14B x Gemma 2 9B) Stock Generator on Mac mini (http://192.168.128.59:11434)..." -ForegroundColor Cyan
python @argsList
