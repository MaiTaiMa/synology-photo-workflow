<!--
Synology Photo Workflow – Spezifikation v9.9 (harmonisiert)
Datei: docs/Synology-Photo-Workflow_Spezifikation_v9-9_harmonisiert.md
Mitentwickler: MaiTaiMa (in Zusammenarbeit mit Perplexity AI)
Erstellt: 2026-08-04
Projektversion: 9.9
Status: Harmonisierte Fassung zur Konsolidierung von v9.8
-->

# Synology Photo Workflow – Spezifikation v9.9

**Status:** Verbindliche, alleinstehende Spezifikation fuer den sicheren, wiederaufnehmbaren Synology Photo Workflow (harmonisierte Fassung).

**Zielsetzung:** Dieses Dokument ist die alleinige normative Quelle fuer Entwicklung, Betrieb, Test und Aenderungen. Es ersetzt alle frueheren Versionen dieser Spezifikation. Abweichende aeltere Fassungen oder Teildokumente sind nicht mehr gueltig.

---

## 0. Metadaten und Geltungsbereich

### 0.1 Dokumentenmetadaten

| Feld | Wert |
|------|------|
| Version | 9.9 |
| Datum | 2026-08-04 |
| Status | Harmonisiert (alle AP1–AP5 umgesetzt) |
| Vorgaenger | v9.8 |
| Aenderungs-Historie | Siehe Kapitel 6.4 |

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
3. **Nutzen:** Jede Funktion muss Fotos besser vorsortieren, Nachvollziehbarkeit oder Betriebssicherheit erhoe hen.
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
- Kalibrierung bezieht bestaetigte Review-Records und wirkt auf Reports und Empfehlungen, niemals selbst aendig auf Automatikflags.

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
    "producer_version": "9.9"
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
- **Zweck:** Liefert ein moderates positives Signal fuer bewusst gepflegte, bekannte Personen. **Keine** allgemeine Gesichtserkennung, kein Clustering unbekannter Gesichter.
- **Ablauf:**
  1. Backend (Registry-basiert, Standard `opencv_yunet_sface_cpu`) erzeugt Embedding.
  2. Vergleich gegen aktive Referenzen einer Person (`faces/<slug>/reference/` mit `selection.json` Status `active`).
  3. Nur bei eindeutigem Match (Schwelle + Sicherheitsmarge zum Zweitbesten) wird `family_score` gesetzt und ein Personentag vergeben.
  4. Klare Treffer erzeugen Vorschlaeg in `faces/<slug>/new_faces/`, die ein Mensch durch Kopieren nach `reference/` bestaetigt.

**Schutzgrenzen:**
- Bilder, Bildbytes, Face-Crops, Referenzbilder sowie Bild-/Face-/CLIP-Embeddings sind ausschliesslich fluechtig im RAM zul aessig und duerfen nie in JSON, Cache, Log, Manifest, CSV, Metadaten oder Report persistiert werden.
- Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt oder als Referenz aktiviert werden.
- Modellgewichte, private Bilder, Caches, Logs, Laufzeitdaten und Secrets duerfen nie in Git eingecheckt werden.

**Face-Backend-Vertrag:** Jedes Backend MUSS eine Registry-ID, einen Adapter-Namen, einen Modellhash, einen Provider-Namen, eine Vorverarbeitungs-Pipeline, eine Metrik und einen Auswahlfingerprint bereitstellen. `family_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 oder `None`.

### 4.6 Manual Keep

- **Status:** Pflicht.
- **Zweck:** Ordnet extern (z. B. per WhatsApp) vorab ausgewaehlte, oft komprimierte/kleine Bilder ihrem Original im aktuellen Batch zu und erzwingt fuer dieses `keep`.
- **Ablauf:**
  1. Zweistufig: schneller aufloesungsrobuster Vorfilter (Seitenverhaeltnis, Perceptual Hash).
  2. Danach strenge normalisierte Endpruefung (Verifikationsscore auf EXIF-korrigierten, gleich skalierten Bildern).
  3. Match nur bei Schwelle **und** ausreichendem Abstand zum Zweitbesten.
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

## 5. Betrieb, Konfiguration, Reporting, Abnahme

### 5.1 Konfiguration

- **Schema:** YAML mit strikter Validierung; unbekannte Schluessel sind Fehler (ausser `extensions`).
- **Fingerprint:** Effektive Konfiguration wird mit SHA256-Fingerprint im Run dokumentiert.
- **Sicherheit:** Keine Geheimnisse, keine Produktionspfade in Git.
- **Config-Schluessel:** Durchgaengig snake_case (z. B. `manual_keep`, `face_backend`, `batch_state`, `work_unit_mode`).

**Config-Kommentierung:** Jede Variable MUSS mit 5 Punkten kommentiert sein (Zweck, Typ/Wertebereich, Standardverhalten, Sicherheits-/Performance-Wirkung, mindestens eine sinnvolle Alternative). Jeder Logikblock MUSS einen einleitenden Block-Kommentar besitzen (fachlicher Zweck, typische Nutzung, Auswirkungen auf Workflow, Sicherheits-/Performance-Aspekte, 3–6 Zeilen).

### 5.2 Betrieb

- **Scheduler:** Container mit persistentem NAS-Mount starten; globaler Lock verhindert parallele Laeufe.
- **Fehlerisolation:** Ein defekter Batch wird quaraentaenisiert statt den ganzen Lauf zu stoppen.
- **Ressourcenverhalten:** Auf Ziel-NAS (RAM, CPU, I/O, Zeitbudget) dokumentieren.
- **Not-Stop:** Bei Zeitbudget oder SIGTERM keinen neuen teuren Schritt beginnen; sicheren aktuellen Schritt abschliessen, Status `paused` atomar schreiben, kontrolliert beenden.

### 5.3 Reporting

- **Status:** Pflicht.
- **Zweck:** Macht jedem Lauf auf einen Blick klar, was passiert ist und was der Mensch tun muss.
- **Ablauf:**
  1. JSON-Run-Summary erzeugen.
  2. Kurze Scheduler-Ausgabe schreiben.
  3. `SAVE/culling_scores.csv` erstellen.
  4. Persistente Logs fuehren.
  5. Priorisierte `user_actions_required` mit Severity `info`/`warning`/`blocking` ausgeben.

**Reporting-Vertrag:** Die Run-Summary MUSS `run_id`, `timestamp`, `config_fingerprint`, `automation_mode`, `batch_count`, `image_count`, `keep_count`, `review_count`, `reject_count`, `error_count`, `blocking_count`, `user_actions_required` enthalten.

### 5.4 Automatikstufen

| Stufe | Modus | System darf | Mensch muss | Normstatus |
|-------|-------|-------------|-------------|------------|
| 1 | `assisted_review` | Phase 1, Reporting, Vorschlaeg | Phase-2-Uebergabe und Referenzaktivierung freigeben | **Aktiv normativ (Standard)** |
| 2 | `automatic_phase2` | Phase 2 nach expliziten Gates | Referenzaktivierung freigeben | Optional mit Gates |
| 3 | `automatic_candidates` | Kandidaten priorisieren/verwalten | Referenzaktivierung freigeben | Optional mit Gates |
| 4 | `reference_activation` | Nur spaeterer Erweiterungspunkt | Audit und explizite Freigabe | **Nicht normativ / spaeterer Ausbau** |

Stufe 1 ist Standard. Stufe 2 erfordert gleichzeitig: `automation.mode`, `automatic_phase2_enabled=true`, `workflow.phase_execution=phase1_then_phase2` sowie dokumentierte NAS-Abnahme und Kalibrierungsbereitschaft. Stufe 3 erfordert zusaetzlich `automatic_candidates_enabled=true`. Stufe 4 ist experimental, standardmaessig verboten und braucht eine eigene spaetere Anforderung.

### 5.5 Abnahme

Die Abnahme ist erst erfuellt, wenn alle Faelle in Anhang E automatisiert reproduzierbar bestehen und der Ziel-NAS-Pilot dokumentiert ist. Unit- oder Containertests ersetzen den NAS-Piloten nicht.

### 5.6 Ordnung und Sauberkeit

- **Altlasten, tote Dateien, ungenutzte Ordner/Module:** Muessen entfernt werden. Wenn sie bewusst erhalten bleiben, MUessen sie als `DEPRECATED` oder `LEGACY` markiert sein, mit Header-Kommentar (Zweck, Entstehung, Migration) und in Kapitel 6.2 dokumentiert sein.
- **Doppelstrukturen:** Parallele Implementierungen, mehrere Config-Varianten ohne klaren Zweck, mehrere Doku-Pfade sind unzulaessig, es sei denn, sie haben einen dokumentierten fachlichen oder technischen Zweck. Zweck, Abgrenzung und Lebenszyklus muessen in Kapitel 6.2 dokumentiert sein.
- **DEPRECATED/LEGACY-Markierung und Dokumentation:** Wenn alte Pfade, Module, Config-Bl ocke oder Doku-Inhalte bewusst erhalten bleiben, muessen sie klar von der aktiven Logik abgegrenzt sein (z. B. `legacy/`, `deprecated/`, `experimental/`), mit Header-Kommentaren versehen sein und in Kapitel 6.2 dokumentiert sein.

---

## 6. Glossar, Migration, Referenzen, Historie

### 6.1 Glossar

| Begriff | Bedeutung |
|---------|-----------|
| batchid | Kameraordner mit unveraenderlicher `batchid`, Eingangsmanifest und zentraler Zustandsdatei. |
| WorkUnit | Interne, sicher fortsetzbare Portion eines physischen Batches. |
| Face-Backend | Explizit registrierter Adapter fuer bekannte Gesichter. |
| Manual Keep | Kontrollierter Eingang fuer externe, vorab ausgewaehlte JPGs (inbox, used). |
| Review-Record | Unveraenderlicher Record einer menschlichen Endentscheidung. |
| Calibration-Index | Index aus bestaetigten Review-Records fuer Gewichtungsassistent. |
| Archivaktivierung | Atomarer Wechsel einer vollstaendig validierten temporaeren ZIP zur finalen ZIP. |
| Quarantaene | Fehlerhafte Artefakte nach `WORKFLOW_DATA/runtime/quarantine` mit Manifest; blockierend melden. |
| Fingerprint | SHA256-basierter Identifier fuer Konfiguration, Cache, Backend, Modell, Auswahl. |
| Hash | SHA256 fuer ARW, JPG, ZIP, Manifest, State; Hash vor/nach Operation pruefen. |

### 6.2 Migration

- **Alte Pfade, Module, Config-Bl ocke, Doku-Inhalte:** Klar von aktiver Logik abgrenzen; `DEPRECATED`/`LEGACY` markieren; in diesem Kapitel dokumentieren.
- **Lebenszyklus:** Fuer jedes `DEPRECATED`/`LEGACY`-Element: Zweck, Entstehung, Migration, geplanter Removal-Zeitpunkt.

### 6.3 Begriffs- und Referenzindex

- **Begriffindex:** Alle Begriffe mit erster Erwaehnung, Glossar-Referenz und relevanten Abschnitten.
- **Referenzindex:** Alle Anhaenge und Kapitel mit stabiler Referenz (z. B. "siehe Abschnitt X.Y", "siehe Anhang X").
- **Querverweisregeln:** Keine impliziten Referenzen ("siehe oben", "siehe unten"); immer mit Abschnitt/Anhang zitieren.

### 6.4 Aenderungs-Historie und Versionierung

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|----------|
| 9.9 | 2026-08-04 | MaiTaiMa + Perplexity AI | Harmonisierte Fassung (AP1–AP5): Begriffe, Regeln, Schutzgrenzen konsolidiert; Redundanzen entfernt; neue Struktur (6 Hauptkapitel + Anhaenge A–P). |
| 9.8 | 2026-08-03 | MaiTaiMa + Perplexity AI | Rechtschreib- und Formatkorrekturen, neuer Abschnitt "Architektur und Compliance", Aktualisierung der Aenderungs-Historie. |
| 9.7 | 2026-08-04 | MaiTaiMa + Perplexity AI | AP5-Umsetzung (Finalisierung, Konsolidierung, Querverweise, Beispiele, Fehlerfaelle, Konfigurations-Beispiel, Migration, Versionierung, Release-Checkliste, Abnahme-Protokoll, Aenderungs-Historie). |

**Versionierungs-Regeln:**
- **Major-Version** (z. B. 9.x): Breaking Changes, neue Kernfunktionen, geaenderte Datenvertraege.
- **Minor-Version** (z. B. x.4): Neue Features, Ergaenzungen, Praezisierungen ohne Breaking Changes.
- **Patch-Version** (z. B. x.x.1): Fehlerkorrekturen, kleinere Verbesserungen, keine neuen Features.

---

## Anhaenge

- **Anhang A — Normative Datenvertraege**
- **Anhang B — Metadaten, CSV und Manifest**
- **Anhang C — Face-Backend-Vertrag**
- **Anhang D — Referenzkonfiguration**
- **Anhang E — Abnahme ACC-01 bis ACC-15**
- **Anhang F — CLI, Exit-Codes, Module**
- **Anhang G — Konfigurationsvertrag**
- **Anhang H — Archivvertrag**
- **Anhang I — Sample-Kapazitaetsvertrag**
- **Anhang J — Reporting, Deployment**
- **Anhang K — Qualitaet, CI**
- **Anhang L — Konsistenz- und Einheitlichkeitsregeln**
- **Anhang M — Mindesttestliste**
- **Anhang N — Projektstruktur (GitHub-Repository)**
- **Anhang O — Skript-Anforderungen**
- **Anhang P — README-Anforderungen fuer Ordner**

*(Die vollstaendigen Anhaenge entsprechen den Inhalten aus v9.8, sind aber bereinigt um Redundanzen und an die neue Struktur angepasst.)*

---

**Ende der Spezifikation v9.9 (harmonisiert)**