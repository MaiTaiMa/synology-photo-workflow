#!/usr/bin/env bash
# =============================================================================
# Synology Photo Workflow — Vorprüfung
# Datei: scripts/preflight.sh
# Zweck: Prüft ausschließlich die lokale Betriebsumgebung vor einem Workflowlauf.
# Seiteneffekte: Keine Bild- oder Batch-Verarbeitung; der Container validiert nur
# die Konfiguration. Das Skript beendet sich bei jedem unsicheren Zustand.
# Entscheidung: Fachliche Regeln, Pfadvalidierung und Workflow-Gates bleiben in
# Python. Dieses Skript prüft nur die äußere Betriebsgrenze (Docker, Pfade, Config).
# =============================================================================
set -Eeuo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DEFAULT_BASEDIR="$ROOT/../NAS_EXAMPLE/TEMP"
SPW_BASEDIR="${SPW_BASEDIR:-$DEFAULT_BASEDIR}"
CONFIG_PATH="${SPW_CONFIG_PATH:-$ROOT/config/config.yaml}"
COMPOSE_SERVICE="${SPW_COMPOSE_SERVICE:-workflow}"
fail(){ printf 'FAIL: %s
' "$*" >&2; exit 2; }
# In das Projektverzeichnis wechseln, damit Docker Compose und relative Pfade stabil sind.
cd "$ROOT"
# Diese Prüfungen verhindern einen Start gegen fehlende oder nicht persistente Datenbereiche.
[[ -f "$CONFIG_PATH" ]] || fail "config missing: $CONFIG_PATH"
[[ -d "$SPW_BASEDIR" ]] || fail "basedir missing: $SPW_BASEDIR"
[[ -r "$SPW_BASEDIR" && -w "$SPW_BASEDIR" ]] || fail "basedir not readable/writable: $SPW_BASEDIR"
command -v docker >/dev/null 2>&1 || fail 'docker unavailable'
docker compose config -q || fail 'docker compose configuration invalid'
# validate_config darf keine Fotos mutieren und prüft die interne Konfigurationslogik.
docker compose run --rm --no-deps "$COMPOSE_SERVICE" --config config/config.yaml validate_config >/dev/null || fail 'container validate_config failed'
printf 'OK: preflight passed; no batch processed
'
