# Changelog

## 7.9.0 — 2026-08-08

### 00AP – Vollständige Architektur (Foundational Layer)

- **`app/safety.py`**: `sha256`, `canonical_hash`, `utcnow`, `atomic_json` (mit
  Pflichtfeldprüfung gem. 00AP.md §8.3), `read_control_json`, `safe_zip`,
  `validate_zip`, `within`, `require_within` ergänzt.
- **`app/result_contract.py`**: `atomic_json_write` (ohne Pflichtfeldprüfung, für
  interne Artefakte) und `FileManifest`-Dataclass ergänzt.
- **`app/batch_state.py`**: Kanonisches Schema: `state_path`, `write_state` (mit
  Vorwärts-Zustandsvalidierung), `load_state`. Zustandsreihenfolge
  `_STATE_ORDER` für Rückwärts-Schutz.
- **`app/runtime.py`**: `RunBudget` (Zeit-Budget-Checkpoint), `BatchLock`
  (exklusiver Batch-Lock, atomare O_EXCL-Erstellung), `quarantine_batch` (mit
  Quarantäne-Manifest), `inspect_recovery`.
- **`app/locks.py`**: `RunLock` (globaler Lauf-Lock, atomare O_EXCL-Erstellung,
  verhindert TOCTOU-Race).
- **`app/calibration.py`**: `rebuild` (Kalibrierungsindex aus
  review_decision_record.json-Dateien).
- **`app/reporting.py`**: `action` und `summary` für Run-Summary-Erzeugung.
- **`app/planning.py`**: `plan_phase1`, `plan_phase2` (lesend, ohne Mutation).
- **`app/phases.py`**: Kanonische `phase1`- und `phase2`-Orchestrierung mit
  Manifest, CSV und Review-Ablage.
- **`app/face_cache.py`**: `rebuild_plan` und `write_cache_manifest` (ohne
  Embedding-Persistenz, vector_storage=none).
- **`NAS_EXAMPLE/TEMP/`**: Vollständige NAS-Verzeichnisstruktur mit README.md
  erstellt.

## 7.8.0 — 2026-07-31

- Vollständige Versionserhöhung von 7.7.0 auf 7.8.0 im gesamten Projekt.
- `producer_version` in `archives.py` und `phases.py` wird aus `app.__init__.VERSION` importiert statt als String-Literal — kein manueller Versionsstring mehr in Laufzeit-Manifesten.
- Stärkere Konfigurationsvalidierung für `taste_model` und `family_recognition.backends`.
- Korrektes Score-Wiring: `reference_score` → `personal_score`.
- Stabilerer Face-Backend-Fingerprint (SHA256-basiert).
- Detailliertere Kommentare in `config/config.yaml`.
- Neue Testdatei `tests/test_ai_model_wiring.py` für KI-Anbindung und Konfigurationskonsistenz.

## 7.7.0 — 2026-07-29

- Neuaufbau nach alleiniger normativer Spezifikation v7.7.
- Kanonische `snake_case`-CLI, Konfiguration, Batch-Zustände und Laufzeitartefakte.
- Sichere Phase-1/Phase-2-Grundimplementierung mit Hashes, atomaren JSON- und ZIP-Transaktionen, Quarantäne und Review-Record.
- Explizite Face-Backend-Registry; Standardbackend ist CPU und Face-Funktion standardmäßig deaktiviert.
- Dokumentation, CI und synthetische Tests ergänzt.

## Migration

Historische Namen sind nicht produktiv. Lokale Konfigurationen müssen in die kommentierte `config/config.example.yaml` überführt werden. Private Daten und Produktionspfade bleiben außerhalb von Git.
