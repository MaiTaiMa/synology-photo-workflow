# Synology Photo Workflow v7.1

A local Docker two-phase workflow for Synology NAS. The secure default is `assistedreview`: Phase 1 places a batch in `TEMPIMAGES`; only an explicit human move to `TEMPDONE` permits Phase 2.

## Quick start

```bash
cp .env.example .env
cp config/config.example.yaml config/config.yaml
# Edit both files, then:
docker compose build
./scripts/preflight.sh
./scripts/run-phase1.sh
./scripts/run-phase2.sh --dry-run
```

Use a dedicated persistent NAS directory as `WORKFLOW_DATA_ROOT`, never the repository or a broad share root. The compose service runs without Linux capabilities, with a read-only application filesystem, a temporary `/tmp`, a read-only configuration mount, and a single read/write data mount.

## Safety model

Phase 2 records a hash-bound archive plan, creates and verifies the RAW ZIP, atomically activates it, and only then deletes planned ARWs. It can resume after interruption and blocks altered planned files. Dry runs do not write states, calibration records, indexes, archives, or delete files.

Automatic Phase 2 is off by default. Even if configured, it requires a matching eligible calibration summary and explicit approval bound to the current configuration, model, and calibration record set. See [DSM deployment](docs/SYNOLOGY_DSM_DEPLOYMENT.md).

## Dokumentation

- [Benutzerhandbuch (Deutsch)](docs/MANUAL_DE.md)
- [Synology-DSM-Bereitstellung und Abnahme](docs/SYNOLOGY_DSM_DEPLOYMENT.md)
- [Vollständig kommentierte Konfiguration](config/config.documented.example.yaml)
