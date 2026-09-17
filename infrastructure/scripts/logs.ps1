# Follow logs. Usage:  .\infrastructure\scripts\logs.ps1 [service] [-Tail 200]
param(
    [string]$Service = "api",
    [int]$Tail = 100
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose logs --follow --tail $Tail $Service
