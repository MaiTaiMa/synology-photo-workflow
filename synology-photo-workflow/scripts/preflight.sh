#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
: "${WORKFLOW_DATA_ROOT:?Set WORKFLOW_DATA_ROOT in .env or environment}"
: "${PUID:?Set PUID in .env or environment}"
: "${PGID:?Set PGID in .env or environment}"
[[ "$WORKFLOW_DATA_ROOT" = /* ]] || { echo "WORKFLOW_DATA_ROOT must be absolute" >&2; exit 2; }
[[ -d "$WORKFLOW_DATA_ROOT" ]] || { echo "Data root does not exist: $WORKFLOW_DATA_ROOT" >&2; exit 2; }
[[ -r config/config.yaml ]] || { echo "Missing readable config/config.yaml" >&2; exit 2; }
[[ -w "$WORKFLOW_DATA_ROOT" ]] || { echo "Data root is not writable by scheduler user" >&2; exit 2; }
docker compose config --quiet
docker compose run --rm --no-deps photo-workflow --config config/config.yaml automation-status
echo "Preflight passed; no image batch was processed."
