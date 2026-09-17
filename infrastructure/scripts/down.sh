#!/usr/bin/env bash
# Stop the stack. Add -v / --volumes to also delete postgres/redis/minio/rabbit data.
# Usage:  ./infrastructure/scripts/down.sh [-v]
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down "$@"
