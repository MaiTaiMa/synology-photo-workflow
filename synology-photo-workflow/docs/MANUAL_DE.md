# Benutzerhandbuch

Der **Synology Photo Workflow** verarbeitet Kamera-Batches in zwei kontrollierten
Phasen. Der sichere Standard `assistedreview` verschiebt nach Phase 1 nach
`TEMPIMAGES`; erst der bewusste manuelle Umzug nach `TEMPDONE` erlaubt Phase 2.
Diese archiviert nicht mehr benötigte ARWs geprüft, bevor sie sie entfernt.

> **Sicherheitsregel:** Phase 2 nur mit Testkopien beginnen. Das historische
> `legacy/nas_photosort.sh` ist ausschließlich eine manuelle Notfallreferenz;
> es darf nicht parallel zum Python-Workflow laufen.

## Voraussetzungen

- Python 3.11 oder neuer für lokale Tests
- Docker Engine mit Docker Compose Plugin für Containerbetrieb
- Für Synology: ein dedizierter, persistenter Datenordner und ein DSM-Konto mit
  Lese-/Schreibrecht darauf
- Optional: ExifTool für eingebettete Metadaten; Familienerkennung bleibt bis
  zur separaten Backend-Abnahme deaktiviert

## Verzeichnisrollen

| Pfad | Zweck |
|---|---|
| `TEMPSD` | Neue vollständige Kamera-Batches (`YYYYMMDD`) |
| `TEMPIMAGES` | Ergebnis aus Phase 1, zur manuellen Sichtung |
| `TEMPDONE` | Ausschließlich manuell freigegebene Batches für Phase 2 |
| `TEMPERROR` | Quarantäne unsicherer oder fehlerhafter Batches |
| `samples`, `faces`, `models`, `runtime` | Persistente Referenzen, Modelle, Zustände, Logs und Zusammenfassungen |

Ein JPG im Batch-Hauptordner ist aktiv. JPGs in `Review/` und `Rejected/` sind
nicht aktiv. In Phase 2 bleibt ein ARW nur erhalten, wenn ein aktives JPG mit
demselben Basisnamen im Hauptordner existiert.

## Konfiguration

1. Kopiere die Vorlage und passe sie an:

   ```sh
   cp .env.example .env
   cp config/config.documented.example.yaml config/config.yaml
   ```

2. Setze in `.env` `WORKFLOW_DATA_ROOT` auf einen **absoluten**, dedizierten
   NAS-Pfad sowie `PUID` und `PGID` auf die numerische DSM-Benutzerkennung.

3. Lasse zunächst `automation.mode: assistedreview`,
   `automation.automaticphase2enabled: false`, `familyrecognition.enabled: false`
   und `metadataculling.enabled: false`.

Die vollständige Erläuterung aller YAML-Optionen enthält
[`config.documented.example.yaml`](../config/config.documented.example.yaml).

## Docker bauen

Führe die Kommandos im Projektwurzelverzeichnis aus:

```sh
cp .env.example .env
cp config/config.documented.example.yaml config/config.yaml
# .env und config/config.yaml bewusst bearbeiten
docker compose build
docker compose run --rm --no-deps photo-workflow --help
./scripts/preflight.sh
```

`preflight.sh` validiert Compose, Konfiguration, Rechte und den Automatikstatus;
es verarbeitet keinen Foto-Batch. Der Container verwendet einen schreibgeschützten
Codebereich, ein temporäres `/tmp`, keine Linux-Capabilities, eine nur-lesbare
Konfiguration und ausschließlich den persistenten Daten-Mount mit Schreibrecht.

### Docker-Ablauf

```sh
./scripts/run-phase1.sh
# Batch in TEMPIMAGES prüfen; JPGs bei Bedarf zwischen Hauptordner, Review und Rejected bewegen
mv "$WORKFLOW_DATA_ROOT/TEMP/TEMPIMAGES/2026-01-01" "$WORKFLOW_DATA_ROOT/TEMP/TEMPDONE/"
./scripts/run-phase2.sh --dry-run
./scripts/run-phase2.sh
```

Prüfe vor dem ersten echten Phase-2-Lauf Testarchive mit `unzip -t` und die
Run-Summaries unter `runtime/runsummaries`. Details und DSM-Scheduler-Anleitung:
[`SYNOLOGY_DSM_DEPLOYMENT.md`](SYNOLOGY_DSM_DEPLOYMENT.md).

## Lokal ohne Docker

Diese Variante verwendet ausschließlich einen lokalen Python-Venv und einen
separaten Testdatenordner. Sie benötigt kein NAS und führt keine Docker-Container
aus.

```sh
python3.11 -m venv .venv
. .venv/bin/activate                 # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python -m compileall -q app
```

Die Tests erzeugen temporäre Daten und verändern weder `data/` noch ein NAS.
Sie prüfen den Kernfluss mit synthetischen JPGs und Dummy-ARWs, aber nicht echte
Kamera-RAW-Dateien, DSM-Rechte, Docker-Mounts oder ein reales ExifTool.

### Lokaler Dry-Run

Erzeuge eine von Git getrennte Sandbox und verwende absolute Pfade darin:

```sh
mkdir -p /tmp/photo-workflow-demo/TEMP/{TEMPSD,TEMPIMAGES,TEMPDONE,TEMPERROR}
mkdir -p /tmp/photo-workflow-demo/{runtime/{state,runsummaries,quarantine,calibration/batches},samples,models}
cp config/config.documented.example.yaml /tmp/photo-workflow-demo/config.yaml
# Ersetze in /tmp/photo-workflow-demo/config.yaml alle data/...-Pfade durch /tmp/photo-workflow-demo/...
python -m app.photoworkflow --config /tmp/photo-workflow-demo/config.yaml automation-status
python -m app.photoworkflow --config /tmp/photo-workflow-demo/config.yaml phase2 --dry-run
```

Für einen vollständigen lokalen Phase-1-Test lege einen **disponiblen** Ordner
`YYYYMMDD` mit mindestens einem JPG in `TEMPSD` an. Verwende niemals Originale.
Der `phase2 --dry-run` erzeugt keinen Archivplan, kein ZIP, keine Kalibrierungs-
artefakte und löscht keine ARWs.


## Modelle und lokale Bewertung

Der Standardworkflow braucht **keine heruntergeladenen KI-Modelle**: Ordnerfluss,
Sicherheitsprüfungen, Archivierung, RAW-Transaktion, lokale technische
Bildmerkmale und die manuelle Freigabe funktionieren ohne sie. Zusätzliche
Modelle erst nach einem Testlauf mit Kopien installieren; die optionale
Familienerkennung bleibt bis zur bewussten Abnahme deaktiviert.

### Verwendete Modelle

Für `familyrecognition.backend: opencvyunetsface` werden zwei vortrainierte
ONNX-Modelle der offiziellen OpenCV-Sammlung gemeinsam benötigt:

| Aufgabe | Datei | Offizieller Download | NAS-Ziel |
|---|---|---|---|
| Gesichter finden | `face_detection_yunet_2023mar.onnx` (YuNet) | [OpenCV: YuNet](https://huggingface.co/opencv/face_detection_yunet/tree/main) | `TEMP/WORKFLOW_DATA/models/face/face_detection_yunet.onnx` |
| Gesichter vergleichen | `face_recognition_sface_2021dec.onnx` (SFace) | [OpenCV: SFace](https://huggingface.co/opencv/face_recognition_sface/tree/main) | `TEMP/WORKFLOW_DATA/models/face/face_recognition_sface.onnx` |

YuNet liefert Position und fünf Orientierungspunkte eines Gesichts. SFace
richtet den gefundenen Ausschnitt daran aus, erzeugt einen Zahlenvektor und
vergleicht ihn mit Vektoren bekannter Personen; es entscheidet nicht allein über
ein Löschen. OpenCV dokumentiert diese Kombination als `FaceDetectorYN` und
`FaceRecognizerSF`; der Ähnlichkeitsschwellenwert muss mit eigenen Testbildern
konservativ abgenommen werden.

### Download und Einbindung

1. Lege zuerst den Zielordner an und lade nur die oben genannten Originaldateien
   über die offiziellen OpenCV-Links herunter:

   ```sh
   mkdir -p "$WORKFLOW_DATA_ROOT/TEMP/WORKFLOW_DATA/models/face"
   # Dateien im Browser herunterladen und anschließend eindeutig benennen:
   # face_detection_yunet_2023mar.onnx -> face_detection_yunet.onnx
   # face_recognition_sface_2021dec.onnx -> face_recognition_sface.onnx
   ```

2. Lege die Dateien in den angegebenen NAS-Zielordner. Verwende zunächst die
   normalen FP32-Dateien; die kleineren `int8`-Varianten nur nach einem eigenen
   Vergleichstest, denn sie können abweichende Ergebnisse liefern.

3. Prüfe die Pfade in `config/config.yaml` und aktiviere die Funktion erst nach
   einem Testlauf:

   ```yaml
   familyrecognition:
     enabled: false
     backend: opencvyunetsface
     detectormodel: data/TEMP/WORKFLOW_DATA/models/face/face_detection_yunet.onnx
     recognizermodel: data/TEMP/WORKFLOW_DATA/models/face/face_recognition_sface.onnx
     similaritymetric: cosine_similarity
     matchthreshold: null
   ```

4. Setze `enabled: true` erst nach erfolgreichem Preflight, einem Testbatch und
   einer dokumentierten Schwellenwertentscheidung. Der Container benötigt dafür
   ein passendes OpenCV-Backend; fehlt es, muss die Funktion deaktiviert bleiben.

### Lokale Modelle und Referenzen

Das optionale persönliche Geschmacksmodell ist **kein vortrainierter Download**.
Es entsteht aus bewusst bestätigten eigenen JPG-Referenzen: Lege geeignete Bilder
nach `TEMP/WORKFLOW_DATA/samples/reference/`, prüfe neue Vorschläge in
`.../samples/newrefs/` und belasse abgelehnte Vorschläge in `.../samples/notused/`.
Wenn `personalscoring.enabled` nach ausreichender, vielfältiger Referenzauswahl
aktiviert und der vorgesehene Trainings-/Aktualisierungslauf ausgeführt wird,
schreibt der Workflow sein kleines lokales Artefakt nach
`TEMP/WORKFLOW_DATA/models/taste/active.json`.

Dafür wird kein externes Modell benötigt, weil der Workflow aus lokalen,
erklärbaren Bildmerkmalen und deinen positiven Referenzen ein persönliches Profil
ableitet, statt ein allgemeines neuronales Modell nachzuladen. Wenige oder sehr
ähnliche Referenzen erzeugen keine verlässliche Präferenz: deshalb zunächst bei
deaktiviertem `personalscoring` bleiben, Referenzen manuell kuratieren und das
Ergebnis mit Testbatches kontrollieren.

Gesichtsreferenzen gehören nach `TEMP/WORKFLOW_DATA/faces/`. Sie sind besonders
sensible personenbezogene Daten: nur mit Einwilligung verwalten, NAS-Zugriff
beschränken, Sicherungen schützen und die Erkennung deaktiviert lassen, wenn sie
nicht benötigt wird.

### Nicht benötigte Downloads

Objektklassifikation, OCR, Segmentierung oder generative Modelle werden vom
aktuellen Projekt nicht verwendet. Nicht vorsorglich installieren: Sie erhöhen
Speicher-, Update- und Datenschutzaufwand und dürfen den manuellen
Freigabeprozess nicht verändern.

## Betriebsroutine

1. Vollständigen Kamera-Batch nach `TEMPSD` kopieren.
2. Phase 1 ausführen und Run-Summary prüfen.
3. In `TEMPIMAGES` sichten; aktive JPGs im Hauptordner lassen, andere nach
   `Review` oder `Rejected` verschieben.
4. Freigegebenen Batch manuell nach `TEMPDONE` verschieben.
5. Zuerst Phase 2 mit `--dry-run` prüfen, dann mit Testkopien produktiv ausführen.
6. Bei `paused`, `blocked`, `warning` oder `failed` Run-Summary und Batch-State
   prüfen; keine Zustandsdateien manuell löschen oder editieren.

## Fehlerbehebung

| Symptom | Sichere Reaktion |
|---|---|
| `LOCKACTIVE` | Anderen Lauf beenden oder auf dessen Abschluss warten; keine aktive Sperre löschen. |
| `BATCHUNSTABLE` | Kopiervorgang abschließen lassen und `stabilityseconds` passend setzen. |
| `ARCHIVEPLANMISMATCH` | Batch nicht verändern; Archive, State und Run-Summary prüfen. |
| `exiftoolmissing` | Metadatenfunktion deaktiviert lassen oder ExifTool im Container prüfen. |
| `backendunavailable` | Familienfunktion deaktiviert lassen; Backend separat auf dem NAS abnehmen. |

## Updates und Rückbau

Vor Updates Zustände, Manifeste, Logs, Referenzen und Modelle im persistenten
Datenordner sichern. Anschließend Image neu bauen, Preflight ausführen und mit
einem Testbatch prüfen. Für einen Rückbau zuerst Scheduler-Aufgaben deaktivieren;
vorhandene `runtime/state`-Dateien und Archive nicht löschen, um einen Lauf zu
"erzwingen".
