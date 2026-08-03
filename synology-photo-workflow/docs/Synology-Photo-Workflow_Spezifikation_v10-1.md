<!--
Synology Photo Workflow – Spezifikation v10.1
Datei: docs/Synology-Photo-Workflow_Spezifikation_v10-1.md
Mitentwickler: MaiTaiMa (in Zusammenarbeit mit Perplexity AI)
Erstellt: 2026-08-04
Projektversion: 10.1
Status: Vollstaendige, bereinigte und konsolidierte Fassung
-->

# Synology Photo Workflow – Spezifikation v10.1

**Status:** Verbindliche, alleinstehende Spezifikation fuer den sicheren, wiederaufnehmbaren Synology Photo Workflow (vollstaendig bereinigte und konsolidierte Fassung).

**Zielsetzung:** Dieses Dokument ist die alleinige normative Quelle fuer Entwicklung, Betrieb, Test und Aenderungen. Es enthaelt alle Informationen aus der vorherigen harmonisierten Fassung, erweitert um die Referenzpool-Verwaltung, Face-Crops, dynamisches Ranking und vollstaendige Anhaenge.

---

## 0. Metadaten und Geltungsbereich

### 0.1 Dokumentenmetadaten

| Feld | Wert |
|------|------|
| Version | 10.1 |
| Datum | 2026-08-04 |
| Status | Vollstaendig bereinigt und konsolidiert |
| Vorgaenger | 10.0 |
| Aenderungs-Historie | Siehe Kapitel 6.4 und Anhang T |

### 0.2 Geltungsbereich und Zielsetzung

Diese Spezifikation definiert den kleinen, produktiv sinnvollen Kern des Synology Photo Workflow. Die Implementierung soll eine vorhandene Codebasis gezielt pruefen und nur die hier beschriebenen Funktionen ergaenzen oder reparieren. Sie soll nicht zu einer grossen allgemeinen Foto- oder Gesichtsdatenplattform ausgebaut werden.

Der Workflow verfolgt drei gleichrangige Ziele:

1. Originaldaten vor Verlust schuetzen.
2. Den wiederkehrenden manuellen Aufwand klein halten.
3. Die Qualitaet der Entscheidungen ueber nachvollziehbare Lernbeispiele verbessern.

Bei Zielkonflikten gilt die Abwaegungslogik aus 0.3.

### 0.3 Lesart und Vorrang

#### 0.3.1 Normative Schluesselwoerter

Die Schluesselwoerter **MUSS**, **DARF NICHT**, **SOLL** und **KANN** sind normativ.

- **MUSS** kennzeichnet eine zwingende Anforderung.
- **DARF NICHT** kennzeichnet ein ausdrueckliches Verbot.
- **SOLL** kennzeichnet eine empfohlene Praxis.
- **KANN** kennzeichnet eine optionale Moeglichkeit.

#### 0.3.2 Abwaegungslogik

Bei Zielkonflikten gilt **zuerst** und **vorrangig vor allen anderen Regeln** folgende Abwaegungslogik:

1. **Sicherheit:** Keine unkontrollierten Datei aenderungen, Datenverluste, Modell-Downloads oder Daten uebertragungen. Bilddaten, Crops, Embeddings und Referenzbilder verlassen nie die erlaubten NAS-Datenbereiche.
2. **Stabilitaet:** Ein einzelnes fehlerhaftes Foto, ein Modellfehler oder ein defekter Ordner stoppt nicht den ueblichen Lauf.
3. **Nutzen:** Jede Funktion muss Fotos besser vorsortieren, Nachvollziehbarkeit oder Betriebssicherheit erhoehen.
4. **Einfachheit:** Wenige verstaendliche Optionen; keine technische Doppelstruktur ohne nachgewiesenen Nutzen.
5. **NAS-Performance:** Ein langsamer, begrenzter und ueber mehrere Tage fortsetzbarer Betrieb ist akzeptabel.

**Richtwert NAS-Performance:** Auf einer typischen NAS (z. B. 2–4 Kerne, 4–8 GB RAM) sind ca. 500–1000 Bilder pro Tag realistisch. Bei groesseren Batches ist der Betrieb ueber mehrere Tage fortsetzbar.

Diese Reihenfolge ist **verbindlich** und darf durch keine andere Regel, keine Konfiguration und keine Implementierungsentscheidung ueberstimmt werden. Sie gilt projektweit, fuer Fachlogik, Architektur, Konfiguration, Betrieb und Tests.

#### 0.3.3 Sekundaere Vorranghierarchie

Erst **nach** Anwendung der Abwaegungslogik aus 0.3.2 gilt in dieser Reihenfolge:

1. Datenintegritaet, Schutz von Originalen, Datenschutz und Sicherheitsgrenzen.
2. Ausdrueckliche Verbote.
3. Haupttext der Spezifikation.
4. Normative Anhaenge.
5. Nichtnormative Referenzwerte.

Ein Entwickler darf interne Algorithmen austauschen, wenn alle externen Vertraege, Artefaktformate, Sicherheitsgrenzen und Abnahmekriterien erhalten bleiben und die Abwaegungslogik aus 0.3.2 nicht verletzt wird.

---

## 1. Zielbild, Abwaegungslogik, Schutzgrenzen

### 1.1 Zielbild

Der Workflow verarbeitet Foto-Batches auf einem Synology-NAS in zwei Phasen:

- **Phase 1** analysiert, bewertet und bereitet die menschliche Pruefung vor.
- **Phase 2** archiviert und bereinigt ARWs erst nach einer nachweislich sicheren Endentscheidung.

Original-JPGs und ARWs duerfen weder still ueberschrieben noch geloescht werden. Bekannte Gesichtserkennung verarbeitet nur bewusst gepflegte bekannte Personen. Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt, als Kandidat protokolliert oder als Referenz aktiviert werden. Ein Gesichtstreffer darf technische Mindestqualitaet, Manual Keep oder Schutzregeln niemals ueberstimmen.

### 1.2 Abwaegungslogik

Siehe Abschnitt 0.3.2 (verbindlich, vorrangig).

### 1.3 Schutzgrenzen

Folgende Datenklassen unterliegen unterschiedlichen Schutzregeln:

| Klasse | Inhalt | Schutzregel |
|--------|--------|-------------|
| Originale | Kamera-JPGs und ARWs | Nur im geregelten Phasenablauf veraenderbar. Nie still ueberschreiben oder loeschen. |
| Abgeleitete Medien | Crops, ZIPs, Vorschauen, Kopien | Nur mit Herkunft, Hash und dokumentierter Aktion. |
| Steuerdaten | Manifeste, Zustaende, Logs, Indizes, Caches | Schema-validiert, atomar, rekonstruierbar. |
| Modellartefakte und Konfiguration | Modellgewichte, Config mit Pfaden | Duerfen separat verwaltet werden, sofern keine geschuetzten Bildinhalte exfiltriert werden. |

**Wichtig:** Bilddaten, Face-Crops, Embeddings und Referenzbilder werden nicht persistent ausserhalb der erlaubten NAS-Datenbereiche gespeichert. Modellartefakte und Konfigurationsdaten duerfen extern verwaltet werden, solange keine geschuetzten Bildinhalte uebertragen oder persistiert werden.

### 1.4 Sicherheits- und Compliance-Grenzen

- Alle produktiven Pfade muessen innerhalb von `paths.basedir` liegen.
- Phase 2 benoetigt valide Freigabe, Locks, konsistenten Batch-State und ein verifiziertes Archiv.
- Archive werden nicht ueberschrieben; unsichere Kollisionen erzeugen neue Namen.
- Persistente Daten liegen ausserhalb des Container-Images.
- Private Bilder, Laufzeitdaten, lokale Secrets und Caches gehoeren nicht in Git.
- Die zentrale `config.yaml` ist eine bewusste Projektabweichung von einer separaten Beispielvorlage und muss daher secrets-frei bleiben.

---

## 2. Architektur, Verzeichnisse, Datenfluesse

### 2.1 Systemuebersicht

Das Projekt trennt Betriebsschnittstelle, CLI, Fachmodule und den persistenten NAS-Datenbereich. Shell-Skripte pruefen nur Umgebung und starten den Workflow; sie enthalten keine Geschaeftslogik. Die Python-CLI laedt `config/config.yaml`, validiert die Konfiguration und delegiert an spezialisierte Module. Die Fachmodule erzeugen testbare Ergebnisobjekte und kapseln Dateisystemmutationen.

### 2.2 Projektstruktur

- `NAS_EXAMPLE/`: Beispiel fuer den persistenten NAS-Bereich.
  - `TEMP_SD/`: Neue Eingangsbatches.
  - `TEMP_IMAGES/`: Phase-1-Review-Ausgabe.
  - `TEMP_DONE/`: Menschlich freigegebene Uebergabe.
  - `TEMP_ERROR/`: Quarantaene und Fehlerfaelle.
  - `WORKFLOW_DATA/`: States, Logs, Summaries, Caches, Referenzen, Modelle.
  - `MANUAL_KEEP/inbox/`: Manuelle Keep-Eingaenge.
  - `MANUAL_KEEP/used/`: Bereits zugeordnete Keep-Dateien.
- `synology-photo-workflow/`
  - `app/`: Python-Fachmodule und CLI.
  - `config/config.yaml`: Zentrale kommentierte Konfiguration.
  - `scripts/`: DSM-/Docker-Start- und Vorpruefungsskripte.
  - `tests/`: Unit- und Vertragspruefungen.
  - `docs/`: Handbuch, Architektur, Testdokumentation.

### 2.3 Abstraktionsschichten

- `app.cli` verarbeitet Argumente, laedt Konfiguration und uebersetzt Ergebnisse in Exit-Codes.
- `app.configuration` validiert YAML, Pfade und Fingerprints.
- `app.inventory` prueft Eingangsstabilitaet, Endungen und exakte JPG-/ARW-Paarbildung.
- `app.phases` orchestriert die Phasen, ohne Bewertungs- oder Archivdetails zu duplizieren.
- `app.culling` berechnet Merkmale, Komponentenscores, Sterne und Vorschlaege.
- `app.metadata` kapselt Exiftool, Keyword-Merge und Ruecklesepruefung.
- `app.archives` kapselt Archivplan, ZIP-Erstellung, Validierung, Hashes, Kollisionen und Aktivierung.
- `app.batch_state` haelt den Zustandsautomaten und atomare Updates.
- `app.locks` schuetzt parallele Laeufe.
- `app.calibration` erzeugt Records, Indizes und Readiness-Auswertung.
- `app.face_backend` definiert modellneutrale Protokolle und die Backend-Registry.
- `app.family_recognition` verarbeitet Referenzen, Caches und Matchlogik, ohne Fachlogik in Adapter zu verlagern.
- `app.reporting` erzeugt Logs, Scheduler-Ausgabe und Run-Summaries.
- `app.work_units` verwaltet Inventar und WorkUnit-States.
- `app.planning` plant WorkUnits und Sortierung.
- `app.runtime` verwaltet State, Lock, Recovery und Quarantaene.
- `app.safety` validiert Pfade und fuehrt Security-Checks durch.

**Wichtig:** Diese Trennung ist der vorgesehene Erweiterungspunkt: Ein neues Face-Backend gehoert in Adapter/Registry, eine neue Bewertungsregel in `culling`, ein anderes Archivformat in `archives` und keine dieser Aenderungen in Shell-Skripte.

### 2.4 Datenquellen und Wirkungen

- Die Inventarisierung bezieht Daten direkt aus `TEMP_SD`; sie erzeugt Manifeste und Paarbindungen.
- `culling` bezieht Bilddaten und Gewichte aus `config.culling`; seine Scores wirken auf Sterne, Vorschlaege und Review-Listen.
- `metadata` bezieht Entscheidungen und erlaubte Schluessel aus den Batch-Ergebnissen; es wirkt ausschliesslich bei aktiviertem Schreibmodus auf Bildmetadaten.
- `archives` beziehen nur validierte Phase-2-Kandidaten und erzeugen verifizierte ZIPs im persistenten Bereich.
- Die Loeschlogik bezieht sich auf Archivmanifest, Hash und State; ohne diese Quellen wird kein ARW geloescht.
- Face-Erkennung bezieht Modelle aus dem gewaehlten Backend, Referenzen und Caches aus `WORKFLOW_DATA`. Ihre Wirkung ist auf Match-Ergebnis, Familien-Score und gegebenenfalls Personentags begrenzt; bei deaktivierter Funktion entstehen keine Face-Artefakte.
- Kalibrierung bezieht bestaetigte Review-Records und wirkt auf Reports und Empfehlungen, niemals selbst aendert auf Automatikflags.

### 2.5 Kanonische Arbeitsordner

| Ordner | Zweck |
|--------|-------|
| `PHOTO_WORKFLOW/README.md` | Gesamtdokument fuer den Workflow, beschreibt Gesamtfluss, manuelle Aktionen und Lebenszyklus. |
| `TEMP_SD` | Eingang fuer neue Kameraordner. |
| `TEMP_IMAGES` | Ergebnis aus Phase 1 zur manuellen Sichtung. |
| `TEMP_DONE` | Manuell freigegebene Ordner fuer Phase 2. |
| `TEMP_ERROR` | Quarantaene fuer fehlerhafte oder unsichere Faelle. |
| `WORKFLOW_DATA` | Zentrale Daten (faces, models, runtime, samples, reports, archives, config). |
| `MANUAL_KEEP` | Vorab ausgewaehlte, extern erhaltene JPGs (inbox, used). |

Die tatsaechlichen Pfade sind konfigurierbar, muessen aber innerhalb eines erlaubten Basisverzeichnisses liegen.

### 2.6 Batch-Struktur und Benennung

Ein Batch enthaelt verbindlich die Unterordner:

- `ARW` (fuer ausgelagerte ARWs)
- `SAVE` (fuer JPG-Archiv und Scores)
- `Review` (fuer zur Pruefung vorgemerkte Bilder)
- `Rejected` (fuer abgelehnte Bilder)

Nur JPGs im Batch-Hauptordner gelten als aktiv. Ein aus `Review` oder `Rejected` in den Hauptordner zurueckgelegtes JPG ist wieder aktiv und schuetzt sein passendes ARW.

**Begriffe (einheitlich):**
- **batchid:** Immer `batchid` (kleingeschrieben, kein Bindestrich). Format: `source-folder-name+fingerprint(8)`.
- **WorkUnit:** Immer `WorkUnit` (CamelCase, keine Leerzeichen).
- **Face-Backend:** Immer `Face-Backend` (Bindestrich, gross F, gross B).
- **Manual Keep:** Immer `Manual Keep` (gross M, gross K, Leerzeichen).
- **Review-Record:** Immer `Review-Record` (Bindestrich, gross R, gross R).
- **Calibration-Index:** Immer `Calibration-Index` (Bindestrich, gross C, gross I).

**ARW-Schutz:** Ein ARW ist geschuetzt, wenn ein aktives JPG mit demselben eindeutig normalisierten Basename existiert. Mehrdeutige Paarungen, mehrere wirksame JPG-Kopien, fehlende Quellhashes oder widerspruechliche Ordnerzustaende blockieren Phase 2 mit `review_state_invalid`; es darf keine ARW-Aktion stattfinden.

### 2.7 Manual Keep (Ueberblick)

**MANUAL_KEEP** ist der kontrollierte Eingang fuer externe, vorab ausgewaehlte JPGs (z. B. per WhatsApp erhalten). Die Zuordnung erfolgt streng getrennt vom Culling, Serienlogik und persoenlichen Geschmack.

- **inbox/**: Neue, noch nicht zugeordnete Manual-Keep-Bilder.
- **used/**: Bereits zugeordnete Manual-Keep-Bilder.

Detaillierte Logik: Siehe Abschnitt 4.6.

---

## 3. Batch-, Phasen- und Recovery-Vertrag

### 3.1 Batch-ID und Zustandsdatei

Die unver aenderliche `batchid` lautet `source-folder-name+fingerprint(8)` und bleibt beim Wechsel zwischen allen Arbeitsordnern gleich. Pro Batch gibt es genau eine zentrale Zustandsdatei `WORKFLOW_DATA/runtime/state/{batchid}.json`; globale Zustandsdateien sind unzulaessig.

**Batch-ID-Bildung:** Die `batchid` wird bei Erstkontakt mit dem Batch aus dem Ordnernamen und einem 8-stelligen Fingerprint (SHA256, gekuerzt) gebildet. Sie bleibt ueber alle Ordnerwechsel hinweg unver aendert.

**Beispiel:** Ein Ordner `2024-08-15_Geburtstag` erhaelt die `batchid` `2024-08-15_Geburtstag+a3f7c2e1`.

### 3.2 Phase 1

Phase 1 MUSS in dieser Reihenfolge arbeiten:

1. Stabilitaets-, Namens-, Lock- und Symlink-Pruefung.
2. Datumsnormalisierung.
3. ARW-Ablage nach `ARW`.
4. Validiertes JPG-Archiv.
5. Feature- und Score-Ermittlung einschliesslich Manual Keep und Serienlogik.
6. Eingebettete Metadaten, CSV und Phase-1-Manifest.
7. Sichtbare Ablage in Hauptordner, `Review` oder `Rejected`.
8. Atomare Uebergabe nach `TEMP_IMAGES`.

### 3.3 Phase 2

Phase 2 MUSS zuerst Phase-1-Manifest und Endentscheidungen validieren, bei manueller Freigabe den unver aenderlichen Review-Record schreiben und erst danach archivieren. Ein ARW darf nur geloescht werden, nachdem ein vollstaendiges Archiv erzeugt, geprueft, auf demselben Dateisystem atomar aktiviert und mit Hash protokolliert wurde.

Bei jedem Fehler bleibt das ARW erhalten; ARW darf erst nach vollstaendig dokumentierter Bereinigung entfernt werden.

**Phase-2-Start:** Phase 2 beginnt erst nach manueller Freigabe (Move nach `TEMP_DONE`) oder nach explizit zugelassener automatischer Uebergabe (`automatic_handoff`).

**Beispiel:** Ein Batch in `TEMP_IMAGES` wird vom Menschen gesichtet. Nach der Sichtung wird der gesamte Batch nach `TEMP_DONE` verschoben. Dies ist das alleinige Freigabesignal fuer Phase 2.

### 3.4 Zustandsautomat (manuell und automatisch)

Fuer manuell freigegebene Batches lautet der Zustandsautomat zwingend:

```
phase1_started → phase1_completed → review_comparison_pending → review_record_committed → calibration_index_committed → phase2_archiving → phase2_completed
```

Der manuelle Move nach `TEMP_DONE` ist das alleinige Freigabesignal.

Bei einer explizit zugelassenen automatischen Uebergabe lautet er:

```
phase1_completed → automatic_handoff → phase2_archiving → phase2_completed
```

Es entsteht kein Trainingslabel.

**Blockierender Zustand:** `review_state_invalid` (bei mehrdeutigen Paarungen, mehreren wirksamen JPG-Kopien, fehlenden Quellhashes oder widerspruechlichen Ordnerzustaenden) blockiert Phase 2; es darf keine ARW-Aktion stattfinden. Der Batch wird in `TEMP_ERROR` verschoben und in der Run-Summary als `blocking` gemeldet.

**Zustands-Ueberg aenge:** Jeder Uebergang MUSS atomar, mit Zeitstempel und Hash protokolliert werden. Ein Rueckwaerts-Uebergang ist nur bei Quarantaene zulaessig.

**Zustands-Details:** Jeder Zustand MUSS folgende Felder enthalten:
- `state` (Zustandsname, snake_case)
- `timestamp` (ISO8601-Zeitstempel)
- `hash` (SHA256 des vorherigen Zustands)
- `reason` (optional, bei Fehler oder Quarantaene)
- `producer_version` (Versionskennung der erzeugenden Software)

**Beispiel-Zustand:**
```json
{
    "state": "phase1_completed",
    "timestamp": "2024-08-15T14:30:00Z",
    "hash": "a3f7c2e1b5d8f9e0c4a6b7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
    "reason": null,
    "producer_version": "10.1"
}
```

### 3.5 WorkUnits / Bildmengenmodus / Resume

- **Status:** Pflicht.
- **Zweck:** Erlaubt es, auch sehr grosse physische Ordner in ueberschaubaren, sicher fortsetzbaren Portionen zu verarbeiten, ohne die sichtbare Ordnerstruktur zu ver aendern.
- **Ablauf:**
  1. `workflow.work_unit_mode: source_batch` (Default, ganzer Ordner = Einheit) oder `image_count` (interne, unsichtbare Portionierung).
  2. Der physische Batch wird erst verschoben, wenn alle WorkUnits abgeschlossen sind.
  3. Angefangene oder wiederherzustellende Arbeit hat immer Vorrang vor neuen Ordnern.
  4. Vor jedem sichtbaren Dateimove wird ein Uebergangsstate (`phase1_moving`) geschrieben, erst danach der Abschluss (`phase1_completed`).

**WorkUnit-Vertrag:** Eine WorkUnit MUSS `work_unit_id`, `batchid`, `image_range` (Start, Ende), `state` (pending, in_progress, completed, failed, paused), `timestamp`, `hash`, `error_reason` (optional) enthalten.

**Beispiel image_count:** Bei `workflow.work_unit_mode: image_count` und `workflow.images_per_work_unit: 200` wird ein physischer Batch mit 800 Bildern in 4 WorkUnits aufgeteilt. Jede WorkUnit wird separat verarbeitet, aber der Batch wird erst nach Abschluss aller 4 WorkUnits nach `TEMP_IMAGES` verschoben.

### 3.6 Archivvertrag

- **ZIP:** Lesbarkeit, Traversal, Groessenlimit, Kompressionsverhaeltnis pruefen.
- **Kollision:** `..._EXTRA_n.zip` statt Ueberschreibung.
- **Hash:** SHA256 fuer ZIP, Manifest, State; Hash vor/nach Aktivierung pruefen.
- **Aktivierung:** Vollstaendiges Archiv erzeugt, geprueft, auf gleichem Dateisystem atomar aktiviert, mit Hash protokolliert.
- **Loeschung:** ARW erst nach vollstaendig dokumentierter Bereinigung entfernen.

**Archiv-Vertrag-Kohaerenz:** Jeder Archiveintrag MUSS folgende Felder enthalten:
- `relative_path` (string, relativ zum Batch)
- `size` (int, Bytes)
- `hash` (string, SHA256)
- `archived_at` (string, ISO8601)

**Archivplan-Details:** Der Archivplan MUSS folgende Felder enthalten:
- `batchid` (Batch-ID)
- `created_at` (ISO8601-Zeitstempel)
- `archive_path` (relativer Pfad zur ZIP)
- `entry_count` (Anzahl der Eintr aeg)
- `total_size` (Gesamtgr oesse in Bytes)
- `entries` (Liste aller Eintr aeg mit Pfad, Groesse, SHA256)
- `config_fingerprint` (SHA256 der effektiven Konfiguration)
- `producer_version` (Versionskennung)

### 3.7 Fehler- und Recovery-Vertrag

- **Fehlende oder ungueltige Steuerdaten:** Nach `WORKFLOW_DATA/runtime/quarantine` kopieren, mit Grund, Zeit, Hash melden; sichere Neuerstellung oder menschliche Pruefung erforderlich.
- **Atomaritaet:** Inhalt erzeugen, validieren, temporaer auf gleichem Dateisystem schreiben, erneut validieren, atomar ersetzen; vorherige Version bis Aktivierung erhalten.
- **Lock:** Globaler Lock verhindert parallele produktive Laeufe; Lock vor/nach Lauf pruefen.
- **Quarantaene:** Fehlerhafte Artefakte nach `WORKFLOW_DATA/runtime/quarantine` mit Manifest; blockierend melden; menschliche Pruefung erforderlich.

---

## 4. Scoring, Serien, Metadaten, Manual Keep, Face-Backend, Kalibrierung

### 4.1 Technisches Culling

- **Status:** Pflicht.
- **Zweck:** Ressourcenschonende Basisbewertung ohne Pflicht-KI-Modell. Bewertet Schaerfe, Belichtung und einfache aesthetische Merkmale. Ergebnis ist `base_score`.
- **Ablauf:**
  1. Kleine technische Vorschau erzeugen (256–512 Pixel laengste Kante).
  2. Teilscores fuer Schaerfe (Kantenvarianz), Belichtung (Clipping, Helligkeitsbalance) und Aesthetik (Kontrast, Saettigung, Bildbalance) berechnen.
  3. Teilscores mit konfigurierbaren Gewichten (`culling.base_weights`) zu `base_score` kombinieren.
  4. Nicht lesbare oder fehlerhafte Bilder erhalten `analysis_error`, aber keinen stillen Ersatzscore.

**Score-Vertrag:** `base_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0. `analysis_error` wird als `null` oder spezieller Wert `-1` repraesentiert, nie als `0.0`.

### 4.2 Persoenlicher Geschmack (lokales CLIP)

- **Status:** Pflicht.
- **Zweck:** Ergaenzt die technische Bewertung um eine gelernte, persoenliche Praeferenz. Bewertet Bilder gegen positive/negative Text-Prompts oder aktive Referenzbilder.
- **Ablauf:**
  1. CLIP-Modell laedt (nur bei aktiviertem Adapter).
  2. Bild wird gegen aktive Referenzen aus `samples/reference/` oder gegen Prompt-Listen bewertet.
  3. Ergebnis ist ausschliesslich `personal_score`; es wird nicht in `base_score` gemischt.
  4. Bilder, die `keep` sind, hoechste Sternklasse erreichen und die aktive Auswahl messbar erweitern, werden automatisch nach `samples/new_refs/` vorgeschlagen.
  5. Nur ein manuelles Kopieren nach `samples/reference/` aktiviert sie und loest ein Retraining aus.

**Score-Vertrag:** `personal_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 oder `None` (bei deaktiviertem/fehlerhaftem Adapter).

### 4.3 Serienerkennung

- **Status:** Pflicht.
- **Zweck:** Verhindert, dass mehrere technisch aehnliche Aufnahmen alle gleich behandelt werden. Hebt das beste Bild einer Serie hervor.
- **Ablauf:**
  1. Gruppierungueber Aufnahmezeit + Bild-Embedding (visuelle Aehnlichkeit) oder deterministische Dateinamenlogik als Fallback.
  2. Pro Bild werden Serien-ID, -Groesse, -Rang, `series_best`-Flag und Abstand zum Besten gespeichert.
  3. Das Bestbild darf hoechstens um eine Klasse aufgewertet werden.
  4. Andere Bilder duerfen nur mit dokumentierter Distanz zum Bestbild abgewertet werden.

**Serien-Vertrag:** `series_id` ist eine eindeutige Zeichenkette pro Serie innerhalb eines Batches. `series_rank` ist 1-basiert (1 = bestes Bild). `series_best` ist ein boolescher Wert.

### 4.4 Eye-Score

- **Status:** Pflicht.
- **Zweck:** Erkennt geschlossene Augen als leichtes Korrektursignal.
- **Ablauf:**
  1. Nur bei genau einem ausreichend grossem Gesicht im Bild.
  2. ONNX-Zweiklassen-Modell liefert `P(offen)`.
  3. Ergebnis ist `eye_score` (eigene Komponente, nicht Teil von `base_score`).

**Score-Vertrag:** `eye_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 (Wahrscheinlichkeit fuer offene Augen) oder `None`.

### 4.5 Bekannte Gesichtserkennung / Familie

- **Status:** Pflicht.
- **Zweck:** Liefert ein moderates positives Signal fuer bewusst gepflegte, bekannte Personen. Keine allgemeine Gesichtserkennung, kein Clustering unbekannter Gesichter.
- **Ablauf:**
  1. Backend (Registry-basiert, Standard `opencv_yunet_sface_cpu`) erzeugt Embedding.
  2. Vergleich gegen aktive Referenzen einer Person (`faces/<slug>/reference/` mit `selection.json` Status `active`).
  3. Nur bei eindeutigem Match (Schwelle + Sicherheitsmarge zum Zweitbesten) wird `family_score` gesetzt und ein Personentag vergeben.
  4. Klare Treffer erzeugen Vorschlaeg in `faces/<slug>/new_faces/`, die ein Mensch durch Kopieren nach `reference/` bestaetigt.

**Schutzgrenzen:** Bilder, Bildbytes, Face-Crops, Referenzbilder sowie Bild-/Face-/CLIP-Embeddings sind ausschliesslich fluechtig im RAM zul aessig und duerfen nie in JSON, Cache, Log, Manifest, CSV, Metadaten oder Report persistiert werden.

**Face-Backend-Vertrag:** Jedes Backend MUSS eine Registry-ID, einen Adapter-Namen, einen Modellhash, einen Provider-Namen, eine Vorverarbeitungs-Pipeline, eine Metrik und einen Auswahlfingerprint bereitstellen. `family_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 oder `None`.

### 4.6 Manual Keep

- **Status:** Pflicht.
- **Zweck:** Ordnet extern (z. B. per WhatsApp) vorab ausgewaehlte, oft komprimierte/kleine Bilder ihrem Original im aktuellen Batch zu und erzwingt fuer dieses `keep`.
- **Ablauf:**
  1. Zweistufig: schneller aufloesungsrobuster Vorfilter (Seitenverhaeltnis, Perceptual Hash).
  2. Danach strenge normalisierte Endpruefung (Verifikationsscore auf EXIF-korrigierten, gleich skalierten Bildern).
  3. Match nur bei Schwelle und ausreichendem Abstand zum Zweitbesten.
  4. Ergebnis erzwingt `keep` mit Grund `manual_keep_match`.
  5. Danach durchlaeuft das Bild normales Scoring; erst nach Zuordnung wird die Quelldatei nach `used/` verschoben.

**Manual-Keep-Vertrag:** `manual_keep` ist ein boolescher Wert (`true` bei Match, `false` oder `null` sonst). `manual_keep_match` wird in der Run-Summary als Zaehler gefuehrt.

### 4.7 Metadaten

- **Status:** Pflicht.
- **Zweck:** Macht Bewertungen und Personentreffer in gaengigen Fotoprogrammen sichtbar.
- **Ablauf:**
  1. Sternrating aus Score-Band bestimmen.
  2. Namespaced Keywords einbetten (`workflow:ai_cull`, `decision:<final>`, `series:*`, `family:match`, `person:<slug>`, `manual_keep:true`).
  3. Per `exiftool` (`shell=False`) in Bild schreiben.
  4. Nach dem Schreiben zuruecklesen und abgleichen.

**Metadaten-Vertrag:** Metadaten MUessen namespaced sein (Praefix `workflow:`). `failed_metadata` ist ein boolescher Wert. `exiftool_status` ist einer von `success`, `disabled`, `failed`, `sidecar`.

### 4.8 Kalibrierung und Gewichtungsassistent

- **Status:** Pflicht.
- **Zweck:** Lernt aus bestaetigten menschlichen Endentscheidungen, ob die vorhandenen Score-Komponenten anders gewichtet werden sollten. Ersetzt nie die Komponenten selbst.
- **Ablauf:**
  1. Pro manuell freigegebenem Batch entsteht ein unver aenderliches `review_decision_record.json`.
  2. Daraus werden Kennzahlen (terminale Uebereinstimmung, `reject_to_keep_rate` etc.) berechnet.
  3. Optional wird ein Gewichtsvorschlag im Schattenmodus erzeugt.
  4. Eine Aktivierung erfordert bewusste Nutzerfreigabe, erfuellte Gates und bleibt jederzeit rollbackf aehig.

**Kalibrierungs-Vertrag:** `review_decision_record.json` MUSS `batchid`, `timestamp`, `human_decision`, `predicted_decision`, `agreement`, `config_fingerprint`, `producer_version` enthalten.

---

## 5. Referenzpool-Verwaltung, Rebuild und Nutzen-Ranking

### 5.1 Ziel

Die Referenzpool-Verwaltung ist die gemeinsame Regel fuer Geschmack und bekannte Gesichter. Sie stellt sicher, dass aktive Referenzen klein, qualitativ sinnvoll und divers bleiben. Sie trennt Vorschlagsdateien von aktiven Referenzen, erzwingt menschliche Freigabe, aktualisiert Wahrheitsdateien und baut bei jeder aktiven Aenderung die Referenzbasis neu auf.

### 5.2 Geltungsbereich

Diese Regeln gelten fuer:

- **Face-Referenzpools:** `WORKFLOW_DATA/faces/<slug>/` (je bekannte Person)
- **Geschmacks-Referenzpool:** `WORKFLOW_DATA/samples/`

Nicht Gegenstand dieser Regel sind: Manual Keep, technische Culling-Bilder ausserhalb der speziell konfigurierten Modellbasis, und unbekannte Gesichter.

### 5.3 Ordnerstruktur

Jeder Pool MUSS folgende Struktur haben:

```text
<pool_root>/
├── reference/           # Aktive Referenzen (max. max_active)
├── new_*/               # Vorschlaege (max. max_new, max. max_new_per_batch pro Batch)
└── selection.json       # EINZIGE Wahrheit fuer diesen Pool
```

- **Face:** `<pool_root>` = `WORKFLOW_DATA/faces/<slug>/`, `new_*` = `new_faces/`, Dateien = Face-Crops.
- **Geschmack:** `<pool_root>` = `WORKFLOW_DATA/samples/`, `new_*` = `new_refs/`, Dateien = Ganzbilder.

### 5.4 Wahrheitsdatei `selection.json`

Jeder Pool hat genau eine `selection.json` im Hauptordner. Sie ist die alleinige Wahrheit ueber aktive Referenzen, offene Vorschlaege, Kapazitaetsgrenzen, Auswahlfingerprint und Rangdetails.

**Pflichtfelder:**
- `schema_version`
- `pool_type`
- `slug` (nur Face)
- `updated_at`
- `selection_fingerprint`
- `pool_build_id`
- `rank_digits`
- `limits`
- `images`

**Verboten:** Embeddings, Bildbytes, Face-Crops oder andere binaere Daten in `selection.json`.

### 5.5 Bild-Metadaten

Jeder Eintrag in `images` MUSS folgende Felder enthalten:

- `source_id`
- `batchid`
- `path` oder `crop_source`
- `status` (`active` oder `new`)
- `quality_score`
- `pool_utility_score` oder `candidate_utility_score`
- `pool_rank` (nur active)
- `approved_at` (nur active)

**Face-spezifisch:** `bounding_box`, `face_confidence`, `original_path`.

**Geschmack-spezifisch:** `base_score`.

### 5.6 Kapazitaetsgrenzen

| Grenze | Typ | Wirkung |
|--------|-----|---------|
| `max_active` | Hard Limit | Darf nicht ueberschritten werden; weitere Aktivierungen blockiert. |
| `max_new` | Hard Limit | Darf nicht ueberschritten werden; weitere Vorschlaege blockiert. |
| `max_new_per_batch` | Hard Limit | Pro `batchid` darf diese Grenze nicht ueberschritten werden. |
| `min_active` | Soft Limit | Warnung, wenn darunter; Modell kann unzulaessig werden. |
| `target_active` | Ziel | Angestrebter Bereich; System meldet, wenn deutlich darunter oder darueber. |

### 5.7 Konfiguration

```yaml
reference_pools:
  common:
    max_active: 100
    min_active: 30
    target_active: 50
    max_new: 20
    max_new_per_batch: 5
  taste:
    min_quality_score: 0.70
    max_redundancy: 0.90
    base_score_pool_size: 50
  faces:
    min_quality_score: 0.70
    max_redundancy: 0.95
    crop_size: 256
    min_face_size: 128
```

### 5.8 Sinnvolle Wertebereiche

| Parameter | Sinnvoller Bereich | Empfohlener Startwert | Begrundung |
|-----------|-------------------|----------------------|------------|
| `max_active` (Face) | 30–200 | 100 | Genug Diversitaet ohne unn oetige Rechenlast. |
| `max_active` (Geschmack) | 30–200 | 100 | Aehnlich wie Face; persoenliche Praeferenzen sind komplexer. |
| `min_active` | 20–50 | 30 | Mindestqualitaet fuer Training. |
| `target_active` | 30–100 | 50 | Zielbereich des Pools. |
| `max_new` | 10–50 | 20 | Begrenzte Anzahl offener Entscheidungen. |
| `max_new_per_batch` | 3–10 | 5 | Schutz vor Batch-Fluten. |
| `crop_size` (Face) | 128–512 | 256 | Gute Balance aus Genauigkeit und Effizienz. |
| `min_quality_score` | 0.6–0.8 | 0.7 | Filtert schlechte Bilder. |
| `max_redundancy` (Face) | 0.90–0.98 | 0.95 | Face-Crops koennen aehnlicher sein. |
| `max_redundancy` (Geschmack) | 0.85–0.95 | 0.90 | Geschmackspool soll diverser sein. |

### 5.9 Auswahl neuer Vorschlaege

Die Auswahl neuer Vorschlaege folgt derselben Logik:

1. Nur menschlich bestaetigte `keep`-Bilder sind Kandidaten.
2. Kandidaten muessen `min_quality_score` erreichen.
3. Kandidaten duerfen bestehende aktive Referenzen nicht zu stark duplizieren.
4. Es wird nach Nutzen fuer den Pool sortiert.
5. Erst danach werden `max_new_per_batch` und `max_new` angewendet.
6. Nur die besten zulaessigen Kandidaten werden als `new_refs/` oder `new_faces/` gespeichert.

**Face-Crop-Erstellung:** Face-Kandidaten werden zusaetzlich als quadratischer Gesichtsausschnitt gespeichert (z. B. 256×256 Pixel). Der Crop enthaelt nur das Gesicht, kein Umfeld. Die Metadaten enthalten Bounding Box, Gesichtskonfidenz und Originalreferenz.

**Nutzenbewertung:**
- **Geschmack:** Stil, Szene, Motive, Farben, Komposition, persoenliche Relevanz.
- **Face:** Pose, Blickrichtung, Licht, Distanz, Ausschnitt, Ausdruck.

### 5.10 Rebuild und Neu-Ranking

Ein Rebuild ist zwingend, wenn sich der aktive Referenzbestand aendert:

- Ein Bild wird von `new_*` nach `reference/` verschoben.
- Ein aktives Bild wird aus `reference/` entfernt.
- Eine aktive Referenzdatei wird veraendert oder ihr Hash aendert sich.
- Die Auswahlparameter, das relevante Modell, die Vorverarbeitung oder der Auswahlfingerprint aendern sich.
- `selection.json` und der Ordnerinhalt stimmen nicht mehr ueberein.

**Was neu aufgebaut wird:**
- Face: Referenz-Embeddings fuer die bekannte Person, Auswahl- und Cache-Fingerprint.
- Geschmack: Aktiver Praeferenzindex bzw. lokales Geschmacksprofil, bei trainierbaren Adaptern auch das lokale Modell.
- Base Score: separate, konfigurierbare Basis fuer technisches Culling.

**Nutzenbasiertes Ranking:**

- `pool_utility_score` beschreibt den marginalen Nutzen eines Bildes fuer den aktuellen Pool.
- **Rang 1 = hoechster Nutzen**.
- **Rang n = geringster Nutzen**.

Der Nutzen muss mindestens technische Mindestqualitaet, Nicht-Redundanz, Diversitaet und poolspezifische Eignung beruecksichtigen.

### 5.11 Dynamische Stellenzahl

Die Stellenzahl der Rangzahl (`rank_digits`) wird automatisch an die Anzahl aktiver Dateien angepasst:

1. Anzahl aktiver Dateien in `reference/` zaehlen.
2. `rank_digits = max(1, ceil(log10(n + 1)))` berechnen.
3. Dateinamen formatieren als `{rank_zfill}__{original_name}_{suffix}.{ext}`.

**Beispiele:**

| n | rank_digits | Beispiel |
|---|------------|----------|
| 5 | 1 | `1__...` bis `5__...` |
| 50 | 2 | `01__...` bis `50__...` |
| 500 | 3 | `001__...` bis `500__...` |
| 1500 | 4 | `0001__...` bis `1500__...` |

**Sortierung:** Dateien werden aufsteigend nach Rang angezeigt. Rang 1 ist oben, Rang n unten. Der Mensch kann die letzten Dateien als geringsten Nutzen erkennen und loeschen.

### 5.12 Atomare Umbenennung

Nach erfolgreichem Rebuild werden alle Dateien in `reference/` neu benannt:

1. Anzahl zaehlen.
2. Stellenzahl berechnen.
3. Nutzenrang aller aktiven Referenzen neu berechnen.
4. Tempor aere eindeutige Namen verwenden.
5. Finale Namen `0001__...`, `0002__...`, ... setzen.
6. Neue `selection.json` temporaer erzeugen und validieren.
7. `selection.json` atomar ersetzen.
8. `rank_digits` und `pool_build_id` schreiben.

Scheitert ein Schritt, bleibt die vorherige Poolversion aktiv; der Fehler wird in der Run-Summary gemeldet.

### 5.13 Manuelle Bedienung

| Aktion des Menschen | Systemwirkung |
|---------------------|---------------|
| Bild aus `new_*` nach `reference/` verschieben | Konsistenzpruefung, Rebuild, neues Ranking. |
| Bild aus `new_*` loeschen | Eintrag aus `selection.json` entfernen; kein Rebuild, solange `reference/` unveraendert bleibt. |
| Aktive Datei aus `reference/` loeschen | Konsistenzpruefung, Rebuild, neues Ranking. |
| `max_new` erreicht | Keine neuen Vorschlaege; Run-Summary meldet Handlungsbedarf. |
| `max_active` erreicht | Keine neue Aktivierung; Run-Summary meldet manuelles Bereinigen. |

### 5.14 Run-Summary-Meldungen

**Meldung: `max_new` erreicht**
```json
{
  "severity": "warning",
  "type": "reference_pool_new_limit_reached",
  "pool": "faces/max_mustermann",
  "message": "Die Hoechstzahl offener Vorschlaege (max_new=20) ist erreicht; es werden keine weiteren neuen Gesichter gespeichert.",
  "action": "Bitte new_faces/ pruefen: relevante Bilder nach reference/ verschieben, uebrige Bilder loeschen."
}
```

**Meldung: `max_new_per_batch` erreicht**
```json
{
  "severity": "info",
  "type": "reference_pool_batch_limit_reached",
  "pool": "samples",
  "batchid": "2024-08-15_Geburtstag+a3f7c2e1",
  "message": "Die Hoechstzahl offener Vorschlaege pro Batch (max_new_per_batch=5) fuer Batch '2024-08-15_Geburtstag+a3f7c2e1' ist erreicht.",
  "action": "Bitte new_refs/ pruefen: relevante Bilder nach reference/ verschieben."
}
```

**Meldung: `max_active` erreicht**
```json
{
  "severity": "info",
  "type": "reference_pool_active_limit_reached",
  "pool": "faces/max_mustermann",
  "message": "Die Hoechstzahl aktiver Referenzen (max_active=100) ist erreicht; es sind keine weiteren Aktivierungen moeglich.",
  "action": "Bitte reference/ pruefen: weniger nuetzliche Bilder entfernen, um Platz fuer neue Referenzen zu schaffen."
}
```

---

## 6. Betrieb, Konfiguration, Reporting, Abnahme

### 6.1 Konfiguration

- **Schema:** YAML mit strikter Validierung; unbekannte Schluessel sind Fehler (ausser `extensions`).
- **Fingerprint:** Effektive Konfiguration wird mit SHA256-Fingerprint im Run dokumentiert.
- **Sicherheit:** Keine Geheimnisse, keine Produktionspfade in Git.
- **Config-Schluessel:** Durchgaengig snake_case.

### 6.2 Betrieb

- **Scheduler:** Container mit persistentem NAS-Mount starten; globaler Lock verhindert parallele Laeufe.
- **Fehlerisolation:** Ein defekter Batch wird quaraentaenisiert statt den ganzen Lauf zu stoppen.
- **Ressourcenverhalten:** Auf Ziel-NAS dokumentieren.
- **Not-Stop:** Bei Zeitbudget oder SIGTERM keinen neuen teuren Schritt beginnen; sicheren aktuellen Schritt abschliessen, Status `paused` atomar schreiben, kontrolliert beenden.

### 6.3 Reporting

- **Status:** Pflicht.
- **Zweck:** Macht jedem Lauf auf einen Blick klar, was passiert ist und was der Mensch tun muss.
- **Ablauf:** JSON-Run-Summary, Scheduler-Ausgabe, CSV, Logs, `user_actions_required`.

### 6.4 Aenderungs-Historie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|----------|
| 10.1 | 2026-08-04 | MaiTaiMa + Perplexity AI | Bereinigte, konsolidierte Fassung: einheitliche Terminologie, konsistente Querverweise, harmonisierter Stil, vollstaendige Inhalte. |
| 10.0 | 2026-08-04 | MaiTaiMa + Perplexity AI | Erweiterung um Referenzpool-Verwaltung, Face-Crops, dynamisches Ranking und neue Anhaenge. |
| 9.9 | 2026-08-04 | MaiTaiMa + Perplexity AI | Harmonisierte Fassung mit allen Anhaengen (A–P). |
| 9.8 | 2026-08-03 | MaiTaiMa + Perplexity AI | Rechtschreib- und Formatkorrekturen, neuer Abschnitt "Architektur und Compliance". |

---

## Anhaenge

### Anhang A — Normative Datenvertraege

Alle Artefakte MUessen folgende Pflichtfelder enthalten:

- `schema_version`: string, Format "major.minor"
- `created_at`: string, Format ISO8601
- `updated_at`: string, Format ISO8601
- `producer_version`: string, Format "major.minor.patch"
- `batchid`: string, falls zutreffend
- `hash`: string, SHA256, falls zutreffend

**Datenvertrags-Vervollstaendigung:**

- **Registry:** Backends ausschliesslich durch explizite Registry und Adapter ausgewaehlt.
- **Adapter:** Jedes Backend implementiert festgelegte Schnittstellen (Laden, Vorverarbeitung, Merkmalsextraktion, Metrik, Cache-Fingerprint).
- **Modellhash:** Jedes Modell hat SHA256-Hash; Hash Teil des Cache-Fingerprints.
- **Provider:** Backend-Provider klar dokumentiert.
- **Vorverarbeitung:** Normalisierung, Skalierung, Zuschneiden einheitlich; Teil des Fingerprints.
- **Metrik:** Kosinus aehnlichkeit (higher_is_better, 0–1) mit Schwelle 0,95 und Marge 0,03; alternative Metrik nur mit vollstaendiger Dokumentation.
- **Auswahlfingerprint:** `selection.json`-Fingerprint Teil des Cache-Fingerprints; unterschiedliche Fingerprints nie mischen.
- **Face-Crop:** Nur fuer sicheren, bekannten Personenmatch; Vorschlag in `new_faces/` mit Herkunft, Hash, Bounding Box, Qualitaet, Neuheit, Konfidenz, Status.

---

### Anhang B — Metadaten, CSV und Manifest

**CSV (`SAVE/culling_scores.csv`):**

Das CSV MUSS folgende Felder enthalten:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `batchid` | string | Batch-ID |
| `image_id` | string | Basename des Bildes |
| `basescore` | float (0.0–1.0) | Technischer Score |
| `eyescore` | float (0.0–1.0) | Augen-Score |
| `personalscore` | float (0.0–1.0) | Geschmacks-Score |
| `familyscore` | float (0.0–1.0) | Gesichts-Score |
| `finalscore` | float (0.0–1.0) | Gesamtscore |
| `predicted_decision` | string | Vorhergesagte Entscheidung |
| `series_id` | string oder null | Serien-ID |
| `series_size` | int oder null | Serien-Groesse |
| `series_rank` | int, 1-basiert, oder null | Rang in der Serie |
| `series_best` | bool oder null | Bestes Bild der Serie |
| `family_match` | bool oder null | Gesichtstreffer |
| `person_slug` | string oder null | Personen-Slug |
| `manual_keep` | bool oder null | Manual-Keep-Treffer |
| `failed_metadata` | bool | Metadaten-Fehler |
| `exiftool_status` | string | Status |

**JSON-Manifest:**

Das Manifest MUSS folgende Felder enthalten:

- `batchid`: string
- `source_folder`: string
- `created_at`: string (ISO8601)
- `updated_at`: string (ISO8601)
- `schema_version`: string
- `producer_version`: string
- `image_count`: int
- `active_jpgs`: int
- `arw_count`: int
- `culling_scores_hash`: string (SHA256)
- `manifest_hash`: string (SHA256)
- `state`: string
- `phase`: string
- `review_state`: string
- `calibration_status`: string
- `quarantine_reason`: string (falls vorhanden)

**Metadaten-Inventarisierung:**

- Vor Schreiben: Exiftool-Argumente inventarisieren.
- Nach Schreiben: Zuruecklesen und Abgleich; `failed_metadata` bei Mismatch.
- Sidecar: Nur als Recovery-Modus (`metadata.sidecar_recovery_enabled: true`).

**Mindest-Tag-Satz:**

- Sternrating
- `workflow:ai_cull`
- `decision`
- Optional: `series_best`, `family_match`, `person_slug`, `manual_keep`

**Run-Summary:**

- Run-Batch-ID
- Konfigurationsfingerprint
- Angeforderter/wirksamer Automatikmodus
- Ergebnisstatus
- Keep/Review/Reject-Zaehler
- Cache-/Metadatenstatus
- ZIP-Konflikte
- Kalibrierungsstatus
- `user_actions_required`

---

### Anhang C — Face-Backend-Vertrag

Jedes Backend MUSS folgende Felder bereitstellen:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `backend_id` | string | Eindeutige ID |
| `adapter_name` | string | Adapter-Name |
| `model_path` | string | Relativer Pfad zum Modell |
| `model_hash` | string | SHA256-Hash des Modells |
| `provider` | string | Provider-Name |
| `preprocessing` | object | Skalierung, Normalisierung, Zuschneiden |
| `metric` | string | Metrik |
| `selection_fingerprint` | string | SHA256 der Auswahl |
| `cache_fingerprint` | string | SHA256 aus allen obigen Feldern |

- `selection_fingerprint` umfasst den Inhalt der aktiven `selection.json`, die Dateihashes der aktiven Referenzen sowie Auswahlparameter.
- Jede Aenderung dieses Fingerprints erzwingt den Neuaufbau des Personen-Referenzindex.
- Der aktive Index darf nur verwendet werden, wenn er zum aktuellen Fingerprint passt.
- Bild-/Face-Embeddings bleiben fluechtig und werden nicht in `selection.json` gespeichert.
- Face-Crops sind die einzige persistente Form von Gesichtsdaten; sie enthalten keine Embeddings.

---

### Anhang D — Referenzkonfiguration

Die Referenzkonfiguration MUSS folgende Pflichtfelder enthalten:

- `schema_version`: string
- `created_at`: string (ISO8601)
- `updated_at`: string (ISO8601)
- `config_fingerprint`: string (SHA256)
- `producer_version`: string

**`reference_pools`-Struktur:**

```yaml
reference_pools:
  common:
    max_active: 100
    min_active: 30
    target_active: 50
    max_new: 20
    max_new_per_batch: 5
  taste:
    min_quality_score: 0.70
    max_redundancy: 0.90
    base_score_pool_size: 50
  faces:
    min_quality_score: 0.70
    max_redundancy: 0.95
    crop_size: 256
    min_face_size: 128
```

---

### Anhang E — Abnahme ACC-01 bis ACC-15

- ACC-01: Konfigurationsvalidierung.
- ACC-02: CLI-Hilfe.
- ACC-03: Unit-Tests.
- ACC-04: Integrationstests.
- ACC-05: Pfad- und ZIP-Sicherheitstests.
- ACC-06: Dependency-Scan.
- ACC-07: ARW-Archiv-Test.
- ACC-08: Paralleler Scheduler-Start.
- ACC-09: Abbruchtest vor Phase-2-Transaktion.
- ACC-10: Abbruchtest nach Phase-2-Transaktion.
- ACC-11: Ressourcenverhalten auf Ziel-NAS.
- ACC-12: Face-Backend-Test.
- ACC-13: MANUAL_KEEP-Test.
- ACC-14: Gewichtungsassistent-Test.
- ACC-15: NAS-Pilot.

---

### Anhang F — CLI, Exit-Codes, Module

- **CLI:** Nur Argumente, Dispatch, Exit-Codes.
- **Exit-Codes:** 0 Erfolg, 1 Konfigurationsfehler, 2 Pfad-/Sicherheitfehler, 3 Lock-Fehler, 4 State-Fehler, 5 Quarantaene-Fehler, 6 Metadaten-Fehler, 7 Modell-Fehler, 8 Face-Backend-Fehler, 9 Interrupt/SIGTERM, 10 Timeout/Budget.
- **Module:** `app/culling`, `app/family_recognition`, `app/archives`, `app/runtime`, `app/safety`, `app/phases`, `app/manual_keep`, `app/calibration`, `app/reporting`, `app/config`, `app/locks`, `app/batch_state`, `app/face_backend`, `app/inference`.

---

### Anhang G — Konfigurationsvertrag

- **Schema:** YAML mit strikter Validierung; unbekannte Schluessel Fehler (ausser `extensions`).
- **Fingerprint:** Effektive Konfiguration mit SHA256-Fingerprint im Run dokumentieren.
- **Sicherheit:** Keine Geheimnisse, keine Produktionspfade in Git.
- **Status:** `stable`, `advanced`, `experimental` je Variable.
- **Migration:** Aenderungen an Gewichten, Schwellen, Feature-Logik, Referenzbasis, Backend, Modell, Metadatenvertrag aendern Versions-, Konfigurations- und ggf. Cache-Kalibrierungsfingerprint.

---

### Anhang H — Archivvertrag

- **ZIP:** Lesbarkeit, Traversal, Groessenlimit, Kompressionsverhaeltnis pruefen.
- **Kollision:** `..._EXTRA_n.zip` statt Ueberschreibung.
- **Hash:** SHA256 fuer ZIP, Manifest, State; Hash vor/nach Aktivierung pruefen.
- **Aktivierung:** Vollstaendiges Archiv erzeugt, geprueft, auf gleichem Dateisystem atomar aktiviert, mit Hash protokolliert.
- **Loeschung:** ARW erst nach vollstaendig dokumentierter Bereinigung entfernen.

**Archiv-Vertrag-Kohaerenz:** Jeder Archiveintrag MUSS folgende Felder enthalten:
- `relative_path` (string, relativ zum Batch)
- `size` (int, Bytes)
- `hash` (string, SHA256)
- `archived_at` (string, ISO8601)

---

### Anhang I — Sample-Kapazitaetsvertrag

- **Kleine NAS:** ARWs werden im MVP nicht dekodiert; technische Vorschauen 256–512 Pixel laengste Kante; Aehnlichkeitsvektoren 32–64 Pixel; Standard-Worker 1; Bilder unmittelbar schliessen; kein Vollbatch im RAM.
- **Referenzprofile, Geschmacksmodell, Face-Merkmale persistent cachen;** nur bei Eingabe aenderung neu aufbauen.
- **Fehler/Timeouts eines Bildes** duerfen Batch nicht abstuerzen lassen.
- **Werte konfigurierbar;** Sicherheitsvertraege nicht abschwaechen.

**Praezisierung:** Die Groesse der Aehnlichkeitsvektoren (32–64 Pixel) bezieht sich auf die reduzierte, technisch genutzte Vorschau fuer technische Culling- und Vergleichsoperationen. Die tatsaechliche Dimension des Embedding-Vektors haengt vom verwendeten Modell ab.

---

### Anhang J — Reporting, Deployment

- **Reporting:** Kurze Scheduler-Ausgabe, strukturierte JSON-Run-Summary, Batch-CSV, persistente Logs.
- **Deployment:** Container mit NAS-Mount; alle Zustaende, Logs, Konfigurationen, Caches, Summaries auf NAS; nicht im beschreibbaren Container-Dateisystem.
- **Docker/GPU:** Separate Images; Dokumentation; not-root-Ausfuehrung anstreben.

**Reporting-Vertrag-Vervollstaendigung:** Die Run-Summary MUSS folgende Felder enthalten:
- `run_id` (string, UUID)
- `timestamp` (string, ISO8601)
- `config_fingerprint` (string, SHA256)
- `automation_mode` (string)
- `batch_count` (int)
- `image_count` (int)
- `keep_count` (int)
- `review_count` (int)
- `reject_count` (int)
- `error_count` (int)
- `blocking_count` (int)
- `user_actions_required` (array of objects)

---

### Anhang K — Qualitaet, CI

- **CI prueft:** Header, Pflichtfelder, Versionskonsistenz, Konfigurationsschema, Konfigurationsfingerprint, Secrets, Python-Compile, Unit-/Integrationstests, Abnahmetests.
- **Qualitaetsmetriken:** Testabdeckung, Fehlerquote, Quarantaenerate, Resume-Rate, Automatisierungsgrad, Performance auf Ziel-NAS.

---

### Anhang L — Konsistenz- und Einheitlichkeitsregeln

#### N1 – Begriffskonsistenz

- **Batch-ID:** Immer `batchid`.
- **WorkUnit:** Immer `WorkUnit`.
- **Face-Backend:** Immer `Face-Backend`.
- **Manual Keep:** Immer `Manual Keep`.
- **Review-Record:** Immer `Review-Record`.
- **Calibration-Index:** Immer `Calibration-Index`.

#### N2 – Referenzintegritaet

- **Anhang-Referenzen:** Immer mit `Anhang X`.
- **Kapitel-Referenzen:** Immer mit `Kapitel X`.
- **Abschnitts-Referenzen:** Immer mit `Abschnitt X.Y`.
- **Keine relativen Pfadverweise.**

#### N3 – Datenvertragskohaerenz

- **Alle Artefakte:** `schema_version`, `created_at`, `updated_at`, `producer_version`.
- **Alle Hashes:** SHA256.
- **Alle States:** Atomar, mit Zeitstempel und Hash.
- **Alle Quarantaene-Faelle:** Mit Grund, Zeit, Hash nach `WORKFLOW_DATA/runtime/quarantine` kopieren.

#### N4 – Zustandsautomaten-Praezisierung

- Alle Ueberg aenge atomar und protokolliert.
- Rueckwaerts-Ueberg aenge nur bei Quarantaene.
- Blockierende Zustaende in Run-Summary melden.
- Pausierte Zustaende mit Zeitstempel, Grund und Hash protokollieren.

#### N5 – Kapitel-Querverweise

- Alle Kapitel konsistent nummeriert.
- Alle Anhaenge konsistent benannt.
- Querverweise immer mit Abschnitt/Anhang.
- Keine impliziten Referenzen.

#### N6 – Glossar-Vervollstaendigung

- Alle Begriffe im Glossar definiert.
- Neue Begriffe sofort ergaenzen.
- Begriffs aenderungen in CHANGELOG.md dokumentieren.

#### N7 – Anhang-Konsolidierung

- Thematisch konsistent, kein Duplikat.
- Alphabetische Reihenfolge.
- Konsistente Querverweise.

#### N8 – Stil- und Formatvereinheitlichung

- Ueberschriften als Markdown-Header.
- Listen mit Bindestrichen.
- Tabellen mit Header und Trennlinie.
- Codebl ocke mit Sprachangabe.
- Zitate mit `>`.

---

### Anhang M — Mindesttestliste

- Konfigurationsvalidierung.
- CLI-Hilfe.
- Unit-Tests.
- Integrationstests.
- Pfad-/ZIP-Sicherheit.
- Dependency-Scan.
- ARW-Archiv.
- Paralleler Scheduler.
- Abbruch vor/nach Phase-2-Transaktion.
- Ressourcenverhalten auf Ziel-NAS.
- Face-Backend.
- MANUAL_KEEP.
- Gewichtungsassistent.
- NAS-Pilot.

---

### Anhang N — Projektstruktur (GitHub-Repository)

#### Q1 – Repository-Uebersicht

Das GitHub-Repository enthaelt den vollstaendigen Code, die Dokumentation und die Konfiguration fuer den Synology Photo Workflow.

#### Q2 – Ordnerstruktur (Beispiel)

```text
synology-photo-workflow/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── CHANGELOG.md
├── Dockerfile
├── README.md
├── SECURITY.md
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── archives.py
│   ├── batch_state.py
│   ├── calibration.py
│   ├── cli.py
│   ├── clip_taste_adapter.py
│   ├── configuration.py
│   ├── culling.py
│   ├── face_adapter_yunet_sface_cpu.py
│   ├── face_backend.py
│   ├── face_cache.py
│   ├── family_recognition.py
│   ├── inventory.py
│   ├── locks.py
│   ├── manual_keep.py
│   ├── metadata.py
│   ├── phases.py
│   ├── photoworkflow.py
│   ├── planning.py
│   ├── reporting.py
│   ├── result_contract.py
│   ├── runtime.py
│   └── safety.py
├── config/
│   └── config.yaml
├── docker-compose.yml
├── docs/
│   └── MANUAL_DE.md
├── legacy/
│   ├── README.md
│   └── nas_photosort.sh
├── pyproject.toml
├── pytest.ini
├── requirements-clip.txt
├── requirements-dev.txt
├── requirements.txt
├── scripts/
│   ├── README.md
│   ├── dsm-acceptance-preflight.sh
│   ├── preflight.sh
│   ├── run-phase1.sh
│   ├── run-phase2.sh
│   └── run-workflow.sh
└── tests/
    ├── README.md
    ├── __init__.py
    ├── conftest.py
    └── integration/
```

#### Q3 – Datenablage

| Ordner/Datei | Zweck | Datenablage |
|--------------|-------|-------------|
| `config/config.yaml` | Konfiguration | Nur Konfiguration, keine Laufzeitdaten |
| `app/` | Quellcode | Nur Python-Code, keine Daten |
| `docs/` | Dokumentation | Nur Dokumente, keine Laufzeitdaten |
| `tests/` | Tests | Nur Testcode, keine Produktionsdaten |
| `scripts/` | Hilfsskripte | Nur Skripte, keine Daten |
| `legacy/` | Altlasten | Nur historische Dateien, keine aktiven Daten |
| `.github/workflows/` | CI/CD | Nur Pipeline-Definitionen |
| NAS | Workflow-Daten | Alle Laufzeitdaten |

#### Q4 – Wichtige Regeln

1. Git enthaelt nie Modellgewichte, private Bilder, Referenzen, Face-Crops, Embeddings, Laufzeitdaten, Caches, Logs oder Secrets.
2. NAS enthaelt alle Workflow-Daten und Konfiguration mit Produktionspfaden.
3. Docker-Container enthaelt nur Code und mountet NAS-Pfade.

---

### Anhang O — Skript-Anforderungen

#### R1 – Geltungsbereich

Diese Anforderung gilt fuer alle Skript-Dateien im Repository.

#### R2 – Struktur-Anforderungen

Jede Skript-Datei MUSS eine feste Struktur haben:

1. Header-Kommentar (6–10 Zeilen).
2. Abschnitts-Kommentare (2–3 Zeilen pro Abschnitt).
3. Funktions-Kommentare (3–5 Zeilen pro Funktion).
4. Einzeiler-Kommentare fuer komplexe Bedingungen.

#### R3 – Kommentar-Dichte und Lesbarkeit

- Header: 6–10 Zeilen.
- Jede Funktion: 3–5 Zeilen Kommentar.
- Jeder Abschnitt: 2–3 Zeilen Kommentar.
- Ca. 20 % Kommentare im Skript.
- Sprechende Namen, konsistente Formatierung, max. 80–100 Zeichen pro Zeile.

#### R4 – Beispiel-Header

```bash
#!/bin/bash
#
# Skript: scripts/run-phase1.sh
# Zweck: Fuehrt Phase 1 fuer einen Batch aus (Inventar, Culling, Metadaten)
# Autor: MaiTaiMa
# Erstellt: 2026-08-04
# Version: 1.0
# Requires: bash, docker, exiftool
# Usage: ./run-phase1.sh <batch-id>
#
# Aenderungsprotokoll:
#   2026-08-04 | v1.0 | Initiale Version
#
```

#### R5 – Beispiel-Abschnitt

```bash
# === Validierung: Pflichtargumente pruefen ===
# Zweck: Stellt sicher, dass alle erforderlichen Argumente uebergeben wurden
# Eingabe: $1 (BATCH_ID)
# Ausgabe: Fehlermeldung bei fehlendem Argument, Abbruch mit Exit-Code 1
if [ -z "$BATCH_ID" ]; then
    echo "Fehler: BATCH_ID ist erforderlich"
    echo "Usage: ./run-phase1.sh <batch-id>"
    exit 1
fi
```

#### R6 – Beispiel-Funktion

```bash
# create_manifest()
# Zweck: Erstellt Batch-Manifest mit Hashes fuer alle JPGs und ARWs
# Eingabe: $1 (Pfad zum Batch-Ordner)
# Ausgabe: manifest.json im Batch-Ordner
# Rueckgabe: 0 bei Erfolg, 1 bei Fehler
# Abhaengigkeiten: jq, sha256sum
create_manifest() {
    local batch_path="$1"
    local jpg_count=$(find "$batch_path" -name "*.jpg" | wc -l)
    local arw_count=$(find "$batch_path" -name "*.arw" | wc -l)
    cat > "$batch_path/manifest.json" <<EOF
{
    "batchid": "$BATCH_ID",
    "image_count": $jpg_count,
    "arw_count": $arw_count,
    "created_at": "$(date -Iseconds)"
}
EOF
    echo "Manifest erstellt: $batch_path/manifest.json"
    return 0
}
```

#### R7 – Validierung und Abnahme

- Header-Kommentar vorhanden?
- Abschnitts-Kommentare vorhanden?
- Funktions-Kommentare vorhanden?
- Ca. 20 % Kommentare?
- Sprechende Namen?
- Konsistente Formatierung?

Bei Fehlern: Skript ungueltig markieren, loggen, manuelle Korrektur.

#### R8 – Versionierung und Aenderungshistorie

- Jede Skript-Datei braucht Versionsnummer im Header.
- Jede Aenderung muss im Header dokumentiert werden.
- Jede Aenderung muss zusaetzlich im CHANGELOG.md dokumentiert werden.

---

### Anhang P — README-Anforderungen fuer Ordner

#### P4.1 Geltungsbereich

Gilt fuer alle README-Dateien im NAS-Workflow-Bereich:

- `PHOTO_WORKFLOW/README.md`
- `TEMP_SD/README.md`, `TEMP_IMAGES/README.md`, `TEMP_DONE/README.md`, `TEMP_ERROR/README.md`
- `MANUAL_KEEP/README.md`, `MANUAL_KEEP/inbox/README.md`, `MANUAL_KEEP/used/README.md`
- `WORKFLOW_DATA/README.md` und alle direkten Unterordner

#### P4.2 Pflichtfelder pro README

1. Zweck
2. Eingaben
3. Prozess
4. Ausgaben
5. Manuelle Aktionen
6. Lebenszyklus
7. Fehlerfaelle
8. Konfiguration (optional, falls relevant)

#### P4.3 Format und Umfang

- Markdown, klare Ueberschriften, Aufzaehlungen mit Bindestrichen.
- Mindestens 100, maximal 500 Woerter.
- Deutsch, technisch praezise, frei von Floskeln.
- Mindestens ein konkretes Beispiel.
- Keine externen URLs.

#### P4.4 Validierung

- Alle 8 Pflichtfelder vorhanden?
- Wortumfang eingehalten?
- Ein Beispiel enthalten?
- Keine externen URLs?
- Technische Korrektheit?

#### P4.5 Versionierung

- README braucht Versionsnummer im Header.
- Aenderungshistorie im CHANGELOG.md.
- Migration bei Struktur- oder Prozessaenderung.

#### P5 — Beispiel-README fuer TEMP_SD

```markdown
## TEMP_SD

### Zweck
Eingang fuer neue Kameraordner. Hier werden frische DCIM-Ordner (z. B. `100CANON`) abgelegt, bevor Phase 1 beginnt.

### Eingaben
- Nur frische Kameraordner
- Nur JPGs und ARWs im Originalzustand
- Abgelegt durch Mensch oder automatischen Import

### Prozess
Phase 1 liest von hier, normalisiert Datum, lagert ARWs aus, erzeugt Batch-Struktur und bewertet JPGs.

### Ausgaben
- Nach Phase 1: Batch wird nach `TEMP_IMAGES/` ueberfuehrt.

### Manuelle Aktionen
- Neue Kameraordner ablegen (erlaubt)
- Bestehende Batches veraendern (verboten)
- Dateien loeschen (verboten)

### Lebenszyklus
Ein Batch gilt als abgeschlossen, wenn Phase 1 erfolgreich nach `TEMP_IMAGES/` verschoben wurde.

### Fehlerfaelle
- Ungueltiger Ordnername: Ignorieren, Log-Eintrag, manuelle Pruefung erforderlich.
- Fehlende ARWs: Phase 1 setzt `failed_metadata`, Batch wandert nach `TEMP_ERROR/`.
- Beschaedigte Dateien: Phase 1 setzt `analysis_error`, Batch wird quaraentaenisiert.

### Konfiguration
- `paths.temp_sd`
- `workflow.batch_sort`
```

---

### Anhang Q — Referenzpool-Vertrag

#### Q1 — Geltungsbereich

Dieser Vertrag gilt fuer:

- **Face-Referenzpools:** `WORKFLOW_DATA/faces/<slug>/` (je bekannte Person)
- **Geschmacks-Referenzpool:** `WORKFLOW_DATA/samples/`

Nicht gueltig fuer Manual Keep, technische Culling-Bilder ausserhalb der konfigurierten Modellbasis und unbekannte Gesichter.

#### Q2 — Ordnerstruktur

```text
<pool_root>/
├── reference/
├── new_*/
└── selection.json
```

- Face: `new_faces/`, Face-Crops.
- Geschmack: `new_refs/`, Ganzbilder.

#### Q3 — `selection.json`

Pflichtfelder:
- `schema_version`
- `pool_type`
- `slug` (nur Face)
- `updated_at`
- `selection_fingerprint`
- `pool_build_id`
- `rank_digits`
- `limits`
- `images`

Verboten: Embeddings, Bildbytes, Face-Crops oder andere binaere Daten.

#### Q4 — Bild-Metadaten

Pflichtfelder:
- `source_id`
- `batchid`
- `path` oder `crop_source`
- `status`
- `quality_score`
- `pool_utility_score` oder `candidate_utility_score`
- `pool_rank`
- `approved_at`

Face-spezifisch: `bounding_box`, `face_confidence`, `original_path`.

Geschmack-spezifisch: `base_score`.

#### Q5 — Kapazitaetsgrenzen

- `max_active`: Hard Limit
- `max_new`: Hard Limit
- `max_new_per_batch`: Hard Limit
- `min_active`: Soft Limit
- `target_active`: Ziel

#### Q6 — Dynamische Stellenzahl

- `rank_digits = max(1, ceil(log10(n + 1)))`
- Dateinamen: `{rank_zfill}__{original_name}_{suffix}.{ext}`
- Aufsteigend sortiert: bester Nutzen zuerst.

#### Q7 — Pool-Rebuild

Ausloeser:
- Verschiebung von `new_*` nach `reference/`
- Entfernen aus `reference/`
- Aenderung von Dateien, Modellen, Vorverarbeitung oder Fingerprint
- Inkonsistenz zwischen `selection.json` und Ordnerinhalt

Schritte:
1. Anzahl aktiver Dateien zaehlen.
2. `rank_digits` berechnen.
3. Nutzenranking berechnen.
4. Temporaere Dateien erzeugen.
5. Finale Namen setzen.
6. Neue `selection.json` validieren.
7. `selection.json` atomar ersetzen.
8. `rank_digits` und `pool_build_id` schreiben.

#### Q8 — Datenschutz

- Embeddings duerfen nie persistent gespeichert werden.
- Face-Crops sind die einzige persistente Form von Gesichtsdaten.
- Originalbilder bleiben unveraendert.

#### Q9 — Abnahmekriterien

- Rebuild bei neuem Geschmacksbild.
- Rebuild pro Person bei neuem Gesichtsbild.
- Atomare Umbenennung ohne Dateiverlust.
- Keine Vorschlaege ueber `max_new_per_batch`.
- Keine automatischen Loeschungen bei `max_new` oder `max_active`.
- Keine Embeddings in `selection.json`.
- Rangzahl am Dateianfang.
- Dynamische Stellenzahl.
- Sortierung im Dateimanager nach Rang.

---

### Anhang R — Konfigurations-Referenz

#### R1 — `reference_pools.common`

| Parameter | Typ | Sinnvoller Bereich | Empfohlener Startwert | Beschreibung |
|-----------|-----|-------------------|----------------------|--------------|
| `max_active` | int | 30–200 | 100 | Maximale aktive Referenzen pro Pool. |
| `min_active` | int | 20–50 | 30 | Minimale aktive Referenzen pro Pool. |
| `target_active` | int | 30–100 | 50 | Zielanzahl aktiver Referenzen. |
| `max_new` | int | 10–50 | 20 | Maximale offene Vorschlaege pro Pool. |
| `max_new_per_batch` | int | 3–10 | 5 | Maximale offene Vorschlaege pro Batch. |

#### R2 — `reference_pools.taste`

| Parameter | Typ | Sinnvoller Bereich | Empfohlener Startwert | Beschreibung |
|-----------|-----|-------------------|----------------------|--------------|
| `min_quality_score` | float (0.0–1.0) | 0.6–0.8 | 0.70 | Mindestqualitaet fuer Vorschlaege. |
| `max_redundancy` | float (0.0–1.0) | 0.85–0.95 | 0.90 | Maximale Redundanz. |
| `base_score_pool_size` | int | 30–100 | 50 | Separate Modellbasis fuer technisches Culling. |

#### R3 — `reference_pools.faces`

| Parameter | Typ | Sinnvoller Bereich | Empfohlener Startwert | Beschreibung |
|-----------|-----|-------------------|----------------------|--------------|
| `min_quality_score` | float (0.0–1.0) | 0.6–0.8 | 0.70 | Mindestqualitaet fuer Vorschlaege. |
| `max_redundancy` | float (0.0–1.0) | 0.90–0.98 | 0.95 | Maximale Redundanz. |
| `crop_size` | int | 128–512 | 256 | Crop-Groesse in Pixeln. |
| `min_face_size` | int | 64–256 | 128 | Mindest-Groesse eines Gesichts. |

---

### Anhang S — Konsistenzpruefung und Recovery

#### S1 — Konsistenzpruefung

- Dateiliste lesen.
- `selection.json` lesen.
- Vergleich: jeder Eintrag muss einer Datei entsprechen; jede Datei muss einem Eintrag entsprechen.
- Fehlende Dateien aus `selection.json` entfernen.
- Neue Dateien in `selection.json` aufnehmen.

#### S2 — Recovery

- Fehlende Dateien: Eintrag entfernen.
- Neue Dateien: Eintrag aufnehmen (`status: unknown`, keine Scores).
- `reference/`-Aenderung: Rebuild ausloesen.

---

### Anhang T — Migration v9.8 → v10.1

#### T1 — Migrationsschritte

1. Ordnerstruktur anpassen.
2. Dateinamen im neuen Format umbenennen.
3. Konfiguration um `reference_pools` ergaenzen.
4. Rebuild ausloesen.

#### T2 — Abwaertskompatibilitaet

- Alte `selection.json`-Dateien werden migriert.
- Alte Dateinamen werden migriert.

---
