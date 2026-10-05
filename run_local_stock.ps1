param(
    [int]$Count = 5,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$argsList = @("-m", "src.main", "--stock-count", "$Count")
if (-not $NoPush) {
    $argsList += "--push"
}

Write-Host "Running Dual-LLM (Qwen 3.5 9B x Gemma 4 12B) + Draw Things (FLUX.2) Weekly 5-Episode Generator on Mac mini M4..." -ForegroundColor Cyan
python @argsList
