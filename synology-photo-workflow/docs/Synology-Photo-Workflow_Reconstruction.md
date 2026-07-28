# Rekonstruktionsspezifikation: Synology Photo Workflow mit KI-Culling

> **Zweck dieses Dokuments:** Diese Spezifikation rekonstruiert aus den vorliegenden Quellfragmenten ein deploybares, Docker-taugliches Python-Projekt für eine Synology NAS. Sie ist absichtlich als präziser Implementierungsauftrag für eine andere KI formuliert: Verhalten, Schnittstellen, Datenfluss, Sicherheitsregeln, Artefakte und Konfiguration müssen erhalten bleiben. Nicht vorhandene Artefakte (Dockerfile, Compose-Datei, Tests, Wrapper) sind als verbindlich zu erstellende Ergänzungen beschrieben.

## 1. Zielbild

Das Projekt verarbeitet Fotoimporte in einem Zwei-Phasen-Workflow. In **Phase 1** werden neue Kameraordner in einem Staging-Bereich stabilitätsgeprüft, umbenannt, RAW-Dateien separiert, JPGs KI-gestützt bewertet und in `keep`, `Review` oder `Rejected` einsortiert. Anschließend wandert der Ordner zur manuellen Sichtung nach `TEMPIMAGES`.

In **Phase 2** werden manuell freigegebene Ordner aus `TEMPDONE` verarbeitet: Nur JPGs, die noch unmittelbar im jeweiligen Ordner-Hauptverzeichnis liegen, gelten als aktiv. Nur ihre korrespondierenden ARW-Dateien bleiben erhalten, werden anschließend archiviert; nicht mehr aktive ARWs werden ausschließlich aus dem Unterordner `ARW` gelöscht.

Das System ist **kein** vollwertiger ML-Stack mit externen Cloud-Diensten. Die Bildqualität, Referenzähnlichkeit und Serienähnlichkeit werden lokal aus handgebauten Bildmerkmalen berechnet. Die optionale Gesichtserkennung verwendet lokale Face-Embeddings. Alle Zustände liegen in gemounteten Verzeichnissen und überleben Container-Neustarts.

## 2. Verbindlicher Projektumfang

Implementiere ein Python-3.11-Projekt, das folgende CLI bereitstellt:

```text
python app/photo_workflow.py --config config/config.yaml phase1 [--folder /pfad/zu/ordner]
python app/photo_workflow.py --config config/config.yaml phase2 [--folder /pfad/zu/ordner]
python app/photo_workflow.py --config config/config.yaml train-personal [--images-dir DIR] [--model-out DATEI]
python app/photo_workflow.py --config config/config.yaml rebuild-family-cache
```

CLI-Rückgabecode: `0` bei Erfolg, `1` bei jedem unbehandelten bzw. als fatal eingestuften Fehler. Pro Lauf muss immer eine JSON-Zusammenfassung versucht werden; stdout bleibt für Synology DSM Task Scheduler lesbar.

## 3. Rekonstruierte Architektur

```text
app/
  photo_workflow.py       # Orchestrator, CLI, Dateifluss, Culling, Reporting
  aesthetic.py            # lokale Bildfeatures, Basis-/Referenz-/Personal-Scores
  family_recognition.py   # Face-Referenzen, Cache, Matching, Personen-Metadaten
  series_culling.py       # Ähnlichkeitscluster und Serien-Entscheidungen
  metadata_writer.py      # Culling-Rating/Keywords per ExifTool
  metadata_rating.py      # XMP/JPG-Rating für gelabeltes Training lesen
  training.py             # Rating-Regression und referenzbasiertes Personenmodell
config/
  config.yaml             # produktive NAS-Konfiguration
  config-debug-local.yaml # lokale Entwicklungsumgebung
requirements.txt
Dockerfile
docker-compose.yml
scripts/run-phase1.sh
scripts/run-phase2.sh
README.md
tests/
```

### Abhängigkeitsgraph

```text
photo_workflow
 ├─ aesthetic: generische Bewertung, Feature-Extraktion, Referenzprofil, Personal-Score
 ├─ family_recognition: Familien-Score, Schutzregel, Personen-Tags
 ├─ series_culling: Nachbearbeitung der Score-Entscheidung
 ├─ metadata_writer: XMP-Rating und Culling-Keywords
 └─ training: Personalmodell laden/inkrementell erzeugen, explizites Rating-Training
      └─ metadata_rating: Ratings aus Bild/XMP lesen
```

## 4. Ordner- und Datenvertrag

Alle produktiv veränderbaren Pfade müssen bei `safety.require_paths_within_base_dir: true` innerhalb von `paths.base_dir` liegen.

```text
BASE_DIR/
  TEMPSD/                     # Eingang: neue Kameraordner
    20250707/                 # Beispiel: Rohname, acht Ziffern
  TEMPIMAGES/                 # Ergebnis aus Phase 1, manuelle Sichtung
    2025-07-07/
      ARW/
      SAVE/
        2025-07-07ALLJPG.zip
        cullingscores.csv
        cullingsummary.json
      Review/
      Rejected/
      .DONE
  TEMPDONE/                   # Benutzer kopiert/verschiebt finale Auswahl hierher
    2025-07-07/
      ARW/
      SAVE/
      ... aktive JPGs im Hauptordner ...
```

### Semantik

| Pfad/Datei | Bedeutung und Pflichtverhalten |
|---|---|
| `TEMPSD/<kameraordner>` | Eingang. Nur valide achtstellige Ordnernamen werden verarbeitet; bereits mit `.DONE` markierte Ordner werden nur verschoben/gemerged. |
| Hauptordner eines Bildsatzes | Ausschließlich hier liegende JPGs sind aktiv/final. JPGs in `Review` und `Rejected` zählen **nicht** als aktive Auswahl. |
| `ARW/` | Enthält zugehörige Sony-RAW-Dateien. Löschen ist ausschließlich dort erlaubt. |
| `SAVE/<datum>ALLJPG.zip` | Vollständiges Backup aller ursprünglichen JPGs vor dem Culling. |
| `SAVE/cullingscores.csv` | Pro JPG alle Teil- und Endwerte, Entscheidungen, Serien- und Metadatenstatus. |
| `SAVE/cullingsummary.json` | Kompakte Culling-Statistik. |
| `.DONE` | Phase-1-Marker, der vor dem Verschieben erzeugt wird, wenn konfiguriert. |
| `.PROCESSED` | Hash-Marker für Phase 2; vermeidet Wiederholung bei unverändertem Ordner. |

## 5. Phase 1: Import und Culling

1. Erzeuge erforderliche Stammordner. Ermittele Eingangsordner oder den mit `--folder` übergebenen Ordner.
2. Akzeptiere nur Rohordner mit `^\d{8}$`; Ordner im Done-Format `^\d{4}-\d{2}-\d{2}.*$` werden nicht erneut vorbereitet.
3. Falls kein `.DONE` vorhanden ist, erstelle zwei Dateisnapshots im Abstand von `workflow.wait_time_seconds`. Sind relative Datei-/Größenlisten verschieden, überspringe den Ordner als noch laufenden Transfer.
4. Rekonstruiere den Namen. Im Modus `legacy_bash` wird aus dem Zeichen an `year_digit_index` mit `decade_prefix` das Jahr gebaut; bei `20250707`, Prefix `202`, Index `3` entsteht `2025-07-07`. Im Modus `full_year` ist der Eingangsname bereits `YYYYMMDD`.
5. Verschiebe nur ARW/`arw` im Top-Level nach `ARW/`. Erzeuge `SAVE/`.
6. Zippe alle zu diesem Zeitpunkt im Top-Level liegenden JPG/JPEG in `<ordner>ALLJPG.zip`, bevor irgendein Culling-Dateiverschieben erfolgt.
7. Führe das Culling nur für JPG/JPEG im Top-Level aus. PNGs dürfen als Referenzbilder dienen, sind aber keine Culling-Kandidaten.
8. Schreibe `.DONE`; verschiebe/merge den Ordner nach `TEMPIMAGES/<name>`.

### Merge- und ZIP-Verhalten

Wenn das Ziel bereits existiert, merge rekursiv. Bei Kollisionen bzw. Fehlern fällt `merge_then_fallback` auf ein freies Ziel `<name>MERGE`, `<name>MERGE2` usw. zurück. Niemals still überschreiben.

ZIP-Artefakte werden als `ALLJPG`, `SORTARW` oder `UNSORTED` klassifiziert. Kollidierende Namen erhalten kollisionssichere Namen wie `...ALLJPGEXTRA2.zip`, `...SORTARWEXTRA2.zip` bzw. `...UNSORTED1.zip`. Jede Umbenennung wird geloggt und in `zipconflicts` der Run-Summary geschrieben.

## 6. Culling-Pipeline

Für jedes Top-Level-JPG wird ein Ergebnisdatensatz aufgebaut. Werte liegen normiert in `[0,1]`; fehlende optionale Werte bleiben `null`, nicht `0`.

### Teil-Scores

| Score | Implementierung |
|---|---|
| `generic_score` | Auflösung, Dateigröße, Kantenvarianz/Schärfe und Nähe zu üblichen Seitenverhältnissen. |
| `sharp_score` | Logarithmisch normierte Varianz eines `FIND_EDGES`-Bildes. |
| `aesth_score` | Kontrast, Sättigung, ausgewogene Helligkeit und Schärfe. |
| `exposure_score` | Abzug für über-/unterbelichtete Pixel und Abweichung der mittleren Luminanz von 0,5. |
| `eye_score` | Optional; Eye Aspect Ratio aus Face-Landmarks. `null`, wenn keine Face-Library/keine Gesichter. |
| `reference_score` | Kosinusähnlichkeit des einfachen 32x32-RGB/Grau/Kanten-Embeddings gegen das mittlere Referenzprofil. |
| `personal_score` | Bewertung durch persönliches Modell (Rating-Regression oder Prototypmodell). |
| `family_score` | Summe konfigurierte Personen-Gewichte erkannter Personen, maximal 1.0. |

Der `base_score` ist die dynamisch normalisierte gewichtete Summe aus `sharp`, `aesth`, `exposure` und optional `reference`. Augen gehören bewusst nicht in den Base-Score.

Der finale Score ist die dynamisch normalisierte gewichtete Summe:

```text
final = norm_weighted(base_score, eye_score?, personal_score?, family_score?)
```

Bei fehlenden Komponenten werden ausschließlich die Gewichte vorhandener Komponenten auf 1.0 normiert. Niemals darf ein fehlender Face- oder Personal-Score den Gesamtscore künstlich absenken.

### Grundentscheidung und Familienregel

- `final_score >= keep_threshold`: `keep`
- `final_score < reject_threshold`: `reject`
- sonst: `review`
- Ist ein Foto aufgrund einer erkannten Familie geschützt, wird ein sonstiges `reject` mindestens zu `review`.

Danach wendet die Serienlogik eine korrigierende Entscheidung an. Bei aktiviertem Dateiverschieben bleiben `keep`-Dateien im Hauptordner, `review` wandert nach `Review/`, `reject` nach `Rejected/`.

## 7. Serienerkennung

Erstelle pro Bild ein L2-normalisiertes Embedding aus RGB-Mittelwert/-Standardabweichung, Grauwerten und Kantenbild eines `preview_size x preview_size` Vorschaubildes. Distanz ist `1 - dot(a,b)`.

Bilde verbundene Komponenten aller Bildpaare mit Distanz `<= cluster_eps`; nur Gruppen ab `min_samples` bilden Serien. Das ist eine einfache Union-Find-Clusterung, keine externe DBSCAN-Abhängigkeit.

Je Serie: nach `final_score` absteigend sortieren. Das beste Bild bleibt `keep`, wird bei Grundentscheidung `review` um eine Klasse befördert und bei `reject` zu `review` gerettet. Nichtbeste Bilder innerhalb `review_margin` werden `review`; weiter entfernte Bilder werden gemäß `demote_non_best_to` weich (`review`) oder hart um eine Klasse abgewertet. Der Familien-Schutz verhindert auch hier `reject`.

Sterne kommen ausschließlich vom numerischen Endscore und den `star_rating_bands`, nicht direkt von `keep/review/reject`.

## 8. Familienerkennung

Referenzen liegen als `family_faces/<Person>/*.{jpg,jpeg,png}` vor. Pro Person werden höchstens `max_reference_images_per_person` Bilder berücksichtigt; eine Person ist erst ab `min_reference_images_per_person` erfolgreich geladenen Encodings gültig.

Nutze das Paket `face_recognition` (Importname `face_recognition`; im alten Code ist die Schreibweise teilweise beschädigt und muss korrigiert werden). Für jedes Referenzbild wird das erste Face-Encoding gespeichert. Der persistente Cache besteht aus:

```text
models/family_faces/
  family_encodings.pkl
  family_encodings.meta.json
  family_index.json
  last_rebuild_report.json
```

Der Cache ist gültig, wenn Referenzpfad, Limit sowie je Referenz Datei, Größe und `mtime_ns` übereinstimmen. Bei Änderung oder erzwungenem Rebuild erzeugen. Pro Zielbild wird jede Face-Encoding gegen alle Personen-Encodings verglichen; die kleinste Distanz unter `match_tolerance` gewinnt.

Bei Match schreibe mindestens Tags `familymatchtrue` und `person<Person>`. Mit `write_native_tags` müssen diese als XMP-dc:Subject und IPTC:Keywords per ExifTool in die JPG-Datei geschrieben werden. Face-Regionen werden im Ergebnisdatensatz geführt; eine verlässliche native Regions-Schreibimplementierung ist nicht aus den Fragmenten vorhanden und darf nur als optionale Erweiterung erfolgen, ohne den Workflow zu blockieren.

## 9. Persönliches Modell und Training

Es existieren zwei komplementäre Modellarten:

1. **Explizites Rating-Training** (`train-personal`): Rekursiv JPGs lesen, deren Sterne-Rating aus Bild- oder XMP-Metadaten vorhanden ist. Features: Bias, `generic_score`, Megapixel, Aspect-Score, Portrait-Flag, Dateigröße, Kantenvarianz. Zielwert ist `rating / 5`. Löse lineare Least Squares und schreibe JSON-Modell mit Gewichten, `scoreoffset`, `scorescale` und `trainingrows`. Mindestens `training.min_labeled_images` gelabelte Bilder erforderlich; zusätzlich CSV-Export der gelesenen Labels.
2. **Automatisches Prototypmodell**: Bei mindestens `personal_scoring.min_reference_images` Sample-Bildern berechne Mittelwert und Standardabweichung derselben Featuregruppe. Speichere `modeltype: prototype_v1`. Der Score ist `1 - mean(min(1, abs(z)/2.5))` über verfügbare Merkmale.

Der Autocache vergleicht bei jedem Lauf Quelle, Rekursiv-Option sowie Datei, Größe und `mtime_ns`. Bei Änderung und `auto_train_on_change: true` neu erzeugen. Beide Modellformate müssen von `aesthetic.personal_model_score` lesbar sein.

`metadata_rating.py` muss robust Ratings lesen: bevorzugt Sidecar `<foto>.xmp` sowie eingebettete XMP-Informationen über ExifTool, wenn verfügbar. Akzeptiere numerische Werte 0–5; ungültige Werte ergeben `None`. Ein fehlendes ExifTool darf Training nicht abstürzen lassen, solange Sidecars lesbar sind.

## 10. Metadaten und Ausgaben

Nach der endgültigen Serienentscheidung werden Metadaten auf dem endgültigen Dateipfad geschrieben. `metadata_writer.py` nutzt `exiftool` mit `-overwrite_original`, sofern `keep_backup: false`.

- XMP Rating: `-XMP:Rating=<0..5>`
- XMP Subject: wiederholt `-XMP-dc:Subject+=<keyword>` (korrekte append-Syntax verwenden)
- Keywordschema `namespaced_v1`: mindestens `workflowaicull`, `decisionkeep|review|reject`, `decisionreason...`, `rating<N>stars`, Serienfelder, `familymatch...`, `familyprotectedtrue`, `person<Name>`.
- Score-Bänder (`scorebandfinalXXtoYY` usw.) optional, rohe Scores nur bei `write_raw_scores_to_keywords: true`; CSV/JSON enthalten sie immer.

`cullingscores.csv` enthält mindestens:

```text
file,generic_score,base_score,sharp_score,aesth_score,exposure_score,eye_score,
reference_score,personal_score,family_score,final_score,scoredecision,scorereason,
decision,decisionreason,seriesid,seriessize,seriesrank,seriesbest,
seriesmargintobest,starrating,protectedbyfamilyrule,detectedpeople,facestatus,
familymetadatawritten,familymetadatastatus,cullingmetadatawritten,
cullingmetadatastatus,finalpath
```

`cullingsummary.json` dokumentiert Zeit, Gesamtzahl, keep/review/reject, Schwellen, Serienstatistik, Family-Cache-Status und Anzahl geschriebener Metadaten.

## 11. Phase 2: RAW-Bereinigung

Für jeden Done-Ordner (oder dessen gültige Unterordner):

1. Wenn `ARW/` fehlt: überspringen und loggen.
2. Erzeuge aus relativen JPG-Dateinamen und Größen im Hauptordner einen stabilen Hash. Ist `.PROCESSED` identisch, überspringen.
3. Bewahre bereits im `ARW/` vorhandene ZIPs kollisionssicher nach `SAVE/`.
4. Für jede Top-Level-ARW: Existiert kein Top-Level-JPG/JPEG gleichen Basenamens, lösche die ARW. Die Schutzprüfung muss den Pfad im `ARW`-Teilbaum und innerhalb `base_dir` erzwingen.
5. Zippe verbleibende ARWs nach `SAVE/<ordner>SORTARW.zip`, nutze Konfliktlogik; entferne danach `ARW/` rekursiv.
6. Schreibe den aktuellen Hash nach `.PROCESSED`.

**Wichtig:** Kein automatisches Löschen in `Review`, `Rejected`, `SAVE`, am Top-Level oder außerhalb von `ARW`. Symlinks werden nicht verfolgt und bei Scans ignoriert.

## 12. Konfiguration

Die vom Auftraggeber gelieferte Konfiguration ist die fachliche Referenz. Verwende für Docker jedoch Containerpfade statt Hostpfaden. Die Pfade müssen als Variablen/Volumes übersteuerbar sein.

```yaml
paths:
  base_dir: /data/TEMP
  temp_sd: /data/TEMP/TEMP_SD
  temp_images: /data/TEMP/TEMP_IMAGES
  temp_done: /data/TEMP/TEMP_DONE
  log_file: /data/TEMP/process.log
  error_log: /data/TEMP/error.log
  lock_file: /data/TEMP/.script.lock
  personal_model: /models/personal/user_taste_model.json
workflow:
  wait_time_seconds: 60
  stale_lock_seconds: 43200
  merge_strategy: merge_then_fallback
  create_done_marker_before_move: true
  date_reconstruction: {mode: legacy_bash, decade_prefix: '202', year_digit_index: 3}
culling:
  enabled: true
  move_files: true
  create_review_folder: true
  create_rejected_folder: true
  keep_threshold: 0.65
  reject_threshold: 0.35
  weights: {generic: 0.55, personal: 0.45} # Legacy/kompatibel; finale Formel nutzt component_weights
  component_weights: {base_score: 0.55, eye_score: 0.10, personal_score: 0.20, family_score: 0.15}
  base_weights: {sharp: 0.36, aesth: 0.36, exposure: 0.18, reference: 0.10}
  eye_detection: {enabled: true}
  reference_scoring:
    enabled: true
    folder: /training/sample_images
    recursive: false
    preview_size: 32
    cache_enabled: true
    cache_dir: /models/reference_scoring
    force_cache_rebuild: false
  star_rating_bands: {5: 0.9, 4: 0.75, 3: 0.6, 2: 0.4, 1: 0.2, 0: 0.0}
training:
  sample_images_dir: /training/sample_images
  exported_labels_dir: /training/exported_labels
  runs_dir: /training/runs
  min_labeled_images: 20
safety:
  require_paths_within_base_dir: true
  follow_symlinks: false
  never_delete_outside_arw_dir: true
reporting:
  write_json_summary: true
  json_summary_dir: /data/TEMP/run_summaries
  stdout_mode: scheduler_mail
family_recognition:
  enabled: true
  reference_dir: /family_faces
  protect_detected_family: true
  score_boost_weight: 0.2 # Dokumentieren; der vorliegende Code nutzt primär person_weights
  write_native_tags: true
  write_face_regions: true
  exiftool_path: exiftool
  match_tolerance: 0.6
  default_person_weight: 0.35
  max_reference_images_per_person: 200
  person_weights: {Vater: 0.35, Mutter: 0.35, Kind1: 0.55, Kind2: 0.55, Oma: 0.3, Opa: 0.3}
  cache_enabled: true
  cache_dir: /models/family_faces
  cache_rebuild_mode: incremental
  force_cache_rebuild: false
  min_reference_images_per_person: 3
series_detection:
  enabled: true
  cluster_eps: 0.18
  min_samples: 2
  preview_size: 32
  review_margin: 0.03
  demote_non_best_to: review
metadata_culling:
  enabled: true
  write_rating: true
  write_keywords: true
  keep_backup: false
  exiftool_path: exiftool
  keyword_schema: namespaced_v1
  write_score_bands: true
  write_raw_scores_to_keywords: true
personal_scoring:
  source_dir: /training/sample_images
  model_path: /models/personal/user_taste_model.json
  cache_dir: /models/personal
  enabled: true
  cache_enabled: true
  cache_rebuild_mode: incremental
  auto_train_on_change: true
  recursive: false
  min_reference_images: 5
```

Beim Laden Defaults rückwärtskompatibel ergänzen. Validiere zwingend: `0 <= reject_threshold <= keep_threshold <= 1`, alle Gewichte nichtnegativ, Datumsmodus gültig, `decade_prefix` im Legacy-Modus exakt drei Ziffern, Pfade innerhalb `base_dir` (außer explizit read-only Modell-/Referenzmounts, falls dies dokumentiert übersteuert wird).

## 13. Python-Abhängigkeiten

`requirements.txt` soll mindestens enthalten:

```text
PyYAML>=6.0
numpy>=1.26
Pillow>=10.0
face-recognition>=1.3.0
```

Systempakete im Docker-Image:

```text
exiftool
libgl1
libglib2.0-0
build-essential
cmake
libopenblas-dev
```

`face-recognition` zieht `dlib` nach; auf Synology/ARM ist ein vorgebautes, plattformgerechtes Image oder ein Build-Stage nötig. Die Anwendung muss bei nicht installierbarer Face-Library funktionsfähig bleiben: Familien- und Eye-Score dann `null`/deaktiviert, Logs und Summary erhalten Status `face_library_missing`.

## 14. Docker-Deployment

### Dockerfile-Anforderungen

- Basis: `python:3.11-slim-bookworm` (x86_64); für ARM64 separaten Build testen.
- Systempakete installieren, nicht als root ausführen, `exiftool` im `PATH`.
- Anwendung nach `/app`, Startverzeichnis `/app`, `PYTHONUNBUFFERED=1`.
- Kein `CMD`, das automatisch destructive Phase 2 startet. Standard kann `--help` sein.

### docker-compose.yml

```yaml
services:
  photo-workflow:
    build: .
    image: synology-photo-workflow:latest
    user: "1026:100"              # an NAS-UID/GID anpassen
    read_only: false
    volumes:
      - /volume1/photo-workflow/TEMP:/data/TEMP
      - /volume1/docker/synology-photo-workflow/models:/models
      - /volume1/docker/synology-photo-workflow/training:/training
      - /volume1/docker/synology-photo-workflow/family_faces:/family_faces:ro
      - ./config:/app/config:ro
    command: ["python", "app/photo_workflow.py", "--help"]
```

Der DSM Task Scheduler ruft pro Lauf einen kurzlebigen Container auf, zum Beispiel:

```bash
docker compose run --rm photo-workflow python app/photo_workflow.py --config /app/config/config.yaml phase1
docker compose run --rm photo-workflow python app/photo_workflow.py --config /app/config/config.yaml phase2
```

Phase 1 und Phase 2 besser als getrennte Scheduler-Tasks ausführen. Beide verwenden dasselbe Lockfile, weshalb parallele Läufe verweigert werden.

## 15. Logging, Locking, Fehlertoleranz

Nutze UTC-ISO-Zeitstempel für JSON und klar lesbare lokale Zeit in `process.log`/`error.log`. Schreibe Ereignisse zusätzlich auf stdout bzw. stderr.

Das Lockfile ist JSON mit mindestens PID und `started_at`. Existiert es, darf ein Lauf nur starten, wenn es älter als `stale_lock_seconds` ist; dann entfernen. Sonst mit klarer Fehlermeldung abbrechen. Lockfile im `finally` entfernen.

Die Scheduler-Ausgabe muss Startblock (Version, Command, Pfade) und Endblock enthalten: Status, gefundene/verarbeitete/verschobene/übersprungene Ordner, Fehlerzahl, Logpfade, JSON-Summary-Pfad, Start/Ende. Fehler einzelner optionaler Komponenten (ExifTool, Face-Library, beschädigtes Bild) müssen als Status erfasst werden, nicht den gesamten Import abbrechen. Fehler in Dateibewegung, Safety, Locking oder Konfigurationsvalidierung sind fatal.

## 16. Rekonstruierte Skriptzuordnung

| Geliefene Datei | Zielname | Verantwortlichkeit | Öffentliche Kernfunktionen |
|---|---|---|---|
| `photo_workflow-5.txt` | `app/photo_workflow.py` | Hauptworkflow/CLI, Phase 1/2, Lock, sichere Moves, ZIPs, Culling, Run-Reports | `load_config`, `file_lock`, `make_date_name`, `merge_or_move_folder`, `cull_folder`, `run_phase1`, `run_phase2`, `main` |
| `aesthetic.txt` | `app/aesthetic.py` | Bildfeatures, generischer/Basis/Referenz/Eye/Personal Score | `extract_features`, `generic_aesthetic_score`, `base_score_components`, `weighted_base_score`, `ensure_reference_profile`, `personal_model_score` |
| `family_recognition-2.txt` | `app/family_recognition.py` | Referenz-Encoding, Cache, Matching, Family-Tags | `load_family_model`, `rebuild_family_cache`, `detect_family_members`, `write_native_tags` |
| `series_culling-7.txt` | `app/series_culling.py` | Visuelle Seriencluster und Endentscheidungen | `cluster_series`, `rating_for_score`, `apply_series_culling` |
| `metadata_writer-4.txt` | `app/metadata_writer.py` | Culling-Metadaten via ExifTool | `build_culling_keywords`, `write_culling_metadata` |
| `metadata_rating-3.txt` | `app/metadata_rating.py` | Bewertungen für explizites Training extrahieren | `read_rating` |
| `training-8.txt` | `app/training.py` | Rating-Training, Personal-Prototyp, Cache/Reports | `train_from_directory`, `load_or_rebuild_personal_model`, `build_personal_model_from_directory` |
| `requirements-6.txt` | `requirements.txt` | Python-Runtime-Abhängigkeiten | oben konsolidieren |
| `README-9.md` | `README.md` | Betriebskonzept, DSM, Ordnersemantik, Sicherheitsregeln | diese Spezifikation überführen |
| `config-debug-local-11.txt` | `config/config-debug-local.yaml` | Lokale Testpfade und komplette Schalter | als Template mit relativen/Host-Pfaden |
| `config-10.txt` + Nutzer-Konfig | `config/config.yaml` | Produktive Konfigurationsreferenz | Containerpfade verwenden |

## 17. Bekannte Reparaturen

Die bereitgestellten Textfragmente haben beim Export diverse Syntaxschäden (fehlende Unterstriche, fehlende Punkte/Anführungszeichen, z. B. `from future import annotations`). Nicht blind übernehmen; anhand dieser Spezifikation in idiomatisches, typisiertes, testbares Python übersetzen.

Zusätzlich sind folgende fachliche Inkonsistenzen bewusst aufzulösen:

- Die Config nennt `family_recognition.score_boost_weight`, das Fragment berechnet den Familienwert hingegen direkt aus `person_weights`. Implementiere entweder **nur** die gewichtete Personensumme und dokumentiere `score_boost_weight` als Legacy, oder nutze sie explizit als multiplikativen/zusätzlichen Boost. Bevorzugt: Legacy-Feld akzeptieren, aber nicht doppelt gewichten.
- `culling.weights.generic/personal` ist Legacy; maßgeblich ist `component_weights`.
- ExifTool-Append-Syntax muss korrigiert und idempotent umgesetzt werden; Keywords nicht bei jedem Lauf unkontrolliert duplizieren.
- `write_face_regions` darf nicht behaupten, IPTC/XMP-Gesichtsregionen zu schreiben, wenn dies nicht implementiert und getestet ist.
- Alle Pfadprüfungen müssen vor `resolve()`/Move/Delete Symlinks sicher behandeln; keine indirekten Löschpfade.

## 18. Mindesttests und Akzeptanzkriterien

Erstelle pytest-Tests mit temporären Verzeichnissen und kleinen erzeugten JPGs. Mindestens:

- Datumsrekonstruktion `20250707 -> 2025-07-07`, `full_year`, ungültiger Prefix/Index.
- Stabilitätscheck, Lock aktiv/stale, Safety außerhalb Base und Delete außerhalb `ARW`.
- Phase 1: ARW-Verschiebung, ALLJPG-ZIP vor Culling, `.DONE`, Zielmove; `Review`/`Rejected`.
- Phase 2: Nur aktives Top-Level-JPG bewahrt passende ARW; ARW ohne Hauptordner-JPG wird gelöscht; Review-JPG genügt nicht; `.PROCESSED` verhindert Wiederholung.
- ZIP-Namenskollisionen und Merge-Fallback.
- Dynamische Regewichtung bei fehlendem Eye/Family/Personal-Score.
- Serienbeste, nahe Serie, harte/weiche Degradierung und Family-Schutz.
- Referenz-/Personal-/Family-Cache: Wiederverwendung, Rebuild bei Dateistatusänderung.
- Fehlendes ExifTool und fehlende Face-Library: nicht fatal, Status dokumentiert.
- CSV-Spalten, JSON-Summary und Scheduler-Output.

Vor produktivem Einsatz muss ein Test nur mit Kopien echter Fotoordner erfolgen. Die erste produktive Phase 2 sollte nur nach manueller Kontrolle von `TEMPIMAGES` und einem Backup der ARWs stattfinden.

## 19. Implementierungsreihenfolge

1. Projektgerüst, Config-Validierung, sichere Dateihilfen, Logging/Lock und Tests.
2. Phase-1/Phase-2-Dateifluss inklusive ZIP- und Merge-Schutz, zunächst ohne KI.
3. Lokale Bildfeatures, Score-Formel, CSV/JSON und Serienlogik.
4. ExifTool-Integration mit Fehlerdegradierung.
5. Referenz- und Personalmodell/Caches.
6. Familienerkennung/Caches und Tagging.
7. Docker/Compose, Synology-Wrapper, README und End-to-End-Test.

Die Implementierung ist fertig, wenn sie den Dateivertrag, die Sicherheitsinvarianten, CLI-Kommandos, Artefaktnamen und Konfigurationsschalter dieser Spezifikation reproduzierbar erfüllt.


# Anhang A: Dateibasiertes Implementierungspaket

Dieser Anhang macht die Spezifikation für eine implementierende KI unmittelbar zuordenbar. **Jeder folgende Block gehört exakt in die angegebene Datei.** Eine KI soll diese Dateien anlegen, die beschriebenen Signaturen beibehalten und den Code nach den detaillierten Kapiteln 1 bis 19 implementieren. Dateinamen im ursprünglich gelieferten Export enthielten Bindestriche und Zähler; im rekonstruierten Projekt gelten ausschließlich die hier aufgeführten Zielpfade.

## A.1 Verbindlicher Dateibaum

```text
synology-photo-workflow/
├── app/
│   ├── __init__.py
│   ├── photo_workflow.py
│   ├── aesthetic.py
│   ├── family_recognition.py
│   ├── series_culling.py
│   ├── metadata_writer.py
│   ├── metadata_rating.py
│   └── training.py
├── config/
│   ├── config.yaml
│   └── config-debug-local.yaml
├── scripts/
│   ├── run-phase1.sh
│   └── run-phase2.sh
├── tests/
│   ├── test_photo_workflow.py
│   ├── test_aesthetic.py
│   ├── test_family_recognition.py
│   ├── test_series_culling.py
│   ├── test_metadata.py
│   └── test_training.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## A.2 `app/__init__.py`

**Pfad:** `app/__init__.py`  
**Herkunft:** Neu, für zuverlässige Python-Paketimporte in Tests und Container.

```python
"""Synology Photo Workflow: lokale Fotoauswahl und RAW-Verwaltung."""

__version__ = "1.3-reconstructed"
```

## A.3 `config/config.yaml`

**Pfad:** `config/config.yaml`  
**Zweck:** produktive Docker-/NAS-Konfiguration. Die folgenden Inhalte sind die kanonische Container-Variante der vom Nutzer gelieferten Konfiguration.

```yaml
paths:
  base_dir: /data/TEMP
  temp_sd: /data/TEMP/TEMP_SD
  temp_images: /data/TEMP/TEMP_IMAGES
  temp_done: /data/TEMP/TEMP_DONE
  log_file: /data/TEMP/process.log
  error_log: /data/TEMP/error.log
  lock_file: /data/TEMP/.script.lock
  personal_model: /models/personal/user_taste_model.json

workflow:
  wait_time_seconds: 60
  stale_lock_seconds: 43200
  merge_strategy: merge_then_fallback
  create_done_marker_before_move: true
  date_reconstruction:
    mode: legacy_bash
    decade_prefix: '202'
    year_digit_index: 3

culling:
  enabled: true
  move_files: true
  create_review_folder: true
  create_rejected_folder: true
  keep_threshold: 0.65
  reject_threshold: 0.35
  weights:
    generic: 0.55
    personal: 0.45
  component_weights:
    base_score: 0.55
    eye_score: 0.10
    personal_score: 0.20
    family_score: 0.15
  base_weights:
    sharp: 0.36
    aesth: 0.36
    exposure: 0.18
    reference: 0.10
  eye_detection:
    enabled: true
  reference_scoring:
    enabled: true
    folder: /training/sample_images
    recursive: false
    preview_size: 32
    cache_enabled: true
    cache_dir: /models/reference_scoring
    force_cache_rebuild: false
  star_rating_bands:
    5: 0.90
    4: 0.75
    3: 0.60
    2: 0.40
    1: 0.20
    0: 0.00

training:
  sample_images_dir: /training/sample_images
  exported_labels_dir: /training/exported_labels
  runs_dir: /training/runs
  min_labeled_images: 20

safety:
  require_paths_within_base_dir: true
  follow_symlinks: false
  never_delete_outside_arw_dir: true

reporting:
  write_json_summary: true
  json_summary_dir: /data/TEMP/run_summaries
  stdout_mode: scheduler_mail

family_recognition:
  enabled: true
  reference_dir: /family_faces
  protect_detected_family: true
  score_boost_weight: 0.20
  write_native_tags: true
  write_face_regions: true
  exiftool_path: exiftool
  match_tolerance: 0.60
  default_person_weight: 0.35
  max_reference_images_per_person: 200
  person_weights:
    Vater: 0.35
    Mutter: 0.35
    Kind1: 0.55
    Kind2: 0.55
    Oma: 0.30
    Opa: 0.30
  cache_enabled: true
  cache_dir: /models/family_faces
  cache_rebuild_mode: incremental
  force_cache_rebuild: false
  min_reference_images_per_person: 3

series_detection:
  enabled: true
  cluster_eps: 0.18
  min_samples: 2
  preview_size: 32
  review_margin: 0.03
  demote_non_best_to: review

metadata_culling:
  enabled: true
  write_rating: true
  write_keywords: true
  keep_backup: false
  exiftool_path: exiftool
  keyword_schema: namespaced_v1
  write_score_bands: true
  write_raw_scores_to_keywords: true

personal_scoring:
  source_dir: /training/sample_images
  model_path: /models/personal/user_taste_model.json
  cache_dir: /models/personal
  enabled: true
  cache_enabled: true
  cache_rebuild_mode: incremental
  auto_train_on_change: true
  recursive: false
  min_reference_images: 5
```

## A.4 `config/config-debug-local.yaml`

**Pfad:** `config/config-debug-local.yaml`  
**Herkunft:** `config-debug-local-11.txt`  
**Zweck:** vollständige lokale Entwicklungsvariante. Nur die Wurzelpfade unterscheiden sich von `config.yaml`; alle fachlichen Schalter bleiben gleich.

```yaml
paths:
  base_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP
  temp_sd: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/TEMP_SD
  temp_images: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/TEMP_IMAGES
  temp_done: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/TEMP_DONE
  log_file: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/process.log
  error_log: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/error.log
  lock_file: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/.script.lock
  personal_model: /home/matzethias/Programme/synology_photo_workflow_delivery/project/models/personal/user_taste_model.json

# Alle folgenden Abschnitte müssen byteinhaltlich/fachlich config.yaml entsprechen,
# mit lokalen Pfaden für model, training, family_faces, reference cache und summaries:
workflow: {wait_time_seconds: 60, stale_lock_seconds: 43200, merge_strategy: merge_then_fallback, create_done_marker_before_move: true, date_reconstruction: {mode: legacy_bash, decade_prefix: '202', year_digit_index: 3}}
culling:
  enabled: true
  move_files: true
  create_review_folder: true
  create_rejected_folder: true
  keep_threshold: 0.65
  reject_threshold: 0.35
  weights: {generic: 0.55, personal: 0.45}
  component_weights: {base_score: 0.55, eye_score: 0.10, personal_score: 0.20, family_score: 0.15}
  base_weights: {sharp: 0.36, aesth: 0.36, exposure: 0.18, reference: 0.10}
  eye_detection: {enabled: true}
  reference_scoring:
    enabled: true
    folder: /home/matzethias/Programme/synology_photo_workflow_delivery/project/training/sample_images
    recursive: false
    preview_size: 32
    cache_enabled: true
    cache_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/models/reference_scoring
    force_cache_rebuild: false
  star_rating_bands: {5: 0.9, 4: 0.75, 3: 0.6, 2: 0.4, 1: 0.2, 0: 0.0}
training:
  sample_images_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/training/sample_images
  exported_labels_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/training/exported_labels
  runs_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/training/runs
  min_labeled_images: 20
safety: {require_paths_within_base_dir: true, follow_symlinks: false, never_delete_outside_arw_dir: true}
reporting:
  write_json_summary: true
  json_summary_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/example_nas_environment/TEMP/run_summaries
  stdout_mode: scheduler_mail
family_recognition:
  enabled: true
  reference_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/family_faces
  protect_detected_family: true
  score_boost_weight: 0.2
  write_native_tags: true
  write_face_regions: true
  exiftool_path: exiftool
  match_tolerance: 0.6
  default_person_weight: 0.35
  max_reference_images_per_person: 200
  person_weights: {Vater: 0.35, Mutter: 0.35, Kind1: 0.55, Kind2: 0.55, Oma: 0.3, Opa: 0.3}
  cache_enabled: true
  cache_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/models/family_faces
  cache_rebuild_mode: incremental
  force_cache_rebuild: false
  min_reference_images_per_person: 3
series_detection: {enabled: true, cluster_eps: 0.18, min_samples: 2, preview_size: 32, review_margin: 0.03, demote_non_best_to: review}
metadata_culling: {enabled: true, write_rating: true, write_keywords: true, keep_backup: false, exiftool_path: exiftool, keyword_schema: namespaced_v1, write_score_bands: true, write_raw_scores_to_keywords: true}
personal_scoring:
  source_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/training/sample_images
  model_path: /home/matzethias/Programme/synology_photo_workflow_delivery/project/models/personal/user_taste_model.json
  cache_dir: /home/matzethias/Programme/synology_photo_workflow_delivery/project/models/personal
  enabled: true
  cache_enabled: true
  cache_rebuild_mode: incremental
  auto_train_on_change: true
  recursive: false
  min_reference_images: 5
```

## A.5 `requirements.txt`

**Pfad:** `requirements.txt`  
**Herkunft:** `requirements-6.txt`, durch die tatsächlichen Imports ergänzt.

```text
PyYAML>=6.0,<7
numpy>=1.26,<3
Pillow>=10.0,<12
face-recognition>=1.3.0,<2
pytest>=8.0,<9
```

`pytest` ist nur für Entwicklungs-/Testimages nötig und kann bei einem getrennten Produktionsimage in `requirements-dev.txt` ausgelagert werden.

## A.6 `Dockerfile`

**Pfad:** `Dockerfile`  
**Herkunft:** Neu; erforderlich für das Docker-Ziel.

```dockerfile
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      libimage-exiftool-perl \
      build-essential cmake \
      libopenblas-dev liblapack-dev \
      libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY app ./app
COPY config ./config

RUN useradd --create-home --uid 1000 workflow \
    && mkdir -p /data/TEMP /models /training /family_faces \
    && chown -R workflow:workflow /app /data /models /training
USER workflow

ENTRYPOINT ["python", "app/photo_workflow.py"]
CMD ["--help"]
```

Für ARM64/Synology muss der CI-Build `face-recognition/dlib` testen. Falls kein verlässlicher dlib-Build möglich ist, ein variantspezifisches Image bereitstellen; die Anwendung selbst bleibt ohne die Bibliothek funktionsfähig.

## A.7 `docker-compose.yml`

**Pfad:** `docker-compose.yml`

```yaml
services:
  photo-workflow:
    build:
      context: .
    image: synology-photo-workflow:latest
    container_name: synology-photo-workflow
    user: "1026:100" # an UID:GID des DSM-Ordnerbesitzers anpassen
    volumes:
      - /volume1/photo-workflow/TEMP:/data/TEMP
      - /volume1/docker/synology-photo-workflow/models:/models
      - /volume1/docker/synology-photo-workflow/training:/training
      - /volume1/docker/synology-photo-workflow/family_faces:/family_faces:ro
      - ./config:/app/config:ro
    command: ["--help"]
    restart: "no"
```

## A.8 Scheduler-Wrapper

**Pfad:** `scripts/run-phase1.sh`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
cd /volume1/docker/synology-photo-workflow
docker compose run --rm photo-workflow \
  --config /app/config/config.yaml phase1
```

**Pfad:** `scripts/run-phase2.sh`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
cd /volume1/docker/synology-photo-workflow
docker compose run --rm photo-workflow \
  --config /app/config/config.yaml phase2
```

Beide Dateien ausführbar machen: `chmod 0750 scripts/run-phase*.sh`. DSM führt sie idealerweise als Benutzer aus, dessen UID/GID Schreibrechte auf `TEMP` und `models` besitzt.

## A.9 Implementierungs- und Importregeln

- Innerhalb des Containers werden Paketimporte `from app.<modul> import ...` verwendet. Für einen Direktaufruf außerhalb des Projektwurzelverzeichnisses ist `PYTHONPATH=/app` zu setzen oder `python -m app.photo_workflow` zu verwenden.
- `photo_workflow.py` darf keine ML- oder Metadatenimplementierung duplizieren; es orchestriert nur die anderen Module.
- Kein Modul darf beim Import Dateien verändern, Caches erzeugen oder ExifTool starten.
- Jede externe Komponente liefert statt eines ungefangenen Fehlers einen Statuswert, sofern die Kern-Dateisicherheit nicht betroffen ist.
- Alle erzeugten JSON-Dateien: UTF-8, `indent=2`, `ensure_ascii=False` für menschenlesbare Personennamen.
- Alle persistierten Pfade in Reports sind absolute Container- bzw. Hostpfade, abhängig von der verwendeten Konfiguration.

## A.10 Endgültige Zuordnung der gelieferten Inhalte

| Quellanhang | Zielpfad im Projekt | Übernahmegrad | Hinweis |
|---|---|---:|---|
| `photo_workflow-5.txt` | `app/photo_workflow.py` | Vollständig fachlich | Export-Syntax reparieren, Sicherheitsregeln verstärken |
| `aesthetic.txt` | `app/aesthetic.py` | Vollständig fachlich | Lokale Heuristiken und Cache-Vertrag beibehalten |
| `family_recognition-2.txt` | `app/family_recognition.py` | Vollständig fachlich | Optionaler dlib-/Face-Library-Fallback |
| `series_culling-7.txt` | `app/series_culling.py` | Vollständig fachlich | Union-Find beibehalten |
| `metadata_writer-4.txt` | `app/metadata_writer.py` | Vollständig fachlich | ExifTool-Append-Syntax korrigieren |
| `metadata_rating-3.txt` | `app/metadata_rating.py` | Fast direkt | Vollständiger Beispielcode in A.3 |
| `training-8.txt` | `app/training.py` | Vollständig fachlich | Zwei Modellformate unterstützen |
| `config-10.txt` | `config/config.yaml` | Vollständig | Docker-Pfade statt lokaler Entwicklungspfade |
| `config-debug-local-11.txt` | `config/config-debug-local.yaml` | Vollständig | Lokale absolute Pfade erhalten |
| `requirements-6.txt` | `requirements.txt` | Erweitert | Tatsächliche Runtime-Imports vollständig abdecken |
| `README-9.md` | `README.md` | Inhaltlich integriert | Diese Gesamtdatei ist die stärkere technische Referenz |



# Anhang B: Verbindliche Ergänzungen zur produktionsfähigen Implementierung

> **Status dieses Anhangs:** Dieser Anhang ergänzt die bestehende Rekonstruktionsspezifikation, ohne deren Originalinhalt zu ändern oder fachliche Regeln zu ersetzen. Bei Widersprüchen gilt für den Foto-Dateifluss, die Culling-Logik und die Konfigurationswerte der vorherige Inhalt. Dieser Anhang präzisiert ausschließlich Implementierungs-, Sicherheits-, Betriebs- und Freigabeentscheidungen, die notwendig sind, um daraus ein belastbares Projekt zu bauen.

## B.1 Implementierbarkeitsentscheidung

Die vorstehende Spezifikation ist als vollständiger Bauplan für ein funktionsfähiges Projekt ausreichend. Sie ist jedoch keine bereits ausführbare Quellcode-Distribution: Die in Anhang A mit `...` markierten Funktionen müssen von der implementierenden KI als getesteter Python-Code umgesetzt werden.

Die folgenden Artefakte gelten bereits als inhaltlich vollständig definierbar und können direkt übernommen werden:

```text
app/__init__.py
app/metadata_rating.py
config/config.yaml
config/config-debug-local.yaml
requirements.txt
Dockerfile
docker-compose.yml
scripts/run-phase1.sh
scripts/run-phase2.sh
```

Die folgenden Module sind anhand ihrer Signaturen, Algorithmen, Datenverträge und Akzeptanztests zu implementieren; sie sind nicht durch Copy/Paste aus dem Dokument fertig:

```text
app/photo_workflow.py
app/aesthetic.py
app/training.py
app/family_recognition.py
app/series_culling.py
app/metadata_writer.py
```

## B.2 Nicht verhandelbare Invarianten

Die folgenden Regeln müssen durch Code und Tests erzwungen werden. Sie sind höher priorisiert als Komfort, automatische Reparatur oder maximale Automatisierung.

1. **Keine Löschung außerhalb von `ARW/`:** `unlink`, `rmtree` und alle indirekten Löschoperationen sind nur erlaubt, wenn der Zielpfad ein regulärer Pfad innerhalb von `paths.base_dir` ist und ein Verzeichniskomponent exakt `ARW` heißt.
2. **Kein Folgen von Symlinks:** Bei Discovery, Hashing, Stabilitätsprüfung, ZIP-Erstellung, Culling und Bereinigung werden Symlinks übersprungen. Vor Move/Delete muss erneut geprüft werden, ob der konkrete Zielpfad kein Symlink ist.
3. **Kein Überschreiben:** Moves, Merges, ZIPs und Metadaten-Backups dürfen keine bestehenden Nutzdaten still überschreiben. Für Ordner/ZIPs gilt der dokumentierte `MERGE`-/`EXTRA`-/`UNSORTED`-Fallback.
4. **Phase 2 ist nur auf explizite Done-Ordner anwendbar:** Der normale Scheduler-Task verarbeitet ausschließlich `paths.temp_done`; ein beliebiger `--folder` muss innerhalb von `temp_done` liegen, sofern kein ausdrücklich dokumentierter Testmodus aktiv ist.
5. **Aktive JPGs sind nur Top-Level-JPGs:** Dateien in `Review`, `Rejected`, `SAVE`, Unterordnern oder Archiven dürfen niemals eine ARW in Phase 2 erhalten.
6. **Optionale Komponenten sind nie fatal:** Fehlendes ExifTool, Pillow-Teilfehler, fehlende Face-Library, fehlende Referenzbilder oder fehlerhafte einzelne Fotos erzeugen einen Status und ein Logevent, aber keinen Abbruch des gesamten Ordners.
7. **Dateifluss- und Sicherheitsfehler sind fatal:** Ungültige Konfiguration, Lock-Konflikte, Pfad-Escape, fehlende Schreibrechte in notwendigen Zielordnern, nicht sicher ausführbare Moves und nicht verifizierbare Löschpfade brechen den Lauf ab.
8. **Eindeutige Zustände:** `.DONE` bedeutet „Phase 1 fachlich abgeschlossen“; `.PROCESSED` enthält ausschließlich den Hash eines erfolgreich vollständig bereinigten Phase-2-Zustands. Marker werden erst nach erfolgreichem Abschluss des jeweiligen Schritts geschrieben.

## B.3 Präzisierung der Pfadsicherheit

Die Originalbeschreibung sieht `models`, `training` und gegebenenfalls `family_faces` außerhalb von `paths.base_dir` vor. Deshalb sind zwei unterschiedliche Prüfklassen erforderlich.

| Prüfklasse | Betroffene Operationen | Zulässige Pfade |
|---|---|---|
| Destruktiv | Löschen, Ordner verschieben, Ordner mergen, ARW-Unterordner entfernen | Ausschließlich innerhalb von `paths.base_dir`; Löschung zusätzlich ausschließlich in `ARW/` |
| Arbeitsdaten | Logdateien, Lockfile, Run-Summaries, `SAVE`, `Review`, `Rejected` | Innerhalb von `paths.base_dir` |
| Modell-/Cache-Schreiben | Personalmodell, Referenzprofil, Family-Cache, Label-Export, Trainingsreports | Ausschließlich die explizit konfigurierten Zielwurzeln `personal_scoring.cache_dir`, `family_recognition.cache_dir`, `reference_scoring.cache_dir`, `training.exported_labels_dir`, `training.runs_dir` |
| Read-only-Referenzen | Sample Images und Familienreferenzen | Konfigurierte Referenzwurzeln; nie verändern |

Implementiere dazu diese konzeptionellen Helfer in `app/photo_workflow.py` oder einem dedizierten Sicherheitsmodul:

```python
def is_within(root: Path, candidate: Path) -> bool:
    """Prüft lexical und nach resolve(), ohne Symlinks als gültige Arbeitsobjekte zu akzeptieren."""
    ...


def require_destructive_path(cfg: dict, path: Path) -> None:
    """Erzwingt base_dir und ARW-Beschränkung bei Löschungen."""
    ...


def require_managed_write_path(cfg: dict, path: Path, category: str) -> None:
    """Erlaubt nur dokumentierte Schreibwurzeln je Kategorie."""
    ...
```

Die frühere Funktion `require_within_base` bleibt für Fotoarbeitsdaten gültig. Sie darf aber nicht irrtümlich Modellcache-Schreiben außerhalb von `/data/TEMP` blockieren.

## B.4 Dry-Run für Phase 2

Vor der ersten produktiven RAW-Bereinigung ist ein Dry-Run zwingend zu implementieren. Er ergänzt die bestehende Konfiguration, ohne ihr Standardverhalten zu verändern.

```yaml
workflow:
  dry_run: false
```

Verhalten bei `dry_run: true`:

- Alle Auswahl-, Hash-, Matching- und ZIP-Zielentscheidungen werden normal berechnet und geloggt.
- Es werden **keine** ARW-Dateien gelöscht, verschoben oder gezippt.
- Es wird kein `ARW/`-Ordner entfernt und kein `.PROCESSED` geschrieben.
- Das JSON-Run-Report enthält `dry_run: true` und pro Ordner mindestens `would_delete_arws`, `would_archive_arws`, `would_remove_arw_directory`.
- Phase 1 kann optional im Dry-Run nur berichten; standardmäßig ist der Dry-Run ausschließlich für Phase 2 verpflichtend.

Der erste reale Phase-2-Lauf erfolgt erst nach manueller Prüfung des Dry-Run-Reports, der Backups und der in `TEMPIMAGES`/`TEMPDONE` sichtbaren Auswahl.

## B.5 Idempotente Metadatenstrategie

ExifTool-Aufrufe müssen wiederholbar sein, ohne Tags zu vervielfachen und ohne fremde Nutzer-Keywords zu löschen. Die ursprünglichen Keyword-Vorgaben bleiben erhalten; ihre Umsetzung wird wie folgt präzisiert:

1. Erzeuge die neue Menge der Workflow-Keywords deterministisch und sortiert.
2. Lese vorhandene `XMP-dc:Subject` und `IPTC:Keywords` aus, wenn ExifTool verfügbar ist.
3. Entferne aus den vorhandenen Listen nur Tags, die durch den Workflow verwaltet werden. Verwaltete Präfixe sind: `workflowaicull`, `decision`, `decisionreason`, `rating`, `series`, `seriestype`, `facestatus`, `familymatch`, `familyprotected`, `person`, `scoreband`, `scorefinal`, `scorebase`, `scorereference`, `scorepersonal`, `scorefamily`.
4. Vereinige verbleibende Nutzer-Tags mit den neu berechneten Workflow-Tags, dedupliziere und schreibe das Ergebnis atomar je Metadatenfeld.
5. Schreibe das XMP-Rating unabhängig davon. Bei `keep_backup: false` gilt `-overwrite_original`.
6. Kann das Auslesen nicht erfolgen, darf der Workflow entweder nur neue deduplizierte Workflow-Tags schreiben oder mit Status `metadata_read_failed` überspringen; fremde Keywords dürfen nicht blind gelöscht werden.

Der Metadatenstatus in CSV und JSON unterscheidet mindestens `written`, `disabled`, `exiftool_missing`, `read_failed`, `write_failed`, `not_attempted`.

## B.6 Konfigurationsvalidierung

`load_config()` ergänzt Defaults; `validate_config()` validiert danach das vollständig aufgelöste Dokument vor jeder Aktion. Bei Fehlern muss eine präzise Meldung mit YAML-Pfad erscheinen.

| YAML-Pfad | Regel |
|---|---|
| `paths.*` | Pflichtpfade nicht leer; Arbeitsdatenpfade bei aktivem Safety-Schalter unter `base_dir` |
| `workflow.wait_time_seconds` | Ganzzahl `>= 0` |
| `workflow.stale_lock_seconds` | Ganzzahl `> 0` |
| `workflow.date_reconstruction.mode` | `legacy_bash` oder `full_year` |
| `workflow.date_reconstruction.decade_prefix` | bei `legacy_bash` exakt drei ASCII-Ziffern |
| `workflow.date_reconstruction.year_digit_index` | Ganzzahl 0 bis 7 |
| `culling.reject_threshold`, `keep_threshold` | `0 <= reject <= keep <= 1` |
| Gewichtungen | numerisch, nicht negativ; bei aktivierten Scoregruppen mindestens eine positive Gewichtung |
| `star_rating_bands` | Scores in `[0,1]`, Sterne 0 bis 5; mindestens ein Band |
| `series_detection.cluster_eps` | `>= 0` |
| `series_detection.min_samples` | Ganzzahl `>= 2` |
| `family_recognition.match_tolerance` | `> 0` |
| Personen- und Featurelimits | Ganzzahlen `>= 1`, wo sie Bildanzahlen begrenzen |
| `metadata_culling.keyword_schema` | aktuell ausschließlich `namespaced_v1` |

## B.7 Fehlerklassifikation

Das Projekt verwendet strukturierte Fehlerklassen oder äquivalente Fehlercodes. Die Scheduler-Mail bleibt kurz; die JSON-Summary enthält Code, Nachricht und Kontext.

```text
CONFIG_INVALID
LOCK_ACTIVE
LOCK_STALE_REMOVED
PATH_ESCAPE
SYMLINK_SKIPPED
TRANSFER_UNSTABLE
FOLDER_NAME_UNSUPPORTED
MOVE_FAILED
MERGE_FALLBACK_USED
ZIP_CREATE_FAILED
ZIP_COLLISION_AVOIDED
IMAGE_READ_FAILED
REFERENCE_PROFILE_UNAVAILABLE
PERSONAL_MODEL_UNAVAILABLE
FACE_LIBRARY_MISSING
FAMILY_REFERENCE_UNAVAILABLE
EXIFTOOL_MISSING
METADATA_WRITE_FAILED
ARW_DELETE_REFUSED
ARW_DELETE_FAILED
PHASE2_DRY_RUN
```

Ein einzelnes defektes JPG wird als `IMAGE_READ_FAILED` in CSV/JSON markiert und standardmäßig nach `Review` gelegt, nicht verworfen. Damit kann ein Bildfehler nicht still zum RAW-Verlust führen.

## B.8 Container- und Supply-Chain-Härtung

Die bereitgestellten Docker-Artefakte sind eine funktionale Basis. Für eine produktive Veröffentlichung kommen folgende Ergänzungen hinzu:

- Python- und APT-Versionen für Release-Builds pinnen oder über einen Lockfile-/Digest-Prozess reproduzierbar machen.
- Container als nichtprivilegierter Benutzer starten; die in Compose angegebene DSM-UID/GID muss tatsächlich zu den Mount-Berechtigungen passen.
- Keine Docker-Socket-Mounts, kein `privileged: true`, keine zusätzlichen Linux-Capabilities.
- Referenzgesichter als Read-only Volume mounten; Modelle, Training und TEMP nur mit den minimal notwendigen Schreibrechten.
- Image in CI auf bekannte Schwachstellen scannen; SBOM erzeugen.
- Für AMD64 und ARM64 getrennt bauen und testen. `face-recognition`/`dlib` ist ein optionaler Feature-Flag, kein Grund für einen kaputten Basisworkflow.
- ExifTool nur über Argumentlisten mit `subprocess.run(..., shell=False, check=False, timeout=<konfigurierbar>)` aufrufen.
- Bilddateien und YAML nie mit `eval`, `shell=True` oder dynamisch erzeugten Shell-Kommandos verarbeiten.

## B.9 Betriebsmodus ohne Face Recognition

Wenn `face_recognition` oder dessen native Abhängigkeit nicht verfügbar ist, muss die Anwendung erfolgreich starten und die folgenden Verhalten zeigen:

```text
family_model.status = "face_library_missing"
eye_score = null
family_score = null
family_tagging = nicht ausgeführt
final_score = dynamisch nur aus vorhandenen Komponenten normalisiert
```

Für die Erstinstallation ist diese Konfiguration zulässig und empfohlen, bis das NAS-spezifische Containerimage überprüft wurde:

```yaml
family_recognition:
  enabled: false
culling:
  eye_detection:
    enabled: false
```

Alle übrigen Teile des Workflows, einschließlich Referenzscore, Personalmodell, Serienerkennung, ZIP-Backup, Reports und Metadaten, bleiben nutzbar.

## B.10 Qualitätssicherung und Freigabegates

Ein Release darf nur freigegeben werden, wenn alle folgenden Gates erfüllt sind.

### Statisches Gate

```bash
python -m compileall app
python -m pytest -q
```

Zusätzlich Typprüfung mit `mypy` oder `pyright` für den Anwendungscode und Linting mit `ruff`. Neue Warnungen ohne begründete Ausnahme sind Release-Blocker.

### Funktionsgate

- Alle Tests aus Kapitel 18 bestehen.
- Ein End-to-End-Test erzeugt temporär mindestens einen Eingangsordner mit JPGs, passenden ARWs, einer Serie und einem fehlenden ARW-Match.
- Die Phase-1-Ausgabe enthält ALLJPG-ZIP, CSV, JSON, `.DONE`, `Review` und/oder `Rejected` nach Score-Regeln.
- Phase 2 im Dry-Run meldet exakt die beabsichtigten ARW-Aktionen.
- Ein anschließender echter Phase-2-Test auf einer Kopie entfernt nur erwartete ARWs, erzeugt SORTARW-ZIP und ist beim zweiten Lauf idempotent.
- Ein Lauf ohne ExifTool und einer ohne Face-Library enden erfolgreich und zeigen die korrekten Statuswerte.

### NAS-Betriebsgate

- Docker-Container kann mit der tatsächlichen DSM-UID/GID in alle vorgesehenen Read-/Write-Mounts schreiben.
- ExifTool ist im Container verfügbar und schreibt ein Test-Rating sowie einen Test-Keyword ohne Beschädigung des Bildes.
- Ein Testordner mit echten Kopien wird erfolgreich durch Phase 1 und nach Sichtung durch Phase 2 verarbeitet.
- Ein Backup der ursprünglichen ARWs und JPGs ist vor realer Phase 2 vorhanden.

## B.11 Empfohlene Release-Abfolge

| Release | Umfang | Freigabekriterium |
|---|---|---|
| `0.1.0` | Config, Locking, sichere Pfade, Phase 1/2, ZIPs, Dry-Run, Logs und Reports | Kein KI-Feature darf nötig sein, um sichere Import-/RAW-Auswahl durchzuführen |
| `0.2.0` | Lokale Features, Base-/Referenzscore, Serienlogik, CSV/JSON | Culling wird nur an Kopien realer Bibliotheken validiert |
| `0.3.0` | Personalmodell und idempotente Metadaten | Trainings- und ExifTool-Tests bestehen auf Ziel-NAS |
| `1.0.0` | Familienerkennung, Mehrarchitektur-Image, vollständige Betriebsdokumentation | AMD64/ARM64 oder dokumentierter Plattformumfang, belastbarer Wiederanlauf und NAS-Abnahme |

## B.12 Ergänzter Testkatalog

Neben den bestehenden Mindesttests müssen folgende konkrete Fälle abgedeckt werden:

```text
- Symlink im TEMPSD wird weder gescannt noch archiviert noch gelöscht.
- Ein Pfad mit Namensbestandteil „ARW“ außerhalb eines echten ARW-Verzeichnisses darf nicht löschbar sein.
- Ein kaputtes JPG führt zu Review und Fehlerstatus, nicht zu einem Absturz oder ARW-Löschen.
- Der zweite identische Phase-1-Lauf erzeugt keine Duplikate und verschiebt keinen bereits korrekt abgelegten Ordner.
- Der zweite identische Phase-2-Lauf erkennt .PROCESSED und führt keine Löschung aus.
- Ein geändertes JPG im Done-Hauptordner verändert den Hash und erlaubt eine kontrollierte erneute Phase 2.
- Workflow-Keywords bleiben bei wiederholtem Metadatenschreiben eindeutig; fremde Keywords bleiben erhalten.
- Ein Family-Cache-Rebuild bei geändertem Referenzbild aktualisiert den Cache-State; unveränderte Referenzen nutzen Cache.
- Ein Personalmodell-Rebuild wird bei Änderung der Sample-Bilder ausgelöst, falls auto_train_on_change aktiv ist.
- Docker-Container kann mit read-only family_faces keine Referenzdatei verändern.
```

## B.13 Abnahmekriterien für eine implementierende KI

Die Implementierung gilt erst als abgeschlossen, wenn sie alle folgenden Punkte nachweisbar erfüllt:

1. Jede in Anhang A definierte Datei existiert am exakten Zielpfad.
2. Jeder dort definierte öffentliche Funktionsname ist implementiert und per Test mindestens einmal aufgerufen.
3. `python -m app.photo_workflow --help` listet alle vier Befehle.
4. Beide YAML-Dateien sind mit `yaml.safe_load` parsebar und bestehen die Konfigurationsvalidierung in ihrer jeweiligen Umgebung.
5. Ein vollständig isolierter Testlauf erzeugt nur innerhalb seines temporären `base_dir` Arbeitsdaten.
6. Kein Test und kein Produktionscode löscht außerhalb eines nachweislich zulässigen `ARW/`-Pfads.
7. Die Reports und CSV-Spalten entsprechen dem Datenvertrag der vorherigen Kapitel.
8. Eine fehlende optionale Laufzeitabhängigkeit führt zu einem dokumentierten Degradierungsstatus, nicht zu einem globalen Fehler.
9. Der Container-Build und ein Smoke-Test sind auf der Zielarchitektur erfolgreich.
10. Die Release-Notes dokumentieren Konfigurationsänderungen, bekannte Einschränkungen und den getesteten DSM-/Container-Umfang.



# Anhang C: Original-Bash-Referenz und Rückfallebene

> **Zweck:** Dieser Anhang nimmt das nachträglich bereitgestellte Originalskript als unveränderte fachliche Altgrundlage in die Rekonstruktionsspezifikation auf. Das Bash-Skript bleibt ein eigenständig ausführbarer Notfall- und Vergleichsworkflow. Es ist kein Ersatz für die Python-/Docker-Erweiterungen zu KI-Culling, Serienerkennung, Personalmodell, Familienerkennung und Metadaten.

## C.1 Verbindliche Legacy-Dateien

Die folgenden Artefakte gehören in das rekonstruierte Repository und müssen mit ihrem gelieferten Originalinhalt erhalten bleiben. Korrekturen am Legacy-Skript erfolgen nur als separater, dokumentierter Patch; die Referenzdatei selbst bleibt unverändert, damit Verhalten verglichen werden kann.

```text
legacy/
├── nas_photosort.sh       # unverändertes Original, Version v4.2
├── README.md              # kurze Kennzeichnung der Legacy-Referenz
└── PATCHES.md             # neu: dokumentiert optionale, nicht originale Härtungen
```

| Gelieferte Datei | Zielpfad | Status | Aufgabe |
|---|---|---|---|
| `nas_photosort.sh` | `legacy/nas_photosort.sh` | Unveränderte Referenz | Ursprünglicher operativer Phase-1-/Phase-2-Fallback für Synology DSM |
| `README-2.md` | `legacy/README.md` | Unveränderte Referenz | Kennzeichnet den Ordner als Altgrundlage für Verhalten, Vergleich, Rückgriff und Migration |
| Neu | `legacy/PATCHES.md` | Dokumentation | Hält Sicherheits-/Kompatibilitätsabweichungen einer optional gepatchten Kopie fest |

`legacy/nas_photosort.sh` benötigt ein gültiges Shebang `#!/bin/bash` und Ausführungsrechte (`chmod 0750`). Sollte das gelieferte Exportformat das einleitende `#` verloren haben, ist dies als Transport-/Exportkorrektur zu dokumentieren, nicht als fachliche Änderung.

## C.2 Legacy-Zweck und Betriebsgrenze

Das Original heißt **„Synology Photo Ingest DONE Workflow“**, Version `v4.2`. Es verarbeitet Kameraordner aus `TEMPSD`, verschiebt bzw. merged sie nach `TEMPIMAGES` und bearbeitet abgeschlossene Ordner in `TEMPDONE`. Es schreibt einen Start-/Endblock, laufende Logzeilen, eine Zusammenfassung sowie getrennte Prozess- und Fehlerlogs und nutzt ein Lockfile gegen parallele Ausführung. [file:14]

Die Python-/Docker-Implementierung übernimmt diesen bewährten Ordnerfluss und erweitert ihn um KI-gestütztes JPG-Culling. Die Bash-Referenz kennt weder `Review`/`Rejected` noch `cullingscores.csv`, `cullingsummary.json`, Referenzscore, Personalmodell, Serienlogik, Familienerkennung oder ExifTool-Metadaten. Sie ist daher ausschließlich eine Rückfallebene für den grundlegenden Dateifluss und keine fachlich gleichwertige Alternative zur vollständigen Python-Pipeline. [file:9][file:14]

## C.3 Rekonstruiertes Bash-Verhalten

### Laufzeitumgebung

Die Originalwerte sind fest im Skript hinterlegt:

```bash
BASEDIR="/volume1/TEMP"
SRC="$BASEDIR/TEMPSD"
DEST="$BASEDIR/TEMPIMAGES"
DONE="$BASEDIR/TEMPDONE"
LOGFILE="$BASEDIR/process.log"
ERRORLOG="$BASEDIR/error.log"
LOCKFILE="$BASEDIR/.script.lock"
WAITTIME=60
```

Das Skript aktiviert `set -euo pipefail` und `nullglob`, verhindert parallele Läufe mit `.script.lock`, protokolliert stdout in `process.log` und stderr in `error.log`, entfernt beim regulären Ende das Lockfile und löscht zu Beginn verbliebene ZIP-Temporärdateien `*.tmp` unterhalb des Base-Verzeichnisses. [file:14]

### Phase 1: `TEMPSD` nach `TEMPIMAGES`

1. Das Skript iteriert Top-Level-Ordner in `TEMPSD`.
2. Es akzeptiert Rohordnernamen mit exakt acht Ziffern sowie bereits umbenannte Namen im Muster `YYYY-MM-DD` mit optionalem Suffix.
3. Nicht als `.DONE` markierte Ordner werden im Abstand von 60 Sekunden auf unveränderte Dateinamen und -größen geprüft; laufende Transfers werden übersprungen.
4. Rohordner werden gemäß der historischen Logik umbenannt: Aus `20250707` wird `2025-07-07`, indem das vierte Zeichen mit Präfix `202` kombiniert wird.
5. ARW-Dateien auf Top-Level werden nach `ARW/` verschoben.
6. JPG-Dateien auf Top-Level werden als `SAVE/<datum>ALLJPG.zip` archiviert, sofern kein aktuelles ZIP vorhanden ist.
7. Das Skript erzeugt `.DONE` und verschiebt bzw. merged den Ordner nach `TEMPIMAGES`.
8. Existiert das Ziel bereits, versucht es zuerst einen `rsync -a`-Merge. Ist `rsync` nicht verfügbar oder schlägt der Merge fehl, erfolgt ein Fallback nach `<ziel>MERGE`, `<ziel>MERGE2` usw. [file:14]

### Phase 2: `TEMPDONE` und RAW-Auswahl

1. Das Skript verarbeitet valide Done-Ordner direkt in `TEMPDONE`; andere Top-Level-Ordner interpretiert es als Container und prüft deren direkte Unterordner.
2. Es berechnet einen MD5-Hash aus relativen JPG-Pfaden und Größen. Stimmt dieser mit `.PROCESSED` überein, wird der Ordner übersprungen.
3. Vorhandene ZIP-Dateien aus `ARW/` werden nach `SAVE/` verschoben; ältere SAVE-ZIPs können in `...ALLJPG.zip` umbenannt werden.
4. Jede ARW ohne gleichnamiges JPG im Hauptordner wird gelöscht.
5. Verbleibende ARWs werden nach `SAVE/<ordner>SORTARW.zip` gezippt; danach löscht das Skript `ARW/`.
6. Abschließend wird der neue Hash in `.PROCESSED` geschrieben. [file:14]

## C.4 Kompatibilitätsvertrag Python zu Bash

Die Python-Implementierung muss für den grundlegenden Dateifluss funktional kompatibel sein, darf aber bei nachweislichen Sicherheitsverbesserungen bewusst abweichen.

| Thema | Legacy Bash v4.2 | Python-/Docker-Ziel | Kompatibilitätsvorgabe |
|---|---|---|---|
| Ordnerbereiche | `TEMPSD`, `TEMPIMAGES`, `TEMPDONE` | Identisch, konfigurierbar | Pflicht |
| Datumslogik | fest `202` + viertes Zeichen | `legacy_bash`, konfigurierbar | Standardwerte müssen gleiches Ergebnis liefern |
| Transferprüfung | zwei `find/stat`-Snapshots | zwei Snapshot-Listen | Gleichwertig |
| ARW-Auslagerung | Top-Level-ARW nach `ARW/` | Identisch | Pflicht |
| JPG-Backup | `SAVE/<datum>ALLJPG.zip` | Identisch, atomar | Pflicht |
| Move/Merge | `mv`, bevorzugt `rsync`, dann `MERGE` | sicherer rekursiver Merge/Fallback | Ergebnis ohne stilles Überschreiben |
| Done-Marker | `.DONE` | `.DONE` vor Move konfigurierbar | Standard: gleichwertig |
| RAW-Selektion | aktives Top-Level-JPG erhält ARW | Identisch | Pflicht |
| RAW-ZIP | `<ordner>SORTARW.zip` | Identisch plus Kollisionsschutz | Erweitert, abwärtskompatibel |
| Wiederholungsschutz | JPG-Hash in `.PROCESSED` | Hash in `.PROCESSED` | Gleichwertig |
| KI-Auswahl | Nicht vorhanden | Keep/Review/Rejected, Scores | Erweiterung, nicht Bash-kompatibel erforderlich |
| Metadaten | Nicht vorhanden | ExifTool/XMP optional | Erweiterung |
| Sicherheit | keine systematische Base-/Symlink-Validierung | harte Safety-Invarianten | Bewusste Verschärfung |
| Dry-Run | Nicht vorhanden | Phase 2 verpflichtend verfügbar | Bewusste Verschärfung |

## C.5 Umschalt- und Fallback-Verfahren

Der Wechsel auf Bash darf nur erfolgen, wenn kein Python-Lauf aktiv ist und das gemeinsame Lockfile nicht existiert. Die Tasks dürfen niemals gleichzeitig auf dieselben `TEMP*`-Verzeichnisse zugreifen.

### Geplanter Fallback

1. Python-DSM-Tasks bzw. Docker-Scheduler pausieren.
2. Laufende Container prüfen und beenden, falls sie tatsächlich aktiv sind.
3. Prüfen, dass `/volume1/TEMP/.script.lock` nicht existiert; bei einem alten Lock zuerst Ursache und Alter prüfen.
4. Sicherstellen, dass `legacy/nas_photosort.sh` auf die **identischen** Arbeitsverzeichnisse zeigt oder eine separate, explizit getestete Fallback-Kopie mit den richtigen Pfaden eingesetzt wird.
5. Bash zunächst gegen eine Kopie eines Fotoordners ausführen und `process.log`, `error.log`, `.DONE`, `SAVE` und Ergebnisordner prüfen.
6. Erst danach den regulären DSM-Task aktivieren.

### Rückkehr zu Python

1. Bash-Task pausieren und einen vollständigen Lauf abwarten.
2. Sicherstellen, dass kein Bash-Lockfile verbleibt.
3. In `TEMPIMAGES` prüfen, ob keine noch offenen Bash-Ordner ohne `.DONE` vorliegen.
4. Python-Phase 1 starten; bereits `.DONE`-markierte Ordner werden gemäß der bestehenden Logik nur weiterbewegt/zusammengeführt.
5. Python-Phase 2 zunächst mit `workflow.dry_run: true` ausführen, bevor echte ARW-Bereinigung freigegeben wird.

## C.6 Sicherheitsbewertung des Originals

Das Original ist eine wertvolle fachliche Referenz, aber nicht auf dem Sicherheitsniveau der neuen Spezifikation. Besonders relevant sind folgende Unterschiede:

- Es nutzt `rm -rf "$ARWDIR"` nach erfolgreichem ZIP und beim leeren ARW-Ordner. Der Python-Workflow muss vorher Base-Pfad, echten `ARW`-Komponentenpfad, Nicht-Symlink und Erfolg des ZIPs verifizieren. [file:14]
- Es löscht alte `*.tmp`-ZIP-Dateien rekursiv unter `BASEDIR`. Die neue Implementierung soll nur explizit bekannte, selbst erzeugte temporäre ZIP-Pfade bereinigen. [file:14]
- Es verschiebt ZIP-Dateien aus `ARW/` nach `SAVE/` und enthält eine ältere Rename-Heuristik. Der Python-Workflow nutzt stattdessen die spezifizierte Klassifikation `ALLJPG`, `SORTARW`, `UNSORTED` und kollisionssichere Namen. [file:14]
- Es verwendet fest verdrahtete Pfade und ein einfaches leeres Lockfile. Die Python-Version konfiguriert Pfade und speichert Lock-Metadaten mit PID/Zeitstempel und Stale-Lock-Logik. [file:14]

Diese Abweichungen sind beabsichtigte Härtungen und keine Änderung des fachlichen Kernziels.

## C.7 Legacy-Tests

Für jede Änderung am Python-Dateifluss müssen Regressionstests gegen den Bash-Vertrag erfolgen. Verwende nur synthetische oder kopierte Testdaten, nie die produktive Bibliothek.

```text
- Eingangsordner 20250707 wird in beiden Systemen zu 2025-07-07.
- Top-Level-ARWs liegen nach Phase 1 in ARW/.
- Vor Culling/Move ist ALLJPG.zip vorhanden und enthält die ursprünglichen Top-Level-JPGs.
- Ein bereits .DONE-markierter Eingangsordner wird nicht erneut vorbereitet.
- Ein stabiles Ziel mit vorhandenem Ordner führt zu Merge oder eindeutigem MERGE-Fallback, nie zu Überschreiben.
- Nur ein Top-Level-JPG mit gleichem Basenamen bewahrt eine ARW in Phase 2.
- Review-/Rejected-JPGs der Python-Pipeline gelten nicht als aktive Auswahl.
- Nach erfolgreicher Phase 2 existiert SORTARW.zip, ARW/ ist entfernt und .PROCESSED verhindert Wiederholung.
- ZIP-Namenskollisionen bleiben im Python-System nachvollziehbar und überschreiben keine Bash-Altarchive.
- Kein Python-Test darf die weniger strengen Lösch-/Symlink-Annahmen des Legacy-Skripts übernehmen.
```

## C.8 `legacy/README.md`-Inhalt

Der gelieferte Legacy-README-Inhalt bleibt erhalten. Ergänze ihn höchstens um diesen Betriebsvermerk, ohne seine Referenzfunktion zu verwässern:

```markdown
# Legacy Reference

Dieser Ordner enthält die ursprüngliche Bash-Referenz inklusive zugehöriger README.
Er dient als fachliche Altgrundlage für Verhalten, Vergleich und Rückgriff bei
Validierung oder Migration.

> Achtung: `nas_photosort.sh` ist ein operativer Fallback für den grundlegenden
> Datei- und RAW-Workflow. Es enthält keine KI-Auswahl, keine Review-/Rejected-
> Logik, keine Familienerkennung und keine strukturierten Culling-Reports.
> Python- und Bash-Scheduler dürfen niemals gleichzeitig auf dieselben TEMP-
> Verzeichnisse zugreifen.
```

## C.9 Abnahmekriterium Legacy-Integration

Die Rekonstruktion ist erst vollständig dokumentiert, wenn `legacy/nas_photosort.sh` und `legacy/README.md` im Repository vorliegen, der Bash-zu-Python-Kompatibilitätsvertrag getestet ist und die Betriebsdokumentation den sicheren Wechsel zwischen beiden Laufzeiten erklärt. Das Bash-Skript bleibt dabei die historische Referenz für den Kernordnerfluss; die Python-/Docker-Pipeline bleibt die führende Implementierung für neue Funktionen und Sicherheitsverbesserungen.


# Anhang D: Übergabepaket für eine implementierende KI

> **Verbindliche Arbeitsanweisung:** Dieses Kapitel ergänzt die Architektur um eine konkrete Dateilandkarte und Quellcode-Verträge. Eine implementierende KI legt jede aufgeführte Datei am **exakt** genannten Repository-Pfad an. Sie darf keine Module umbenennen, Importpfade ändern oder die Sicherheitseigenschaften abschwächen. Die frühere Anforderung „vollständiges Docker-Projekt“ bedeutet: Alle unten als *zu erstellen* markierten Dateien müssen als echter, ausführbarer Inhalt geliefert werden, nicht nur als Pseudocode.

## D.1 Ziel-Repository

```text
synology-photo-workflow/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .dockerignore
├── config/
│   ├── config.example.yaml
│   ├── config.yaml                  # lokal, nicht einchecken
│   └── config.debug-local.yaml
├── app/
│   ├── __init__.py
│   ├── photo_workflow.py             # CLI und Orchestrierung
│   ├── aesthetic.py                  # Bildmerkmale, Basis- und Referenzscore
│   ├── series_culling.py             # Serien-Cluster und finale Serienentscheidung
│   ├── training.py                   # Rating-Training und Personal-Score-Cache
│   ├── metadata_rating.py             # XMP-Ratings lesen
│   ├── metadata_writer.py             # XMP-Sterne und Keywords schreiben
│   └── family_recognition.py          # Gesichtsmodell, Cache, Familien-Score
├── scripts/
│   ├── run_phase1.sh
│   ├── run_phase2.sh
│   └── run_all.sh
├── legacy/
│   ├── nas_photosort.sh
│   ├── README.md
│   └── PATCHES.md
├── tests/
│   ├── test_workflow_legacy.py
│   ├── test_zip_safety.py
│   ├── test_series_culling.py
│   ├── test_metadata_writer.py
│   └── test_family_recognition.py
└── docs/
    └── RECONSTRUCTION_SPEC.md
```

## D.2 Dateivertrag

| Repository-Pfad | Eingabe/Abhängigkeiten | Ausgabe/Verantwortung | Nicht verhandelbare Regeln |
|---|---|---|---|
| `app/photo_workflow.py` | YAML, Bilder, RAWs, alle App-Module | CLI, Moves, ZIPs, CSV/JSON, Logs | Einziger Orchestrator; Phase 2 nur mit Path-Safety und Dry-Run |
| `app/aesthetic.py` | Pillow, NumPy, optionale Referenzbilder | normierte Komponenten 0.0–1.0 | Keine Netzwerkanfragen; Bildfehler dürfen den Lauf nicht stoppen |
| `app/series_culling.py` | Score-Zeilen und JPGs | `series_*`, finale Entscheidung, Sterne | Bestes Serienbild niemals `reject`; Familien-Schutz wirkt nach Serienlogik |
| `app/training.py` | Beispielbilder, optionale XMP-Ratings | JSON-Personalmodell, Cache-Metadaten, Reports | Fehlende Labels/Beispiele sind kontrolliert, kein Crash der Phase 1 |
| `app/metadata_rating.py` | JPG/XMP-Sidecar | Sternrating 0–5 oder `None` | Read-only, tolerant gegenüber fehlerhaftem XMP |
| `app/metadata_writer.py` | Culling-Zeile, ExifTool | XMP-Rating und Subject-Keywords | ExifTool fehlt: Status melden, nicht abbrechen |
| `app/family_recognition.py` | Referenzbilder, optionale `face_recognition`-Lib | Personen, Familien-Score, Cache, Tags | Optional; ohne Library/Fotos weiterlauffähig |
| `config/config.example.yaml` | Benutzer bearbeitet Pfade/Schwellen | einzige produktive Konfigurationsvorlage | Keine lokalen `/home/...`-Entwicklungspfade |
| `Dockerfile` | `requirements.txt`, Debian-Pakete | reproduzierbares Image für NAS | ExifTool; Face-Library als optionales Build-Profil dokumentieren |
| `docker-compose.yml` | Image und Konfigurationsdatei | bindet NAS-Daten und Projektpersistenz ein | Nur erlaubte Host-Pfade mounten; kein Docker-Privileged-Modus |
| `scripts/run_*.sh` | Docker Compose | Scheduler-fähige Befehle | `set -euo pipefail`, keine parallelen Phase-Tasks |
| `legacy/nas_photosort.sh` | Originaldatei | Bash-Fallback | Inhalt nicht fachlich umschreiben |

## D.3 Import- und Aufrufvertrag

Die Importe des Orchestrators müssen genau dieser Verantwortung entsprechen. Kleinere interne Hilfsfunktionen sind erlaubt, die öffentlichen Funktionen und Datenfelder dürfen aber nicht ohne Aktualisierung von Tests und Dokumentation entfernt werden.

```python
from aesthetic import (
    base_score_components,
    ensure_reference_profile,
    generic_aesthetic_score,
    load_personal_model,
    personal_model_score,
    weighted_base_score,
)
from family_recognition import (
    detect_family_members,
    load_family_model,
    rebuild_family_cache,
    write_native_tags,
)
from series_culling import apply_series_culling
from metadata_writer import write_culling_metadata
from training import train_from_directory, load_or_rebuild_personal_model
```

Pflicht-CLI:

```bash
python app/photo_workflow.py --config config/config.yaml phase1
python app/photo_workflow.py --config config/config.yaml phase2 --dry-run
python app/photo_workflow.py --config config/config.yaml phase2
python app/photo_workflow.py --config config/config.yaml train-personal
python app/photo_workflow.py --config config/config.yaml rebuild-family-cache
```

## D.4 Quellcode: `app/metadata_rating.py`

**Funktion:** Liest Ratings aus `<bild>.xmp`, `<bild>.JPG.xmp` oder eingebetteten Textbereichen. Dies ist die Basis für das optionale Rating-Training.

```python
from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

RATING_PATTERNS = [
    re.compile(r"<xmp:Rating>([0-5])</xmp:Rating>", re.IGNORECASE),
    re.compile(r'xmp:Rating="([0-5])"', re.IGNORECASE),
    re.compile(r'<Rating>([0-5])</Rating>', re.IGNORECASE),
    re.compile(r'Rating="([0-5])"', re.IGNORECASE),
]


def _extract_rating_from_text(text: str) -> Optional[float]:
    for pattern in RATING_PATTERNS:
        match = pattern.search(text)
        if match:
            return float(match.group(1))
    return None


def read_rating(image_path: str | Path) -> Optional[float]:
    path = Path(image_path)
    sidecars = [path.with_suffix(path.suffix + '.xmp'), path.with_suffix('.xmp')]
    for sidecar in sidecars:
        if sidecar.exists() and sidecar.is_file():
            try:
                text = sidecar.read_text(encoding='utf-8', errors='ignore')
                rating = _extract_rating_from_text(text)
                if rating is not None:
                    return rating
            except OSError:
                pass

    try:
        data = path.read_bytes()
        text = data.decode('utf-8', errors='ignore')
        rating = _extract_rating_from_text(text)
        if rating is not None:
            return rating
    except OSError:
        return None
    return None
```

## D.5 Quellcode: `app/metadata_writer.py`

**Funktion:** Schreibt nach der finalen Entscheidung optionale XMP-Sterne und durchsuchbare, namensbasierte Keywords. Die Funktion ist fehlertolerant: Fehlt ExifTool, wird ein Status zurückgegeben.

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _bool(cfg: dict, key: str, default: bool) -> bool:
    return bool(cfg.get('metadata_culling', {}).get(key, default))


def _as_people(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    raw = str(value).strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]


def _score_band(value) -> str | None:
    if value is None or value == '':
        return None
    try:
        value = float(value)
    except Exception:
        return None
    if value < 0:
        value = 0.0
    if value > 1:
        value = 1.0
    lo = int(value * 100) // 10 * 10
    hi = min(lo + 9, 99)
    return f'{lo:02d}_{hi:02d}'


def build_culling_keywords(row: dict, cfg: dict) -> list[str]:
    mc = cfg.get('metadata_culling', {})
    schema = str(mc.get('keyword_schema', 'namespaced_v1')).strip().lower()
    if schema != 'namespaced_v1':
        schema = 'namespaced_v1'
    rating = int(row.get('star_rating', 0) or 0)
    keywords = [
        'workflow:ai_cull',
        f"decision:{str(row.get('decision', 'unknown')).lower()}",
        f"decision_reason:{str(row.get('decision_reason', 'unknown')).lower()}",
        f'rating:stars:{rating}',
    ]
    series_id = row.get('series_id')
    if series_id and str(series_id) != 'single':
        keywords.append(f'series:id:{series_id}')
        keywords.append(f"series:size:{int(row.get('series_size', 1) or 1)}")
        keywords.append(f"series:rank:{int(row.get('series_rank', 1) or 1)}")
        keywords.append(f"series:best:{str(bool(row.get('series_best', False))).lower()}")
    elif series_id:
        keywords.append('series:type:single')
    face_status = str(row.get('face_status', '') or '').strip()
    if face_status:
        keywords.append(f'face:status:{face_status}')
    protected = bool(row.get('protected_by_family_rule', False))
    if row.get('family_score') not in (None, ''):
        keywords.append(f'family:match:{str(float(row.get("family_score", 0.0)) > 0.0).lower()}')
    if protected:
        keywords.append('family:protected:true')
    for person in _as_people(row.get('detected_people')):
        keywords.append(f'person:{person}')
    if _bool(cfg, 'write_score_bands', True):
        score_fields = {
            'final': row.get('final_score'),
            'base': row.get('base_score'),
            'reference': row.get('reference_score'),
            'personal': row.get('personal_score'),
            'family': row.get('family_score'),
        }
        for label, value in score_fields.items():
            band = _score_band(value)
            if band:
                keywords.append(f'score_band:{label}:{band}')
    if _bool(cfg, 'write_raw_scores_to_keywords', False):
        score_fields = {
            'final': row.get('final_score'),
            'base': row.get('base_score'),
            'reference': row.get('reference_score'),
            'personal': row.get('personal_score'),
            'family': row.get('family_score'),
        }
        for label, value in score_fields.items():
            if value not in (None, ''):
                keywords.append(f'score:{label}:{float(value):.2f}')
    return sorted(set(keywords))


def write_culling_metadata(path: str | Path, row: dict, cfg: dict) -> tuple[bool, str]:
    mc = cfg.get('metadata_culling', {})
    if not bool(mc.get('enabled', True)):
        return False, 'disabled'
    exiftool = str(mc.get('exiftool_path', 'exiftool'))
    if shutil.which(exiftool) is None:
        return False, 'exiftool_missing'
    target = Path(path)
    rating = int(row.get('star_rating', 0) or 0)
    keywords = build_culling_keywords(row, cfg) if _bool(cfg, 'write_keywords', True) else []
    cmd = [exiftool]
    if not bool(mc.get('keep_backup', False)):
        cmd.append('-overwrite_original')
    if _bool(cfg, 'write_rating', True):
        cmd.append(f'-XMP:Rating={rating}')
    for kw in keywords:
        cmd.append(f'-XMP-dc:Subject+={kw}')
    cmd.append(str(target))
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True, 'written'
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or exc.stdout or '').strip()
        return False, f'failed:{msg[:120]}' if msg else 'failed'
```

## D.6 Quellcode: `app/series_culling.py`

**Funktion:** Erstellt einfache, lokale Bildembeddings, clustert ähnliche Bilder und korrigiert die Score-Entscheidung. `series_best` wird immer mindestens `review`; ein Familienbild wird nie durch Serienlogik auf `reject` gesetzt.

```python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable
import math

import numpy as np
from PIL import Image, ImageFilter


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _load_embedding(path: str | Path, preview_size: int = 32) -> np.ndarray:
    img = Image.open(path).convert('RGB')
    img = img.resize((preview_size, preview_size))
    gray = img.convert('L')
    edges = gray.filter(ImageFilter.FIND_EDGES)
    rgb = np.asarray(img, dtype=np.float32) / 255.0
    gray_arr = np.asarray(gray, dtype=np.float32) / 255.0
    edge_arr = np.asarray(edges, dtype=np.float32) / 255.0
    feat = np.concatenate([
        rgb.mean(axis=(0, 1)),
        rgb.std(axis=(0, 1)),
        gray_arr.reshape(-1),
        edge_arr.reshape(-1),
    ])
    norm = float(np.linalg.norm(feat))
    return feat if norm <= 1e-12 else (feat / norm)


def _pairwise_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(1.0 - np.dot(a, b))


def cluster_series(paths: Iterable[str | Path], cluster_eps: float = 0.18, min_samples: int = 2, preview_size: int = 32) -> tuple[list[int], list[np.ndarray | None]]:
    path_list = [Path(p) for p in paths]
    embeddings: list[np.ndarray | None] = []
    for path in path_list:
        try:
            embeddings.append(_load_embedding(path, preview_size=preview_size))
        except Exception:
            embeddings.append(None)
    labels = [-1] * len(path_list)
    parent = list(range(len(path_list)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(len(path_list)):
        if embeddings[i] is None:
            continue
        for j in range(i + 1, len(path_list)):
            if embeddings[j] is None:
                continue
            if _pairwise_distance(embeddings[i], embeddings[j]) <= float(cluster_eps):
                union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for idx in range(len(path_list)):
        if embeddings[idx] is None:
            continue
        groups[find(idx)].append(idx)

    next_label = 0
    for idxs in groups.values():
        if len(idxs) < int(min_samples):
            continue
        for idx in idxs:
            labels[idx] = next_label
        next_label += 1
    return labels, embeddings


def _rating_for_score(final_score: float, cfg: dict) -> int:
    bands = cfg.get('culling', {}).get('star_rating_bands', {5: 0.90, 4: 0.75, 3: 0.60, 2: 0.40, 1: 0.20, 0: 0.00})
    normalized = []
    for stars, min_score in bands.items():
        try:
            normalized.append((int(stars), float(min_score)))
        except Exception:
            continue
    if not normalized:
        normalized = [(5, 0.90), (4, 0.75), (3, 0.60), (2, 0.40), (1, 0.20), (0, 0.00)]
    score = max(0.0, min(1.0, float(final_score)))
    for stars, min_score in sorted(normalized, key=lambda x: (-x[1], -x[0])):
        if score >= min_score:
            return stars
    return 0


def _decision_rank(decision: str) -> int:
    return {'reject': 0, 'review': 1, 'keep': 2}.get(str(decision).strip().lower(), 1)


def _decision_name(rank: int) -> str:
    return {0: 'reject', 1: 'review', 2: 'keep'}.get(max(0, min(2, int(rank))), 'review')


def _promote_one(decision: str) -> str:
    return _decision_name(_decision_rank(decision) + 1)


def _demote_one(decision: str) -> str:
    return _decision_name(_decision_rank(decision) - 1)

def apply_series_culling(rows: list[dict], cfg: dict) -> list[dict]:
    series_cfg = cfg.get('series_detection', {})
    enabled = bool(series_cfg.get('enabled', True)) and len(rows) > 1
    if not enabled:
        for row in rows:
            row['score_decision'] = row.get('score_decision', row.get('decision', 'review'))
            row['series_id'] = 'single'
            row['series_size'] = 1
            row['series_rank'] = 1
            row['series_best'] = True
            row['series_margin_to_best'] = 0.0
            row['decision'] = row['score_decision']
            row['decision_reason'] = row.get('score_reason', 'score_threshold')
            row['star_rating'] = _rating_for_score(float(row.get('final_score', 0.0)), cfg)
        return rows

    labels, _ = cluster_series(
        [row['_source_path'] for row in rows],
        cluster_eps=float(series_cfg.get('cluster_eps', 0.18)),
        min_samples=int(series_cfg.get('min_samples', 2)),
        preview_size=int(series_cfg.get('preview_size', 32)),
    )
    for row, label in zip(rows, labels):
        row['_series_label'] = label
        row['score_decision'] = row.get('score_decision', row.get('decision', 'review'))

    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row['_series_label'])].append(row)

    review_margin = float(series_cfg.get('review_margin', 0.03))
    demote_non_best_to = str(series_cfg.get('demote_non_best_to', 'review')).strip().lower()
    for label, items in grouped.items():
        if label == -1:
            for item in items:
                item['series_id'] = 'single'
                item['series_size'] = 1
                item['series_rank'] = 1
                item['series_best'] = True
                item['series_margin_to_best'] = 0.0
                item['decision'] = item['score_decision']
                item['decision_reason'] = item.get('score_reason', 'score_threshold')
                item['star_rating'] = _rating_for_score(float(item.get('final_score', 0.0)), cfg)
            continue

        ranked = sorted(items, key=lambda x: (-float(x['final_score']), x['file']))
        best_score = float(ranked[0]['final_score'])
        for pos, item in enumerate(ranked, start=1):
            margin = round(best_score - float(item['final_score']), 4)
            item['series_id'] = f'series_{label}'
            item['series_size'] = len(ranked)
            item['series_rank'] = pos
            item['series_best'] = pos == 1
            item['series_margin_to_best'] = margin
            base_decision = str(item.get('score_decision', item.get('decision', 'review'))).strip().lower()

            if pos == 1:
                if base_decision == 'keep':
                    final_decision = 'keep'
                    reason = 'series_best_confirmed'
                elif base_decision == 'review':
                    final_decision = 'keep'
                    reason = 'series_best_promoted'
                else:
                    final_decision = 'review'
                    reason = 'series_best_salvaged'
            elif margin <= review_margin:
                final_decision = 'review'
                reason = 'series_near_best'
            else:
                if demote_non_best_to == 'reject':
                    final_decision = _demote_one(base_decision)
                    reason = 'series_demoted_hard'
                else:
                    final_decision = 'review' if base_decision == 'keep' else base_decision
                    reason = 'series_demoted_soft' if base_decision == 'keep' else item.get('score_reason', 'score_threshold')

            if item.get('protected_by_family_rule') and final_decision == 'reject':
                final_decision = 'review'
                reason = 'family_protected_series'

            item['decision'] = final_decision
            item['decision_reason'] = reason
            item['star_rating'] = _rating_for_score(float(item.get('final_score', 0.0)), cfg)

    for row in rows:
        row.pop('_series_label', None)
    return rows
```

**Hinweis für die implementierende KI:** Diese Datei ist absichtlich als präziser Codevertrag plus Implementierungsstelle markiert, weil der Algorithmus ausführlich in der Hauptspezifikation beschrieben ist. Sie muss vor Auslieferung vollständig implementiert werden; ein `NotImplementedError` ist nicht zulässig.

## D.7 Quellcode-Verträge der großen Module

Die folgenden Dateien sind umfangreiche Kernmodule. Ihre tatsächliche Implementierung muss die in diesem Dokument und den vorherigen Kapiteln festgelegten Ein-/Ausgaben erfüllen.

### `app/aesthetic.py`

```python
from __future__ import annotations

from pathlib import Path
from math import log1p
from typing import Dict, Optional
import json
import statistics

import numpy as np

try:
    from PIL import Image, ImageFilter, ImageStat
except Exception:
    Image = None
    ImageFilter = None
    ImageStat = None

try:
    import face_recognition
except Exception:
    face_recognition = None

IMAGE_EXTS = {'.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG'}
_REFERENCE_PROFILE_CACHE: dict[tuple[str, bool, int], np.ndarray] = {}


def clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _variance(values) -> float:
    if not values:
        return 0.0
    try:
        return statistics.pvariance(values)
    except statistics.StatisticsError:
        return 0.0


def _open_image(path: Path):
    if Image is None:
        raise RuntimeError('Pillow not available')
    return Image.open(path).convert('RGB')


def extract_features(image_path: str | Path) -> Dict[str, float]:
    path = Path(image_path)
    size_bytes = path.stat().st_size if path.exists() else 0
    width = 0
    height = 0
    edge_var = 0.0
    mean_luma = 0.5
    clipped_dark = 0.0
    clipped_bright = 0.0
    contrast = 0.0
    saturation = 0.0

    if Image is not None:
        try:
            with _open_image(path) as img:
                width, height = img.size
                gray = img.convert('L')
                edges = gray.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edges)
                edge_var = float(stat.var[0]) if stat.var else 0.0
                gray_arr = np.asarray(gray, dtype=np.float32)
                hsv = np.asarray(img.convert('HSV'), dtype=np.float32)
                mean_luma = float(gray_arr.mean() / 255.0) if gray_arr.size else 0.5
                clipped_dark = float((gray_arr < 5).mean()) if gray_arr.size else 0.0
                clipped_bright = float((gray_arr > 250).mean()) if gray_arr.size else 0.0
                contrast = float(gray_arr.std() / 64.0) if gray_arr.size else 0.0
                saturation = float(hsv[:, :, 1].mean() / 255.0) if hsv.size else 0.0
        except Exception:
            width = 0
            height = 0
            edge_var = 0.0
            mean_luma = 0.5
            clipped_dark = 0.0
            clipped_bright = 0.0
            contrast = 0.0
            saturation = 0.0

    megapixels = (width * height) / 1_000_000 if width and height else 0.0
    aspect = (width / height) if width and height else 1.0
    aspect_targets = [1.5, 1.3333, 1.7777]
    aspect_score = 1.0 - min(abs(aspect - target) for target in aspect_targets)
    aspect_score = clip01(aspect_score)
    portrait = 1.0 if height > width else 0.0
    filesize_mb = size_bytes / (1024 * 1024) if size_bytes else 0.0

    return {
        'width': float(width),
        'height': float(height),
        'megapixels': float(megapixels),
        'aspect_ratio': float(aspect),
        'aspect_score': float(aspect_score),
        'portrait': float(portrait),
        'filesize_mb': float(filesize_mb),
        'edge_var': float(edge_var),
        'mean_luma': float(mean_luma),
        'clipped_dark': float(clipped_dark),
        'clipped_bright': float(clipped_bright),
        'contrast': float(contrast),
        'saturation': float(saturation),
    }


def generic_aesthetic_score(image_path: str | Path) -> float:
    f = extract_features(image_path)
    resolution_score = clip01(f['megapixels'] / 24.0)
    size_score = clip01(log1p(f['filesize_mb']) / log1p(12.0))
    sharpness_score = clip01(log1p(f['edge_var']) / log1p(8000.0))
    score = (
        0.35 * resolution_score
        + 0.25 * size_score
        + 0.25 * sharpness_score
        + 0.15 * f['aspect_score']
    )
    return clip01(score)


def sharpness_component(image_path: str | Path) -> float:
    f = extract_features(image_path)
    return clip01(log1p(f['edge_var']) / log1p(8000.0))


def exposure_component(image_path: str | Path) -> float:
    f = extract_features(image_path)
    clip_penalty = min(1.0, (f['clipped_dark'] + f['clipped_bright']) * 5.0)
    balance_penalty = abs(f['mean_luma'] - 0.5) * 1.2
    return clip01(1.0 - (0.6 * clip_penalty + 0.4 * balance_penalty))


def classic_aesthetic_component(image_path: str | Path) -> float:
    f = extract_features(image_path)
    score = (
        0.35 * clip01(f['contrast'])
        + 0.25 * clip01(f['saturation'])
        + 0.20 * (1 - abs(f['mean_luma'] - 0.5) * 2)
        + 0.20 * clip01(log1p(f['edge_var']) / log1p(8000.0))
    )
    return clip01(score)


def _simple_embedding(image_path: str | Path, size: int = 32) -> np.ndarray:
    with _open_image(Path(image_path)) as img:
        img = img.resize((size, size))
        gray = img.convert('L')
        edges = gray.filter(ImageFilter.FIND_EDGES)
        rgb = np.asarray(img, dtype=np.float32) / 255.0
        gray_arr = np.asarray(gray, dtype=np.float32) / 255.0
        edge_arr = np.asarray(edges, dtype=np.float32) / 255.0
    feat = np.concatenate([rgb.mean(axis=(0, 1)), rgb.std(axis=(0, 1)), gray_arr.reshape(-1), edge_arr.reshape(-1)])
    norm = float(np.linalg.norm(feat))
    return feat if norm <= 1e-12 else (feat / norm)


def _reference_images(folder: Path, recursive: bool) -> list[Path]:
    iterator = folder.rglob('*') if recursive else folder.glob('*')
    return [p for p in sorted(iterator) if p.is_file() and p.suffix in IMAGE_EXTS]



def _reference_cfg(cfg: dict) -> dict:
    ref_cfg = cfg.get('culling', {}).get('reference_scoring', {}) or {}
    base_dir = Path(cfg.get('paths', {}).get('base_dir', '.'))
    folder = Path(ref_cfg.get('folder', base_dir / 'reference_images'))
    preview_size = int(ref_cfg.get('preview_size', 32))
    cache_dir = Path(ref_cfg.get('cache_dir', base_dir / 'models' / 'reference_scoring'))
    return {
        'enabled': bool(ref_cfg.get('enabled', False)),
        'folder': folder,
        'recursive': bool(ref_cfg.get('recursive', False)),
        'preview_size': preview_size,
        'cache_enabled': bool(ref_cfg.get('cache_enabled', True)),
        'cache_dir': cache_dir,
        'force_cache_rebuild': bool(ref_cfg.get('force_cache_rebuild', False)),
    }


def _reference_cache_paths(cfg: dict) -> dict:
    ref = _reference_cfg(cfg)
    cache_dir = Path(ref['cache_dir'])
    cache_dir.mkdir(parents=True, exist_ok=True)
    return {
        'dir': cache_dir,
        'profile': cache_dir / 'reference_profile.npy',
        'meta': cache_dir / 'reference_profile_meta.json',
        'report': cache_dir / 'last_reference_profile_report.json',
    }


def build_reference_profile_state(cfg: dict) -> dict:
    ref = _reference_cfg(cfg)
    folder = Path(ref['folder'])
    refs = _reference_images(folder, ref['recursive']) if folder.exists() and folder.is_dir() else []
    return {
        'folder': str(folder),
        'recursive': ref['recursive'],
        'preview_size': ref['preview_size'],
        'images': [
            {
                'relative_path': str(p.relative_to(folder)),
                'size': p.stat().st_size,
                'mtime_ns': p.stat().st_mtime_ns,
            }
            for p in refs
        ],
    }


def _write_reference_report(cfg: dict, payload: dict) -> None:
    paths = _reference_cache_paths(cfg)
    paths['report'].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')


def ensure_reference_profile(cfg: dict) -> tuple[Optional[np.ndarray], dict]:
    ref = _reference_cfg(cfg)
    info = {
        'status': 'disabled' if not ref['enabled'] else 'missing',
        'used_cache': False,
        'rebuilt_cache': False,
        'reference_image_count': 0,
        'folder': str(ref['folder']),
        'cache_dir': str(ref['cache_dir']),
        'preview_size': ref['preview_size'],
    }
    if not ref['enabled']:
        return None, info
    folder = Path(ref['folder'])
    if not str(folder) or not folder.exists() or not folder.is_dir() or Image is None:
        info['status'] = 'reference_dir_missing' if not folder.exists() else 'pillow_missing'
        _write_reference_report(cfg, info)
        return None, info
    state = build_reference_profile_state(cfg)
    info['reference_image_count'] = len(state['images'])
    if not state['images']:
        info['status'] = 'no_reference_images'
        _write_reference_report(cfg, info | {'reference_state': state})
        return None, info
    key = (str(folder.resolve()), ref['recursive'], ref['preview_size'])
    paths = _reference_cache_paths(cfg)
    rebuild = bool(ref['force_cache_rebuild'])
    meta = {}
    if paths['meta'].exists():
        try:
            meta = json.loads(paths['meta'].read_text(encoding='utf-8'))
        except Exception:
            meta = {}
    if key in _REFERENCE_PROFILE_CACHE and not rebuild:
        info['status'] = 'memory_cache_used'
        info['used_cache'] = True
        _write_reference_report(cfg, info | {'reference_state': state})
        return _REFERENCE_PROFILE_CACHE[key], info
    if ref['cache_enabled'] and paths['profile'].exists() and meta.get('reference_state') == state and not rebuild:
        try:
            profile = np.load(paths['profile'])
            _REFERENCE_PROFILE_CACHE[key] = profile
            info['status'] = 'cache_used'
            info['used_cache'] = True
            _write_reference_report(cfg, info | {'reference_state': state})
            return profile, info
        except Exception:
            rebuild = True
    refs = _reference_images(folder, ref['recursive'])
    emb = np.stack([_simple_embedding(p, size=ref['preview_size']) for p in refs])
    profile = emb.mean(axis=0)
    norm = float(np.linalg.norm(profile))
    profile = profile if norm <= 1e-12 else (profile / norm)
    _REFERENCE_PROFILE_CACHE[key] = profile
    if ref['cache_enabled']:
        np.save(paths['profile'], profile)
        meta_payload = {'reference_state': state, 'preview_size': ref['preview_size'], 'status': 'cache_rebuilt'}
        paths['meta'].write_text(json.dumps(meta_payload, indent=2, ensure_ascii=False), encoding='utf-8')
    info['status'] = 'cache_rebuilt'
    info['rebuilt_cache'] = True
    _write_reference_report(cfg, info | {'reference_state': state})
    return profile, info


def reference_score_component(image_path: str | Path, cfg: dict) -> Optional[float]:
    ref = _reference_cfg(cfg)
    if not ref['enabled']:
        return None
    runtime_profile = cfg.get('culling', {}).get('reference_scoring', {}).get('_runtime_profile')
    profile = runtime_profile
    if profile is None:
        profile, _ = ensure_reference_profile(cfg)
    if profile is None:
        return None
    img_emb = _simple_embedding(image_path, size=ref['preview_size'])
    return clip01((float(np.dot(img_emb, profile)) + 1.0) / 2.0)


def eye_open_component(image_path: str | Path, cfg: dict) -> Optional[float]:
    eye_cfg = cfg.get('culling', {}).get('eye_detection', {})
    if not bool(eye_cfg.get('enabled', True)):
        return None
    if face_recognition is None:
        return None
    try:
        image = face_recognition.load_image_file(str(image_path))
        faces = face_recognition.face_landmarks(image)
    except Exception:
        return None
    if not faces:
        return None

    def eye_score(points) -> float:
        if len(points) < 6:
            return 0.5
        pts = np.asarray(points[:6], dtype=np.float32)
        d1 = np.linalg.norm(pts[1] - pts[5])
        d2 = np.linalg.norm(pts[2] - pts[4])
        d3 = np.linalg.norm(pts[0] - pts[3])
        ear = (d1 + d2) / (2.0 * d3 + 1e-6)
        return clip01((ear - 0.16) / 0.18)

    scores = []
    for face in faces:
        left = face.get('left_eye')
        right = face.get('right_eye')
        if not left or not right:
            continue
        scores.append((eye_score(left) + eye_score(right)) / 2.0)
    if not scores:
        return None
    return clip01(sum(scores) / len(scores))


def _normalized_active_weights(weight_map: dict[str, float], active: dict[str, Optional[float]]) -> dict[str, float]:
    valid = {k: float(weight_map.get(k, 0.0)) for k, v in active.items() if v is not None and float(weight_map.get(k, 0.0)) > 0}
    total = sum(valid.values()) or 1.0
    return {k: v / total for k, v in valid.items()}


def base_score_components(image_path: str | Path, cfg: dict) -> Dict[str, Optional[float]]:
    return {
        'sharp': sharpness_component(image_path),
        'aesth': classic_aesthetic_component(image_path),
        'exposure': exposure_component(image_path),
        'eyes': eye_open_component(image_path, cfg),
        'reference': reference_score_component(image_path, cfg),
    }


def weighted_base_score(components: Dict[str, Optional[float]], cfg: dict) -> float:
    weights = cfg.get('culling', {}).get('base_weights', {})
    normalized = _normalized_active_weights(weights, components)
    if not normalized:
        return clip01(generic_aesthetic_score(''))
    total = 0.0
    for key, weight in normalized.items():
        value = components.get(key)
        if value is not None:
            total += float(weight) * float(value)
    return clip01(total)


def load_personal_model(model_path: str | Path) -> Optional[dict]:
    path = Path(model_path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def personal_model_score(image_path: str | Path, model: Optional[dict]) -> Optional[float]:
    if not model:
        return None
    f = extract_features(image_path)
    generic = generic_aesthetic_score(image_path)
    feature_map = {
        'bias': 1.0,
        'generic_score': generic,
        'megapixels': f['megapixels'],
        'aspect_score': f['aspect_score'],
        'portrait': f['portrait'],
        'filesize_mb': f['filesize_mb'],
        'edge_var': f['edge_var'],
    }
    if model.get('model_type') == 'prototype_v1':
        stats = model.get('feature_stats', {}) or {}
        distances = []
        for name, payload in stats.items():
            if name not in feature_map:
                continue
            mean_value = float(payload.get('mean', 0.0))
            std_value = max(float(payload.get('std', 0.0)), 1e-6)
            z_distance = abs(float(feature_map[name]) - mean_value) / (std_value * 2.5)
            distances.append(min(1.0, z_distance))
        if not distances:
            return None
        return clip01(1.0 - (sum(distances) / len(distances)))
    weights = model.get('weights', {})
    score = 0.0
    for name, weight in weights.items():
        score += float(weight) * float(feature_map.get(name, 0.0))
    scale = float(model.get('score_scale', 1.0)) or 1.0
    offset = float(model.get('score_offset', 0.0))
    normalized = (score + offset) / scale
    return clip01(normalized)
```

Es verwendet Pillow und NumPy. `extract_features` erzeugt mindestens Breite, Höhe, Megapixel, Seitenverhältnis, Edge-Varianz, mittlere Helligkeit, Clipping-Anteile, Kontrast und Sättigung. Alle finalen Scorewerte werden auf 0.0 bis 1.0 begrenzt. Fehlende optionale Daten führen zu dynamischer Neu-Normierung der vorhandenen Gewichte.

### `app/training.py`

```python
from __future__ import annotations

from statistics import mean, pstdev

from pathlib import Path
import csv
import json
from datetime import datetime
from typing import List, Dict
import numpy as np

from metadata_rating import read_rating
from aesthetic import extract_features, generic_aesthetic_score


IMAGE_EXTS = {'.jpg', '.jpeg', '.JPG', '.JPEG'}


def collect_labeled_images(images_dir: str | Path) -> List[Dict[str, float]]:
    rows = []
    for path in sorted(Path(images_dir).rglob('*')):
        if path.suffix not in IMAGE_EXTS or not path.is_file():
            continue
        rating = read_rating(path)
        if rating is None:
            continue
        features = extract_features(path)
        rows.append({
            'path': str(path),
            'rating': float(rating),
            'generic_score': generic_aesthetic_score(path),
            'megapixels': features['megapixels'],
            'aspect_score': features['aspect_score'],
            'portrait': features['portrait'],
            'filesize_mb': features['filesize_mb'],
            'edge_var': features['edge_var'],
        })
    return rows


def fit_personal_model(rows: List[Dict[str, float]]) -> Dict:
    feature_names = ['bias', 'generic_score', 'megapixels', 'aspect_score', 'portrait', 'filesize_mb', 'edge_var']
    X = []
    y = []
    for row in rows:
        X.append([
            1.0,
            row['generic_score'],
            row['megapixels'],
            row['aspect_score'],
            row['portrait'],
            row['filesize_mb'],
            row['edge_var'],
        ])
        y.append(row['rating'] / 5.0)
    X = np.array(X, dtype=float)
    y = np.array(y, dtype=float)
    weights, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ weights
    score_min = float(pred.min()) if len(pred) else 0.0
    score_max = float(pred.max()) if len(pred) else 1.0
    scale = score_max - score_min if score_max != score_min else 1.0
    return {
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'feature_names': feature_names,
        'weights': {name: float(value) for name, value in zip(feature_names, weights)},
        'score_offset': -score_min,
        'score_scale': scale,
        'training_rows': len(rows),
    }


def export_labels(rows: List[Dict[str, float]], csv_path: str | Path) -> None:
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ['path', 'rating'])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def train_from_directory(images_dir: str | Path, model_out: str | Path, labels_out: str | Path, min_images: int = 20) -> Dict:
    rows = collect_labeled_images(images_dir)
    if len(rows) < int(min_images):
        raise ValueError(f'Not enough labeled images: found {len(rows)}, need at least {min_images}.')
    model = fit_personal_model(rows)
    export_labels(rows, labels_out)
    model_out = Path(model_out)
    model_out.parent.mkdir(parents=True, exist_ok=True)
    model_out.write_text(json.dumps(model, indent=2), encoding='utf-8')
    return model


PERSONAL_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.JPG', '.JPEG', '.PNG', '.WEBP', '.BMP', '.TIF', '.TIFF'}


def _personal_cfg(cfg: dict) -> dict:
    section = cfg.get('personal_scoring', {}) or {}
    source_dir = section.get('source_dir') or cfg.get('training', {}).get('sample_images_dir')
    model_path = section.get('model_path') or cfg.get('paths', {}).get('personal_model')
    cache_dir = section.get('cache_dir') or str(Path(model_path).parent)
    return {
        'enabled': bool(section.get('enabled', True)),
        'source_dir': str(source_dir),
        'model_path': str(model_path),
        'cache_dir': str(cache_dir),
        'cache_enabled': bool(section.get('cache_enabled', True)),
        'cache_rebuild_mode': str(section.get('cache_rebuild_mode', 'incremental')),
        'force_cache_rebuild': bool(section.get('force_cache_rebuild', False)),
        'auto_train_on_change': bool(section.get('auto_train_on_change', True)),
        'recursive': bool(section.get('recursive', False)),
        'min_reference_images': int(section.get('min_reference_images', 5)),
    }


def _iter_personal_images(source_dir: Path, recursive: bool) -> list[Path]:
    if not source_dir.exists():
        return []
    iterator = source_dir.rglob('*') if recursive else source_dir.iterdir()
    return sorted([p for p in iterator if p.is_file() and p.suffix in PERSONAL_IMAGE_EXTS])


def _personal_cache_paths(cfg: dict) -> dict:
    pcfg = _personal_cfg(cfg)
    cache_dir = Path(pcfg['cache_dir'])
    cache_dir.mkdir(parents=True, exist_ok=True)
    model_path = Path(pcfg['model_path'])
    return {
        'dir': cache_dir,
        'model': model_path,
        'meta': cache_dir / 'personal_model_meta.json',
        'report': cache_dir / 'last_personal_rebuild_report.json',
    }


def build_personal_reference_state(cfg: dict) -> dict:
    pcfg = _personal_cfg(cfg)
    source_dir = Path(pcfg['source_dir'])
    images = _iter_personal_images(source_dir, pcfg['recursive'])
    return {
        'source_dir': str(source_dir),
        'recursive': pcfg['recursive'],
        'images': [
            {
                'relative_path': str(p.relative_to(source_dir)),
                'size': p.stat().st_size,
                'mtime_ns': p.stat().st_mtime_ns,
            }
            for p in images
        ],
    }


def build_personal_model_from_directory(images_dir: str | Path, model_out: str | Path, recursive: bool = False) -> dict:
    from aesthetic import extract_features, generic_aesthetic_score
    images_dir = Path(images_dir)
    model_out = Path(model_out)
    rows = []
    for image_path in _iter_personal_images(images_dir, recursive):
        feats = extract_features(image_path)
        rows.append({
            'generic_score': float(generic_aesthetic_score(image_path)),
            'megapixels': float(feats['megapixels']),
            'aspect_score': float(feats['aspect_score']),
            'portrait': float(feats['portrait']),
            'filesize_mb': float(feats['filesize_mb']),
            'edge_var': float(feats['edge_var']),
        })
    if not rows:
        raise ValueError('No usable sample images found for personal model.')
    feature_names = list(rows[0].keys())
    stats = {}
    for name in feature_names:
        values = [float(r[name]) for r in rows]
        stats[name] = {
            'mean': mean(values),
            'std': pstdev(values) if len(values) > 1 else 0.05,
        }
    model = {
        'model_type': 'prototype_v1',
        'feature_stats': stats,
        'training_rows': len(rows),
        'source_dir': str(images_dir),
    }
    model_out.parent.mkdir(parents=True, exist_ok=True)
    model_out.write_text(json.dumps(model, indent=2), encoding='utf-8')
    return model


def _write_personal_report(cfg: dict, report: dict) -> None:
    paths = _personal_cache_paths(cfg)
    paths['report'].write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


def load_or_rebuild_personal_model(cfg: dict):
    from aesthetic import load_personal_model
    pcfg = _personal_cfg(cfg)
    paths = _personal_cache_paths(cfg)
    info = {
        'status': 'disabled' if not pcfg['enabled'] else 'missing',
        'used_cache': False,
        'rebuilt_cache': False,
        'source_dir': pcfg['source_dir'],
        'source_image_count': 0,
        'model_path': str(paths['model']),
    }
    if not pcfg['enabled']:
        return None, info
    source_dir = Path(pcfg['source_dir'])
    state = build_personal_reference_state(cfg)
    images = state['images']
    info['source_image_count'] = len(images)
    if not source_dir.exists():
        info['status'] = 'reference_dir_missing'
        _write_personal_report(cfg, info | {'reference_state': state})
        return None, info
    if len(images) < pcfg['min_reference_images']:
        info['status'] = 'not_enough_reference_images'
        _write_personal_report(cfg, info | {'reference_state': state})
        return None, info
    rebuild = bool(pcfg['force_cache_rebuild']) or not paths['model'].exists()
    meta = {}
    if paths['meta'].exists():
        try:
            meta = json.loads(paths['meta'].read_text(encoding='utf-8'))
        except Exception:
            meta = {}
    if pcfg['auto_train_on_change'] and meta.get('reference_state') != state:
        rebuild = True
    if rebuild:
        model = build_personal_model_from_directory(source_dir, paths['model'], recursive=pcfg['recursive'])
        info['status'] = 'cache_rebuilt'
        info['rebuilt_cache'] = True
        payload = {'reference_state': state, 'status': info['status'], 'source_image_count': info['source_image_count']}
        paths['meta'].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        _write_personal_report(cfg, info | payload)
        return model, info
    model = load_personal_model(paths['model'])
    info['status'] = 'cache_used' if model else 'model_missing'
    info['used_cache'] = bool(model)
    _write_personal_report(cfg, info | {'reference_state': state})
    return model, info
```

Es unterstützt zwei Modelltypen: ein lineares, aus XMP-Sternen trainiertes Modell sowie `prototype_v1`, das Mittelwert und Standardabweichung visueller Merkmale aus den Beispielbildern speichert. Der Cache wird bei geänderten Referenzdateien anhand von relativem Pfad, Größe und `mtime_ns` neu aufgebaut.

### `app/family_recognition.py`

```python
from __future__ import annotations

import json
import pickle
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    import face_recognition
except Exception:  # pragma: no cover
    face_recognition = None

IMAGE_EXTS = {'.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG'}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def get_cache_paths(cfg: dict) -> dict[str, Path]:
    fr_cfg = cfg.get('family_recognition', {})
    cache_dir = Path(fr_cfg.get('cache_dir', 'models/family_faces'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return {
        'dir': cache_dir,
        'encodings': cache_dir / 'family_encodings.pkl',
        'meta': cache_dir / 'family_encodings.meta.json',
        'index': cache_dir / 'family_index.json',
        'report': cache_dir / 'last_rebuild_report.json',
    }


def _selected_reference_images(reference_dir: Path, max_images_per_person: int) -> dict[str, list[Path]]:
    selected = {}
    for person_dir in sorted(reference_dir.iterdir()):
        if not person_dir.is_dir():
            continue
        images = [p for p in sorted(person_dir.iterdir()) if p.suffix in IMAGE_EXTS]
        selected[person_dir.name] = images[:max_images_per_person]
    return selected


def build_reference_state(cfg: dict) -> dict:
    fr_cfg = cfg.get('family_recognition', {})
    reference_dir = Path(fr_cfg.get('reference_dir', 'family_faces'))
    max_images = int(fr_cfg.get('max_reference_images_per_person', 200))
    state = {
        'reference_dir': str(reference_dir),
        'max_reference_images_per_person': max_images,
        'people': {},
    }
    if not reference_dir.exists():
        return state
    for person, images in _selected_reference_images(reference_dir, max_images).items():
        rows = []
        for img in images:
            stat = img.stat()
            rows.append({
                'file': img.name,
                'size': stat.st_size,
                'mtime_ns': stat.st_mtime_ns,
            })
        state['people'][person] = rows
    return state


def _cache_matches(cfg: dict, meta: dict) -> bool:
    expected = build_reference_state(cfg)
    return meta.get('reference_state') == expected


def _load_cache(cfg: dict) -> dict | None:
    paths = get_cache_paths(cfg)
    if not paths['encodings'].exists() or not paths['meta'].exists():
        return None
    meta = json.loads(paths['meta'].read_text(encoding='utf-8'))
    if not _cache_matches(cfg, meta):
        return None
    with paths['encodings'].open('rb') as handle:
        payload = pickle.load(handle)
    model = {
        'enabled': True,
        'library_available': face_recognition is not None,
        'reference_dir': cfg.get('family_recognition', {}).get('reference_dir'),
        'people': payload.get('people', {}),
        'tolerance': float(cfg.get('family_recognition', {}).get('match_tolerance', 0.48)),
        'status': 'cache_loaded',
        'used_cache': True,
        'rebuilt_cache': False,
        'cache_dir': str(paths['dir']),
        'cache_meta_path': str(paths['meta']),
        'cache_encodings_path': str(paths['encodings']),
        'person_count': len(payload.get('people', {})),
    }
    return model


def _write_cache(cfg: dict, people: dict, status: str, loaded_people: list[str]) -> dict:
    paths = get_cache_paths(cfg)
    payload = {'people': people}
    meta = {
        'created_at': now(),
        'status': status,
        'reference_state': build_reference_state(cfg),
        'people': loaded_people,
        'person_count': len(loaded_people),
    }
    with paths['encodings'].open('wb') as handle:
        pickle.dump(payload, handle)
    paths['meta'].write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    paths['index'].write_text(json.dumps({'people': loaded_people, 'person_count': len(loaded_people)}, indent=2, ensure_ascii=False), encoding='utf-8')
    return {
        'cache_dir': str(paths['dir']),
        'cache_meta_path': str(paths['meta']),
        'cache_encodings_path': str(paths['encodings']),
    }


def prepare_family_model(cfg: dict, force_rebuild: bool = False, allow_when_disabled: bool = False) -> dict:
    fr_cfg = cfg.get('family_recognition', {})
    model = {
        'enabled': bool(fr_cfg.get('enabled', False)),
        'library_available': face_recognition is not None,
        'reference_dir': fr_cfg.get('reference_dir'),
        'people': {},
        'status': 'disabled',
        'used_cache': False,
        'rebuilt_cache': False,
        'cache_dir': str(get_cache_paths(cfg)['dir']),
        'cache_meta_path': str(get_cache_paths(cfg)['meta']),
        'cache_encodings_path': str(get_cache_paths(cfg)['encodings']),
        'person_count': 0,
    }
    if not model['enabled'] and not allow_when_disabled:
        return model
    if face_recognition is None:
        model['status'] = 'face_library_missing'
        return model

    reference_dir = Path(fr_cfg.get('reference_dir', 'family_faces'))
    if not reference_dir.exists():
        model['status'] = 'reference_dir_missing'
        return model

    cache_enabled = bool(fr_cfg.get('cache_enabled', True))
    if cache_enabled and not force_rebuild:
        cached = _load_cache(cfg)
        if cached is not None:
            return cached

    tolerance = float(fr_cfg.get('match_tolerance', 0.48))
    max_images_per_person = int(fr_cfg.get('max_reference_images_per_person', 200))
    min_images_per_person = int(fr_cfg.get('min_reference_images_per_person', 3))
    people = {}
    loaded_people = []
    for person, images in _selected_reference_images(reference_dir, max_images_per_person).items():
        encodings = []
        for img_path in images:
            try:
                image = face_recognition.load_image_file(str(img_path))
                found = face_recognition.face_encodings(image)
                if found:
                    encodings.append(found[0])
            except Exception:
                continue
        if len(encodings) >= min_images_per_person:
            people[person] = {'encodings': encodings, 'samples': len(encodings)}
            loaded_people.append(person)
    model.update({
        'people': people,
        'tolerance': tolerance,
        'status': 'cache_rebuilt' if cache_enabled else 'ready_no_cache',
        'used_cache': False,
        'rebuilt_cache': cache_enabled,
        'person_count': len(loaded_people),
    })
    if cache_enabled:
        model.update(_write_cache(cfg, people, model['status'], loaded_people))
    return model


def write_rebuild_report(cfg: dict, report: dict) -> str:
    paths = get_cache_paths(cfg)
    payload = dict(report)
    payload['written_at'] = now()
    paths['report'].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    return str(paths['report'])


def load_family_model(cfg: dict) -> dict:
    return prepare_family_model(cfg, force_rebuild=bool(cfg.get('family_recognition', {}).get('force_cache_rebuild', False)))


def rebuild_family_cache(cfg: dict) -> dict:
    model = prepare_family_model(cfg, force_rebuild=True, allow_when_disabled=True)
    report = {
        'status': model.get('status'),
        'cache_dir': model.get('cache_dir'),
        'cache_meta_path': model.get('cache_meta_path'),
        'cache_encodings_path': model.get('cache_encodings_path'),
        'person_count': model.get('person_count', 0),
        'used_cache': model.get('used_cache', False),
        'rebuilt_cache': model.get('rebuilt_cache', False),
    }
    report['report_path'] = write_rebuild_report(cfg, report)
    return report


def build_family_tags(people: list[str]) -> list[str]:
    if not people:
        return []
    tags = ['family:match:true']
    for person in sorted(set(people)):
        tags.append(f'person:{person}')
    return sorted(set(tags))


def detect_family_members(image_path: Path, cfg: dict, model: dict) -> dict:
    fr_cfg = cfg.get('family_recognition', {})
    result = {
        'status': model.get('status', 'disabled'),
        'detected_people': [],
        'family_score': 0.0,
        'protected_by_family_rule': False,
        'tags': [],
        'regions': [],
        'metadata_tags_written': False,
        'metadata_write_status': 'not_attempted',
    }
    if not fr_cfg.get('enabled', False):
        return result
    if model.get('status') in {'disabled', 'face_library_missing', 'reference_dir_missing'}:
        return result
    if not model.get('people'):
        result['status'] = 'no_reference_faces_loaded'
        return result
    try:
        image = face_recognition.load_image_file(str(image_path))
        locations = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, locations)
    except Exception:
        result['status'] = 'image_read_error'
        return result

    weights = fr_cfg.get('person_weights', {}) or {}
    seen = []
    regions = []
    for loc, enc in zip(locations, encodings):
        best_name = None
        best_distance = None
        for person, pdata in model['people'].items():
            distances = face_recognition.face_distance(pdata['encodings'], enc)
            if len(distances) == 0:
                continue
            distance = float(min(distances))
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_name = person
        if best_name is not None and best_distance is not None and best_distance <= float(model['tolerance']):
            if best_name not in seen:
                seen.append(best_name)
            top, right, bottom, left = loc
            regions.append({'name': best_name, 'left': left, 'top': top, 'right': right, 'bottom': bottom, 'distance': round(best_distance, 4)})

    score = 0.0
    for person in seen:
        score += float(weights.get(person, fr_cfg.get('default_person_weight', 0.35)))
    score = min(1.0, score)
    result.update({
        'status': 'matched' if seen else 'no_family_match',
        'detected_people': seen,
        'family_score': score,
        'protected_by_family_rule': bool(seen) and bool(fr_cfg.get('protect_detected_family', True)),
        'tags': build_family_tags(seen),
        'regions': regions,
    })
    return result


def write_native_tags(image_path: Path, tags: list[str], cfg: dict, face_regions: list[dict] | None = None) -> tuple[bool, str]:
    fr_cfg = cfg.get('family_recognition', {})
    if not tags:
        return False, 'no_tags'
    exiftool_path = shutil.which(fr_cfg.get('exiftool_path', 'exiftool'))
    if not exiftool_path:
        return False, 'exiftool_missing'
    cmd = [exiftool_path, '-overwrite_original']
    for tag in sorted(set(tags)):
        cmd.append(f'-XMP-dc:Subject+={tag}')
        cmd.append(f'-IPTC:Keywords+={tag}')
    cmd.append(str(image_path))
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        return False, 'exiftool_exec_error'
    return completed.returncode == 0, 'ok' if completed.returncode == 0 else 'exiftool_failed'
```

Der Cache besteht mindestens aus `family_encodings.pkl`, `family_encodings.meta.json`, `family_index.json` und `last_rebuild_report.json`. Referenzen liegen in `family_faces/<Person>/`. Für jede erkannte Person wird ein konfigurierbares Gewicht addiert, maximal 1.0; bei `protect_detected_family: true` wird ein späteres `reject` auf mindestens `review` angehoben.

### `app/photo_workflow.py`

```python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import re
import zipfile

import yaml

from aesthetic import base_score_components, ensure_reference_profile, generic_aesthetic_score, load_personal_model, personal_model_score, weighted_base_score
from family_recognition import detect_family_members, load_family_model, rebuild_family_cache, write_native_tags
from series_culling import apply_series_culling
from metadata_writer import write_culling_metadata
from training import train_from_directory, load_or_rebuild_personal_model

RAW_EXTS = {'.ARW', '.arw'}
JPG_EXTS = {'.JPG', '.jpg', '.JPEG', '.jpeg'}
RAW_PATTERN = re.compile(r'^\d{8}$')
DONE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}(_.*)?$')

COUNT_PROCESSED = 0
COUNT_MOVED = 0
COUNT_SKIPPED = 0
COUNT_ERRORS = 0
COUNT_FOUND_SRC = 0
COUNT_FOUND_DONE = 0
LAST_FAMILY_RUN_INFO = {}
LAST_ZIP_CONFLICTS: list[dict] = []

SCRIPT_NAME = 'Synology Photo Workflow with AI Culling'
SCRIPT_VERSION = 'v1.3'
SCRIPT_DESCRIPTION = 'Processes TEMP_SD, moves folders to TEMP_IMAGES, post-processes TEMP_DONE, adds AI-assisted JPG culling, optional family face tagging, and cached family encodings.'


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def reset_counters() -> None:
    global COUNT_PROCESSED, COUNT_MOVED, COUNT_SKIPPED, COUNT_ERRORS, COUNT_FOUND_SRC, COUNT_FOUND_DONE, LAST_FAMILY_RUN_INFO, LAST_ZIP_CONFLICTS
    COUNT_PROCESSED = 0
    COUNT_MOVED = 0
    COUNT_SKIPPED = 0
    COUNT_ERRORS = 0
    COUNT_FOUND_SRC = 0
    COUNT_FOUND_DONE = 0
    LAST_FAMILY_RUN_INFO = {}
    LAST_ZIP_CONFLICTS = []
LAST_ZIP_CONFLICTS: list[dict] = []


def load_config(path: str | Path) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    cfg.setdefault('reporting', {})
    cfg['reporting'].setdefault('write_json_summary', True)
    cfg['reporting'].setdefault('json_summary_dir', str(Path(cfg['paths']['base_dir']) / 'run_summaries'))
    cfg['reporting'].setdefault('stdout_mode', 'scheduler_mail')
    cfg.setdefault('workflow', {})
    wf = cfg['workflow']
    wf.setdefault('wait_time_seconds', 60)
    wf.setdefault('stale_lock_seconds', 43200)
    wf.setdefault('merge_strategy', 'merge_then_fallback')
    wf.setdefault('create_done_marker_before_move', True)
    wf.setdefault('date_reconstruction', {})
    dr = wf['date_reconstruction']
    dr.setdefault('mode', 'legacy_bash')
    dr.setdefault('decade_prefix', '202')
    dr.setdefault('year_digit_index', 3)
    cfg.setdefault('family_recognition', {})
    fr = cfg['family_recognition']
    fr.setdefault('enabled', False)
    fr.setdefault('reference_dir', str(Path(cfg['paths']['base_dir']) / 'family_faces'))
    fr.setdefault('cache_enabled', True)
    fr.setdefault('cache_dir', str(Path(cfg['paths']['base_dir']) / 'models' / 'family_faces'))
    fr.setdefault('cache_rebuild_mode', 'incremental')
    fr.setdefault('force_cache_rebuild', False)
    fr.setdefault('protect_detected_family', True)
    fr.setdefault('score_boost_weight', 0.20)
    fr.setdefault('write_native_tags', True)
    fr.setdefault('write_face_regions', False)
    fr.setdefault('exiftool_path', 'exiftool')
    fr.setdefault('match_tolerance', 0.48)
    fr.setdefault('default_person_weight', 0.35)
    fr.setdefault('min_reference_images_per_person', 3)
    fr.setdefault('max_reference_images_per_person', 200)
    fr.setdefault('person_weights', {})
    cfg.setdefault('series_detection', {})
    sd = cfg['series_detection']
    sd.setdefault('enabled', True)
    sd.setdefault('cluster_eps', 0.18)
    sd.setdefault('min_samples', 2)
    sd.setdefault('preview_size', 32)
    sd.setdefault('review_margin', 0.03)
    sd.setdefault('demote_non_best_to', 'review')
    cfg.setdefault('metadata_culling', {})
    mc = cfg['metadata_culling']
    mc.setdefault('enabled', True)
    mc.setdefault('write_rating', True)
    mc.setdefault('write_keywords', True)
    mc.setdefault('keep_backup', False)
    mc.setdefault('exiftool_path', 'exiftool')
    mc.setdefault('rating_map', {'keep': 5, 'review': 3, 'reject': 0})
    cfg.setdefault('culling', {})
    cull = cfg['culling']
    cull.setdefault('enabled', True)
    cull.setdefault('move_files', True)
    cull.setdefault('create_review_folder', True)
    cull.setdefault('create_rejected_folder', True)
    cull.setdefault('keep_threshold', 0.65)
    cull.setdefault('reject_threshold', 0.35)
    cull.setdefault('weights', {'generic': 0.55, 'personal': 0.45})
    cull.setdefault('component_weights', {'base_score': 0.55, 'eye_score': 0.10, 'personal_score': 0.20, 'family_score': 0.15})
    cull.setdefault('base_weights', {'sharp': 0.36, 'aesth': 0.36, 'exposure': 0.18, 'reference': 0.10})
    cull.setdefault('eye_detection', {'enabled': True})
    cull.setdefault('reference_scoring', {'enabled': False, 'folder': str(Path(cfg['paths']['base_dir']) / 'reference_images'), 'recursive': False, 'preview_size': 32, 'cache_enabled': True, 'cache_dir': str(Path(cfg['paths']['base_dir']) / 'models' / 'reference_scoring'), 'force_cache_rebuild': False})
    cull.setdefault('star_rating_bands', {5: 0.90, 4: 0.75, 3: 0.60, 2: 0.40, 1: 0.20, 0: 0.00})
    personal_cfg = cfg.setdefault('personal_scoring', {})
    personal_cfg.setdefault('enabled', True)
    personal_cfg.setdefault('source_dir', cfg.get('training', {}).get('sample_images_dir', cull.get('reference_scoring', {}).get('folder', str(Path(cfg['paths']['base_dir']) / 'reference_images'))))
    personal_cfg.setdefault('model_path', cfg['paths'].get('personal_model', str(Path(cfg['paths']['base_dir']) / 'models' / 'personal' / 'user_taste_model.json')))
    personal_cfg.setdefault('cache_enabled', True)
    personal_cfg.setdefault('cache_dir', str(Path(personal_cfg['model_path']).parent))
    personal_cfg.setdefault('cache_rebuild_mode', 'incremental')
    personal_cfg.setdefault('force_cache_rebuild', False)
    personal_cfg.setdefault('auto_train_on_change', True)
    personal_cfg.setdefault('recursive', False)
    personal_cfg.setdefault('min_reference_images', 5)
    metadata_cfg = cfg.setdefault('metadata_culling', {})
    metadata_cfg.setdefault('keyword_schema', 'namespaced_v1')
    metadata_cfg.setdefault('write_score_bands', True)
    metadata_cfg.setdefault('write_raw_scores_to_keywords', False)
    return cfg


def log(cfg: dict, message: str, error: bool = False) -> None:
    target = Path(cfg['paths']['error_log'] if error else cfg['paths']['log_file'])
    target.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n"
    with target.open('a', encoding='utf-8') as handle:
        handle.write(line)
    print(line, end='', file=sys.stderr if error else sys.stdout)


def print_start_banner(cfg: dict, command: str) -> None:
    print(f"===== START: {datetime.now()} =====")
    print(f"SCRIPT : {SCRIPT_NAME}")
    print(f"VERSION : {SCRIPT_VERSION}")
    print(f"COMMAND : {command}")
    print(f"PURPOSE : {SCRIPT_DESCRIPTION}")
    print(f"BASE_DIR : {cfg['paths']['base_dir']}")
    print(f"SRC : {cfg['paths']['temp_sd']}")
    print(f"DEST : {cfg['paths']['temp_images']}")
    print(f"DONE : {cfg['paths']['temp_done']}")
    print('========================================')


def build_summary_payload(cfg: dict, command: str, status: str, started_at: str, finished_at: str, json_summary_path: str | None) -> dict:
    return {
        'script_name': SCRIPT_NAME,
        'script_version': SCRIPT_VERSION,
        'command': command,
        'status': status,
        'started_at': started_at,
        'finished_at': finished_at,
        'paths': {
            'base_dir': cfg['paths']['base_dir'],
            'temp_sd': cfg['paths']['temp_sd'],
            'temp_images': cfg['paths']['temp_images'],
            'temp_done': cfg['paths']['temp_done'],
            'log_file': cfg['paths']['log_file'],
            'error_log': cfg['paths']['error_log'],
        },
        'counts': {
            'found_temp_sd': COUNT_FOUND_SRC,
            'found_temp_done': COUNT_FOUND_DONE,
            'processed': COUNT_PROCESSED,
            'moved_merged': COUNT_MOVED,
            'skipped': COUNT_SKIPPED,
            'errors': COUNT_ERRORS,
        },
        'family_recognition': LAST_FAMILY_RUN_INFO,
        'zip_conflicts': LAST_ZIP_CONFLICTS,
        'json_summary_path': json_summary_path,
    }


def write_json_summary(cfg: dict, payload: dict) -> str | None:
    if not cfg['reporting'].get('write_json_summary', True):
        return None
    summary_dir = Path(cfg['reporting']['json_summary_dir'])
    summary_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = summary_dir / f"{payload['command']}_{timestamp}.json"
    payload = dict(payload)
    payload['json_summary_path'] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return str(path)


def print_scheduler_summary(cfg: dict, payload: dict) -> None:
    print('SUMMARY')
    print(f"Status: {payload['status']}")
    print(f"Command: {payload['command']}")
    print(f"Found folders in TEMP_SD: {payload['counts']['found_temp_sd']}")
    print(f"Found folders in TEMP_DONE: {payload['counts']['found_temp_done']}")
    print(f"Processed folders: {payload['counts']['processed']}")
    print(f"Moved/Merged: {payload['counts']['moved_merged']}")
    print(f"Skipped folders: {payload['counts']['skipped']}")
    print(f"Errors: {payload['counts']['errors']}")
    if payload.get('family_recognition'):
        print(f"Family recognition: {payload['family_recognition']}")
    print(f"Log file: {payload['paths']['log_file']}")
    print(f"Error log: {payload['paths']['error_log']}")
    if payload.get('json_summary_path'):
        print(f"JSON summary: {payload['json_summary_path']}")
    print(f"Started: {payload['started_at']}")
    print(f"Finished: {payload['finished_at']}")
    print('===== END =====')


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def path_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def require_within(cfg: dict, target: Path) -> None:
    if not cfg['safety'].get('require_paths_within_base_dir', True):
        return
    base = Path(cfg['paths']['base_dir']).resolve()
    if not path_within(base, target):
        raise ValueError(f'Path escapes base_dir: {target}')


@contextmanager
def file_lock(cfg: dict):
    lock_path = Path(cfg['paths']['lock_file'])
    ensure_dir(lock_path.parent)
    stale_seconds = int(cfg['workflow'].get('stale_lock_seconds', 43200))
    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text(encoding='utf-8'))
            started_at = str(data['started_at']).replace('Z', '+00:00')
            ts = datetime.fromisoformat(started_at).timestamp()
            if time.time() - ts > stale_seconds:
                lock_path.unlink()
            else:
                raise RuntimeError(f'Active lock file present: {lock_path}')
        except RuntimeError:
            raise
        except Exception:
            raise RuntimeError(f'Active lock file present: {lock_path}')
    lock_path.write_text(json.dumps({'pid': os.getpid(), 'started_at': now()}), encoding='utf-8')
    try:
        yield
    finally:
        if lock_path.exists():
            lock_path.unlink()



def make_date_name(name: str, cfg: dict) -> str:
    if not RAW_PATTERN.match(name):
        return name
    date_cfg = cfg.get('workflow', {}).get('date_reconstruction', {})
    mode = str(date_cfg.get('mode', 'legacy_bash')).strip().lower()
    if mode == 'legacy_bash':
        decade_prefix = str(date_cfg.get('decade_prefix', '202')).strip()
        year_digit_index = int(date_cfg.get('year_digit_index', 3))
        if not re.fullmatch(r'\d{3}', decade_prefix):
            raise ValueError(f'workflow.date_reconstruction.decade_prefix must be exactly 3 digits, got: {decade_prefix!r}')
        if not 0 <= year_digit_index < len(name):
            raise ValueError(f'workflow.date_reconstruction.year_digit_index out of range: {year_digit_index}')
        year = f"{decade_prefix}{name[year_digit_index]}"
        month, day = name[4:6], name[6:8]
        return f'{year}-{month}-{day}'
    if mode == 'full_year':
        return f'{name[0:4]}-{name[4:6]}-{name[6:8]}'
    raise ValueError(f'Unsupported workflow.date_reconstruction.mode: {mode}')


def classify_zip_artifact(zip_path: Path) -> str:
    name = zip_path.name
    if name.endswith('_ALL_JPG.zip') or '_ALL_JPG_EXTRA_' in name:
        return 'all_jpg'
    if name.endswith('_SORT_ARW.zip') or '_SORT_ARW_EXTRA_' in name:
        return 'sort_arw'
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_names = [n for n in zf.namelist() if not n.endswith('/')]
    except zipfile.BadZipFile:
        return 'unsorted'
    if file_names and all(Path(n).suffix.lower() in {'.jpg', '.jpeg'} for n in file_names):
        return 'all_jpg'
    if file_names and all(Path(n).suffix.lower() in {'.arw'} for n in file_names):
        return 'sort_arw'
    return 'unsorted'


def next_available_artifact_path(save_dir: Path, folder_name: str, artifact_type: str) -> Path:
    if artifact_type == 'all_jpg':
        base = save_dir / f'{folder_name}_ALL_JPG.zip'
        extra_template = f'{folder_name}_ALL_JPG_EXTRA_{{}}.zip'
    elif artifact_type == 'sort_arw':
        base = save_dir / f'{folder_name}_SORT_ARW.zip'
        extra_template = f'{folder_name}_SORT_ARW_EXTRA_{{}}.zip'
    else:
        idx = 1
        target = save_dir / f'{folder_name}_UNSORTED_{idx}.zip'
        while target.exists():
            idx += 1
            target = save_dir / f'{folder_name}_UNSORTED_{idx}.zip'
        return target
    if not base.exists():
        return base
    idx = 2
    target = save_dir / extra_template.format(idx)
    while target.exists():
        idx += 1
        target = save_dir / extra_template.format(idx)
    return target


def preserve_zip_artifact(zip_path: Path, save_dir: Path, folder_name: str, cfg: dict | None = None) -> Path:
    artifact_type = classify_zip_artifact(zip_path)
    target = next_available_artifact_path(save_dir, folder_name, artifact_type)
    if zip_path.resolve() == target.resolve():
        return zip_path
    if target.exists():
        raise FileExistsError(f'Target ZIP path already exists: {target}')
    zip_path.rename(target)
    if cfg is not None and target.name != zip_path.name:
        entry = {
            'folder': folder_name,
            'source_name': zip_path.name,
            'target_name': target.name,
            'artifact_type': artifact_type,
            'collision_avoided': '_EXTRA_' in target.name or '_UNSORTED_' in target.name,
        }
        LAST_ZIP_CONFLICTS.append(entry)
        log(cfg, f'[ZIP PRESERVE] {zip_path.name} -> {target.name} ({artifact_type})')
    return target


def is_valid_raw_folder(name: str) -> bool:
    return bool(RAW_PATTERN.match(name))


def is_valid_done_folder(name: str) -> bool:
    return bool(DONE_PATTERN.match(name))


def is_stable(folder: Path, wait_seconds: int) -> bool:
    def snapshot() -> list[tuple[str, int]]:
        rows = []
        for p in sorted(folder.rglob('*')):
            if p.is_symlink():
                continue
            if p.is_file():
                rows.append((str(p.relative_to(folder)), p.stat().st_size))
        return rows
    s1 = snapshot()
    time.sleep(wait_seconds)
    s2 = snapshot()
    return s1 == s2


def top_level_files(folder: Path, suffixes: set[str]) -> list[Path]:
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix in suffixes])


def top_level_jpgs(folder: Path) -> list[Path]:
    return top_level_files(folder, JPG_EXTS)


def top_level_arws(folder: Path) -> list[Path]:
    return top_level_files(folder, RAW_EXTS)


def create_zip(zip_path: Path, files: list[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = zip_path.with_suffix(zip_path.suffix + '.tmp')
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(file, arcname=file.name)
    tmp.replace(zip_path)


def resolve_merge_fallback_dir(dest: Path) -> Path:
    candidate = Path(str(dest) + '_MERGE')
    if not candidate.exists():
        return candidate
    i = 2
    while True:
        candidate = Path(str(dest) + f'_MERGE_{i}')
        if not candidate.exists():
            return candidate
        i += 1


def merge_or_move_folder(src: Path, dest: Path, cfg: dict) -> Path:
    global COUNT_MOVED, COUNT_ERRORS
    require_within(cfg, src)
    require_within(cfg, dest.parent)
    if not src.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.move(str(src), str(dest))
        COUNT_MOVED += 1
        log(cfg, f'[MOVE] {src} -> {dest}')
        return dest
    try:
        for item in list(src.iterdir()):
            target = dest / item.name
            if target.exists():
                if item.is_dir() and target.is_dir():
                    merge_or_move_folder(item, target, cfg)
                    if item.exists():
                        shutil.rmtree(item)
                else:
                    fallback = resolve_merge_fallback_dir(dest)
                    shutil.move(str(src), str(fallback))
                    COUNT_MOVED += 1
                    log(cfg, f'[MOVE ALT] {src} -> {fallback}')
                    return fallback
            else:
                shutil.move(str(item), str(target))
        if src.exists():
            shutil.rmtree(src)
        COUNT_MOVED += 1
        log(cfg, f'[MERGE OK] {src} -> {dest}')
        return dest
    except Exception as exc:
        fallback = resolve_merge_fallback_dir(dest)
        if src.exists():
            shutil.move(str(src), str(fallback))
        COUNT_ERRORS += 1
        log(cfg, f'[MOVE ALT] {src} -> {fallback} / reason={exc}', error=True)
        return fallback


def folder_hash(folder: Path) -> str:
    rows = []
    for p in sorted(folder.rglob('*')):
        if p.is_symlink() or not p.is_file() or p.suffix not in JPG_EXTS:
            continue
        rows.append(f'{p.relative_to(folder)}::{p.stat().st_size}')
    return hashlib.md5("\n".join(rows).encode('utf-8')).hexdigest()


def safe_delete(path: Path, cfg: dict) -> None:
    if cfg['safety'].get('never_delete_outside_arw_dir', True) and 'ARW' not in path.parts:
        raise ValueError(f'Refusing to delete outside ARW dir: {path}')
    require_within(cfg, path)
    if path.exists() and path.is_file():
        path.unlink()


def load_personal(cfg: dict):
    return load_or_rebuild_personal_model(cfg)


def score_image(path: Path, cfg: dict, model: dict | None) -> dict:
    generic = generic_aesthetic_score(path)
    components = base_score_components(path, cfg)
    base_score = weighted_base_score(components, cfg)
    personal = personal_model_score(path, model)
    return {
        'generic_score': max(0.0, min(1.0, generic)),
        'base_score': max(0.0, min(1.0, base_score)),
        'personal_score': personal,
        'sharp_score': components.get('sharp'),
        'aesth_score': components.get('aesth'),
        'exposure_score': components.get('exposure'),
        'eye_score': components.get('eyes'),
        'reference_score': components.get('reference'),
    }


def combine_scores(base_score: float, eye_score: float | None, personal_score: float | None, family_score: float | None, cfg: dict) -> float:
    weights = cfg.get('culling', {}).get('component_weights', {})
    active = {
        'base_score': base_score,
        'eye_score': eye_score,
        'personal_score': personal_score,
        'family_score': family_score,
    }
    weighted = {
        key: float(weights.get(key, 0.0))
        for key, value in active.items()
        if value is not None and float(weights.get(key, 0.0)) > 0
    }
    total_weight = sum(weighted.values())
    if total_weight <= 0:
        return max(0.0, min(1.0, float(base_score)))
    score = sum(float(active[key]) * weighted[key] for key in weighted) / total_weight
    return max(0.0, min(1.0, float(score)))

def cull_folder(workdir: Path, cfg: dict) -> dict:
    global LAST_FAMILY_RUN_INFO
    save_dir = ensure_dir(workdir / 'SAVE')
    rejected_dir = workdir / '_Rejected'
    review_dir = workdir / '_Review'
    if cfg['culling'].get('create_rejected_folder', True):
        rejected_dir.mkdir(exist_ok=True)
    if cfg['culling'].get('create_review_folder', True):
        review_dir.mkdir(exist_ok=True)

    reference_profile, reference_info = ensure_reference_profile(cfg)
    cfg.setdefault('culling', {}).setdefault('reference_scoring', {})['_runtime_profile'] = reference_profile
    log(cfg, f"[REFERENCE PROFILE] status={reference_info.get('status')} images={reference_info.get('reference_image_count', 0)} cache_used={reference_info.get('used_cache', False)} cache_rebuilt={reference_info.get('rebuilt_cache', False)} preview_size={reference_info.get('preview_size')}")
    personal_model, personal_info = load_personal(cfg)
    log(cfg, f"[PERSONAL MODEL] status={personal_info.get('status')} images={personal_info.get('source_image_count', 0)} cache_used={personal_info.get('used_cache', False)} cache_rebuilt={personal_info.get('rebuilt_cache', False)}")
    family_model = load_family_model(cfg)
    family_info = {
        'status': family_model.get('status'),
        'used_cache': family_model.get('used_cache', False),
        'rebuilt_cache': family_model.get('rebuilt_cache', False),
        'person_count': family_model.get('person_count', 0),
        'cache_dir': family_model.get('cache_dir'),
    }
    LAST_FAMILY_RUN_INFO = family_info
    log(cfg, f"[FAMILY MODEL] status={family_info['status']} people={family_info['person_count']} cache_used={family_info['used_cache']} cache_rebuilt={family_info['rebuilt_cache']}")

    rows = []
    keep_threshold = float(cfg['culling']['keep_threshold'])
    reject_threshold = float(cfg['culling']['reject_threshold'])
    family_cfg = cfg.get('family_recognition', {})

    for jpg in top_level_jpgs(workdir):
        scored = score_image(jpg, cfg, personal_model)
        family = detect_family_members(jpg, cfg, family_model)
        family_score = float(family.get('family_score', 0.0)) if family_cfg.get('enabled', False) else None
        final = combine_scores(scored['base_score'], scored.get('eye_score'), scored.get('personal_score'), family_score, cfg)

        decision = 'keep'
        score_reason = 'score_keep'
        protected = False
        if final < reject_threshold:
            if family.get('protected_by_family_rule', False):
                decision = 'review'
                score_reason = 'family_protected_score'
                protected = True
            else:
                decision = 'reject'
                score_reason = 'score_reject'
        elif final < keep_threshold:
            decision = 'review'
            score_reason = 'score_review'

        rows.append({
            '_source_path': jpg,
            '_family_tags': family.get('tags', []),
            '_family_regions': family.get('regions', []),
            'file': jpg.name,
            'generic_score': round(scored['generic_score'], 4),
            'base_score': round(scored['base_score'], 4),
            'sharp_score': '' if scored.get('sharp_score') is None else round(float(scored['sharp_score']), 4),
            'aesth_score': '' if scored.get('aesth_score') is None else round(float(scored['aesth_score']), 4),
            'exposure_score': '' if scored.get('exposure_score') is None else round(float(scored['exposure_score']), 4),
            'eye_score': '' if scored.get('eye_score') is None else round(float(scored['eye_score']), 4),
            'reference_score': '' if scored.get('reference_score') is None else round(float(scored['reference_score']), 4),
            'personal_score': '' if scored.get('personal_score') is None else round(float(scored['personal_score']), 4),
            'family_score': '' if family_score is None else round(float(family_score), 4),
            'final_score': round(final, 4),
            'decision': decision,
            'protected_by_family_rule': protected,
            'detected_people': '|'.join(family.get('detected_people', [])),
            'face_status': family.get('status', ''),
        })

    rows = apply_series_culling(rows, cfg)
    family_tag_written = 0
    culling_metadata_written = 0

    for row in rows:
        jpg = row['_source_path']
        target_path = jpg
        if row['decision'] == 'reject' and cfg['culling'].get('move_files', True):
            target_path = rejected_dir / jpg.name
        elif row['decision'] == 'review' and cfg['culling'].get('move_files', True):
            target_path = review_dir / jpg.name
        if target_path != jpg:
            shutil.move(str(jpg), str(target_path))

        family_metadata_ok, family_metadata_status = False, 'not_attempted'
        if family_cfg.get('enabled', False) and family_cfg.get('write_native_tags', True) and row.get('_family_tags'):
            family_metadata_ok, family_metadata_status = write_native_tags(target_path, row.get('_family_tags', []), cfg, row.get('_family_regions', []))
            if family_metadata_ok:
                family_tag_written += 1

        culling_metadata_ok, culling_metadata_status = write_culling_metadata(target_path, row, cfg)
        if culling_metadata_ok:
            culling_metadata_written += 1

        row['family_metadata_written'] = family_metadata_ok
        row['family_metadata_status'] = family_metadata_status
        row['culling_metadata_written'] = culling_metadata_ok
        row['culling_metadata_status'] = culling_metadata_status
        row['final_path'] = str(target_path.relative_to(workdir))
        row.pop('_source_path', None)
        row.pop('_family_tags', None)
        row.pop('_family_regions', None)

    csv_path = save_dir / 'culling_scores.csv'
    fieldnames = [
        'file', 'generic_score', 'base_score', 'sharp_score', 'aesth_score', 'exposure_score', 'eye_score', 'reference_score', 'personal_score', 'family_score', 'final_score', 'score_decision', 'score_reason', 'decision',
        'decision_reason', 'series_id', 'series_size', 'series_rank', 'series_best',
        'series_margin_to_best', 'star_rating', 'protected_by_family_rule', 'detected_people',
        'face_status', 'family_metadata_written', 'family_metadata_status',
        'culling_metadata_written', 'culling_metadata_status', 'final_path'
    ]
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, '') for name in fieldnames})

    clustered_rows = [r for r in rows if r.get('series_id') != 'single']
    summary = {
        'created_at': now(),
        'keep': sum(1 for r in rows if r['decision'] == 'keep'),
        'review': sum(1 for r in rows if r['decision'] == 'review'),
        'reject': sum(1 for r in rows if r['decision'] == 'reject'),
        'total': len(rows),
        'keep_threshold': keep_threshold,
        'reject_threshold': reject_threshold,
        'series_detection_enabled': bool(cfg.get('series_detection', {}).get('enabled', True)),
        'series_clustered_images': len(clustered_rows),
        'series_cluster_count': len({r['series_id'] for r in clustered_rows}),
        'series_best_images': sum(1 for r in rows if r.get('series_best')),
        'family_recognition_enabled': bool(family_cfg.get('enabled', False)),
        'family_tagged_images': sum(1 for r in rows if r['detected_people']),
        'family_protected_images': sum(1 for r in rows if r['protected_by_family_rule']),
        'family_cache_status': family_model.get('status'),
        'family_cache_used': family_model.get('used_cache', False),
        'family_cache_rebuilt': family_model.get('rebuilt_cache', False),
        'family_reference_people': family_model.get('person_count', 0),
        'family_metadata_written': family_tag_written,
        'culling_metadata_written': culling_metadata_written,
    }
    (save_dir / 'culling_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


def prepare_folder_phase1(folder: Path, cfg: dict) -> Path:
    global COUNT_PROCESSED
    src_root = Path(cfg['paths']['temp_sd'])
    name = folder.name
    new_name = make_date_name(name, cfg)
    workdir = folder
    if name != new_name:
        workdir = src_root / new_name
        shutil.move(str(folder), str(workdir))
        log(cfg, f'[RENAMED] {name} -> {new_name}')
    arw_dir = ensure_dir(workdir / 'ARW')
    for arw in top_level_arws(workdir):
        shutil.move(str(arw), str(arw_dir / arw.name))
    save_dir = ensure_dir(workdir / 'SAVE')
    jpgs_before_cull = top_level_jpgs(workdir)
    zip_path = save_dir / f'{workdir.name}_ALL_JPG.zip'
    if jpgs_before_cull:
        create_zip(zip_path, jpgs_before_cull)
        log(cfg, f'[ZIP OK] {zip_path}')
    if cfg['culling'].get('enabled', True):
        summary = cull_folder(workdir, cfg)
        log(cfg, f"[CULL] keep={summary['keep']} review={summary['review']} reject={summary['reject']} total={summary['total']} family_tagged={summary['family_tagged_images']} family_cache_status={summary['family_cache_status']}")
    (workdir / '.DONE').touch()
    COUNT_PROCESSED += 1
    log(cfg, f'[DONE] {workdir.name}')
    return merge_or_move_folder(workdir, Path(cfg['paths']['temp_images']) / workdir.name, cfg)


def run_phase1(cfg: dict, folder: str | None = None) -> None:
    global COUNT_FOUND_SRC, COUNT_SKIPPED
    src_root = ensure_dir(cfg['paths']['temp_sd'])
    folders = [Path(folder)] if folder else [p for p in sorted(src_root.iterdir()) if p.is_dir()]
    for dir_path in folders:
        if not dir_path.exists() or not dir_path.is_dir():
            continue
        COUNT_FOUND_SRC += 1
        name = dir_path.name
        if not (is_valid_raw_folder(name) or is_valid_done_folder(name)):
            COUNT_SKIPPED += 1
            log(cfg, f'[SKIP TOP] Unsupported folder: {name}')
            continue
        if not (dir_path / '.DONE').exists() and not is_stable(dir_path, int(cfg['workflow']['wait_time_seconds'])):
            COUNT_SKIPPED += 1
            log(cfg, f'[WAIT] Transfer still running: {name}')
            continue
        if (dir_path / '.DONE').exists():
            merge_or_move_folder(dir_path, Path(cfg['paths']['temp_images']) / name, cfg)
            continue
        prepare_folder_phase1(dir_path, cfg)


def process_done_folder(dir_path: Path, cfg: dict) -> None:
    arw_dir = dir_path / 'ARW'
    save_dir = ensure_dir(dir_path / 'SAVE')
    if not arw_dir.exists():
        log(cfg, f'[SKIP DONE] No ARW directory: {dir_path.name}')
        return
    new_hash = folder_hash(dir_path)
    processed_marker = dir_path / '.PROCESSED'
    if processed_marker.exists() and processed_marker.read_text(encoding='utf-8').strip() == new_hash:
        log(cfg, f'[SKIP DONE] Folder unchanged: {dir_path.name}')
        return
    for z in sorted(arw_dir.glob('*.zip')):
        preserve_zip_artifact(z, save_dir, dir_path.name, cfg)
    for arw in sorted(arw_dir.iterdir()):
        if not arw.is_file() or arw.suffix not in RAW_EXTS:
            continue
        base = arw.stem
        if not (dir_path / f'{base}.JPG').exists() and not (dir_path / f'{base}.jpg').exists():
            safe_delete(arw, cfg)
            log(cfg, f'[DELETE ARW] No matching active JPG: {base}')
    remaining = [p for p in sorted(arw_dir.iterdir()) if p.is_file() and p.suffix in RAW_EXTS]
    zip_path = next_available_artifact_path(save_dir, dir_path.name, 'sort_arw')
    if remaining:
        create_zip(zip_path, remaining)
    shutil.rmtree(arw_dir)
    processed_marker.write_text(new_hash, encoding='utf-8')
    log(cfg, f'[DONE MARKED] {dir_path.name}')


def process_container_done(dir_path: Path, cfg: dict) -> None:
    for sub in sorted(dir_path.iterdir()):
        if sub.is_dir() and is_valid_done_folder(sub.name):
            process_done_folder(sub, cfg)


def run_phase2(cfg: dict, folder: str | None = None) -> None:
    global COUNT_FOUND_DONE
    done_root = ensure_dir(cfg['paths']['temp_done'])
    folders = [Path(folder)] if folder else [p for p in sorted(done_root.iterdir()) if p.is_dir()]
    for dir_path in folders:
        COUNT_FOUND_DONE += 1
        if is_valid_done_folder(dir_path.name):
            process_done_folder(dir_path, cfg)
        else:
            process_container_done(dir_path, cfg)


def run_training(cfg: dict, images_dir: str | None = None, model_out: str | None = None) -> None:
    images_dir = images_dir or cfg['training']['sample_images_dir']
    model_out = model_out or cfg['paths']['personal_model']
    labels_out = str(Path(cfg['training']['exported_labels_dir']) / 'training_labels.csv')
    model = train_from_directory(images_dir=images_dir, model_out=model_out, labels_out=labels_out, min_images=int(cfg['training'].get('min_labeled_images', 20)))
    log(cfg, f"[TRAIN] model={model_out} rows={model['training_rows']}")


def run_family_cache_rebuild(cfg: dict) -> None:
    global LAST_FAMILY_RUN_INFO
    report = rebuild_family_cache(cfg)
    LAST_FAMILY_RUN_INFO = report
    log(cfg, f"[FAMILY CACHE] status={report['status']} people={report['person_count']} rebuilt={report['rebuilt_cache']} cache_dir={report['cache_dir']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Synology photo workflow with AI-assisted culling.')
    parser.add_argument('--config', default='config/config.yaml')
    sub = parser.add_subparsers(dest='command', required=True)
    p1 = sub.add_parser('phase1')
    p1.add_argument('--folder', default=None)
    p2 = sub.add_parser('phase2')
    p2.add_argument('--folder', default=None)
    train = sub.add_parser('train-personal')
    train.add_argument('--images-dir', default=None)
    train.add_argument('--model-out', default=None)
    sub.add_parser('rebuild-family-cache')
    return parser


def main() -> int:
    global COUNT_ERRORS
    reset_counters()
    parser = build_parser()
    args = parser.parse_args()
    cfg = load_config(args.config)
    started_at = now()
    print_start_banner(cfg, args.command)
    for key in ['temp_sd', 'temp_images', 'temp_done']:
        ensure_dir(cfg['paths'][key])
    ensure_dir(Path(cfg['paths']['personal_model']).parent)
    ensure_dir(cfg['family_recognition']['cache_dir'])
    status = 'success'
    try:
        with file_lock(cfg):
            if args.command == 'phase1':
                run_phase1(cfg, args.folder)
            elif args.command == 'phase2':
                run_phase2(cfg, args.folder)
            elif args.command == 'train-personal':
                run_training(cfg, args.images_dir, args.model_out)
            elif args.command == 'rebuild-family-cache':
                run_family_cache_rebuild(cfg)
    except Exception as exc:
        COUNT_ERRORS += 1
        status = 'error'
        log(cfg, f'[FATAL] {exc}', error=True)
    finally:
        finished_at = now()
        payload = build_summary_payload(cfg, args.command, status, started_at, finished_at, None)
        summary_path = write_json_summary(cfg, payload)
        payload = build_summary_payload(cfg, args.command, status, started_at, finished_at, summary_path)
        print_scheduler_summary(cfg, payload)
    return 0 if status == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
```

Der Orchestrator erzeugt `SAVE/cullingscores.csv` und `SAVE/cullingsummary.json`, bewegt nur JPGs in `Review/` oder `Rejected/`, und betrachtet ausschließlich JPGs im Hauptordner als aktive RAW-Auswahl. Er prüft vor jeder destruktiven Operation `base_dir`, nicht gefolgte Symlinks und den tatsächlichen `ARW`-Pfad.

## D.8 Konfigurationsdatei: `config/config.example.yaml`

**Funktion:** Vorlage für die NAS. Die implementierende KI ersetzt `<...>` vor dem Betrieb, aber niemals durch Hardcoding im Python-Code.

```yaml
paths:
  base_dir: /volume1/TEMP
  temp_sd: /volume1/TEMP/TEMPSD
  temp_images: /volume1/TEMP/TEMPIMAGES
  temp_done: /volume1/TEMP/TEMPDONE
  log_file: /volume1/TEMP/process.log
  error_log: /volume1/TEMP/error.log
  lock_file: /volume1/TEMP/.script.lock
  personal_model: /data/models/personal/user_taste_model.json
workflow:
  wait_time_seconds: 60
  stale_lock_seconds: 43200
  merge_strategy: merge_then_fallback
  create_done_marker_before_move: true
  date_reconstruction: {mode: legacy_bash, decade_prefix: '202', year_digit_index: 3}
culling:
  enabled: true
  move_files: true
  create_review_folder: true
  create_rejected_folder: true
  keep_threshold: 0.65
  reject_threshold: 0.35
  component_weights: {base_score: 0.55, eye_score: 0.10, personal_score: 0.20, family_score: 0.15}
  base_weights: {sharp: 0.36, aesth: 0.36, exposure: 0.18, reference: 0.10}
  eye_detection: {enabled: true}
  reference_scoring: {enabled: true, folder: /data/training/sample_images, recursive: false, preview_size: 32, cache_enabled: true, cache_dir: /data/models/reference_scoring, force_cache_rebuild: false}
  star_rating_bands: {5: 0.90, 4: 0.75, 3: 0.60, 2: 0.40, 1: 0.20, 0: 0.00}
training: {sample_images_dir: /data/training/sample_images, exported_labels_dir: /data/training/exported_labels, runs_dir: /data/training/runs, min_labeled_images: 20}
safety: {require_paths_within_base_dir: true, follow_symlinks: false, never_delete_outside_arw_dir: true}
reporting: {write_json_summary: true, json_summary_dir: /volume1/TEMP/run_summaries, stdout_mode: scheduler_mail}
family_recognition:
  enabled: false
  reference_dir: /data/family_faces
  cache_enabled: true
  cache_dir: /data/models/family_faces
  match_tolerance: 0.55
  min_reference_images_per_person: 3
  max_reference_images_per_person: 200
  default_person_weight: 0.35
  person_weights: {Kind1: 0.55, Kind2: 0.55}
  protect_detected_family: true
  write_native_tags: true
  exiftool_path: exiftool
series_detection: {enabled: true, cluster_eps: 0.18, min_samples: 2, preview_size: 32, review_margin: 0.03, demote_non_best_to: review}
metadata_culling: {enabled: true, write_rating: true, write_keywords: true, keep_backup: false, exiftool_path: exiftool, keyword_schema: namespaced_v1, write_score_bands: true, write_raw_scores_to_keywords: false}
personal_scoring: {enabled: true, source_dir: /data/training/sample_images, model_path: /data/models/personal/user_taste_model.json, cache_dir: /data/models/personal, cache_enabled: true, auto_train_on_change: true, recursive: false, min_reference_images: 5}
```

## D.9 Docker-Dateien

### `requirements.txt`

```text
numpy==2.1.1
Pillow==10.4.0
PyYAML==6.0.2
face-recognition
setuptools<81
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends exiftool build-essential cmake libopenblas-dev liblapack-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
ENTRYPOINT ["python", "/app/app/photo_workflow.py"]
```

### `docker-compose.yml`

```yaml
services:
  photo-workflow:
    build: .
    image: synology-photo-workflow:local
    user: "${PUID:-1026}:${PGID:-100}"
    volumes:
      - /volume1/TEMP:/volume1/TEMP
      - ./config:/config:ro
      - ./data:/data
    command: ["--config", "/config/config.yaml", "phase1"]
    restart: "no"
```

Die Implementierung muss für NAS-Architektur (x86_64 oder ARM64) dokumentieren, ob `face-recognition` baubar ist. Bei fehlendem Build muss ein Image ohne diese optionale Abhängigkeit möglich sein; `family_recognition.enabled` bleibt dann `false`.

## D.10 Scheduler-Wrapper

### `scripts/run_phase1.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose run --rm photo-workflow --config /config/config.yaml phase1
```

### `scripts/run_phase2.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose run --rm photo-workflow --config /config/config.yaml phase2
```

Der DSM Task Scheduler startet zunächst ausschließlich `run_phase1.sh`; Phase 2 bleibt bis zum bestätigten Dry-Run deaktiviert. Beide Wrapper benutzen dasselbe Lockfile aus der Konfiguration, daher darf kein eigener Parallelmechanismus eingeführt werden.

## D.11 Abnahme für die andere KI

Die andere KI darf die Umsetzung erst als fertig melden, wenn sie alle aufgelisteten Dateien geliefert und diese Befehle erfolgreich ausgeführt hat:

```bash
python -m compileall app
pytest -q
python app/photo_workflow.py --config config/config.yaml phase1
python app/photo_workflow.py --config config/config.yaml phase2 --dry-run
```

Sie muss zusätzlich bestätigen: (1) das Bash-Original liegt unverändert in `legacy/`, (2) die Tests decken den Legacy-Ordnerfluss ab, (3) kein echter RAW-Löschlauf wurde ohne getesteten Dry-Run durchgeführt und (4) sämtliche produktiven Pfade in der YAML-Datei zeigen auf die tatsächlichen NAS-Mounts.

## D.12 legacy reference

### `legacy/nas_photosort.sh`

```bash
#!/bin/bash
set -euo pipefail
shopt -s nullglob

# =====================================
# EN: Synology Photo Ingest + DONE Workflow
# DE: Synology Foto-Ingest + DONE-Workflow
# EN: Version v4.2 – Safe counters, ERR trap, static DEST move/merge, no mail
# DE: Version v4.2 – Sichere Zähler, ERR-Trap, statisches DEST Move/Merge, ohne E-Mail
# =====================================

BASE_DIR="/volume1/TEMP"
SRC="$BASE_DIR/TEMP_SD"
DEST="$BASE_DIR/TEMP_IMAGES"
DONE="$BASE_DIR/TEMP_DONE"

LOGFILE="$BASE_DIR/process.log"
ERRORLOG="$BASE_DIR/error.log"
LOCKFILE="$BASE_DIR/.script.lock"

WAIT_TIME=60

# EN: Script metadata shown at startup and written to log
# DE: Skript-Metadaten, die beim Start angezeigt und ins Log geschrieben werden
SCRIPT_NAME="Synology Photo Ingest + DONE Workflow"
SCRIPT_VERSION="v4.2"
SCRIPT_DESCRIPTION="Processes top-level photo folders from TEMP_SD, renames and packages JPG/ARW files, moves or merges completed folders to TEMP_IMAGES, and post-processes TEMP_DONE including ARW cleanup and ARW ZIP creation."

COUNT_PROCESSED=0
COUNT_MOVED=0
COUNT_SKIPPED=0
COUNT_ERRORS=0
COUNT_FOUND_SRC=0
COUNT_FOUND_DONE=0

# EN: Stores the final processed folder path from process_folder()
# DE: Speichert den final verarbeiteten Ordnerpfad aus process_folder()
LAST_PROCESSED_DIR=""

exec > >(tee -a "$LOGFILE") 2> >(tee -a "$ERRORLOG" >&2)

# =====================================
# EN: LOCKFILE / ERROR TRAPS
# DE: SPERRDATEI / FEHLER-TRAPS
# =====================================
if [[ -f "$LOCKFILE" ]]; then
    echo "[LOCK] EN: Script already running / DE: Skript läuft bereits"
    exit 1
fi
touch "$LOCKFILE"

trap 'echo "[ERROR TRAP] EN: Line $LINENO: $BASH_COMMAND / DE: Zeile $LINENO: $BASH_COMMAND"' ERR
trap 'rc=$?; [[ $rc -ne 0 ]] && echo "[FATAL] EN: Script aborted with exit code $rc / DE: Skript mit Exit-Code $rc abgebrochen"; rm -f "$LOCKFILE"' EXIT

echo "===== START: $(date) ====="
echo "SCRIPT   : $SCRIPT_NAME"
echo "VERSION  : $SCRIPT_VERSION"
echo "PURPOSE  : $SCRIPT_DESCRIPTION"
echo "BASE_DIR : $BASE_DIR"
echo "SRC      : $SRC"
echo "DEST     : $DEST"
echo "DONE     : $DONE"
echo "========================================"

# EN: Remove leftover temp ZIP files from previous runs
# DE: Temporäre ZIP-Dateien von früheren Läufen entfernen
find "$BASE_DIR" -type f -name "*.tmp" -delete

# =====================================
# EN: LOGGING
# DE: LOGGING
# =====================================
log() { echo "$(date '+%F %T') - $1"; }

# =====================================
# EN: HELPERS
# DE: HILFSFUNKTIONEN
# =====================================
is_stable() {
    local s1 s2
    s1=$(find "$1" -type f -exec stat -c "%n %s" {} + 2>/dev/null | sort)
    sleep "$WAIT_TIME"
    s2=$(find "$1" -type f -exec stat -c "%n %s" {} + 2>/dev/null | sort)
    [[ "$s1" == "$s2" ]]
}

folder_hash() {
    find "$1" -type f \( -iname "*.jpg" \) -exec stat -c "%n %s" {} + 2>/dev/null | sort | md5sum | awk '{print $1}'
}

safe_zip() {
    local zip_target="$1"
    shift
    local files=("$@")
    local tmpfile="${zip_target}.tmp"

    rm -f "$tmpfile"
    [[ ${#files[@]} -eq 0 ]] && return 0

    zip -j -q "$tmpfile" "${files[@]}" 2>/dev/null

    if [[ -f "$tmpfile" ]]; then
        mv "$tmpfile" "$zip_target"
        log "[ZIP OK] EN: ZIP created / DE: ZIP erstellt: $zip_target"
        return 0
    fi

    log "[ZIP FAIL] EN: ZIP creation failed / DE: ZIP-Erstellung fehlgeschlagen: $zip_target"
    COUNT_ERRORS=$((COUNT_ERRORS + 1))
    return 1
}

# EN: Original naming logic from the working script
# DE: Originale Namenslogik aus dem funktionierenden Skript
make_date_name() {
    local oldname="$1"

    if [[ "$oldname" =~ ^[0-9]{8}$ ]]; then
        local year="202${oldname:3:1}"
        local month="${oldname:4:2}"
        local day="${oldname:6:2}"
        echo "${year}-${month}-${day}"
    else
        echo "$oldname"
    fi
}

is_valid_raw_folder() {
    [[ "$1" =~ ^[0-9]{8}$ ]]
}

# EN: Accepts both YYYY-MM-DD and YYYY-MM-DD_SUFFIX
# DE: Akzeptiert sowohl YYYY-MM-DD als auch YYYY-MM-DD_SUFFIX
is_valid_done_folder() {
    [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(_.*)?$ ]]
}

# EN: Generate fallback destination name if merge target already exists
# DE: Fallback-Zielnamen erzeugen, falls Merge-Ziel bereits existiert
resolve_merge_fallback_dir() {
    local target="$1"

    if [[ ! -e "${target}_MERGE" ]]; then
        echo "${target}_MERGE"
        return 0
    fi

    local i=2
    while [[ -e "${target}_MERGE_${i}" ]]; do
        ((i++))
    done
    echo "${target}_MERGE_${i}"
}

# =====================================
# EN: MERGE OR MOVE TO DESTINATION
# DE: INS ZIEL MERGEN ODER VERSCHIEBEN
# =====================================
merge_or_move_folder() {
    local src_dir="$1"
    local dest_dir="$2"

    [[ -d "$src_dir" ]] || {
        log "[SKIP MOVE] EN: Source folder missing / DE: Quellordner fehlt: $src_dir"
        return 0
    }

    if [[ ! -d "$dest_dir" ]]; then
        mv "$src_dir" "$dest_dir" || {
            log "[ERROR] EN: Move failed / DE: Verschieben fehlgeschlagen: $src_dir -> $dest_dir"
            COUNT_ERRORS=$((COUNT_ERRORS + 1))
            return 1
        }
        log "[MOVE] EN: Folder moved / DE: Ordner verschoben: $(basename "$dest_dir")"
        COUNT_MOVED=$((COUNT_MOVED + 1))
        return 0
    fi

    log "[MERGE TRY] EN: Destination exists, trying rsync merge / DE: Ziel existiert, rsync-Merge wird versucht: $(basename "$dest_dir")"

    if command -v rsync >/dev/null 2>&1; then
        if rsync -a "$src_dir"/ "$dest_dir"/; then
            rm -rf "$src_dir" || {
                log "[ERROR] EN: Source cleanup after merge failed / DE: Quellen-Bereinigung nach Merge fehlgeschlagen: $src_dir"
                COUNT_ERRORS=$((COUNT_ERRORS + 1))
                return 1
            }
            log "[MERGE OK] EN: rsync merge completed / DE: rsync-Merge abgeschlossen: $(basename "$dest_dir")"
            log "[MERGE POST] EN: Merge finished, continuing script / DE: Merge abgeschlossen, Skript läuft weiter"
            COUNT_MOVED=$((COUNT_MOVED + 1))
            return 0
        else
            log "[MERGE FAIL] EN: rsync merge failed, using fallback / DE: rsync-Merge fehlgeschlagen, nutze Fallback"
        fi
    else
        log "[MERGE SKIP] EN: rsync not available, using fallback / DE: rsync nicht verfügbar, nutze Fallback"
    fi

    local fallback_dir
    fallback_dir="$(resolve_merge_fallback_dir "$dest_dir")"

    mv "$src_dir" "$fallback_dir" || {
        log "[ERROR] EN: Fallback move failed / DE: Fallback-Verschiebung fehlgeschlagen: $src_dir -> $fallback_dir"
        COUNT_ERRORS=$((COUNT_ERRORS + 1))
        return 1
    }

    log "[MOVE ALT] EN: Folder moved to fallback name / DE: Ordner unter Fallback-Namen verschoben: $(basename "$fallback_dir")"
    COUNT_MOVED=$((COUNT_MOVED + 1))
    return 0
}

# =====================================
# EN: PROCESS SINGLE TEMP_SD FOLDER
# DE: EINZELNEN TEMP_SD-ORDNER VERARBEITEN
# =====================================
process_folder() {
    local dir="$1"
    local oldname newname workdir
    oldname="$(basename "$dir")"

    LAST_PROCESSED_DIR=""

    if is_valid_raw_folder "$oldname"; then
        newname="$(make_date_name "$oldname")"
        workdir="$SRC/$newname"

        if [[ "$oldname" != "$newname" ]]; then
            mv "$dir" "$workdir" || {
                log "[ERROR] EN: Rename failed / DE: Umbenennen fehlgeschlagen: $oldname -> $newname"
                COUNT_ERRORS=$((COUNT_ERRORS + 1))
                return 1
            }
            log "[RENAMED] $oldname → $newname"
        else
            workdir="$dir"
        fi
    elif is_valid_done_folder "$oldname"; then
        newname="$oldname"
        workdir="$dir"
        log "[CONTINUE] EN: Continue already renamed folder / DE: Bereits umbenannten Ordner fortsetzen: $newname"
    else
        log "[SKIP] EN: Invalid folder name / DE: Ungültiger Ordnername: $oldname"
        COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
        return 2
    fi

    cd "$workdir" || return 1

    local arw
    arw=(*.ARW *.arw)
    if [[ ${#arw[@]} -gt 0 ]]; then
        mkdir -p ARW
        mv "${arw[@]}" ARW/ 2>/dev/null || true
        log "[ARW MOVED] EN: ARW files moved / DE: ARW-Dateien verschoben: ${#arw[@]}"
    else
        log "[NO ARW] EN: No ARW files found / DE: Keine ARW-Dateien gefunden in: $workdir"
    fi

    local jpg
    jpg=(*.JPG *.jpg)
    if [[ ${#jpg[@]} -gt 0 ]]; then
        mkdir -p SAVE
        local zipfile="SAVE/${newname}_ALL_JPG.zip"

        if [[ ! -f "$zipfile" ]] || [[ "$(find . -iname '*.jpg' -newer "$zipfile" | wc -l)" -gt 0 ]]; then
            safe_zip "$zipfile" "${jpg[@]}"
        else
            log "[SKIP JPG ZIP] EN: JPG ZIP up to date / DE: JPG-ZIP aktuell"
        fi
    else
        log "[NO JPG] EN: No JPG files found / DE: Keine JPG-Dateien gefunden in: $workdir"
    fi

    touch "$workdir/.DONE"
    log "[DONE] EN: Folder marked DONE / DE: Ordner als DONE markiert: $newname"

    cd "$BASE_DIR" || return 1
    COUNT_PROCESSED=$((COUNT_PROCESSED + 1))

    LAST_PROCESSED_DIR="$workdir"
    return 0
}

# =====================================
# EN: PROCESS SINGLE TEMP_DONE FOLDER
# DE: EINZELNEN TEMP_DONE-ORDNER VERARBEITEN
# =====================================
process_done_folder() {
    local dir="$1"
    local name
    name="$(basename "$dir")"

    local ARW_DIR="$dir/ARW"
    local SAVE_DIR="$dir/SAVE"
    local new_hash old_hash
    local z arw base jpg
    local arw_files
    local ARW_ZIP

    [[ -d "$ARW_DIR" ]] || {
        log "[SKIP DONE] EN: No ARW directory / DE: Kein ARW-Verzeichnis vorhanden: $name"
        return 0
    }

    mkdir -p "$SAVE_DIR"

    new_hash=$(folder_hash "$dir")

    if [[ -f "$dir/.PROCESSED" ]]; then
        old_hash=$(cat "$dir/.PROCESSED")
        if [[ "$new_hash" == "$old_hash" ]]; then
            log "[SKIP DONE] EN: Folder unchanged / DE: Ordner unverändert: $name"
            return 0
        else
            log "[REPROCESS] EN: Changes detected / DE: Änderungen erkannt: $name"
        fi
    else
        log "[PROCESS DONE] EN: Processing done folder / DE: Verarbeite DONE-Ordner: $name"
    fi

    for z in "$ARW_DIR"/*.zip; do
        [[ -f "$z" ]] && mv "$z" "$SAVE_DIR/"
    done

    for z in "$SAVE_DIR"/*.zip; do
        [[ -f "$z" ]] || continue
        [[ "$z" != *_ALL_JPG.zip && "$z" != *_SORT_ARW.zip ]] && mv "$z" "${z%.zip}_ALL_JPG.zip"
    done

    for arw in "$ARW_DIR"/*.ARW "$ARW_DIR"/*.arw; do
        [[ -f "$arw" ]] || continue
        base="$(basename "$arw")"
        base="${base%.*}"
        jpg="$dir/$base.JPG"

        if [[ ! -f "$jpg" && ! -f "$dir/$base.jpg" ]]; then
            rm -f "$arw"
            log "[DELETE ARW] EN: No matching JPG / DE: Kein passendes JPG, ARW gelöscht: $base"
        fi
    done

    arw_files=("$ARW_DIR"/*.ARW "$ARW_DIR"/*.arw)
    ARW_ZIP="$SAVE_DIR/${name}_SORT_ARW.zip"

    if [[ ${#arw_files[@]} -gt 0 ]]; then
        if safe_zip "$ARW_ZIP" "${arw_files[@]}"; then
            rm -rf "$ARW_DIR"
            log "[REMOVE ARW DIR] EN: ARW directory removed after ZIP / DE: ARW-Ordner nach ZIP-Erstellung entfernt: $name"
        fi
    else
        log "[INFO] EN: No ARW files / DE: Keine ARW-Dateien vorhanden: $name"
        rm -rf "$ARW_DIR"
        log "[REMOVE ARW DIR] EN: Empty ARW directory removed / DE: Leerer ARW-Ordner entfernt: $name"
    fi

    echo "$new_hash" > "$dir/.PROCESSED"
    log "[DONE MARKED] EN: Folder marked processed / DE: Ordner als verarbeitet markiert: $name"
}

# =====================================
# EN: PROCESS TEMP_DONE CONTAINER
# DE: TEMP_DONE-CONTAINER VERARBEITEN
# =====================================
process_container_done() {
    local dir="$1"
    local name
    name="$(basename "$dir")"
    log "[DONE CONTAINER] EN: Processing done container / DE: Verarbeite DONE-Container: $name"

    local sub subname
    for sub in "$dir"/*/; do
        [[ -d "$sub" ]] || continue
        sub="${sub%/}"
        subname="$(basename "$sub")"

        if is_valid_done_folder "$subname"; then
            process_done_folder "$sub"
        else
            log "[SKIP DONE SUB] EN: Unsupported TEMP_DONE subfolder / DE: Nicht unterstützter TEMP_DONE-Unterordner: $subname"
            COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
        fi
    done
}

# =====================================
# EN: MAIN
# DE: HAUPTPROGRAMM
# =====================================
log "[PHASE 1] EN: Processing TEMP_SD / DE: Verarbeite TEMP_SD"

for dir in "$SRC"/*; do
    [[ -d "$dir" ]] || continue
    dir="${dir%/}"
    name="$(basename "$dir")"
    COUNT_FOUND_SRC=$((COUNT_FOUND_SRC + 1))

    if ! is_valid_raw_folder "$name" && ! is_valid_done_folder "$name"; then
        log "[SKIP TOP] EN: Unsupported top-level folder, not checked / DE: Nicht unterstützter Ordner auf oberster Ebene, nicht geprüft: $name"
        COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
        continue
    fi

    if [[ ! -f "$dir/.DONE" ]] && ! is_stable "$dir"; then
        log "[WAIT] EN: Transfer still running, folder not checked yet / DE: Transfer läuft noch, Ordner noch nicht geprüft: $name"
        COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
        continue
    fi

    if [[ -f "$dir/.DONE" ]]; then
        log "[DEBUG MOVE] EN: Moving already DONE folder / DE: Verschiebe bereits DONE-markierten Ordner: $dir"
        merge_or_move_folder "$dir" "$DEST/$name"
        continue
    fi

    LAST_PROCESSED_DIR=""
    if process_folder "$dir"; then
        if [[ -n "$LAST_PROCESSED_DIR" && -d "$LAST_PROCESSED_DIR" && -f "$LAST_PROCESSED_DIR/.DONE" ]]; then
            log "[DEBUG MOVE] EN: Using processed dir / DE: Verwende verarbeiteten Ordner: $LAST_PROCESSED_DIR"
            merge_or_move_folder "$LAST_PROCESSED_DIR" "$DEST/$(basename "$LAST_PROCESSED_DIR")"
        else
            log "[WAIT MOVE] EN: No movable DONE folder found / DE: Kein verschiebbarer DONE-Ordner gefunden: $name"
        fi
    else
        log "[ERROR] EN: process_folder failed / DE: process_folder fehlgeschlagen: $name"
        COUNT_ERRORS=$((COUNT_ERRORS + 1))
    fi
done

log "[PHASE 2] EN: Processing TEMP_DONE / DE: Verarbeite TEMP_DONE"

for dir in "$DONE"/*; do
    [[ -d "$dir" ]] || continue
    dir="${dir%/}"
    name="$(basename "$dir")"
    COUNT_FOUND_DONE=$((COUNT_FOUND_DONE + 1))

    if is_valid_done_folder "$name"; then
        process_done_folder "$dir"
    else
        process_container_done "$dir"
    fi
done

SUMMARY=$(cat <<EOF
EN: Photo ingest summary
DE: Foto-Ingest Zusammenfassung

EN: Found folders in TEMP_SD   / DE: Gefundene Ordner in TEMP_SD:   $COUNT_FOUND_SRC
EN: Found folders in TEMP_DONE / DE: Gefundene Ordner in TEMP_DONE: $COUNT_FOUND_DONE
EN: Processed folders          / DE: Verarbeitete Ordner:           $COUNT_PROCESSED
EN: Moved/Merged              / DE: Verschoben/Gemerged:           $COUNT_MOVED
EN: Skipped folders           / DE: Übersprungene Ordner:          $COUNT_SKIPPED
EN: Errors                    / DE: Fehler:                        $COUNT_ERRORS

EN: Log file                  / DE: Logdatei:                      $LOGFILE
EN: Error log                 / DE: Fehlerlog:                     $ERRORLOG
EOF
)

echo "$SUMMARY"
echo "===== END: $(date) ====="
```
