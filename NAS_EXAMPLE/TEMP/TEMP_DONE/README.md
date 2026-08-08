# TEMP_DONE – Abgeschlossene Batches

**Zweck:** Archivierungsverzeichnis für vollständig abgeschlossene Batches nach PHASE2.

**Eingaben:** Batches verschoben aus TEMP_IMAGES nach erfolgter Archivierung.

**Prozess:** PHASE2 verschiebt den Batch nach Erstellung und Verifizierung des ZIP-Archivs hierher.

**Ausgaben:** Batch-Verzeichnis mit SAVE/-Unterordner, ZIP-Archiv und Status-Dateien.

**Manuelle Aktionen:** Review-Entscheidungen werden in SAVE/review_record.json eingetragen.

**Lebenszyklus:** Batches verbleiben hier bis zur manuellen Bereinigung oder PHASE3-Transfer.

**Fehlerfälle:** Nur vollständig verifizierte Batches werden verschoben; bei Fehler bleibt der Batch in TEMP_IMAGES.

**Beispiel:** `TEMP_DONE/batch_20260808/SAVE/phase1_manifest.json`
