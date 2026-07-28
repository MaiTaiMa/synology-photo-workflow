#!/bin/sh
# Non-destructive DSM preflight. It deliberately never invokes Phase 1 or Phase 2.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
fail(){ printf '%s
' "FAIL: $*" >&2; exit 1; }
[ -f .env ] || fail '.env missing; copy .env.example and configure it'
[ -f config/config.yaml ] || fail 'config/config.yaml missing; copy and review example'
command -v docker >/dev/null 2>&1 || fail 'docker unavailable'
docker compose config -q || fail 'docker compose configuration invalid'
./scripts/verify-legacy.sh
# Require a mounted persistent root, but only inspect the configured host path.
DATA=$(sed -n 's/^WORKFLOW_DATA_ROOT=//p' .env | tail -n 1)
[ -n "$DATA" ] || fail 'WORKFLOW_DATA_ROOT missing'
[ -d "$DATA" ] || fail "persistent data root missing: $DATA"
[ -r "$DATA" ] && [ -w "$DATA" ] || fail "data root not readable/writable: $DATA"
printf '%s
' "OK: preflight passed; no photo batch was processed"
