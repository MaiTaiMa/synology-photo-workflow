# TEMP_ERROR – Fehlerquarantäne

**Zweck:** Quarantäneverzeichnis für Batches, die in einem undefinierten oder fehlerhaften Zustand enden.

**Eingaben:** Batches, die durch den Workflow als fehlerhaft klassifiziert wurden.

**Prozess:** Automatischer Transfer durch den Workflow bei `review_state_invalid` oder `quarantine`.

**Ausgaben:** Unveränderter Batch-Inhalt für manuelle Inspektion.

**Manuelle Aktionen:** Inspektion, Ursachenanalyse und manuelle Wiederherstellung erforderlich.

**Lebenszyklus:** Dateien verbleiben dauerhaft hier bis zur manuellen Intervention.

**Fehlerfälle:** Dieses Verzeichnis ist selbst ein Fehlerzustand; bei Transfer-Fehler wird geloggt.

**Beispiel:** `TEMP_ERROR/batch_20260808_error/SAVE/state.json`
