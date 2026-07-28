#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
./scripts/preflight.sh
docker compose run --rm photo-workflow --config config/config.yaml phase1 "$@"
