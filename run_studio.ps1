param(
    [int]$Port = 8505
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Starting Rikejo Science Novel Web UI Studio (http://localhost:$Port)..." -ForegroundColor Magenta
python -m src.main --web --port $Port
