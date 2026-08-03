# Master-Implementierungsspezifikation v7.9.0 (konsolidierte Endfassung)

**Repository:** `MaiTaiMa/synology-photo-workflow`
**Referenz-Commit für diese Prüfung:** `8b616a8b` (Branch `main`)
**Ziel:** Vollständige fachliche und technische Vorgabe für das Versionsupdate 7.8.0 → 7.9.0, einschließlich Fehlerbehebung (Paket 0), Bildmengen-/Resume-Fähigkeit, KI-Funktionsvertrag und auflösungsunabhängigem MANUAL_KEEP-Abgleich.
**Status:** Verbindliches Planungs- und Umsetzungsdokument für Entwickler:innen und KI-Agenten. Es autorisiert **keinen** Commit, Push, Modell-Download oder produktive Konfigurationsänderung außerhalb der beschriebenen Pakete und Gates.
**Herkunft:** Dieses Dokument ersetzt die vier Zwischenvorschläge (Basis, rev2, rev3, rev4). Es wurde gegen den tatsächlichen Quellcode des Repositories verifiziert (siehe Anhang C) und übernimmt ausschließlich die durch den Code bestätigten Befunde. Widersprüchliche oder unbelegte Aussagen der Zwischenvorschläge wurden korrigiert.
**Lesereihenfolge:** Teil A ist menschenlesbar und beschreibt das Zielverhalten fachlich, ohne Code. Teil B ist der verbindliche technische Implementierungsleitfaden für Entwickler:innen und KI-Agenten. Anhang A enthält die vollständige Zielkonfiguration, Anhang B die Test- und Abnahmematrix, Anhang C die Verifikation gegen den bestehenden Code.

---

# Teil A – Fachliche Funktionsbeschreibung

## A1. Zielbild und Prioritäten

Der Workflow verarbeitet Fotoordner lokal auf einer Synology NAS. Er bewertet Fotos technisch und ergänzt dies optional durch lokale KI-Funktionen: persönlicher Geschmack, visuelle Serien, Familie/Gesichter, offene Augen, einen vorsichtigen Gewichtungsassistenten sowie einen auflösungsunabhängigen MANUAL_KEEP-Abgleich. Der Workflow dient der Vorsortierung und Nachvollziehbarkeit; menschliche Entscheidungen bleiben maßgeblich.

Alle Entscheidungen folgen zwingend dieser Reihenfolge:

1. **Sicherheit:** Keine unkontrollierten Dateiänderungen, Datenverluste, Modell-Downloads oder Datenübertragungen. Bilder, Referenzen, Gesichts-Crops und Vektoren verlassen nie die NAS.
2. **Stabilität:** Ein einzelnes fehlerhaftes Foto, ein Modellfehler oder ein defekter Ordner stoppt nicht den übrigen Lauf.
3. **Nutzen:** Jede Funktion muss Fotos besser vorsortieren, Nachvollziehbarkeit oder Betriebssicherheit erhöhen.
4. **Einfachheit:** Wenige verständliche Optionen; keine technische Doppelstruktur ohne nachgewiesenen Nutzen.
5. **NAS-Performance:** Ein langsamer, begrenzter und über mehrere Tage fortsetzbarer Betrieb ist akzeptabel.

Keine bestehende Funktion wird entfernt. Eine Funktion darf nur durch bewusste Konfiguration deaktiviert werden; dann muss ein sicherer bestehender Fallback erhalten bleiben. Eine deaktivierte, fehlende oder fehlerhafte optionale KI-Funktion darf niemals einen künstlich schlechten Score erzeugen (`None`, nicht `0.0`).

## A2. Physische Batches und logische Bildmengen

Ein Quellordner ist stets der sichtbare **physische Batch**. Er bleibt die alleinige Einheit für Lock, Quarantäne, Review, Archivierung und endgültige Moves.

| Arbeitsweise | Verhalten |
|---|---|
| `source_batch` | Ein vollständiger Quellordner ist eine Arbeitseinheit (bisheriges Verhalten, Default). |
| `image_count` | Der Ordner bleibt unverändert sichtbar; sein Inventar wird intern in feste logische Bildmengen (z. B. 25/50/100 Bilder) geteilt. |

Bildmengen erzeugen **niemals** sichtbare Teilordner. Ein physischer Batch wird erst verschoben, wenn alle zugehörigen WorkUnits sämtlicher erforderlicher Phasen vollständig und nachvollziehbar abgeschlossen sind.

Für **neue** Ordner ist die Auswahl konfigurierbar: `oldest_first` oder `newest_first`. Bereits begonnene oder wiederherzustellende Arbeit hat in jedem Fall Vorrang vor der Auswahl neuer Ordner, damit laufend eintreffende neue Ordner keine unvollständige Arbeit verdrängen.

## A3. Fortsetzung, Budgets und Recovery

Nach Zeitlimit, Tagesende, kontrolliertem Stopp, NAS-Neustart, Prozessabbruch oder Modellfehler muss der Lauf exakt fortsetzbar sein. Er speichert mindestens: aktiven Batch, aktive Phase, Inventar, offene und erledigte Bild-IDs, offene Dateioperation, Pausengrund, Konfigurationsfingerprint und relevante Zähler.

Ein fertig verarbeitetes Bild darf weder erneut verschoben noch doppelt mit Metadaten beschrieben oder archiviert werden. Ist nach einem Abbruch nicht eindeutig feststellbar, ob eine Dateioperation abgeschlossen wurde, **rät das System nicht**. Es prüft ausschließlich den erwarteten Quell- und Zielzustand; jeder andere Zustand führt zu `recovery_required` und Quarantäne bzw. manueller Prüfung.

Laufbegrenzungen können enthalten: maximale Batches/WorkUnits pro Lauf, maximale Anzahl neu begonnener Bilder, maximales Zeitbudget (`max_run_hours`) sowie Budgets einzelner Modelle. Nach Erreichen eines Limits beginnt keine neue WorkUnit mehr. Eine bereits gestartete atomare Mutation wird vollständig abgeschlossen oder in einem eindeutig fortsetzbaren State pausiert — niemals in einem unklaren Zwischenzustand belassen.

## A4. Fehlerisolation und Quarantäne

Ein nicht lesbares Bild führt zu einem sichtbaren Analysefehler nur für dieses Bild; die restlichen Bilder des Batches werden regulär weiterverarbeitet. Ein unsicherer, veränderter oder aus Sicherheitssicht fehlerhafter physischer Batch wird **quarantänisiert**; der Scheduler fährt danach unmittelbar mit dem nächsten zulässigen Batch fort. Ein einzelner defekter Batch darf **niemals** den gesamten Lauf (alle nachfolgenden Batches) beenden.

Vor jedem sichtbaren Batch-Move wird ein Übergangsstate (`phase1_moving`) atomar geschrieben. Erst nach erfolgreichem Move wird der Zustand als abgeschlossen (`phase1_completed`) markiert. Damit sind Unterbrechungen sowohl zwischen State-Write und Move als auch zwischen Move und Abschluss-State wiederherstellbar. Scheitert selbst die Quarantäne, wird dies separat protokolliert; ein Folge-Batch darf dennoch nicht unkontrolliert verändert werden.

## A5. Bewertungen und KI-Funktionen

| Funktion | Output | Verhalten bei Deaktivierung/Fehler |
|---|---|---|
| Technisches Culling | `base_score` | immer verfügbar; sichtbarer `analysis_error`, kein stiller Ersatzscore |
| Persönlicher Geschmack (lokales CLIP) | `personal_score` | `None`; technische Bewertung läuft unverändert weiter |
| Visuelle Serien | Cluster + Bestbild | bestehende deterministische Dateinamen-Serienlogik bleibt Fallback aktiv |
| Familie/Gesicht | `family_score` | `None`, wenn Referenz/Match nicht eindeutig sicher ist |
| Eye State | `eye_score = P(offen)` | `None` bei keinem, mehreren, zu kleinem oder unsicherem Gesicht |
| Gewichtungsassistent | Proposal, optionale Aktivierung | keine Änderung der festen YAML ohne alle Gates |
| MANUAL_KEEP | `matched \| unmatched \| ambiguous \| error` | kein Move bei Unsicherheit oder Fehler |

### Technisches Culling
Immer verfügbar, benötigt kein KI-Modell. Bewertet Schärfe, Belichtung und einfache ästhetische Merkmale (`sharpness`, `aesthetic`, `exposure` → `base_score`). Ein Analysefehler beeinflusst nicht die Bearbeitung nachfolgender Bilder und erzeugt keinen stillen Ersatzscore.

### Persönlicher Geschmack
Ein lokales CLIP-Modell bewertet positive und negative Bildbeschreibungen (Prompts). Das Ergebnis ist ausschließlich `personal_score`; es wird nicht in `base_score` vermischt. Positive Prompts können z. B. gewünschte Familienmomente oder bevorzugte Bildstile ausdrücken, negative Prompts unscharfe oder schlecht belichtete Bilder. Fehlende, deaktivierte oder fehlerhafte Modelle setzen nie `0.0`, sondern `None`.

### Serienerkennung
Ein eigenes lokales Serienmodell gruppiert visuell ähnliche Bilder anhand Aufnahmezeit und Bildähnlichkeit und bestimmt über den bereits vorhandenen Gesamtscore ein Bestbild. Es entscheidet **nie** direkt Keep/Review/Reject. Bei deaktiviertem oder fehlerhaftem Modell bleibt die vorhandene deterministische Serienlogik (z. B. über Dateinamen) aktiv. Im Bildmengenmodus darf eine visuelle Serie erst endgültig geschlossen werden, wenn der gesamte physische Batch analysiert wurde.

### Gesichtserkennung und Familie
Vergleicht Bilder ausschließlich mit ausdrücklich aktivierten Familienreferenzen. `family_score` wird nur bei einem eindeutigen, ausreichend guten und vom zweitbesten Treffer ausreichend getrennten Match gesetzt. Unbekannte oder unsichere Fälle bleiben neutral. Face-Crops, Embeddings und Referenzbilder dürfen weder in Git, Logs, CSVs noch Manifesten landen.

### Eye Score
Beurteilt nur genau ein ausreichend großes Gesicht. Bei sicherer Klassifikation ist `eye_score` die Wahrscheinlichkeit offener Augen. Mehrere Gesichter, kleine Gesichter, Unsicherheit oder Modellfehler führen zu einem neutralen Score. Eye Score allein führt nie zu einem automatischen Reject.

### Gewichtungsassistent
Lernt ausschließlich aus menschlich bestätigten Review-Entscheidungen. Erzeugt zunächst einen Gewichtsvorschlag. Eine automatische Aktivierung ist optional, gilt frühestens im nächsten Lauf, ist auditierbar und rollbackfähig. Die feste YAML-Konfiguration wird dabei nie still überschrieben.

### MANUAL_KEEP – auflösungsunabhängiger, sicherer Abgleich
MANUAL_KEEP verarbeitet bewusst behaltene Bilder aus seinem Inbox-Ordner gegen zulässige Kandidatenpfade. Es muss dieselbe Aufnahme erkennen, wenn Bilddateien unterschiedliche Auflösung, Dateigröße, JPEG-Kompression, Dateinamen, EXIF-Daten oder EXIF-Orientierung besitzen. Zweck ist keine allgemeine Ähnlichkeit, sondern eine **hochsichere Identitätsentscheidung**: Ein anderes Bild derselben Serie, dieselbe Szene eine Sekunde später, eine ähnliche Pose oder eine semantisch ähnliche CLIP-Repräsentation genügt **nicht** als Match.

| Status | Bedeutung | Dateiaktion |
|---|---|---|
| `matched` | eindeutige identische Aufnahme | nur bei `allow_automatic_move=true`: Move nach `used` |
| `ambiguous` | mehrere gleich gute bzw. zu nahe Treffer | Inbox unverändert |
| `unmatched` | kein ausreichend guter Treffer | Inbox unverändert |
| `error` | Lese- oder Verarbeitungsfehler | Inbox unverändert |

Der Abgleich läuft zweistufig: ein schneller, auflösungsrobuster Kandidaten-Vorfilter, danach eine strenge, normalisierte Endprüfung. Ein Auto-Move ist nur erlaubt, wenn der beste Score die Schwelle erreicht **und** sein Abstand zum zweitbesten Kandidaten mindestens der konfigurierten Margin entspricht.

### Warum Culling, Serien und MANUAL_KEEP nicht fachlich verschmolzen werden
Culling bewertet Qualität, das Serienmodell visuelle Nähe, CLIP semantische/stilistische Ähnlichkeit — MANUAL_KEEP benötigt den Nachweis derselben Aufnahme. Deshalb werden ausschließlich **technische Ressourcen** geteilt (Dekodierung, EXIF-Korrektur, RGB-Konvertierung, Vorschauerzeugung, flüchtiger Cache pro Lauf), niemals die fachliche Entscheidung. Ein Culling-, Geschmacks- oder Serien-Score darf für MANUAL_KEEP höchstens als optionaler Kandidaten-Vorfilter dienen und niemals allein einen Move bestätigen.

## A6. Lokale Modelle, Datenschutz und Worker

Alle Modelle arbeiten ausschließlich lokal. Modellinstallation ist eine bewusste Verwaltungsaktion, nie ein Nebenprodukt des normalen Workflow-Laufs. Modellartefakte werden nur über erlaubte Quellen, sichere Verbindung (HTTPS), Größenlimit und Hash-Prüfung installiert. Modellgewichte liegen ausschließlich unter `models/` und werden nie in Git committed.

Bilder, Bildbytes, Face-Crops, Referenzbilder sowie Bild-, Face- und CLIP-Embeddings sind ausschließlich flüchtig im RAM zulässig; sie dürfen nicht in JSON, Cache, Log, Manifest, CSV, Metadaten oder Report persistiert werden.

Standard ist ein Inferenzworker. Optional sind maximal zwei Worker möglich. Worker liefern ausschließlich Rechenresultate; States, Manifeste, Metadaten und Datei-Moves verbleiben deterministisch im seriellen Hauptprozess. Bei knappen Ressourcen, Worker-Ausfall oder Budgetende wird sicher seriell weitergearbeitet oder nur der betreffende optionale Score neutral gesetzt.

## A7. Versionsmodell und Nachvollziehbarkeit

Es gibt **genau zwei** Versionsbegriffe:

| Begriff | Bedeutung |
|---|---|
| Projektversion | Herkunft der schreibenden Anwendung (`app.VERSION`) |
| Dateiversion | Format der JSON-Steuer-, State-, Manifest- oder Report-Datei (`schema_version`) |

Die Dateiversion entscheidet über Lesbarkeit. Die Projektversion ist ein Audit-Metadatum und darf eine strukturell korrekte Datei **niemals** ablehnen. Alle Writer verwenden ausschließlich die zentral gepflegte Projektversion; alte, fest codierte Versionsstrings dürfen nicht verbleiben.

Jeder Lauf berichtet: Batches/WorkUnits, Resume-Ereignisse, Pausengrund, Quarantäne, Modellzustände, verwendete Scores, MANUAL_KEEP-Resultate, Gewichtungsproposal/-aktivierung/-rollback und Recovery-Ereignisse.

---

# Teil B – Verbindlicher Implementierungsplan

## B1. Verifizierte Ausgangsbefunde

Alle Befunde wurden gegen den tatsächlichen Code im Referenz-Commit `8b616a8b` geprüft (Details siehe Anhang C). Die ursprünglich gemeldeten Befunde S1 und T1 sind **bestätigte aktive Fehler**, kein theoretisches Risiko.

| ID | Schwere | Ist-Zustand (verifiziert) | Verbindliche Behebung |
|---|---|---|---|
| **S1** | 🔴 kritisch | `app/__init__.py` setzt `VERSION = "7.8.0"`. `app/safety.py::validate_control_record()` prüft hartcodiert `payload['producer_version'] != '7.7.0'` und wirft `SafetyError`. Jede aktuell mit `VERSION` (7.8.0) geschriebene Kontrolldatei wird von der eigenen Sicherheitsprüfung abgelehnt. | Dateiversion (`schema_version`) und Projektversion (`producer_version`) sauber trennen; `safety.py` darf nur noch `schema_version` hart prüfen und `producer_version` nur auf Typ/Nichtleere prüfen, nicht auf exakten Wert. |
| **T1** | 🔴 kritisch | `runtime.py::quarantine_batch()` ist vollständig implementiert, wird aber laut Code-Suche im Repository **ausschließlich** in `runtime.py` selbst und in `tests/test_runtime_recovery.py` referenziert — **nicht** in `phases.py`. Die Batch-Schleife in `phases.py` enthält keinen `try/except SafetyError`-Block um den Verarbeitungsaufruf je Batch. Ein `SafetyError` aus einem Batch propagiert daher unkontrolliert durch die gesamte Schleife. | In `phases.py` jeden Batch-Verarbeitungsschritt einzeln mit `try/except SafetyError` umschließen, `quarantine_batch()` aufrufen und mit `continue` fortfahren. |
| **S3** | 🟠 hoch | Repository-Scan (`search_code` nach `producer_version`) bestätigt Literal `'7.7.0'` in: `app/locks.py` (Lock-Manifest), `app/runtime.py` (Batch-Lock **und** Quarantäne-Manifest, zwei Stellen), `app/calibration.py` (`record()` **und** Readiness-Report, zwei Stellen), `app/batch_state.py`, `app/reporting.py`, `app/face_cache.py`. **Bereits korrekt** (laut CHANGELOG 7.8.0 und Code-Fund): `app/archives.py` und `app/phases.py` verwenden bereits `producer_version: VERSION` per Import — diese beiden Dateien sind von S3 **nicht** betroffen und dürfen nicht erneut angefasst werden, um keine Regression einzuführen. | Nur die sieben tatsächlich betroffenen Fundstellen auf zentralen `VERSION`-Import umstellen; vor Abschluss erneuten Repository-Scan nach `'7.7.0'` und `'7.8.0'` als Literal durchführen, um keine weitere Fundstelle zu übersehen. |
| **T2** | 🟠 hoch | In der Phase-1-Verarbeitung (`phases.py`) erfolgt der sichtbare `shutil.move()` des Batches, bevor ein abschließender State-Write erfolgt. Bricht der Lauf (z. B. durch `RunBudget`) zwischen Move und State-Write ab, liegt der Batch in `temp_images`, ohne dass ein State-Eintrag dies dokumentiert — Resume kann den Batch dann nicht sicher wiederfinden. | Vor jedem sichtbaren Move `phase1_moving` atomar schreiben; erst nach erfolgreichem Move `phase1_completed` schreiben. Recovery muss beide Zwischenzustände eindeutig auflösen können. |
| W1 | mittel | Kein Bildmengenmodus, kein vollständiges Resume unterhalb der Batch-Ebene vorhanden. | WorkUnits, Inventar, Checkpoints und Recovery gemäß B4 einführen. |
| W2 | niedrig | Konfiguration erlaubt aktuell nur eine Sortierrichtung für neue Ordner. | `oldest_first` und `newest_first` erlauben; Resume-Priorität bleibt in jedem Fall höher (siehe A2/B5). |
| M1 | mittel | `manual_keep.py` delegiert Ähnlichkeit über eine injizierbare `Callable`, ohne selbst Auflösungen/Kompression zu normalisieren. | `ResolutionAwareSimilarity` und gemeinsamen `ImageFeatureService` gemäß B9/B10 ergänzen, bestehende `Callable`-Schnittstelle beibehalten. |

**Paket-0-Regel:** Kein KI-bezogenes Paket (2–7) darf begonnen werden, bevor S1, S3, T1 und T2 behoben, getestet und freigegeben sind. Dies ist eine harte Vorbedingung, keine Empfehlung.

## B2. Versionsmodell (S1, S3)

```python
# app/__init__.py
VERSION = "7.9.0"
CONTROL_FILE_VERSION = 1
```

`schema_version` bleibt aus Kompatibilitätsgründen der JSON-Key für die Dateiversion. Jeder kontrollierte JSON-Writer importiert zentral:

```python
from . import CONTROL_FILE_VERSION, VERSION
```

und schreibt ausschließlich:

```python
{"schema_version": CONTROL_FILE_VERSION, "producer_version": VERSION, "created_at": now, "updated_at": now}
```

### Konkret zu ändernde Fundstellen (verifiziert, siehe B1/S3 und Anhang C)

| Datei | Fundstelle(n) | Änderung |
|---|---|---|
| `app/locks.py` | `BatchLock`/Run-Lock-Schreiben | Literal `'7.7.0'` → `VERSION` |
| `app/runtime.py` | Batch-Lock-Schreiben, `quarantine_batch()`-Manifest | beide Literale `'7.7.0'` → `VERSION` |
| `app/calibration.py` | `record()`, Readiness-/Kalibrierungsreport | beide Literale `'7.7.0'` → `VERSION` |
| `app/batch_state.py` | `write_state()` | Literal `'7.7.0'` → `VERSION` |
| `app/reporting.py` | Run-Summary-Schreiben | Literal `'7.7.0'` → `VERSION` |
| `app/face_cache.py` | Cache-Manifest-Schreiben | Literal `'7.7.0'` → `VERSION` |
| `app/archives.py`, `app/phases.py` | bereits `VERSION`-Import | **keine Änderung nötig**, nur in Test-/Diff-Review als bereits konform bestätigen |

Ergänzend: Vor Abschluss von Paket 0 einen Repository-weiten Scan (`grep -rn "producer_version" app/` bzw. `search_code`) gegen `'7.7.0'` und `'7.8.0'` als Stringliteral ausführen. Jeder verbleibende Treffer ist ein offener S3-Fall.

### Anpassung von `app/safety.py`

```python
def validate_control_record(payload: dict[str, Any], scope_key: str | None = None) -> None:
    if not isinstance(payload, dict):
        raise SafetyError("control_record_not_mapping")
    required = {"schema_version", "created_at", "updated_at", "producer_version"}
    if not required.issubset(payload):
        raise SafetyError("control_record_missing_required_field")
    if payload["schema_version"] != CONTROL_FILE_VERSION:
        raise SafetyError("control_record_schema_version")
    if not isinstance(payload["producer_version"], str) or not payload["producer_version"]:
        raise SafetyError("control_record_producer_version")
    if scope_key is not None and scope_key not in payload:
        raise SafetyError("control_record_missing_scope_key")
```

**Keine Whitelist konkreter Projektversionen einführen.** Die Prüfung bleibt strukturell (Typ, Nichtleere), nie ein exakter String-Vergleich gegen eine bestimmte Version. Damit bleiben ältere, strukturell gültige Dateien nach künftigen Versionssprüngen weiterhin lesbar (siehe A7).

## B3. Konfigurationsschnittstelle

Vollständige Zielkonfiguration siehe **Anhang A**. Kernauszug für Workflow- und Inferenzsteuerung:

```yaml
workflow:
  phase_execution: phase1_then_phase2
  batch_limit: 1
  batch_sort: oldest_first              # oldest_first | newest_first
  skip_incomplete_batches: false
  resume_incomplete_batches: true
  max_run_hours: 4
  dry_run: false
  work_unit_mode: source_batch          # source_batch | image_count
  images_per_work_unit: null            # positive Ganzzahl bei image_count
  max_images_per_run: 0                 # 0 = unbegrenzt
  progress_checkpoint_interval: 5

inference:
  workers: 1
  start_method: spawn
  queue_size: 4
  maximum_worker_ram_mb: 2048
  allow_parallel_clip: false
  allow_parallel_onnx: false

manual_keep:
  enabled: true
  similarity_backend: resolution_aware_v1
  comparison_long_edge: 256
  aspect_ratio_tolerance: 0.02
  perceptual_hash_max_distance: 6
  verification_threshold: 0.95
  minimum_best_second_margin: 0.03
  allow_automatic_move: true
  use_series_embedding_prefilter: false
```

### Validierungsregeln in `app/configuration.py`

```python
if workflow["batch_sort"] not in {"oldest_first", "newest_first"}:
    raise ValueError("CONFIGINVALID workflow.batch_sort")
if workflow["work_unit_mode"] not in {"source_batch", "image_count"}:
    raise ValueError("CONFIGINVALID workflow.work_unit_mode")
if workflow["work_unit_mode"] == "image_count":
    if not isinstance(workflow["images_per_work_unit"], int) or workflow["images_per_work_unit"] < 1:
        raise ValueError("CONFIGINVALID workflow.images_per_work_unit")
elif workflow["images_per_work_unit"] is not None:
    raise ValueError("CONFIGINVALID workflow.images_per_work_unit_requires_image_count")
```

Weitere Pflichtprüfungen: `max_images_per_run` nichtnegativ; `inference.workers` ∈ {1, 2}, wobei 2 die jeweils passenden `allow_parallel_*`-Opt-ins voraussetzt; Modellpfade müssen innerhalb `paths.model_dir` liegen (kein Pfadausbruch); `culling.final_component_weights` nichtnegativ mit Summe 1; MANUAL_KEEP-Kantenlänge positiv, Toleranz in `(0,1)`, Hash-Distanz `>= 0`, Schwellen in `[0,1]`, Margin in `[0,1)`. Deaktivierte Modelle dürfen weder optionale Abhängigkeiten importieren noch Modelldateien öffnen oder prüfen.

## B4. WorkUnits, Inventar und State (W1, W2)

Neue Datei: `app/work_units.py`.

```python
@dataclass(frozen=True)
class InventoryItem:
    image_id: str
    relative_path: str
    size_bytes: int
    mtime_ns: int

@dataclass(frozen=True)
class BatchInventory:
    batch_id: str
    source_fingerprint: str
    inventory_fingerprint: str
    items: tuple[InventoryItem, ...]

@dataclass(frozen=True)
class WorkUnit:
    work_unit_id: str
    parent_batch_id: str
    phase: Literal["phase1", "phase2"]
    ordinal: int
    image_ids: tuple[str, ...]
    inventory_fingerprint: str

@dataclass(frozen=True)
class WorkUnitPlan:
    work_unit: WorkUnit
    batch_path: Path
    image_paths: tuple[Path, ...]
    resume: bool
```

Öffentliche Funktionen:

```python
def build_inventory(batch_path: Path, basedir: Path) -> BatchInventory: ...
def create_work_units(inventory: BatchInventory, phase: str, mode: str, images_per_work_unit: int | None) -> list[WorkUnit]: ...
def load_work_unit_state(runtime: Path, unit: WorkUnit) -> dict[str, Any] | None: ...
def write_work_unit_state(runtime: Path, unit: WorkUnit, status: str, **extra: Any) -> dict[str, Any]: ...
def recover_pending_mutation(state: dict[str, Any], batch_path: Path) -> dict[str, Any]: ...
def select_next_work_units(config: dict[str, Any], phase: str) -> list[WorkUnitPlan]: ...
```

**Inventarregeln:** nur erlaubte Bilddateien, sichere relative POSIX-Pfade, stabile lexikographische Sortierung. Der Inventar-Fingerprint entsteht deterministisch aus der vollständigen Liste von Pfad, Größe und `mtime_ns`. Ändert sich das Inventar eines bereits begonnenen Batches, ist Fortsetzung **verboten**: Ergebnis `source_inventory_changed`, Batch wird quarantänisiert oder als manuell zu prüfen markiert.

**State-Pfad:**
```text
<workflow_data>/runtime/work_units/<batch_id>/<phase>/<work_unit_id>.json
```

**Mindestfelder:** `schema_version`, `producer_version`, `work_unit_id`, `parent_batch_id`, `phase`, `ordinal`, `inventory_fingerprint`, `config_fingerprint`, `status`, `image_ids`, `completed_image_ids`, Zähler, Fehler, Pausengrund, `pending_mutation`.

**Statusgraph:**
```text
planned → in_progress → mutation_planned → in_progress → completed
in_progress → paused_budget | paused_runtime | quarantined
mutation_planned → recovery_required
```

## B5. Dateioperationen, Planner und Quarantäne (T1, T2, W2)

### Pending-Mutation-Contract

Vor jeder sichtbaren Änderung eines Bildes wird ein State atomar geschrieben:

```python
pending_mutation = {
    "image_id": image_id,
    "operation": "metadata_write|file_move|archive_add",
    "source_relative_path": source_rel,
    "target_relative_path": target_rel,
    "expected_source_exists": False,
    "expected_target_exists": True,
}
```

Danach wird die Operation ausgeführt und ihr Ergebnis am bekannten Ziel geprüft. Erst dann wird `pending_mutation` entfernt und die Bild-ID zu `completed_image_ids` hinzugefügt.

**Recovery-Regeln (ausschließlich, keine freie Dateisuche):**
- erwartetes Ziel existiert → Abschlussstate nachtragen;
- erwartete Quelle existiert (Ziel fehlt) → identische Operation einmal idempotent wiederholen;
- jeder andere Zustand → `recovery_required`, Batch quarantänisieren oder manuell melden.

### Planner (`app/planning.py`)

Auswahlreihenfolge, verbindlich:
1. `recovery_required`;
2. `paused_runtime`, `paused_budget`, `in_progress` (angefangene Arbeit hat immer Vorrang, unabhängig von `batch_sort` — Umsetzung von A2/W2);
3. neue physische Batches, sortiert nach `batch_sort` (`oldest_first` | `newest_first`);
4. Begrenzung durch `batch_limit`, `max_images_per_run` und Zeitbudget.

Im `source_batch`-Modus zählt `batch_limit` physische Ordner, im `image_count`-Modus zählt es WorkUnits. Eine WorkUnit wird niemals mitten in ihrer Bearbeitung durch ein globales Bildlimit abgebrochen.

### Phase 1 (`app/phases.py`) — korrigierte Reihenfolge für T2

1. WorkUnit-Plan laden, Recovery vor jeder neuen Analyse ausführen.
2. Lock auf den physischen Batch setzen.
3. Noch offene Bilder bearbeiten, dabei `pending_mutation`-Contract je Bildoperation einhalten.
4. Nach jedem Bild bzw. Checkpoint Fortschritt atomar schreiben.
5. Nach Abschluss aller WorkUnits des physischen Batch: Manifest fertigstellen.
6. **`phase1_moving` schreiben — zwingend vor Schritt 7.**
7. Gesamten physischen Batch nach `temp_images` bewegen (`shutil.move`).
8. **`phase1_completed` schreiben — erst nach erfolgreich verifiziertem Move.**

Diese Reihenfolge behebt T2 unmittelbar: Ein Abbruch zwischen Schritt 6 und 7 zeigt beim Resume einen Batch mit State `phase1_moving`, dessen Zielzustand eindeutig geprüft werden kann (Batch noch am Quellpfad oder bereits am Ziel); ein Abbruch zwischen 7 und 8 zeigt einen Batch am Ziel ohne `phase1_completed`, der beim Resume den Abschlussstate nachträgt, statt erneut zu verschieben.

### Phase 2

Verwendet dieselbe WorkUnit-Planung, belässt die sichtbare Review-Struktur jedoch bis alle WorkUnits abgeschlossen sind. Ein Bild wird nur mit eindeutig vorliegender, unveränderlicher Review-Entscheidung finalisiert.

### Quarantäne-Isolation in der Batch-Schleife — verbindliche Behebung von T1

```python
for batch_or_unit in scheduled:
    try:
        process_physical_batch_or_work_unit(batch_or_unit, config)
    except SafetyError as error:
        quarantine_batch(
            batch_or_unit.path,
            basedir=config["paths"]["basedir"],
            temp_error=config["paths"]["temp_error"],
            reason=str(error),
        )
        results.append({"batch_id": batch_or_unit.batch_id, "status": "quarantined", "reason": str(error)})
        continue
    results.append({"batch_id": batch_or_unit.batch_id, "status": "completed"})
```

**Verbindlich:** Der `try/except`-Block muss den kleinsten sinnvollen Verarbeitungsschritt je physischem Batch umschließen (nicht die gesamte Schleife über alle Batches). Ein Inventarfehler betrifft den ganzen physischen Batch und führt zur Quarantäne dieses Batches; ein reiner Bildanalyse- oder Modellfehler betrifft nur das jeweilige Bild und führt zu einer neutralen Zusatzbewertung bzw. einem sichtbaren `analysis_error`-Feld, nicht zur Quarantäne des ganzen Batches.

## B6. Score-Contract und Adapter

`app/culling.py` behält bestehende Contracts: `technical_components()`, `final_score()`, `predicted()`, `stars()`, `apply_series()`. Die einzige finale Komponentenstruktur lautet:

```python
components = {
    "base_score": base_score,       # float | None
    "eye_score": eye_score,         # float | None
    "personal_score": personal_score,  # float | None
    "family_score": family_score,   # float | None
}
```

`technical_components()` ergänzt zusätzlich `analysis_error: str | None`. `final_score(components, weights)` verwendet ausschließlich Werte ungleich `None` und renormiert die konfigurierten Gewichte proportional. `personal_score` wird nie in `base_score` vermischt. Der bestehende `reference_score` wird an der Phase-1-Grenze zu `personal_score` überführt (Rename, keine neue Semantik).

Neue bzw. angepasste Schnittstellen:

```python
class ClipAdapter:
    def diagnose(self, options: dict[str, Any]) -> ModelDiagnosis: ...
    def score_prompts(self, image_path: Path, positive_prompts: list[str], negative_prompts: list[str]) -> float | None: ...
    def embed_image(self, image_path: Path) -> tuple[float, ...] | None: ...

class ClipSeriesAdapter:
    def diagnose(self, options: dict[str, Any]) -> ModelDiagnosis: ...
    def embed_image(self, image_path: Path) -> tuple[float, ...] | None: ...

@dataclass(frozen=True)
class FaceAnalysis:
    face_status: str
    family_score: float | None
    eye_score: float | None
    person_slug: str | None
    match_score: float | None
    second_best_score: float | None
    error_code: str | None
```

## B7. Modelle, Diagnose, Installation und Worker

Neue zentrale Module: `app/model_runtime.py`, `app/model_diagnostics.py`, `app/model_download.py`, `app/inference_runtime.py`.

```python
@dataclass(frozen=True)
class ModelDiagnosis:
    enabled: bool
    ready: bool
    backend: str
    adapter_version: str
    provider: str
    model_paths: tuple[str, ...]
    model_fingerprints: tuple[str, ...]
    reason_code: str
    message: str
```

**Standardisierte `reason_code`-Werte:** `disabled`, `dependency_missing`, `model_path_invalid`, `model_file_missing`, `model_manifest_invalid`, `model_hash_mismatch`, `model_load_failed`, `budget_exhausted`, `worker_failed`, `unsupported_backend`, `ready`. Kein Adapter wechselt bei einem Fehler unbemerkt Modell oder Backend; kein deaktiviertes Modell erzeugt einen Dummy-Score.

Modellordner (`models/taste/`, `models/series/`, `models/faces/yunet-sface/`, `models/faces/eye-state/`) enthalten je ein `README` und Manifest-Beispiel. README beschreibt Zweck, erwartete Dateien, Quelle/Lizenz, Input, Normalisierung, Output, Labels und SHA256. `.gitignore` schließt Modellbinärdateien, echte Modellmanifeste und `workflow-data/runtime/` aus; `README`, `.gitkeep` und `*.example` bleiben versionierbar.

Downloads erfolgen ausschließlich über einen expliziten CLI-Verwaltungsbefehl: lokaler Katalog erlaubter Modell-IDs, HTTPS, Host-Allowlist, Größenlimit, SHA256-Prüfung, sicheres Staging, atomare Installation; Archive mit Pfadausbruch oder Symlinks werden abgelehnt. Workflow-Phasen laden oder installieren nie selbst Modelle.

Worker starten mit `spawn`, standardmäßig ein Worker, optional maximal zwei. Worker führen ausschließlich Inferenz aus und liefern nur Rechenresultate. Der Hauptprozess schreibt deterministisch alle States, Manifeste und Dateien.

## B8. Geschmack, Serien, Face und Eye — Implementierungsdetails

Der `ClipAdapter` lädt ausschließlich lokale, vollständige Modellverzeichnisse ohne Netzwerkzugriff, hält Modell/Processor pro Lauf im Speicher, bietet `score_prompts()` und `embed_image()`, L2-normalisiert Bildvektoren und persistiert sie nie. `clip_taste_adapter.py` bleibt ein schlanker fachlicher Wrapper darüber.

**Serienmodell:** EXIF-Aufnahmezeit mit Fallback auf `mtime`; Zeitfenster-Filter oder explizites Opt-in für unbeschränkte Vergleiche; Kosinus-Ähnlichkeit L2-normalisierter Embeddings; deterministische Connected Components mit Mindestclustergröße; `series_best` wird über den bereits berechneten `final_score` bestimmt, bei Gleichstand über `relative_path` als Tie-Breaker. Bei Fehler oder Deaktivierung bleibt der `apply_series()`-Fallback sichtbar im Manifest aktiv. Kein Seriencluster entscheidet direkt Keep/Review/Reject.

**Face-Service:** bei deaktivierter Family-Funktion ohne OpenCV/ONNX-Import neutral zurückgeben. Nur explizit aktivierte Referenzen; Referenzembeddings ausschließlich im RAM. YuNet-Crop sicher begrenzen; Identity nur bei numerischer Threshold/Margin-Konfiguration über das bestehende `match_valid()`. `family_score` nur bei eindeutigem, sicherem Match; unbekannte/mehrdeutige Fälle bleiben neutral und erzeugen keine Kandidatenartefakte.

**Eye-State-Adapter (ONNX, CPU):** genau ein ausreichend großes Gesicht; RGB → konfigurierte Normalisierung → NCHW float32 → Inferenz; validierter Zweiklassen-Output mit Labels exakt `[closed, open]`; `confidence = max(P)`; unter Mindestkonfidenz neutral, sonst `eye_score = P(open)`. Statuscodes: `open`, `closed`, `uncertain`, `no_face`, `multiple_faces`, `face_too_small`, `error`.

## B9. Gemeinsamer `ImageFeatureService`

Neue Datei `app/image_features.py`. Enthält **keinerlei Geschäftsentscheidung** und schreibt **keine** Daten auf Datenträger.

```python
@dataclass(frozen=True)
class ImageSourceKey:
    canonical_path: str
    size_bytes: int
    mtime_ns: int

@dataclass(frozen=True)
class NormalizedImage:
    key: ImageSourceKey
    width: int
    height: int
    aspect_ratio: float
    rgb_image: Image.Image

@dataclass(frozen=True)
class ImageFeatures:
    key: ImageSourceKey
    width: int
    height: int
    aspect_ratio: float
    perceptual_hash: str | None
    technical_preview: Image.Image | None
    comparison_preview: Image.Image | None
    series_embedding: tuple[float, ...] | None

class ImageFeatureService:
    def load_rgb(self, path: Path) -> NormalizedImage | None: ...
    def preview(self, image: NormalizedImage, long_edge: int) -> Image.Image: ...
    def perceptual_hash(self, image: NormalizedImage) -> str | None: ...
    def features(self, path: Path, *, technical_edge: int | None = None,
                 comparison_edge: int | None = None, need_hash: bool = False) -> ImageFeatures | None: ...
    def clear(self) -> None: ...
```

**Regeln:** `load_rgb()` führt vor jeder weiteren Verarbeitung `ImageOps.exif_transpose()` aus und konvertiert nach RGB. Cache-Key ist der kanonische Pfad plus Größe und `mtime_ns`; jede Änderung invalidiert den Eintrag. Der Cache lebt ausschließlich im RAM des laufenden Prozesses/Laufs und wird am Ende des Laufs geleert. Culling kann z. B. eine 512-Pixel-, MANUAL_KEEP eine 256-Pixel-Vorschau aus derselben korrigierten Quelle anfordern — das vermeidet redundantes Dekodieren, ohne fachliche Kopplung zu erzeugen. `rgb_image` darf nie außerhalb des Prozessflusses persistiert oder in einem Report verwendet werden.

## B10. MANUAL_KEEP: Adapter, Algorithmus und Audit (M1)

Bestehende Schnittstelle bleibt vollständig kompatibel:

```python
Similarity = Callable[[Path, Path], float | None]
```

Neue Datei `app/manual_keep_similarity.py`:

```python
@dataclass(frozen=True)
class SimilarityResult:
    score: float | None
    perceptual_hash_distance: int | None
    verification_score: float | None
    aspect_ratio_compatible: bool
    reason: str | None

class ResolutionAwareSimilarity:
    def __init__(self, features: ImageFeatureService, options: Mapping[str, Any]) -> None: ...
    def compare(self, source: Path, candidate: Path) -> SimilarityResult: ...
    def __call__(self, source: Path, candidate: Path) -> float | None:
        return self.compare(source, candidate).score
```

### Verbindlicher Vergleichsalgorithmus

1. Beide Dateien über `ImageFeatureService.load_rgb()` lesen. Lesefehler → `score=None`, `reason="image_unreadable"`, kein Move.
2. EXIF-korrigierte RGB-Daten verwenden; Originalauflösung und Dateiname sind ab hier irrelevant.
3. Relative Seitenverhältnisabweichung bestimmen. Über `aspect_ratio_tolerance` → keine Endprüfung, `reason="aspect_ratio_incompatible"`.
4. Perceptual Hash auf kleiner Graustufenrepräsentation berechnen. Hamming-Distanz über `perceptual_hash_max_distance` → `reason="hash_distance_exceeded"`.
5. Nur überlebende Kandidaten proportional (kein verzerrendes Stretching) auf `comparison_long_edge` skalieren.
6. Deterministischen Verifikationsscore berechnen: normierte Luminanz-/RGB-Differenz gleicher Größe, optional strukturgewichtete lokale Kachelprüfung, Ergebnis auf `[0,1]` normiert. SSIM nur verwenden, wenn im Projekt bereits eine verlässliche Abhängigkeit existiert — **keine neue schwere wissenschaftliche Bibliothek nur für MANUAL_KEEP einführen.**
7. Kombinierten Endscore nur bei gültigen Gates (Schritte 3–6 erfolgreich) zurückgeben. `_rank()` bleibt stabil: absteigender Score, danach Pfad als Tie-Breaker.
8. Ein im selben Lauf bereits vorhandenes Serienembedding darf, wenn `use_series_embedding_prefilter=true`, ausschließlich die Kandidatenmenge reduzieren — es darf niemals Hash-Gate, Endprüfung oder Margin ersetzen oder umgehen. Ein CLIP-Geschmacksscore ist für MANUAL_KEEP grundsätzlich ausgeschlossen.

### Entscheidungslogik in `process_inbox()`

`manual_keep.py` verwendet standardmäßig `ResolutionAwareSimilarity`, akzeptiert weiterhin einen injizierten Legacy-`Callable` für Tests/Abwärtskompatibilität.

| Ergebnis | Bedingung | Dateiaktion |
|---|---|---|
| `matched` | `best >= verification_threshold` **und** `best - second_best >= minimum_best_second_margin` | nur bei `allow_automatic_move=true`: Move nach `manual_keep_used` |
| `ambiguous` | Schwelle erreicht, Margin nicht erreicht | Inbox unverändert |
| `unmatched` | kein Kandidat vorhanden oder Score unter Schwelle | Inbox unverändert |
| `error` | Lese- oder Verarbeitungsfehler | Inbox unverändert |

**Auditrecord** (rückwärtskompatibel ergänzt): `similarity_backend`, Status, Kandidatenanzahl, bester/zweitbester Score, Hash-Distanz als Zahl, Verifikationsscore, `reason`-Code, zulässige Quell-/Zielpfade, Move-Status. **Enthält niemals:** Hashbitfolgen, Bilddaten, Vorschauen oder Embeddings.

## B11. Gewichtungsassistent

`app/weight_assistant.py` nutzt ausschließlich unveränderliche, menschlich bestätigte Review-Records und exakt die vier Scorekomponenten (`base_score`, `personal_score`, `eye_score`, `family_score`; Target Keep=1, Review/Reject=0). Training erfolgt mit zeitlichem Train-/Validation-Split, L2-regulierter logistischer Regression und klaren Regeln für fehlende Werte.

Der Assistent erzeugt zuerst ein JSON-Proposal. Eine Aktivierung gilt frühestens im Folgelauf und nur bei erfüllten Gates: Mindestdatenmenge, messbarer Validierungsgewinn, begrenzte Gewichtsänderung, Höchstgewicht pro Komponente, Cooldown-Zeitraum, kompatible aktive Konfiguration, atomar schreibbarer Aktivierungsrecord. Die YAML wird nie still überschrieben; die Laufzeitgewichte liegen unter `workflow-data/runtime/calibration/active_weights.json`. Bei Überschreiten eines Validation-Loss-Grenzwerts erfolgt automatischer Rollback auf die letzte stabile Gewichtung. **MANUAL_KEEP-Resultate sind niemals Trainingslabels für Culling-Gewichte.**

## B12. Betroffene Dateien (vollständige Übersicht)

| Bereich | Dateien |
|---|---|
| Version/Safety (Paket 0) | `app/__init__.py`, `app/safety.py`, `app/locks.py`, `app/runtime.py`, `app/calibration.py`, `app/batch_state.py`, `app/reporting.py`, `app/face_cache.py` |
| Fehlerisolation/Recovery (Paket 0) | `app/phases.py`, `app/planning.py` |
| Scheduling/WorkUnits (Paket 1) | `app/work_units.py` (neu), `app/planning.py`, `app/phases.py`, `app/batch_state.py`, `app/runtime.py`, `app/locks.py` |
| Bildfeatures/MANUAL_KEEP (Paket 2/7) | `app/image_features.py` (neu), `app/manual_keep_similarity.py` (neu), `app/manual_keep.py` |
| Scoring/Modelle (Paket 3–4) | `app/culling.py`, `app/clip_taste_adapter.py`, `app/clip_adapter.py` (neu), `app/clip_series_adapter.py` (neu), `app/face_backend.py`, `app/face_adapter_yunet_sface_cpu.py`, `app/family_recognition.py`, `app/eye_state_adapter_onnx.py` (neu) |
| Modell-/Worker-Infrastruktur (Paket 2) | `app/model_runtime.py` (neu), `app/model_diagnostics.py` (neu), `app/model_download.py` (neu), `app/inference_runtime.py` (neu) |
| Lernen/Reports (Paket 5) | `app/weight_assistant.py` (neu), `app/calibration.py`, `app/reporting.py`, `app/archives.py`, `app/face_cache.py` |
| Konfiguration/Dokumente (alle Pakete) | `config/config.yaml`, `app/configuration.py`, `docs/MANUAL_DE.md`, `CHANGELOG.md`, `.gitignore` |
| Tests | `tests/test_security_core.py`, `tests/test_runtime_recovery.py`, `tests/test_calibration_reporting.py`, neue Tests je Paket gemäß Anhang B |

**Hinweis zu bestehenden Modulnamen:** Das Repository verwendet bereits `face_backend.py`, `face_adapter_yunet_sface_cpu.py` und `family_recognition.py` statt eines einzigen `face_service.py`. Neue Face-/Eye-Logik ist in diese bestehende Modulstruktur zu integrieren, nicht als Parallelstruktur `face_service.py` neu anzulegen, um Redundanz und Namenskonflikte zu vermeiden.

## B13. Umsetzungsreihenfolge und Gates

1. **Paket 0 (Vorbedingung, blockierend):** S1, S3, T1, T2 beheben; zugehörige Tests (Anhang B, Abschnitt „Sicherheit/State“) müssen grün sein, bevor irgendein weiteres Paket beginnt.
2. **Paket 1:** WorkUnits, Bildmodus, beide Sortierungen, Resume, Dry-Run, Recovery.
3. **Paket 2:** `ImageFeatureService`, Modellvertrag (`ModelDiagnosis`), lokale Modellpfade, sichere Installation/Diagnose.
4. **Paket 3:** Persönlicher Geschmack (CLIP) und Serienmodell samt Fallback.
5. **Paket 4:** Face, Eye und optionale Worker.
6. **Paket 5:** Gewichtungsassistent, Aktivierung, Rollback.
7. **Paket 6:** MANUAL_KEEP-Auflösungsabgleich (`ResolutionAwareSimilarity`) — zunächst **ohne** Serien-Embedding-Vorfilter. Der Vorfilter darf erst nach eigenständiger, erfolgreicher MANUAL_KEEP-Abnahme optional aktiviert werden.
8. **Paket 7:** Dokumentation, vollständige Tests, Python-Compile-Check, Konfigurationsvalidierung, Secret-Scan, vollständiger Diff-Review gegen dieses Dokument.

Nach jedem Paket: Tests ausführen, Ergebnisse prüfen, vollständigen Diff prüfen und **erst nach expliziter Freigabe** das nächste Paket beginnen. Ein Paket darf keine ungetestete Nebenänderung einführen. Fehler, unklare Testausgänge, Sicherheitsabweichungen oder unvollständige Dokumentation stoppen die Umsetzung bis zur Korrektur und erneuten Prüfung.

## B14. Abnahmekriterien (Gesamtprojekt)

Die Implementierung ist erst abgenommen, wenn:

1. Kein Writer mehr ein `producer_version`-Literal enthält (S1/S3 vollständig behoben, per Scan bestätigt).
2. `safety.validate_control_record()` jede strukturell gültige Datei unabhängig von der konkreten Projektversion akzeptiert.
3. Ein fehlerhafter physischer Batch quarantänisiert wird und alle Folge-Batches regulär weiterlaufen (T1 behoben, per Test bestätigt).
4. Kein Abbruch zwischen Move und State-Write zu Doppelmutation, Datenverlust oder unauffindbarem Batch führt (T2 behoben).
5. Ordner- und Bildmengenmodus sicher, deterministisch und fortsetzbar arbeiten; angefangene Arbeit hat stets Vorrang vor neuen Batches.
6. Projekt- und Dateiversion getrennt, zentral und rückwärtslesbar verwendet werden.
7. Alle KI-Funktionen optional, lokal, diagnostizierbar sind und einen Fallback besitzen; keine fehlende KI wertet ein Bild künstlich ab (`None`, nie `0.0`).
8. Keine sensiblen Bild-, Face- oder Vektordaten persistiert oder versioniert werden.
9. MANUAL_KEEP dieselbe Aufnahme über Auflösungen/Kompression/EXIF-Drehung hinweg erkennt, aber ähnliche, nicht identische Aufnahmen niemals automatisch bewegt.
10. Alle Paket-Gates, Tests, Compile-, Konfigurations-, Secret- und Diff-Prüfungen dokumentiert erfolgreich abgeschlossen sind.

---

# Anhang A — Vollständige Zielkonfiguration

```yaml
workflow:
  phase_execution: phase1_then_phase2
  batch_limit: 1
  batch_sort: oldest_first                 # oldest_first | newest_first
  skip_incomplete_batches: false
  resume_incomplete_batches: true
  max_run_hours: 4
  dry_run: false
  work_unit_mode: source_batch             # source_batch | image_count
  images_per_work_unit: null               # positive Ganzzahl bei image_count
  max_images_per_run: 0                    # 0 = unbegrenzt
  progress_checkpoint_interval: 5

paths:
  model_dir: ../models

inference:
  workers: 1
  start_method: spawn
  queue_size: 4
  maximum_worker_ram_mb: 2048
  allow_parallel_clip: false
  allow_parallel_onnx: false

models:
  download:
    enabled: false
    allow_hosts: []
    require_https: true
    connect_timeout_seconds: 15
    read_timeout_seconds: 120
    maximum_artifact_size_mb: 2048
    allow_redirects: false
  taste: {enabled: false, model_id: taste-clip-vit-base-patch32, install_dir: taste/clip-vit-base-patch32}
  series: {enabled: false, model_id: series-clip-vit-base-patch32, install_dir: series/clip-vit-base-patch32}
  face: {enabled: false, model_id: yunet-sface-cpu, install_dir: faces/yunet-sface/yunet-sface-cpu}
  eye_state: {enabled: false, model_id: eye-state-onnx, install_dir: faces/eye-state/eye-state-onnx}

culling:
  base_weights: {sharpness: 0.45, aesthetic: 0.35, exposure: 0.20}
  final_component_weights: {base_score: 0.60, personal_score: 0.20, eye_score: 0.10, family_score: 0.10}
  taste_model:
    enabled: false
    backend: clip_prompt_cpu
    model_id: taste-clip-vit-base-patch32
    max_inferences_per_run: 100
    positive_prompts: ["a photograph matching my personal preference", "sharp, well composed photograph"]
    negative_prompts: ["blurred photograph", "poorly exposed photograph"]
  series_model:
    enabled: false
    backend: clip_image_embeddings_cpu
    model_id: series-clip-vit-base-patch32
    max_images_per_batch: 200
    max_embeddings_per_run: 100
    max_time_gap_seconds: 8
    allow_unbounded_comparison: false
    visual_similarity_threshold: 0.90
    minimum_cluster_size: 2

family_recognition:
  enabled: false
  backend: opencv_yunet_sface_cpu
  execution_profile: cpu
  reference_root: ../workflow-data/family-references
  match_threshold: null
  min_best_second_margin: null
  matched_score: 1.0
  eye_state:
    enabled: false
    backend: onnx_open_closed_eye_cpu
    model_id: eye-state-onnx
    input_size: 224
    minimum_face_area_ratio: 0.03
    minimum_confidence: 0.80
    labels: [closed, open]
    normalization: {mean: [0.485, 0.456, 0.406], std: [0.229, 0.224, 0.225]}

manual_keep:
  enabled: true
  similarity_backend: resolution_aware_v1
  comparison_long_edge: 256
  aspect_ratio_tolerance: 0.02
  perceptual_hash_max_distance: 6
  verification_threshold: 0.95
  minimum_best_second_margin: 0.03
  allow_automatic_move: true
  use_series_embedding_prefilter: false

calibration:
  weight_assistant:
    enabled: false
    automatic_activation: false
    minimum_images: 500
    validation_fraction: 0.20
    l2_regularization: 0.10
    minimum_validation_gain: 0.03
    maximum_weight_delta: 0.05
    maximum_component_weight: 0.70
    cooldown_days: 14
    rollback_validation_loss: 0.03
    require_all_active_components: true
```

---

# Anhang B — Test- und Abnahmematrix

**Sicherheit/State (Paket 0, blockierend):**
- Alte Projektversion mit gültiger Dateiversion ist lesbar; strukturell ungültige Dateiversion wird abgelehnt.
- Jede der sieben in B2 gelisteten Writer-Dateien schreibt ausschließlich die zentrale `VERSION`-Konstante, kein Literal mehr.
- Repository-weiter Scan nach `'7.7.0'`/`'7.8.0'` als String-Literal liefert null Treffer außerhalb von Tests/Changelog.
- Ein `SafetyError` in einem physischen Batch führt zur Quarantäne genau dieses Batches; alle Folge-Batches im selben Lauf werden regulär verarbeitet.
- Abbruch vor `phase1_moving`, zwischen `phase1_moving` und Move, und zwischen Move und `phase1_completed` führt in allen drei Fällen zu korrektem, nicht-doppeltem Resume.

**WorkUnits (Paket 1):**
- Stabiler Inventar-Fingerprint über wiederholte Läufe hinweg.
- Bildmodus (`image_count`) erzeugt keine sichtbaren Teilordner.
- Angefangene WorkUnits werden vor neuen Batches fortgesetzt, auch bei `newest_first`.
- Beide Sortierungen (`oldest_first`, `newest_first`) funktionieren für neue Batches korrekt.
- Erreichte Limits (`batch_limit`, `max_images_per_run`, `max_run_hours`) beginnen keine neue WorkUnit, brechen aber keine laufende ab.
- Inventaränderung eines angefangenen Batches führt zu `source_inventory_changed`, nicht zu stillem Fortsetzen.
- Physischer Batch bewegt sich erst nach Abschluss der letzten zugehörigen WorkUnit.

**Modelle/Scores (Paket 2–5):**
- Deaktivierter Adapter importiert keine optionalen Abhängigkeiten und liefert `None`, nie `0.0`.
- Modellpfad-Ausbruch außerhalb `model_dir` wird abgelehnt.
- Fehlendes/beschädigtes Modell liefert `ModelDiagnosis` statt Absturz.
- `final_score()` renormiert korrekt bei fehlenden Komponenten.
- Serien-Fallback (Dateinamen-Logik) greift bei deaktiviertem/fehlerhaftem Serienmodell.
- Eye Score wird nur bei genau einem ausreichend großen Gesicht gesetzt, sonst neutral mit korrektem Statuscode.
- Keine Embeddings, Face-Crops oder Bildbytes erscheinen in State-, Report- oder Cache-Dateien.

**MANUAL_KEEP (Paket 6):**
- Dieselbe Aufnahme in kleinerer/größerer Auflösung → `matched`.
- Dieselbe Aufnahme mit JPEG-Rekompression und anderem Dateinamen → `matched`.
- Gedrehte EXIF-Variante derselben Aufnahme → `matched`.
- Anderes Foto desselben Motivs/derselben Serie → kein automatischer Match.
- Deutlich anderes Seitenverhältnis → kein Match (`aspect_ratio_incompatible`).
- Zwei ähnlich gute Kandidaten → `ambiguous`, kein Move.
- Bester Score unter Schwelle → `unmatched`, kein Move.
- Beschädigte Quelle oder Kandidat → `error`, kein Move.
- Neustart nach vorbereitetem, aber unterbrochenem MANUAL_KEEP-Move → kein Doppelmove.
- Cache-Invalidierung nach Änderung von Dateigröße oder `mtime_ns`.
- Serienembedding als Vorfilter führt ohne bestandene Endprüfung nie zu `matched`.
- Auditrecord enthält keine Hashbitfolgen, Bilddaten, Vorschauen oder Embeddings.

**Abschluss-Gates (Paket 7):**
- Alle Tests grün, Python-Compile-Check ohne Fehler.
- Konfigurationsvalidierung deckt alle in B3/Anhang A beschriebenen Regeln ab.
- Deterministische Wiederholbarkeit (gleicher Input → gleiches Ergebnis).
- Vollständiger Diff-Review gegen dieses Dokument, insbesondere gegen B1–B11.
- Secret-Scan ohne Funde; `.gitignore` schließt Modellgewichte und Runtime-Daten korrekt aus.

---

# Anhang C — Verifikation gegen den bestehenden Code (Referenz-Commit `8b616a8b`)

Diese Spezifikation wurde nicht nur aus den vier Zwischenvorschlägen konsolidiert, sondern zusätzlich per GitHub-Codesuche gegen das reale Repository geprüft:

- **`app/__init__.py`** enthält tatsächlich `VERSION = "7.8.0"` — bestätigt per Direktabruf.
- **`app/safety.py`** enthält tatsächlich `REQUIRED_CONTROL_FIELDS = {'schema_version', 'created_at', 'updated_at', 'producer_version'}` und die Zeile `if payload['producer_version'] != '7.7.0': raise SafetyError('control_record_producer_version')` — S1 damit als **aktiver, reproduzierbarer Fehler** bestätigt, nicht nur als theoretisches Risiko.
- **Codesuche nach `producer_version`** über das gesamte Repository bestätigt Literal `'7.7.0'` in `locks.py`, `runtime.py` (zwei Stellen), `calibration.py` (zwei Stellen), `batch_state.py`, `reporting.py`, `face_cache.py`. Gleichzeitig bestätigt dieselbe Suche, dass `archives.py` und `phases.py` bereits `producer_version: VERSION` verwenden (Änderung aus CHANGELOG 7.8.0) — diese ursprünglich in einem der Zwischenvorschläge pauschal als „betroffen“ gelistete Dateien wurden **korrigiert entfernt**, um keine überflüssige Änderung an bereits korrektem Code vorzuschlagen.
- **Codesuche nach `quarantine_batch`** zeigt die Funktion nur definiert in `runtime.py` und referenziert in `tests/test_runtime_recovery.py`. Kein Treffer in `phases.py`. **T1 damit als aktiver Fehler bestätigt:** Die Batch-Schleife nutzt die vorhandene Quarantänefunktion nicht.
- **Codesuche nach `shutil.move`** zeigt zwei Move-Aufrufe in `phases.py` (Archiv-Rohdaten und Zielordner-Move) sowie einen in `manual_keep.py` und einen in `runtime.py` (innerhalb `quarantine_batch()` selbst, dort bereits korrekt vor dem Manifest-Write). Die Reihenfolge von State-Write und Move in der Phase-1-Batchverschiebung wurde anhand dieser Fundstellen für B5 präzisiert.
- **Modulstruktur:** Das Repository verwendet bereits granulare Module (`face_backend.py`, `face_adapter_yunet_sface_cpu.py`, `family_recognition.py`, `clip_taste_adapter.py`, `result_contract.py`, `inventory.py`) statt einer einzigen `face_service.py`/`clip_adapter.py`-Datei, wie einige Zwischenvorschläge implizit annahmen. B12 wurde entsprechend korrigiert: neue Logik wird in die bestehende Modulstruktur integriert statt parallele, redundante Module anzulegen.

**Ergebnis der Prüfung:** Die Kernbefunde S1 und T1 sind vollständig bestätigt und werden als blockierende Vorbedingung (Paket 0) behandelt. S3 wurde präzisiert (zwei Dateien waren bereits korrekt, das pauschale „alle Writer“ aus den Zwischenvorschlägen wurde auf die sieben tatsächlich betroffenen Dateien reduziert). T2 wurde anhand der Codepfade in eine konkrete, prüfbare Schreibreihenfolge übersetzt. Die MANUAL_KEEP-, WorkUnit- und KI-Adapter-Vorschläge aus rev2–rev4 waren in sich konsistent, sicherheits- und stabilitätskonform sowie mit dem defensiven Coding-Stil des Projekts (Dataclasses, explizite Fehlercodes, atomare JSON-Writer, injizierbare Callables für Tests) harmonisiert und wurden mit den oben genannten Korrekturen übernommen.

*Dokument: `Master_Implementierungsspezifikation_v7_9_0_FINAL.md`*
*Konsolidiert und gegen Repository-Code verifiziert am: 2026-08-


# Übergabe-Notiz: Branch `feature/v7.9.0-workunits-ai-contract`

**Zweck:** Fortsetzung der Umsetzung von `Master_Implementierungsspezifikation_v7_9_0_FINAL.md` (Referenz-Commit `8b616a8b`, Branch `main`). Diese Datei richtet sich an die nächste bearbeitende Person oder KI-Instanz.

## Was auf diesem Branch bereits committet ist (Weg 2, sicher — nur neue Dateien)

Alle folgenden Dateien sind **neu**, überschreiben nichts Bestehendes und wurden vor dem Commit per Sandbox-Test (Syntax + Kernlogik) verifiziert:

| Datei | Paket | Zweck |
|---|---|---|
| `app/work_units.py` | 1 | WorkUnits, Inventar, Resume-Priorität, `select_next_work_units` |
| `app/image_features.py` | 2 | Gemeinsamer RAM-Bildcache (`ImageFeatureService`) |
| `app/model_diagnostics.py` | 2 | `ModelDiagnosis`-Vertrag, `REASON_CODES` |
| `app/model_download.py` | 2 | Sichere, katalogbasierte Modellinstallation |
| `app/model_runtime.py` | 2 | Modell-Laden/-Caching pro Lauf, Pfadprüfung |
| `app/inference_runtime.py` | 2 | Optionaler Worker-Pool (max. 2, `spawn`), serieller Fallback |
| `app/clip_series_adapter.py` | 3 | CLIP-Embedding-Serienähnlichkeit |
| `app/eye_state_adapter_onnx.py` | 4 | Augenzustand, genau ein Gesicht |
| `app/weight_assistant.py` | 5 | Gewichtsvorschlag, Aktivierungsgates, Rollback |
| `app/manual_keep_similarity.py` | 6 | `ResolutionAwareSimilarity`, Vorfilter-Hook (deaktiviert) |
| `scripts/scan_producer_version_literals.py` | 0 | **Rein lesender** Scanner für S1/S3 |

**Wichtig:** Keine dieser Dateien ist bisher irgendwo im bestehenden Code (`phases.py`, `culling.py`, …) tatsächlich verdrahtet. Sie liegen bereit, sind aber noch nicht aktiv.

## Warum Paket 0 und alle Integrations-Diffs NICHT committet wurden

Die verfügbaren GitHub-Werkzeuge in dieser Sitzung konnten den **vollständigen** Inhalt folgender Dateien nicht zuverlässig liefern (`get_file_contents` gibt keinen Text zurück, `search_code` nur Fragmente, `get_commit` für den großen Initial-Commit wird vor `app/*.py` abgeschnitten):

`app/safety.py`, `app/phases.py`, `app/planning.py`, `app/locks.py`, `app/runtime.py`, `app/calibration.py`, `app/batch_state.py`, `app/reporting.py`, `app/face_cache.py`, `app/culling.py`, `app/family_recognition.py`, `app/face_backend.py`, `app/face_adapter_yunet_sface_cpu.py`, `app/manual_keep.py`, `app/configuration.py`.

Ein blindes Überschreiben dieser Dateien aus Fragmenten wäre ein Sicherheitsrisiko (Datenverlust, Bruch der Sicherheitsprüfung) und widerspricht A1 der Spezifikation. **Vorgehen für die Fortsetzung:** Volltext dieser Dateien beschaffen (lokaler Checkout, `git show main:synology-photo-workflow/app/<datei>.py`, oder vom Nutzer bereitgestellt) und erst dann patchen.

## Konkret verifizierte, aber noch offene Befunde (per `search_code` bestätigt, siehe B1/Anhang C)

### S1 — `app/safety.py` (kritisch, blockierend)
Bestätigter Fundort (Fragment, per Codesuche exakt bestätigt):
```python
    if payload['producer_version'] != '7.7.0':
        raise SafetyError('control_record_producer_version')
```
**Verbindliche Ersetzung gemäß B2:**
```python
    if not isinstance(payload['producer_version'], str) or not payload['producer_version']:
        raise SafetyError('control_record_producer_version')
```
Zusätzlich: `CONTROL_FILE_VERSION`-Import und `schema_version`-Prüfung gemäß B2 vollständig umsetzen (`app/__init__.py`: `VERSION = "7.9.0"`, `CONTROL_FILE_VERSION = 1`).

### S3 — Literal `'7.7.0'` statt zentralem `VERSION`-Import (hoch, blockierend)
Bestätigte Fundstellen (je ein `atomic_json(...)`-Aufruf mit `'producer_version': '7.7.0'` literal):
- `app/locks.py` (Run-Lock-Schreiben)
- `app/runtime.py` (Batch-Lock-Schreiben **und** `quarantine_batch()`-Manifest — zwei Stellen)
- `app/calibration.py` (`record()` **und** Readiness-Report — zwei Stellen)
- `app/batch_state.py` (`write_state()`)
- `app/reporting.py` (Run-Summary)
- `app/face_cache.py` (Cache-Manifest)

**Nicht anfassen:** `app/archives.py`, `app/phases.py` verwenden laut Spezifikation und eigener Prüfung bereits `VERSION`-Import.

Nach jedem Fix: `python scripts/scan_producer_version_literals.py app` ausführen — muss ohne Fund enden.

### T1 — Fehlende Quarantäne-Anbindung in `app/phases.py` (kritisch, blockierend)
`quarantine_batch()` ist in `app/runtime.py` vollständig implementiert, wird aber in der Batch-Schleife von `phases.py` nicht aufgerufen. Verbindliche Struktur siehe B5:
```python
for batch_or_unit in scheduled:
    try:
        process_physical_batch_or_work_unit(batch_or_unit, config)
    except SafetyError as error:
        quarantine_batch(batch_or_unit.path, basedir=config['paths']['basedir'], temp_error=config['paths']['temp_error'], reason=str(error))
        results.append({'batch_id': batch_or_unit.batch_id, 'status': 'quarantined', 'reason': str(error)})
        continue
    results.append({'batch_id': batch_or_unit.batch_id, 'status': 'completed'})
```
Der `try/except` muss den kleinsten sinnvollen Schritt je physischem Batch umschließen, nicht die gesamte Schleife.

### T2 — Move-Reihenfolge in `app/phases.py` (hoch, blockierend)
Aktuell (laut Codesuche `shutil.move` in `phases.py`) erfolgt der sichtbare Batch-Move vor dem Abschluss-State. Verbindliche Reihenfolge (B5): `phase1_moving` atomar **vor** `shutil.move()`, `phase1_completed` **erst nach** verifiziertem Move.

### Integrationsdiffs aus den Chat-Paketen 1, 3, 4, 6
Vollständig ausformulierte, aber **gegen den echten Volltext noch nicht gegengeprüfte** Diff-Vorschläge liegen im Gesprächsverlauf dieser Session vor (nicht in diesem Repository committet):
- Paket 1: `planning.py`/`phases.py` → `select_next_work_units()`-Anbindung, WorkUnit-Checkpoints.
- Paket 3: `culling.py` → `personal_taste_score()` statt `reference_score`-Vermischung; `apply_series()` → echtes Clustering statt Dateinamen-Gruppierung.
- Paket 4: `face_backend.py` → `FaceAnalysis`-Dataclass; `family_recognition.py` → `analyze_faces()`-Orchestrierung (Signatur von `backend.match()` **vor Verdrahtung verifizieren**).
- Paket 6: `manual_keep.py` → `ResolutionAwareSimilarity` als Default-Similarity, Vorfilter bleibt deaktiviert.

### Noch nicht begonnen
- Paket 5 Integration in `calibration.py`/`reporting.py` (nur `weight_assistant.py` selbst ist committet).
- `config/config.yaml`, `app/configuration.py` (Anhang A/B3 vollständig).
- `docs/MANUAL_DE.md`, `CHANGELOG.md`-Eintrag 7.9.0 (Entwurf lag im Chat vor, nicht committet, da aktueller Volltext von `CHANGELOG.md` seit 7.8.0 unbekannt).
- Vollständige neue Tests gemäß Anhang B.
- Finaler Diff-Review, Secret-Scan, Python-Compile-Check gegen den echten, vollständigen Baum (Paket 7).

## Empfehlung für die Fortsetzung
1. Volltext der oben gelisteten Paket-0-Dateien beschaffen.
2. S1/S3/T1/T2 einzeln fixen, jeweils mit dem zugehörigen Test aus Anhang B absichern.
3. Erst nach grünem Paket 0 die Integrationsdiffs aus Paket 1–6 gegen echten Volltext verdrahten.
4. Paket 7 zuletzt.

