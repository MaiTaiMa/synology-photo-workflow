#!/usr/bin/env bash
# =============================================================================
# Synology Photo Workflow — Start ausschließlich Phase 1
# Datei: scripts/run-phase1.sh
# Zweck: Führt Inventarisierung, Bewertung und Review-Vorbereitung aus.
# Seiteneffekte: Phase 1 darf Batch-Artefakte erzeugen, aber keine Phase-2-
# Bereinigung auslösen. Alle fachlichen Sicherheitsprüfungen erfolgen im Container.
# =============================================================================
set -Eeuo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_SERVICE="${SPW_COMPOSE_SERVICE:-workflow}"
cd "$ROOT"
# Die Vorprüfung verhindert Starts mit ungültiger Konfiguration oder fehlendem NAS-Mount.
./scripts/preflight.sh
docker compose run --rm "$COMPOSE_SERVICE" --config config/config.yaml phase1 "$@"
