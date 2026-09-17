#!/usr/bin/env bash
# Follow logs. Usage:  ./infrastructure/scripts/logs.sh [api] [200]
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose logs --follow --tail "${2:-100}" "${1:-api}"
