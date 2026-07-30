#!/usr/bin/env bash
# =============================================================================
# Synology Photo Workflow — Kanonischer Gesamtstart
# Datei: scripts/run-workflow.sh
# Zweck: Startet den CLI-Befehl `run`, der die konfigurierte Phasenreihenfolge
# ausführt. Der Standardmodus ist `phase1_then_phase2`.
# Seiteneffekte: Abhängig von der Konfiguration und validen Gates. Das Skript
# selbst verschiebt keine Dateien und simuliert keine menschliche Freigabe.
# Entscheidung: Der Wrapper delegiert Reihenfolge, Recovery und Löschfreigaben
# bewusst an die testbare Python-Orchestrierung statt Logik zu duplizieren.
# =============================================================================
set -Eeuo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_SERVICE="${SPW_COMPOSE_SERVICE:-workflow}"
COMMAND="${1:-run}"
shift || true
cd "$ROOT"
./scripts/preflight.sh
# Zusätzliche CLI-Argumente werden unverändert durchgereicht.
docker compose run --rm "$COMPOSE_SERVICE" --config config/config.yaml "$COMMAND" "$@"
