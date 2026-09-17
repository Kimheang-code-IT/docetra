# Start the Docetra backend stack (local).
# Usage:  .\infrastructure\scripts\up.ps1 [-Build]
param(
    [switch]$Build
)
$ErrorActionPreference = "Stop"
$infra = Split-Path $PSScriptRoot -Parent
Set-Location $infra

if (-not (Test-Path (Join-Path $infra ".env"))) {
    Copy-Item (Join-Path $infra ".env.example") (Join-Path $infra ".env")
    Write-Host "Created .env from .env.example - review it before first use." -ForegroundColor Yellow
}

if ($Build) {
    docker compose up --build -d
} else {
    docker compose up -d
}
docker compose ps
