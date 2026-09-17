# Run one postgres + minio backup cycle into the backend_backups volume.
# Schedule with Windows Task Scheduler, e.g. daily at 02:00:
#   powershell -File D:\project\bongLymeng\infrastructure\scripts\backup.ps1
# To copy a dump out of the volume:
#   docker run --rm -v docetra-backend_backend_backups:/backups -v ${PWD}:/out alpine cp /backups/<file> /out/
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose --profile operations run --rm postgres-backup
docker compose --profile operations run --rm minio-backup
Write-Host "Backups stored in the backend_backups volume." -ForegroundColor Green
