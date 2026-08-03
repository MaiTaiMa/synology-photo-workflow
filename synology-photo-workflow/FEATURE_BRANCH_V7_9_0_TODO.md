# Feature Branch v7.9.0 - Uebergabe-Notiz

Branch: `feature/v7.9.0-workunits-ai-contract`
Basiert auf: `Master_Implementierungsspezifikation_v7_9_0_FINAL.md`

## Status

Alle unten aufgefuehrten Dateien sind **neu** und wurden **noch nicht** in bestehende Ablaeufe
(`phases.py`, `planning.py`, Manual-Keep-UI, Face-Pipeline, CLI) verdrahtet. Sie sind eigenstaendig
lauffaehig/importierbar, haben aber keinen Aufrufer im bestehenden Code. Kein bestehendes Verhalten
wurde durch diesen Branch veraendert.

## Neue Dateien

- `app/work_units.py` - WorkUnit-Modell, Inventar-Fingerprinting, Resume-Prioritaet, `source_inventory_changed`-Schutz.
- `app/image_features.py` - `ImageFeatureService`: EXIF-korrigiertes Laden, Previews, Perceptual Hash, Embedding-Slot.
- `app/model_diagnostics.py` - gemeinsamer `ModelDiagnosis`-Vertrag und `reason_code`-Katalog.
- `app/model_download.py` - verwaltete Modellinstallation (HTTPS-Zwang, Host-Allowlist, SHA256-Pruefung).
- `app/model_runtime.py` - Laufzeit-Cache fuer lokale Modellverzeichnisse, kein Netzwerkzugriff.
- `app/inference_runtime.py` - optionaler Worker-Pool (`spawn`, max. 2 Worker), serieller Fallback.
- `app/clip_series_adapter.py` - CLIP-Serien-Embeddings, liefert nur Aehnlichkeit, keine Entscheidung.
- `app/eye_state_adapter_onnx.py` - ONNX-Adapter fuer Augenzustand, optionaler Score.
- `app/weight_assistant.py` - Gewichtsvorschlaege aus manuellen Entscheidungen, schreibt nichts selbst.
- `app/manual_keep_similarity.py` - technische Aehnlichkeit fuer Manual-Keep-Vorschlaege.
- `scripts/scan_producer_version_literals.py` - rein lesendes Diagnosewerkzeug fuer Versions-Drift.

## Offene Integrationsschritte (bewusst nicht in diesem Branch)

1. `work_units.py` in `planning.py`/`phases.py` als Ersatz oder Ergaenzung fuer die bisherige
   Batch-Auswahl verdrahten; Resume-Logik gegen bestehende `runtime/`-Statusdateien testen.
2. `ImageFeatureService`-Instanz pro Lauf in `phases.py` erzeugen und an Manual-Keep sowie an
   Adapter durchreichen, um doppeltes Laden/Decodieren zu vermeiden.
3. `ClipSeriesAdapter` und `EyeStateAdapterOnnx` hinter Feature-Flags in der bestehenden
   Scoring-Pipeline registrieren; `ModelDiagnosis`-Resultate im Report sichtbar machen.
4. `InferenceRuntime` optional unter den Adaptern einhaengen, die heute synchron laufen.
5. `weight_assistant.py` an ein neues, explizites CLI-Kommando anbinden (kein Auto-Apply).
6. `manual_keep_similarity.py` in die Manual-Keep-Ansicht integrieren, inklusive UI-Anzeige fuer
   `similarity_unavailable`.
7. Konfigurationsschema (`config.yaml`) um `models.clip_series`, `models.eye_state`,
   `models.download`, `workflow.work_unit_mode` und `workflow.images_per_work_unit` erweitern.
8. `scan_producer_version_literals.py` optional in eine CI-Pruefung einbinden.

## Sicherheitshinweise fuer die Integration

- Kein Adapter darf bei einem Fehler auf einen Zufalls- oder Default-Score zurueckfallen; stets
  `ModelDiagnosis.reason_code != 'ready'` respektieren und den Score als nicht verfuegbar behandeln.
- `work_units.py` darf ein Batch mit geaendertem Inventar niemals stillschweigend fortsetzen; das
  Ergebnis muss `source_inventory_changed` sein und einen manuellen Eingriff erfordern.
- Modellinstallation bleibt eine separate, bewusste Aktion (`model_download.py`); kein normaler
  Workflow-Lauf darf implizit ein Modell herunterladen.
