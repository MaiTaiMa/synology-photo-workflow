#!/usr/bin/env bash
# =============================================================================
# Synology Photo Workflow — Start ausschließlich Phase 2
# Datei: scripts/run-phase2.sh
# Zweck: Führt nur die freigegebene Archiv- und Bereinigungsphase aus.
# Seiteneffekte: Phase 2 kann nach verifizierter Archivierung ARWs bereinigen.
# Entscheidung: Dieses Skript erzwingt keine Übergabe; das Python-Projekt prüft
# Batch-State, Review-Freigabe, Lock, Integrität und Archivvertrag selbst.
# =============================================================================
set -Eeuo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_SERVICE="${SPW_COMPOSE_SERVICE:-workflow}"
cd "$ROOT"
./scripts/preflight.sh
docker compose run --rm "$COMPOSE_SERVICE" --config config/config.yaml phase2 "$@"
