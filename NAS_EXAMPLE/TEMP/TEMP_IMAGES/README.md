# TEMP_IMAGES – Arbeitsverzeichnis für laufende Batch-Verarbeitung

**Zweck:** Arbeitsverzeichnis für JPG-Dateien während der aktiven PHASE1-Verarbeitung.

**Eingaben:** JPG-Dateien verschoben aus TEMP_SD durch PHASE1.

**Prozess:** PHASE1 schreibt Scoring-Ergebnisse und Manifest. PHASE2 liest von hier für Archivierung.

**Ausgaben:** Verarbeitete Dateien mit SAVE/-Unterordner (Manifest, CSV).

**Manuelle Aktionen:** Keine während des aktiven Laufs.

**Lebenszyklus:** Dateien verbleiben hier bis PHASE2 die Archivierung abschließt.

**Fehlerfälle:** Bei Fehler bleibt das Verzeichnis erhalten und kann manuell inspiziert werden.

**Beispiel:** `TEMP_IMAGES/batch_20260808/2026-08-08_001.jpg`
