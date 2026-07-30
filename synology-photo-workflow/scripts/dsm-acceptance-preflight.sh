#!/usr/bin/env bash
# =============================================================================
# Synology Photo Workflow — DSM-Abnahmevorprüfung
# Datei: scripts/dsm-acceptance-preflight.sh
# Zweck: Prüft die Voraussetzungen eines DSM-/Scheduler-Betriebs ohne Batchlauf.
# Seiteneffekte: Keine Fotoverarbeitung; nur Docker- und Dateisystem-Prüfungen.
# Entscheidung: Der Status des persistenten Mounts wird vor dem Schedulerbetrieb
# geprüft, weil Container ohne dauerhaften Datenbereich keine sicheren States halten.
# =============================================================================
set -Eeuo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DEFAULT_BASEDIR="$ROOT/../NAS_EXAMPLE/TEMP"
SPW_BASEDIR="${SPW_BASEDIR:-$DEFAULT_BASEDIR}"
CONFIG_PATH="${SPW_CONFIG_PATH:-$ROOT/config/config.yaml}"
fail(){ printf 'FAIL: %s
' "$*" >&2; exit 1; }
cd "$ROOT"
[[ -f "$CONFIG_PATH" ]] || fail "config missing: $CONFIG_PATH"
command -v docker >/dev/null 2>&1 || fail 'docker unavailable'
docker compose config -q || fail 'docker compose configuration invalid'
[[ -d "$SPW_BASEDIR" ]] || fail "persistent data root missing: $SPW_BASEDIR"
[[ -r "$SPW_BASEDIR" && -w "$SPW_BASEDIR" ]] || fail "data root not readable/writable: $SPW_BASEDIR"
./scripts/preflight.sh >/dev/null
printf 'OK: DSM acceptance preflight passed; no photo batch was processed
'
