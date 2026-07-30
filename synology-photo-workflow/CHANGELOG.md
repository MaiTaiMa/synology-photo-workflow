# Changelog

## 7.7.0 — 2026-07-29

- Neuaufbau nach alleiniger normativer Spezifikation v7.7.
- Kanonische `snake_case`-CLI, Konfiguration, Batch-Zustände und Laufzeitartefakte.
- Sichere Phase-1/Phase-2-Grundimplementierung mit Hashes, atomaren JSON- und ZIP-Transaktionen, Quarantäne und Review-Record.
- Explizite Face-Backend-Registry; Standardbackend ist CPU und Face-Funktion standardmäßig deaktiviert.
- Dokumentation, CI und synthetische Tests ergänzt.

## Migration

Historische Namen sind nicht produktiv. Lokale Konfigurationen müssen in die kommentierte `config/config.example.yaml` überführt werden. Private Daten und Produktionspfade bleiben außerhalb von Git.
