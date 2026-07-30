# Synology Photo Workflow — Vollständiges Betriebs-, Architektur- und Nutzungshandbuch

## Überblick

Der Synology Photo Workflow ist ein konservativ ausgelegter Zwei-Phasen-Workflow für Kamera- und Foto-Batches. Das Projekt verarbeitet Eingänge kontrolliert, trennt Bewertung und Sichtprüfung von späterer Archiv- und Bereinigungslogik und erzwingt damit eine klare Sicherheitsgrenze zwischen "bewerten" und "endgültig handeln". Es ist ausdrücklich kein blind automatisierender Foto-Sortierer, sondern ein Workflow-System mit Review-Punkt, reproduzierbaren Zuständen, testbarer Orchestrierung und einem persistenten NAS-Arbeitsbereich.

Das aktuelle Projekt nutzt eine Python-CLI für die fachliche Ausführung, kommentierte Shell-Skripte als Betriebswrapper, eine zentrale `config/config.yaml` als aktive Konfiguration und einen persistenten Datenbereich außerhalb des Container-Images. Die Shell-Skripte starten keine eigene Fachlogik und verschieben keine Bilder selbst. Alle sicherheitsrelevanten Entscheidungen bleiben in den Python-Modulen, damit diese testbar, konsistent und austauschbar bleiben.

Dieses Handbuch vereint die Inhalte der früheren Handbuchfassung mit der aktuellen Projektstruktur. Inhalte aus der älteren Fassung wurden übernommen, wenn sie noch zutreffen, und sonst auf die heutige Struktur, Namensgebung und Konfigurationsform angepasst.

## Leitprinzipien

- Der Workflow ist standardmäßig konservativ.
- Phase 1 und Phase 2 sind fachlich getrennt.
- Menschliche Freigabe bleibt der zentrale Kontrollpunkt.
- Riskante Aktionen benötigen valide States, Freigaben und Archivprüfung.
- Persistente Daten liegen außerhalb des Container-Images.
- Shell-Skripte sind nur Betriebshilfen, nicht der Ort für Geschäftslogik.
- Optionale Modellfunktionen bleiben deaktiviert, bis sie auf realen Testdaten sauber abgenommen wurden.

## Projektbestandteile

Die sichtbare Projektstruktur besteht aus zwei Hauptbereichen: dem Quellcodeprojekt und der persistenten NAS-Zielstruktur.

| Bereich | Rolle |
|---|---|
| `synology-photo-workflow/` | Quellcode, Tests, Dokumentation, Skripte, Konfiguration |
| `NAS_EXAMPLE/` | Beispiel einer persistenten NAS-Arbeitsstruktur für Eingänge, Freigaben, Logs, States, Modelle und Referenzen |

Das Repository ist damit absichtlich zweigeteilt: Alles, was fachliche Regeln beschreibt oder ausführt, liegt im Projektordner. Alles, was laufzeitabhängige Daten, Zustände, Batch-Ergebnisse, Referenzen, Modelle oder Archive enthält, gehört in den persistenten Datenbereich.

## Ordnerstruktur im Detail

### Quellcodeprojekt

| Pfad | Funktion |
|---|---|
| `app/` | Python-CLI und Fachmodule des Workflows |
| `config/` | Projektkonfiguration, aktuell mit aktiver `config.yaml` |
| `scripts/` | Bash-Wrapper für Vorprüfung, DSM-Betrieb und Start einzelner Workflowmodi |
| `tests/` | Testsuite für Verträge, Logik, Skripte und Projektkonsistenz |
| `docs/` | Handbuch, Architektur- und Testdokumentation |
| `legacy/` | Historische Referenzen oder Altartefakte, nicht parallel zum aktuellen Workflow verwenden |

### Persistenter Datenbereich

Die tatsächliche operative Struktur wird über `paths.basedir` und die Unterpfade in `config/config.yaml` definiert.

| Pfad | Funktion |
|---|---|
| `TEMP_SD/` | Eingang für neue Kamera- oder Geräte-Batches |
| `TEMP_IMAGES/` | Ergebnisbereich aus Phase 1, zur menschlichen Sichtung |
| `TEMP_DONE/` | Ausschließlich manuell freigegebene Batches für Phase 2 |
| `TEMP_ERROR/` | Quarantäne- oder Fehlerbereich für unsichere, inkonsistente oder blockierte Batches |
| `WORKFLOW_DATA/` | Persistente technische Daten wie States, Logs, Summaries, Archive, Referenzen, Modelle und Kalibrierung |
| `MANUAL_KEEP/inbox/` | Eingang für manuell geschützte Keep-Dateien oder Hilfszuordnungen |
| `MANUAL_KEEP/used/` | Bereits verwendete und nicht erneut unverändert zu nutzende Manual-Keep-Dateien |

### Bedeutung der Ordnerrollen

`TEMP_SD` ist kein Archiv und kein allgemeiner Ablageort. Hier liegen ausschließlich neue, noch unverarbeitete Eingangsbatches. `TEMP_IMAGES` ist noch keine produktive Freigabezone, sondern eine Review-Zone. `TEMP_DONE` ist die Sicherheitsgrenze: Erst hier darf ein Batch fachlich in Phase 2 betrachtet werden. `TEMP_ERROR` ist kein "Mülleimer", sondern ein kontrollierter Bereich für blockierte oder unklare Situationen.

`WORKFLOW_DATA` ist das technische Gedächtnis des Projekts. Dort entstehen Laufzeitdaten, States, Summaries, Kalibrierungsergebnisse, Archiv-Manifeste, Caches, Referenzen und gegebenenfalls lokale Modellartefakte. Dieser Bereich muss persistent, nachvollziehbar und außerhalb des Container-Images liegen.

## Kamera-Batches und Ordnernamen

Die ältere Handbuchfassung verwies auf Kamera-Batches mit Datumsordnern wie `YYYYMMDD`. Dieses Konzept bleibt fachlich sinnvoll und weiterhin plausibel: Ein Batch sollte als klar abgegrenzter Ordner bereitgestellt werden, idealerweise mit einem stabilen, nachvollziehbaren Namen. Die frühere Beschreibung `YYYYMMDD` ist weiterhin als empfohlene Konvention brauchbar, weil sie Sortierbarkeit und manuelle Nachvollziehbarkeit verbessert.

Ein Batch darf nicht während der Verarbeitung weiter verändert werden. Insbesondere dürfen Kopiervorgänge nicht parallel zum Workflow abgeschlossen werden. Ein unvollständiger oder wachsender Eingang muss blockiert oder übersprungen werden. Dadurch verhindert das Projekt halb verarbeitete Inventare und unvollständige Paarbindungen.

## Aktive, Review- und Rejected-JPGs

Die ältere Fassung erklärte eine wichtige Regel, die weiterhin sinnvoll und im aktuellen Sicherheitsmodell enthalten ist: Ein aktives JPG liegt im Batch-Hauptordner. JPGs in `Review/` und `Rejected/` gelten nicht als aktiv. Für Phase 2 ist diese Unterscheidung zentral, weil der Workflow nur dann ein ARW als geschützt betrachten darf, wenn ein dazu passendes aktives JPG im Hauptordner existiert.

Das bedeutet praktisch:

- JPG im Hauptordner: aktiv, schützt das zugehörige ARW.
- JPG in `Review/`: nicht aktiv, schützt das ARW nicht final.
- JPG in `Rejected/`: nicht aktiv, schützt das ARW nicht final.

Diese Regel ist für die Logik plausibel, weil sie den menschlichen Auswahlzustand direkt über die Batch-Struktur ausdrückt und keine zusätzliche unsichtbare Statusquelle benötigt.

## Zwei-Phasen-Modell

Der Projektkern ist die Trennung in Phase 1 und Phase 2.

| Phase | Ziel | Typische Eingaben | Typische Ergebnisse | Risikoebene |
|---|---|---|---|---|
| Phase 1 | Inventarisieren, bewerten, Review vorbereiten | Neue Batches in `TEMP_SD` | Bewertete Batch-Artefakte, Review-Ausgabe in `TEMP_IMAGES`, Zustände und Summaries | Niedriger, weil keine ARW-Bereinigung erfolgt |
| Phase 2 | Freigegebene Batches sicher archivieren und bereinigen | Manuell freigegebene Batches in `TEMP_DONE` | Archivplan, verifiziertes Archiv, protokollierte Bereinigung, aktualisierte States und Run-Summaries | Hoch, deshalb nur mit Gates, Archivprüfung und validem State |

### Phase 1 im Detail

Phase 1 verarbeitet neue Eingangsbatches, prüft Stabilität, inventarisiert Dateien, bildet zulässige JPG-/ARW-Paare und erzeugt die Bewertungs- und Review-Artefakte. Sie darf keine finale Bereinigung auslösen. Ihr Ergebnis ist eine vorbereitete Sichtprüfung und ein reproduzierbarer technischer Status.

Dazu gehören typischerweise:

- Eingangsstabilität prüfen.
- Pfade und Dateitypen prüfen.
- JPG-/ARW-Paare anhand des vollständigen Basisnamens bilden.
- Bewertungsmerkmale und Scores berechnen.
- Review-Struktur aufbauen.
- Batch-Zustand dokumentieren.
- Laufzusammenfassung schreiben.

### Phase 2 im Detail

Phase 2 akzeptiert ausschließlich freigegebene und fachlich konsistente Batches. Vor jeder Bereinigung muss ein unveränderlicher Archivplan erzeugt werden. Das daraus entstehende Archiv wird lesend geprüft und gegen erwartete Inhalte, Pfade und Hashes validiert. Erst dann darf eine Bereinigung der nicht mehr benötigten ARWs erfolgen.

Die Grundlogik lautet:

1. Gültigen Batch-State finden.
2. Freigabe- und Integritätsbedingungen prüfen.
3. Archivplan erzeugen.
4. Archiv schreiben.
5. Archiv vollständig validieren.
6. Erst danach berechtigte ARWs bereinigen.
7. Ergebnisse und Zeiten protokollieren.

## Freigabelogik und manueller Eingriff

Das Projekt ist ausdrücklich nicht so gebaut, dass ein Modell oder Score alleine über endgültige Dateibereinigung entscheidet. Der Standardmodus ist `assisted_review`. Das bedeutet: Phase 1 liefert Vorschläge, die Sichtprüfung erfolgt manuell, und die fachliche Freigabe wird bewusst vollzogen.

Manuell eingegriffen werden muss mindestens in folgenden Situationen:

- Sichtprüfung der Phase-1-Ergebnisse.
- Entscheidung, welche JPGs aktiv im Hauptordner bleiben.
- Gegebenenfalls Verschiebung anderer JPGs nach `Review/` oder `Rejected/`.
- Übergabe eines freigegebenen Batches nach `TEMP_DONE`.
- Prüfung neuer Modell- oder Referenzvorschläge.
- Entscheidung über Aktivierung optionaler Face- oder Automatikfunktionen.

## Konfiguration

### Grundprinzip

Das aktuelle Projekt verwendet eine zentrale `config/config.yaml`. Diese Datei ist aktiv, kommentiert und versioniert. Sie ist bewusst zur zentralen Hauptkonfiguration gemacht worden. Deshalb muss sie secrets-frei bleiben. Für installationsspezifische Varianten sollte eine lokale Kopie erzeugt und über einen alternativen Pfad verwendet werden.

### Relevante Konfigurationsblöcke

| Block | Funktion |
|---|---|
| `paths` | Definiert den persistenten Arbeitsbereich und seine Unterpfade |
| `workflow` | Steuert Reihenfolge, Batch-Limits, Laufzeit und Wiederaufnahme |
| `culling` | Gewichte, Schwellwerte, Sterne und Bewertungskomponenten |
| `phase2` | Regeln für Archivierung und ARW-Bereinigung |
| `metadata` | Schaltstellen für Metadaten-Änderung und Rückprüfung |
| `family_recognition` | Optionales Face-Backend, Profil, Metrik und Schwellen |
| `automation` | Erlaubter Automatisierungsgrad |
| `calibration` | Mindestmengen und Qualitätsgrenzen für Readiness und Kalibrierung |

### Empfohlener Startzustand

Für einen sicheren Projektstart sollten folgende Leitlinien eingehalten werden:

- `automation.mode: assisted_review`
- `automation.automatic_phase2_enabled: false`
- `automation.automatic_reference_activation: false`
- `automation.automatic_sample_activation: false`
- `family_recognition.enabled: false`
- `metadata.write_mode: disabled`

Damit bleibt das System zunächst beobachtbar und kontrollierbar, ohne vorzeitig tiefer in Metadaten, Referenzlogik oder Personenmatching einzugreifen.


## Docker, lokale Ausführung und Modelle

### Konfiguration

1. Kopiere die Vorlage und passe sie an:

   ```sh
   cp .env.example .env
   cp config/config.yaml config/config.local.yaml
   ```

2. Setze in `.env` `WORKFLOW_DATA_ROOT` auf einen **absoluten**, dedizierten
   NAS-Pfad sowie `PUID` und `PGID` auf die numerische DSM-Benutzerkennung.

3. Lasse zunächst `automation.mode: assisted_review`,
   `automation.automatic_phase2_enabled: false`,
   `family_recognition.enabled: false`
   und `metadata.write_mode: disabled`.

Die vollständige Erläuterung aller YAML-Optionen enthält
[`config/config.yaml`](../config/config.yaml).

### Docker bauen

Führe die Kommandos im Projektwurzelverzeichnis aus:

```sh
cp .env.example .env
cp config/config.yaml config/config.local.yaml
# .env und config/config.local.yaml bewusst bearbeiten
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
# Batch in TEMP_IMAGES prüfen; JPGs bei Bedarf zwischen Hauptordner, Review und Rejected bewegen
mv "$WORKFLOW_DATA_ROOT/TEMP/TEMP_IMAGES/2026-01-01" "$WORKFLOW_DATA_ROOT/TEMP/TEMP_DONE/"
./scripts/run-phase2.sh --dry-run
./scripts/run-phase2.sh
```

Prüfe vor dem ersten echten Phase-2-Lauf Testarchive mit `unzip -t` und die
Run-Summaries unter `WORKFLOW_DATA_ROOT/runtime/runsummaries`.

### Lokal ohne Docker

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
mkdir -p /tmp/photo-workflow-demo/TEMP/{TEMP_SD,TEMP_IMAGES,TEMP_DONE,TEMP_ERROR}
mkdir -p /tmp/photo-workflow-demo/{runtime/{state,runsummaries,quarantine,calibration/batches},samples,models}
cp config/config.yaml /tmp/photo-workflow-demo/config.yaml
# Ersetze in /tmp/photo-workflow-demo/config.yaml alle data/...-Pfade durch /tmp/photo-workflow-demo/...
python -m app.photoworkflow --config /tmp/photo-workflow-demo/config.yaml automation-status
python -m app.photoworkflow --config /tmp/photo-workflow-demo/config.yaml phase2 --dry-run
```

Für einen vollständigen lokalen Phase-1-Test lege einen **disponiblen** Ordner
`YYYYMMDD` mit mindestens einem JPG in `TEMP_SD` an. Verwende niemals Originale.
Der `phase2 --dry-run` erzeugt keinen Archivplan, kein ZIP, keine Kalibrierungs-
artefakte und löscht keine ARWs.

### Modelle und lokale Bewertung

Der Standardworkflow braucht **keine heruntergeladenen KI-Modelle**: Ordnerfluss,
Sicherheitsprüfungen, Archivierung, RAW-Transaktion, lokale technische
Bildmerkmale und die manuelle Freigabe funktionieren ohne sie. Zusätzliche
Modelle erst nach einem Testlauf mit Kopien installieren; die optionale
Familienerkennung bleibt bis zur bewussten Abnahme deaktiviert.

### Verwendete Modelle

Für `family_recognition.backend: opencvyunetsface` werden zwei vortrainierte
ONNX-Modelle der offiziellen OpenCV-Sammlung gemeinsam benötigt:

| Aufgabe | Datei | Offizieller Download | NAS-Ziel |
|---|---|---|---|
| Gesichter finden | `face_detection_yunet_2023mar.onnx` (YuNet) | [OpenCV: YuNet](https://huggingface.co/opencv/face_detection_yunet/tree/main) | `WORKFLOW_DATA/models/face/face_detection_yunet.onnx` |
| Gesichter vergleichen | `face_recognition_sface_2021dec.onnx` (SFace) | [OpenCV: SFace](https://huggingface.co/opencv/face_recognition_sface/tree/main) | `WORKFLOW_DATA/models/face/face_recognition_sface.onnx` |

YuNet liefert Position und fünf Orientierungspunkte eines Gesichts. SFace
richtet den gefundenen Ausschnitt daran aus, erzeugt einen Zahlenvektor und
vergleicht ihn mit Vektoren bekannter Personen; es entscheidet nicht allein über
ein Löschen. OpenCV dokumentiert diese Kombination als `FaceDetectorYN` und
`FaceRecognizerSF`; der Ähnlichkeitsschwellenwert muss mit eigenen Testbildern
konservativ abgenommen werden.

### Download und Einbindung

1. Lege zuerst den Zielordner an und lade nur die oben genannten Originaldateien
   über die offiziellen OpenCV-Links herunter.

2. Lege die Dateien in den angegebenen NAS-Zielordner. Verwende zunächst die
   normalen FP32-Dateien; die kleineren `int8`-Varianten nur nach einem eigenen
   Vergleichstest, denn sie können abweichende Ergebnisse liefern.

3. Prüfe die Pfade in `config/config.yaml` und aktiviere die Funktion erst nach
   einem Testlauf.

4. Setze `family_recognition.enabled: true` erst nach erfolgreichem Preflight,
   einem Testbatch und einer dokumentierten Schwellenwertentscheidung.

### Modelle tauschen

Ein Modellwechsel ist nur sinnvoll, wenn Backend, Profil und Laufzeit dazu passen.
Wechsle zuerst die Modelldateien, dann die Konfiguration, dann die Diagnose.
Alte Caches dürfen bei geändertem Fingerprint nicht blind weiterverwendet werden.

### Persönliche Referenzen

Das optionale persönliche Geschmacksmodell ist kein vortrainierter Download.
Es entsteht aus bewusst bestätigten eigenen JPG-Referenzen: Lege geeignete Bilder
nach `WORKFLOW_DATA/samples/reference/`, prüfe neue Vorschläge in
`.../samples/newrefs/` und belasse abgelehnte Vorschläge in `.../samples/notused/`.

### Wann manuell eingegriffen werden muss

Manuelle Prüfung ist nötig, wenn neue Modellvorschläge bewertet, Schwellen angepasst,
Face-Funktionen aktiviert oder Batches nach `TEMP_DONE` überführt werden sollen.
Die Automatik darf diese Entscheidungen nicht eigenmächtig ersetzen.

## Skripte und ihre Aufgaben

Die Bash-Skripte sind bewusst schmal gehalten. Sie prüfen die Betriebsumgebung und rufen anschließend die Python-CLI mit dem passenden Befehl auf.

| Skript | Rolle | Seiteneffekt |
|---|---|---|
| `scripts/preflight.sh` | Allgemeine Vorprüfung von Pfaden, Docker und Konfiguration | Keine Bildverarbeitung |
| `scripts/dsm-acceptance-preflight.sh` | DSM-/Scheduler-orientierte Betriebsprüfung | Keine Bildverarbeitung |
| `scripts/run-phase1.sh` | Führt ausschließlich Phase 1 aus | Batch-Artefakte aus Phase 1 möglich |
| `scripts/run-phase2.sh` | Führt ausschließlich Phase 2 aus | Archivierung und ggf. Bereinigung möglich |
| `scripts/run-workflow.sh` | Startet den kanonischen Gesamtbefehl `run` | Abhängig von Konfiguration und Gates |

### Warum die Skripte keine Fachlogik enthalten

Diese Designentscheidung ist zentral für Wartbarkeit und Harmonisierung. Wenn Freigabelogik, Archivbedingungen, Dateimutation oder Matching-Regeln in Shell-Skripten dupliziert würden, entstünden mehrere Wahrheiten im Projekt. Das aktuelle Modell vermeidet das: Shell übernimmt Betrieb, Python übernimmt Regeln.

## Python-Schichten und Modularisierung

Das Projekt ist in fachlich getrennte Module aufgeteilt. Die genaue interne Modulbelegung kann wachsen oder sich feiner gliedern, aber die dokumentierte Schichtung bleibt projektlogisch konsistent.

| Schicht/Modul | Funktion | Typische Änderungsstelle |
|---|---|---|
| `app.cli` | Argumente, Konfigurationspfad, Befehlsdispatch, Exit-Codes | Neue Befehle oder veränderte CLI-Oberfläche |
| `app.configuration` | Laden, Validieren, Normalisieren und Fingerprinting der Konfiguration | Neue Konfigurationswerte, neue Validierungsregeln |
| `app.inventory` | Eingangsprüfung, Paarbildung, Dateiinventar | Neue Dateiregeln oder zusätzliche Inventarprüfungen |
| `app.phases` | Orchestrierung und Reihenfolge von Phase 1 und Phase 2 | Neue Ablaufformen, Recovery-Reihenfolgen |
| `app.culling` | Merkmale, Scores, Sterne, Bewertungslogik | Neue Bewertungsmerkmale, neue Gewichtung oder neue Score-Komponenten |
| `app.metadata` | Metadaten schreiben, prüfen, zusammenführen | Metadatenstrategie oder neue Zielschlüssel |
| `app.archives` | Archivplan, ZIP, Kollision, Validierung, Aktivierung | Neues Archivverhalten oder zusätzliche Prüfungen |
| `app.batchstate` | Zustandsautomat, Übergänge, Persistenz | Neue Zustandsübergänge oder robustere Wiederaufnahme |
| `app.locks` | Sperrlogik für parallele Läufe | Lock-Verbesserungen oder Host-/PID-Prüfungen |
| `app.calibration` | Review-Records, Auswertung, Readiness, Berichte | Neue Kennzahlen oder geänderte Mindestgrenzen |
| `app.facebackend` | Backend-Protokoll und Registry | Neues Face-Backend oder neues Laufzeitprofil |
| `app.familyrecognition` | Referenzen, Cache, Matchlogik, Kandidaten | Andere Referenzstrategie oder Matchlogik |
| `app.reporting` | Logs, Scheduler-Ausgabe, Run-Summaries | Zusätzliche Berichtsfelder |

Diese Aufteilung ist der wichtigste Hebel für Änderungen. Wer ein neues Face-Modell einführen will, sollte es nicht in `app.culling` oder Shell-Skripten verstecken, sondern in der Backend- und Match-Schicht anschließen. Wer die Archivlogik ändern will, tut das in `app.archives` und nicht in Phase-Wrappern.

## Datenquellen und Auswirkungen der Kernfunktionen

### Inventarisierung

**Quelle:** Dateien in `TEMP_SD`.

**Nutzt:** Dateinamen, Endungen, Pfade, Stabilität, Basename-Beziehungen.

**Wirkt auf:** Zulässige Paarbildung, Batch-Manifeste, Blockierung unsicherer Eingänge und Grundlage für alle weiteren Schritte.

### Culling und Bewertung

**Quelle:** Bilddaten der aktiven Dateien sowie Werte aus `config.culling`.

**Nutzt:** Technische Merkmale, Gewichtungen, Schwellwerte und Sternbänder.

**Wirkt auf:** Vorschlagsbewertung, Sterne, Review-Sichtung und Phase-1-Ausgabe.

### Manuelle Keep-Logik

**Quelle:** `MANUAL_KEEP/inbox`, `MANUAL_KEEP/used`, manuelle Entscheidungen.

**Nutzt:** Vom Menschen markierte oder kontrolliert zugeordnete Dateien.

**Wirkt auf:** Schutzentscheidungen, Nachvollziehbarkeit und Vermeidung doppelter manueller Nutzung.

### Metadaten

**Quelle:** Batch-Ergebnisse, erlaubter Modus aus `config.metadata`, gegebenenfalls Exiftool.

**Nutzt:** Bewertungsentscheidungen und definierte Zielschlüssel.

**Wirkt auf:** Bildmetadaten, aber nur wenn der Schreibmodus aktiv ist.

### Archivierung

**Quelle:** Freigegebene Batch-Zustände aus Phase 2.

**Nutzt:** Archivplan, erwartete Inhalte, Pfade, Hashes, Kollisionserkennung.

**Wirkt auf:** Persistente ZIP-Artefakte und deren Validierungsstatus.

### Bereinigung

**Quelle:** Verifiziertes Archivmanifest und zulässiger Batch-State.

**Nutzt:** Welche ARWs exakt im Archiv abgesichert sind.

**Wirkt auf:** Kontrollierte ARW-Entfernung. Ohne valide Quelle darf nichts gelöscht werden.

### Face-Erkennung und Familienfunktion

**Quelle:** Referenzen, Caches und Modellartefakte in `WORKFLOW_DATA`, Konfiguration in `family_recognition`.

**Nutzt:** Backend-ID, Profil, Metrik, Schwelle und Referenzbilder.

**Wirkt auf:** Match-Ergebnisse, Familien-Score und mögliche Personenzuordnung. Ist die Funktion deaktiviert, entstehen keine Face-Artefakte.

### Kalibrierung

**Quelle:** Bestätigte Review-Ergebnisse und Batch-Records.

**Nutzt:** Mindestmengen, Fehlerraten und Übereinstimmungsgrenzen aus `config.calibration`.

**Wirkt auf:** Berichte, Indizes und Empfehlungen. Nicht auf automatische Freigaben ohne ausdrückliche Konfiguration.

## Modelle: Welche relevant sind und wie sie eingebunden werden

Wichtig ist die Trennung zwischen **zwingend benötigten** und **optional möglichen** Modellen.

### Was der Standardworkflow ohne zusätzliche Modelle kann

Der Standardworkflow benötigt keine extern heruntergeladenen KI-Modelle, um seine Kernfunktion zu erfüllen. Inventarisierung, Paarbildung, Culling-Grundlogik, Review-Ablauf, Archivierung, Recovery und Zustandsführung funktionieren auch ohne aktivierte Face-Erkennung.

### Optionale Face-Modelle

Die ältere Handbuchfassung nannte als plausiblen Modellpfad eine OpenCV-Kombination aus YuNet für Erkennung und SFace für Wiedererkennung. Diese Beschreibung bleibt als Projektoption weiterhin stimmig, **sofern** das implementierte Backend und die Registry diese Modellart tatsächlich als konfigurierbares Backend unterstützen. Weil das aktuelle Projekt `family_recognition.backend` und ein backend-basiertes Face-System kennt, ist die allgemeine Beschreibung weiterhin passend: Ein Face-Backend kann eigene Modelldateien benötigen, die im persistenten Datenbereich liegen und von dort geladen werden.

Im aktuellen Projekt gelten für Modellwechsel daher folgende belastbare Aussagen:

- Modelle gehören nicht in den Codeordner, sondern in `WORKFLOW_DATA`.
- Die Wahl des Modells erfolgt über das konfigurierte Backend oder dessen Zusatzparameter.
- Aktivierung erfordert eine erfolgreiche Diagnose des Backends.
- Ein Modellwechsel kann Fingerprints, Caches, Schwellen und Match-Verhalten beeinflussen.
- Bei anderem Backend oder Modellfingerprint dürfen alte Caches nicht blind weiterverwendet werden.

### Wie Modelle gewechselt werden

1. Das gewünschte Backend identifizieren.
2. Prüfen, ob das Projekt dafür bereits eine registrierte Backend-ID besitzt.
3. Erforderliche Dateien im persistenten Modellbereich ablegen.
4. Die Konfiguration im Block `family_recognition` anpassen.
5. `validate_config` und die Backend-Diagnose erfolgreich ausführen.
6. Nur mit Testdaten starten.
7. Caches oder Referenzartefakte bei geändertem Fingerprint kontrolliert neu erzeugen.

### Welche Modelle in Betracht kommen

Das Projekt beschreibt aktuell ein backendbasiertes Face-System. Daraus folgt logisch: In Betracht kommen nur Modelle, die zu einem tatsächlich im Projekt vorgesehenen Backend passen. Allgemein denkbar sind CPU- und GPU-Profile oder ONNX-basierte Face-Backends, sofern diese im Projekt registriert sind. Dieses Handbuch nennt bewusst keine fiktiven Backends, die im aktuellen Projekt nicht vorhanden sein müssen. Der sichere Grundsatz lautet: Nur das verwenden, was die Registry, Diagnose und Konfiguration des aktuellen Projekts tatsächlich unterstützen.

### Wie das Projekt "KI anlernt"

Das Projekt trainiert im Standardbetrieb kein großes allgemeines neuronales Modell nach. Was im Projekt lernähnlich ist, betrifft vor allem zwei Bereiche:

1. **Kalibrierung aus bestätigten Review-Ergebnissen** – das System beobachtet bestätigte Entscheidungen und kann daraus Kennzahlen, Trends und Empfehlungen ableiten.
2. **Optionale lokale Referenz- und Samplelogik** – persönliche oder familienbezogene Referenzen können lokale Cache- oder Modellartefakte beeinflussen, wenn die Funktion aktiviert und fachlich abgenommen ist.

Damit gilt: Das Projekt "lernt" nicht autonom alles selbst, sondern nutzt kontrollierte, bestätigte Datenquellen. Manuell eingegriffen werden muss immer dann, wenn Referenzen erweitert, Modelle getauscht, neue Schwellen festgelegt oder automatische Vorschlagsfunktionen freigegeben werden sollen.

## Inbetriebnahme Schritt für Schritt

### Variante 1: Betrieb mit Docker und NAS

1. Projektordner und persistenten Datenbereich sauber trennen.
2. `paths.basedir` in `config/config.yaml` auf den echten NAS-Arbeitsbereich anpassen.
3. Docker Compose und Rechte des DSM-/Scheduler-Benutzers prüfen.
4. `./scripts/dsm-acceptance-preflight.sh` ausführen.
5. Danach `./scripts/preflight.sh` ausführen.
6. Mit einem Testbatch in `TEMP_SD` starten.
7. `./scripts/run-phase1.sh` ausführen.
8. Ergebnisse in `TEMP_IMAGES` prüfen.
9. Erst danach freigegebenen Batch nach `TEMP_DONE` überführen.
10. `./scripts/run-phase2.sh --dry-run` verwenden, sofern der CLI-Befehl dies unterstützt.
11. Erst nach erfolgreicher Prüfung echten Phase-2-Lauf starten.

### Variante 2: Lokaler Test ohne NAS-Produktion

1. Virtuelle Umgebung oder lokale Python-Umgebung vorbereiten.
2. Tests ausführen.
3. Einen separaten, disponiblen Testdatenpfad verwenden.
4. Keine Originaldateien verwenden.
5. Phase-1-Läufe auf Kopien prüfen.
6. Erst nach erfolgreichem Verhalten eine NAS-Umgebung vorbereiten.

## Beispiel-Betriebsroutine

| Schritt | Aktion | Ziel |
|---|---|---|
| 1 | Batch nach `TEMP_SD` kopieren | Eingang bereitstellen |
| 2 | `run-phase1.sh` ausführen | Inventar und Review-Artefakte erzeugen |
| 3 | Batch in `TEMP_IMAGES` prüfen | Menschliche Qualitätsentscheidung |
| 4 | Aktive JPGs im Hauptordner belassen, andere umsortieren | Schutzlogik für ARWs festlegen |
| 5 | Freigegebenen Batch nach `TEMP_DONE` verschieben | Kontrollierte Übergabe an Phase 2 |
| 6 | Optionaler Dry-Run für Phase 2 | Risiko vor echter Bereinigung reduzieren |
| 7 | `run-phase2.sh` ausführen | Archivierung und kontrollierte Bereinigung |
| 8 | Run-Summary und Archiv prüfen | Nachvollziehbarkeit und Abnahme |

## Recovery, Plausibilität und typische Fehlerbilder

Das Projekt ist auf kontrollierte Wiederaufnahme ausgelegt. Ein Abbruch bedeutet nicht automatisch Datenverlust. Entscheidend ist, dass keine Zustands- oder Archivdateien manuell gelöscht oder improvisiert editiert werden.

| Symptom | Bedeutung | Sichere Reaktion |
|---|---|---|
| Aktiver Lock | Ein anderer Lauf hält den Batch oder den Workflow | Auf Abschluss warten oder Prozess sauber beenden |
| Instabiler Batch | Eingang wurde noch kopiert oder verändert sich | Kopiervorgang abschließen lassen |
| Archivkollision | Zielname bereits vorhanden oder nicht vertrauenswürdig | Kollisionsfall prüfen, nicht überschreiben |
| Backend nicht verfügbar | Face-Funktion passt nicht zu Runtime oder Modellen | Face deaktiviert lassen und Diagnose prüfen |
| Ungültige Konfiguration | Pfade, Werte oder Abhängigkeiten stimmen nicht | `validate_config` und Kommentare der `config.yaml` prüfen |

## Konsistenzgrenzen des Dokuments

Dieses Handbuch beschreibt nur Funktionen, die zum aktuellen Projekt passen oder sich logisch belastbar aus dessen dokumentierter Struktur ableiten lassen. Aussagen aus der älteren Handbuchfassung wurden nur dort übernommen, wo sie mit der aktuellen Struktur konsistent sind. Wo alte Namen oder alte Konfigurationsdateien nicht mehr zum Projekt passen, wurden sie bewusst aktualisiert.

Dazu gehören insbesondere diese Aktualisierungen:

- Zentrale aktive Konfiguration ist jetzt `config/config.yaml`.
- Die Shell-Skripte besitzen dokumentierte Header und Betriebskommentare.
- `run-workflow.sh` ist der kanonische Wrapper für den Gesamtstart.
- Dokumentation und Ordnerrollen wurden an die heutige Projektstruktur angepasst.

## Empfehlungen für Erweiterungen

Sinnvolle Erweiterungen des Projekts sollten weiter entlang der vorhandenen Modularisierung erfolgen:

- Neue Bewertungsmerkmale in `app.culling`.
- Neue Archivvalidierungen in `app.archives`.
- Neue Face-Backends in `app.facebackend` und zugehöriger Matchlogik.
- Neue Auswertungen in `app.calibration` oder `app.reporting`.
- Neue CLI-Befehle in `app.cli`, ohne Fachlogik in Shell zu verschieben.

Nicht sinnvoll wäre:

- Fachlogik in Bash nachbauen.
- Modelle in den Codeordner legen.
- Freigabelogik durch direkte Dateilöschung zu umgehen.
- Caches nach Modellwechsel ungeprüft weiterzuverwenden.
- Produktive Originale für erste Phase-2-Tests zu verwenden.

## Abschlussorientierte Checkliste für Betreiber

- Ist `paths.basedir` ein echter persistenter Pfad?
- Sind Docker und Rechte geprüft?
- Läuft `preflight.sh` erfolgreich?
- Ist Face-Erkennung deaktiviert, solange keine Abnahme erfolgt ist?
- Wird `assisted_review` verwendet?
- Werden Batches sauber in `TEMP_SD` bereitgestellt?
- Wird `TEMP_DONE` nur manuell und bewusst befüllt?
- Wurden Phase-2-Läufe zuerst mit Testdaten geprüft?
- Werden Run-Summaries, States und Archive nicht manuell manipuliert?
- Ist die Backup-Strategie unabhängig vom Workflow vorhanden?
