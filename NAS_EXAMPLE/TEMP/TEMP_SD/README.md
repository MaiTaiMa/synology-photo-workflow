# TEMP_SD – Eingangsverzeichnis für SD-Karten-Importe

**Zweck:** Temporäres Eingangsverzeichnis für frisch importierte JPG-Dateien von SD-Karten.

**Eingaben:** JPG-Dateien direkt aus der Kamera oder SD-Karte.

**Prozess:** PHASE1 liest alle stabilen JPG-Dateien aus diesem Verzeichnis, prüft die Dateiintegrität und verschiebt die Dateien nach TEMP_IMAGES.

**Ausgaben:** Leeres Verzeichnis nach erfolgreichem PHASE1-Lauf.

**Manuelle Aktionen:** Keine. Dateien werden ausschließlich vom Workflow gelesen.

**Lebenszyklus:** Dateien verbleiben hier bis PHASE1 sie verarbeitet. Nach dem Verschieben ist das Verzeichnis leer.

**Fehlerfälle:** Bei Stabilitätsfehler (Datei noch nicht vollständig geschrieben) bleibt die Datei und wird beim nächsten Lauf erneut geprüft.

**Beispiel:** `TEMP_SD/2026-08-08_001.jpg`
