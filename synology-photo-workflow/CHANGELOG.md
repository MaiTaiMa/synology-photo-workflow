# Changelog

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
