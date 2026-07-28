# NAS_EXAMPLE – Beispielstruktur

Leere Vorlage für den persistenten NAS-Bind-Mount. Sie enthält absichtlich keine Fotos, RAWs, Modelle, Referenzen, Logs oder Zustandsdaten.

## Einrichtung

1. Lege diesen Ordner auf dem NAS an, beispielsweise unter `/volume1/photos/NAS_EXAMPLE`.
2. Setze `WORKFLOW_DATA_ROOT` in der Projektdatei `.env` auf diesen absoluten Pfad.
3. Gib dem DSM-Scheduler-Benutzer Lese- und Schreibrechte auf den gesamten Ordner.
4. Führe im Projekt `./scripts/dsm-acceptance-preflight.sh` aus.

## Struktur

- `TEMP/TEMPSD`, `TEMP/TEMPIMAGES`, `TEMP/TEMPDONE`, `TEMP/TEMPERROR`: Batch-Eingang, Sichtung, Freigabe und Quarantäne.
- `TEMP/MANUALKEEP`: externe, manuell vorgewählte JPGs.
- `TEMP/WORKFLOW_DATA/faces`: Personenreferenzen und Gesichtsvorschläge.
- `TEMP/WORKFLOW_DATA/models`: lokale Modell- und Cacheartefakte.
- `TEMP/WORKFLOW_DATA/samples`: Geschmacksreferenzen und Vorschläge.
- `TEMP/WORKFLOW_DATA/runtime`: Zustände, Logs, Summaries, Kalibrierung und Quarantäne.

`.gitkeep` erhält absichtlich leere Ordner im Beispielarchiv und darf auf dem NAS bleiben oder entfernt werden.
