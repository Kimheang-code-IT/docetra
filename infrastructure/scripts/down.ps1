# Stop the stack. Add -Volumes to also delete postgres/redis/minio/rabbit data.
# Usage:  .\infrastructure\scripts\down.ps1 [-Volumes]
param(
    [switch]$Volumes
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if ($Volumes) {
    docker compose down -v
} else {
    docker compose down
}
