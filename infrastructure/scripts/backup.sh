#!/usr/bin/env bash
# Run one postgres + minio backup cycle into the backend_backups volume.
# Cron example (daily 02:00 UTC):  0 2 * * * /srv/docetra/infrastructure/scripts/backup.sh >> /var/log/docetra-backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose --profile operations run --rm postgres-backup
docker compose --profile operations run --rm minio-backup
echo "Backups stored in the backend_backups volume."
