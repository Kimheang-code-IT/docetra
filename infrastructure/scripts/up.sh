#!/usr/bin/env bash
# Start the Docetra backend stack (local or VPS).
# Usage:  ./infrastructure/scripts/up.sh [--build]
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - review it before first use."
fi

docker compose up "$@" -d
docker compose ps
