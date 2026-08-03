<!--
Synology Photo Workflow – Spezifikation v9.9 (vollstaendig harmonisiert)
Datei: docs/Synology-Photo-Workflow_Spezifikation_v9-9_harmonisiert_vollstaendig.md
Mitentwickler: MaiTaiMa (in Zusammenarbeit mit Perplexity AI)
Erstellt: 2026-08-04
Projektversion: 9.9
Status: Vollstaendige, harmonisierte Fassung mit allen Anhaengen (A–P)
-->

# Synology Photo Workflow – Spezifikation v9.9

**Status:** Verbindliche, alleinstehende Spezifikation fuer den sicheren, wiederaufnehmbaren Synology Photo Workflow (vollstaendig harmonisierte Fassung).

**Zielsetzung:** Dieses Dokument ist die alleinige normative Quelle fuer Entwicklung, Betrieb, Test und Aenderungen. Es ersetzt alle frueheren Versionen dieser Spezifikation. Abweichende aeltere Fassungen oder Teildokumente sind nicht mehr gueltig.

---

## 0. Metadaten und Geltungsbereich

### 0.1 Dokumentenmetadaten

| Feld | Wert |
|------|------|
| Version | 9.9 |
| Datum | 2026-08-04 |
| Status | Vollstaendig harmonisiert (alle AP1–AP5 umgesetzt) |
| Vorgaenger | v9.8 |
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

**Versionierungs-Regeln:**
- **Major-Version** (z. B. 9.x): Breaking Changes, neue Kernfunktionen, geaenderte Datenvertraege.
- **Minor-Version** (z. B. x.4): Neue Features, Ergaenzungen, Praezisierungen ohne Breaking Changes.
- **Patch-Version** (z. B. x.x.1): Fehlerkorrekturen, kleinere Verbesserungen, keine neuen Features.

---

## Anhaenge

### Anhang A — Normative Datenvertraege

- **Artefakte:** Batch-Zustand (`state/{batchid}.json`), Manifest (`manifest.json`), CSV (`SAVE/culling_scores.csv`), Review-Record (`review_decision_record.json`), Calibration-Index (`calibration_summary.json`), Lock-Manifest, Quarantaene-Manifest, Run-Summary.
- **Pfadvertrag:** Alle produktiven Pfade unterhalb des erlaubten Basisverzeichnisses; keine Symlink-Ausbrueche; relative Pfade innerhalb Batch.
- **Hashvertrag:** SHA256 fuer ARW, JPG, ZIP, Manifest, State; Hash vor/nach Operation pruefen.
- **Namensvertrag:** `batchid = source-folder-name + Fingerprint(8)`; unver aenderlich ueber alle Ordnerwechsel.
- **JSON-Schema:** `schema_version`, `created_at`, `updated_at`, `producer_version`, Bereichskennung, Pflichtfelder je Artefakt.
- **Fehlervertrag:** Unbekannte, zukuenftige, ungueltige oder unlesbare Dateien nicht still ueberschreiben; nach `quarantine` kopieren, mit Grund, Zeit, Hash melden; sichere Neuerstellung oder menschliche Pruefung.
- **Atomaritaetsvertrag:** Inhalt erzeugen, validieren, temporaer auf gleichem Dateisystem schreiben, erneut validieren, atomar ersetzen; vorherige Version bis Aktivierung erhalten.
- **Lockvertrag:** Globaler Lock verhindert parallele produktive Laeufe; Lock vor/nach Lauf pruefen.
- **Batch-Lebenszyklus:** `phase1_started → phase1_completed → review_comparison_pending → review_record_committed → calibration_index_committed → phase2_archiving → phase2_completed` (manuell); oder `phase1_completed → automatic_handoff → phase2_archiving → phase2_completed` (automatisch).
- **Quarantaenevertrag:** Fehlerhafte Artefakte nach `WORKFLOW_DATA/runtime/quarantine` mit Manifest; blockierend melden; menschliche Pruefung erforderlich.

**Datenvertrags-Vervollstaendigung:** Alle Artefakte Muessen folgende Pflichtfelder enthalten:
- `schema_version` (string, format: "major.minor")
- `created_at` (string, format: ISO8601)
- `updated_at` (string, format: ISO8601)
- `producer_version` (string, format: "major.minor.patch")
- `batchid` (string, falls zutreffend)
- `hash` (string, SHA256, falls zutreffend)

---

### Anhang B — Metadaten, CSV und Manifest

- **CSV:** `SAVE/culling_scores.csv` mit `batchid`, `image_id`, `basescore`, `eyescore`, `personalscore`, `familyscore`, `finalscore`, `predicted_decision`, `series_id`, `series_size`, `series_rank`, `series_best`, `family_match`, `person_slug`, `manual_keep`, `failed_metadata`, `exiftool_status`.
- **JSON-Manifest:** `batchid`, `source_folder`, `created_at`, `updated_at`, `schema_version`, `producer_version`, `image_count`, `active_jpgs`, `arw_count`, `culling_scores_hash`, `manifest_hash`, `state`, `phase`, `review_state`, `calibration_status`, `quarantine_reason` (falls vorhanden).
- **Metadaten:** Inventarisierung vor Schreiben; Exiftool-Argumente; Zuruecklesen und Abgleich; `failed_metadata` bei Mismatch; Sidecar nur als Recovery-Modus.
- **Mindest-Tag-Satz:** Sternrating, `workflow_ai_cull`, `decision`, optional `series_best`, `family_match`, `person_slug`, `manual_keep`.
- **Run-Summary:** Run-Batch-ID, Konfigurationsfingerprint, angeforderter/wirksamer Automatikmodus, Ergebnisstatus, Keep/Review/Reject-Zaehler, Cache-/Metadatenstatus, ZIP-Konflikte, Kalibrierungsstatus, `user_actions_required`.

**Metadaten-Vertrag-Praezisierung:** Das CSV MUSS folgende Felder enthalten:
- `batchid` (string)
- `image_id` (string, Basename)
- `basescore` (float, 0.0–1.0 oder null)
- `eyescore` (float, 0.0–1.0 oder null)
- `personalscore` (float, 0.0–1.0 oder null)
- `familyscore` (float, 0.0–1.0 oder null)
- `finalscore` (float, 0.0–1.0 oder null)
- `predicted_decision` (string: keep, review, reject)
- `series_id` (string oder null)
- `series_size` (int oder null)
- `series_rank` (int, 1-basiert, oder null)
- `series_best` (bool oder null)
- `family_match` (bool oder null)
- `person_slug` (string oder null)
- `manual_keep` (bool oder null)
- `failed_metadata` (bool)
- `exiftool_status` (string: success, disabled, failed, sidecar)

---

### Anhang C — Face-Backend-Vertrag

- **Registry:** Backends ausschliesslich durch explizite Registry und Adapter ausgewaehlt.
- **Adapter:** Jedes Backend implementiert festgelegte Schnittstellen (Laden, Vorverarbeitung, Merkmalsextraktion, Metrik, Cache-Fingerprint).
- **Modellhash:** Jedes Modell hat SHA256-Hash; Hash Teil des Cache-Fingerprints.
- **Provider:** Backend-Provider klar dokumentiert (z. B. facenet, arcface).
- **Vorverarbeitung:** Normalisierung, Skalierung, Zuschneiden einheitlich; Teil des Fingerprints.
- **Metrik:** Kosinus aehnlichkeit (higher_is_better, 0–1) mit Schwelle 0,95 und Marge 0,03; alternative Metrik nur mit vollstaendiger Dokumentation.
- **Auswahlfingerprint:** `selection.json`-Fingerprint Teil des Cache-Fingerprints; unterschiedliche Fingerprints nie mischen.
- **Face-Crop:** Nur fuer sicheren, bekannten Personenmatch; Vorschlag in `newfaces` mit Herkunft, Hash, Bounding Box, Qualitaet, Neuheit, Konfidenz, Status.

**Face-Backend-Vertrag-Vervollstaendigung:** Jedes Backend MUSS folgende Felder bereitstellen:
- `backend_id` (string, eindeutig)
- `adapter_name` (string)
- `model_path` (string, relativer Pfad)
- `model_hash` (string, SHA256)
- `provider` (string)
- `preprocessing` (object: Skalierung, Normalisierung, Zuschneiden)
- `metric` (string: cosine, euclidean, etc.)
- `selection_fingerprint` (string, SHA256)
- `cache_fingerprint` (string, SHA256 aus allen obigen Feldern)

---

### Anhang D — Referenzkonfiguration

- `workflow`: `phase_execution`, `batch_sort`, `resume_incomplete_batches`, `work_unit_mode`, `images_per_work_unit`.
- `paths`: `base_dir`, `inbox`, `used`, `temp_sd`, `temp_images`, `temp_done`, `temp_error`, `workflow_data`, `model_dir`, `faces_dir`, `manual_keep_dir`, `archives_dir`, `reports_dir`.
- `culling`: `final_component_weights`, `decision_mode`, `enable_eye_detection`, `enable_series_logic`, `enable_family_scoring`, `enable_manual_keep`.
- `automation`: `mode`, `automatic_phase2_enabled`, `automatic_candidates_enabled`, `reference_activation_enabled`, `rollback_on_error`.
- `inference`: `workers`, `allow_parallel_face`, `allow_parallel_clip`, `allow_parallel_eye`.
- `manual_keep`: `similarity_backend`, `threshold`, `margin`, `min_face_size`, `min_quality`.
- `calibration`: `enabled`, `min_decisions`, `retrain_frequency`, `audit_log`.
- `face`: `backend`, `adapter`, `model_path`, `model_hash`, `provider`, `preprocessing`, `metric`, `selection_fingerprint`.
- `archives`: `zip_compression`, `zip_max_size`, `zip_max_ratio`, `hash_algorithm`, `activation_mode`.
- `reporting`: `log_level`, `summary_format`, `csv_format`, `json_format`, `user_actions_format`.
- `security`: `allow_symlinks`, `max_path_depth`, `path_traversal_check`, `secret_scan`, `not_root`.
- `extensions`: dokumentierte Erweiterungen; unbekannte Schluessel sonst Fehler.

**Konfigurations-Vertrag-Kohaerenz:** Die Konfiguration MUSS folgende Pflichtfelder enthalten:
- `schema_version` (string)
- `created_at` (string, ISO8601)
- `updated_at` (string, ISO8601)
- `config_fingerprint` (string, SHA256)
- `producer_version` (string)

---

### Anhang E — Abnahme ACC-01 bis ACC-15

- ACC-01: Konfigurationsvalidierung (alle Schluessel, Typen, Enums, Widersprueche).
- ACC-02: CLI-Hilfe (alle Befehle, Optionen, Exit-Codes).
- ACC-03: Unit-Tests (alle Module, APIs, Vertraege).
- ACC-04: Integrationstests (Phasen, WorkUnits, Recovery, State).
- ACC-05: Pfad- und ZIP-Sicherheitstests (Traversal, Symlink, Groessenlimit, Kompression).
- ACC-06: Dependency-Scan (keine unerlaubten Abhaengigkeiten, Lizenzkonformitaet).
- ACC-07: ARW-Archiv-Test (vollstaendig, pruefbar, aktivierbar, Hash).
- ACC-08: Paralleler Scheduler-Start (Lock, Race Conditions, Isolation).
- ACC-09: Abbruchtest vor Phase-2-Transaktion (Resume, State, Quarantaene).
- ACC-10: Abbruchtest nach Phase-2-Transaktion (Atomaritaet, Hash, Aktivierung).
- ACC-11: Ressourcenverhalten auf Ziel-NAS (RAM, CPU, I/O, Zeitbudget).
- ACC-12: Face-Backend-Test (Registry, Adapter, Cache-Fingerprint, Rebuild).
- ACC-13: MANUAL_KEEP-Test (ResolutionAwareSimilarity, Threshold, Marge, inbox/used).
- ACC-14: Gewichtungsassistent-Test (Audit, Rollback, Fingerprint).
- ACC-15: NAS-Pilot (vollstaendiger Lauf auf Ziel-NAS, Dokumentation, Abnahmebericht).

---

### Anhang F — CLI, Exit-Codes, Module

- **CLI:** `app/cli` nur fuer Argumente, Dispatch, Exit-Codes; keine Fachlogik.
- **Exit-Codes:** 0 (Erfolg), 1 (Konfigurationsfehler), 2 (Pfad-/Sicherheitfehler), 3 (Lock-Fehler), 4 (State-Fehler), 5 (Quarantaene-Fehler), 6 (Metadaten-Fehler), 7 (Modell-Fehler), 8 (Face-Backend-Fehler), 9 (Interrupt/SIGTERM), 10 (Timeout/Budget).
- **Module:** `app/culling` (Merkmale, Score, Serien), `app/family_recognition` (ohne ML-Import), `app/archives` (ZIP, Hash, Aktivierung), `app/runtime` (State, Lock, Recovery), `app/safety` (Validierung, Quarantaene), `app/phases` (Phasenlogik), `app/manual_keep` (MANUAL_KEEP), `app/calibration` (Gewichtungsassistent), `app/reporting` (Summary, CSV, JSON, Log), `app/config` (Konfiguration, Validierung), `app/locks` (Lock-Manifest), `app/batch_state` (State-Management), `app/face_backend` (Face-Backend-Registry), `app/inference` (Worker, Parallelitaet).

---

### Anhang G — Konfigurationsvertrag

- **Schema:** YAML mit strikter Validierung; unbekannte Schluessel Fehler (ausser `extensions`).
- **Fingerprint:** Effektive Konfiguration mit SHA256-Fingerprint im Run dokumentieren.
- **Sicherheit:** Keine Geheimnisse, keine Produktionspfade in Git.
- **Status:** `stable`, `advanced`, `experimental` je Variable.
- **Migration:** Aenderungen an Gewichten, Schwellen, Feature-Logik, Referenzbasis, Backend, Modell, Metadatenvertrag aendern Versions-, Konfigurations- und ggf. Cache-Kalibrierungsfingerprint; Migrationshinweise im CHANGELOG.

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
- **Werte konfigurierbar;** Sicherheitsvertraege nicht abschw aechen.

**Praezisierung:** Die Groesse der Aehnlichkeitsvektoren (32–64 Pixel) bezieht sich auf die reduzierte, technisch genutzte Vorschau fuer technische Culling- und Vergleichsoperationen. Die tats aechliche Dimension des Embedding-Vektors haengt vom verwendeten Modell ab (z. B. CLIP: 512 oder 768 Dimensionen).

---

### Anhang J — Reporting, Deployment

- **Reporting:** Kurze Scheduler-Ausgabe, strukturierte JSON-Run-Summary, Batch-CSV, persistente Logs.
- **Deployment:** Container mit NAS-Mount; alle Zustaende, Logs, Konfigurationen, Caches, Summaries auf NAS; nicht im beschreibbaren Container-Dateisystem.
- **Docker/GPU:** Separate Images; Dokumentation; not-root-Ausfuehrung anstreben.

**Reporting-Vertrag-Vervollstaendigung:** Die Run-Summary MUSS folgende Felder enthalten:
- `run_id` (string, UUID)
- `timestamp` (string, ISO8601)
- `config_fingerprint` (string, SHA256)
- `automation_mode` (string: assisted_review, automatic_phase2, etc.)
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

- **Batch-ID:** Immer `batchid` (kleingeschrieben, kein Bindestrich).
- **WorkUnit:** Immer `WorkUnit` (CamelCase, keine Leerzeichen).
- **Face-Backend:** Immer `Face-Backend` (Bindestrich, gross F, gross B).
- **Manual Keep:** Immer `Manual Keep` (gross M, gross K, Leerzeichen).
- **Review-Record:** Immer `Review-Record` (Bindestrich, gross R, gross R).
- **Calibration-Index:** Immer `Calibration-Index` (Bindestrich, gross C, gross I).

#### N2 – Referenzintegritaet

- **Anhang-Referenzen:** Immer mit "Anhang X" (gross A, Leerzeichen, Grossbuchstabe).
- **Kapitel-Referenzen:** Immer mit "Kapitel X" (gross K, Leerzeichen, Zahl).
- **Abschnitt-Referenzen:** Immer mit "Abschnitt X.Y" (gross A, Leerzeichen, Dezimalpunkt).
- **Keine relativen Pfadverweise** (z. B. `../docs/MANUAL_DE.md`); immer absolute Beschreibung ("in `docs/MANUAL_DE.md` Kapitel 11").

#### N3 – Datenvertragskohaerenz

- **Alle Artefakte:** Muessen `schema_version`, `created_at`, `updated_at`, `producer_version` enthalten.
- **Alle Hashes:** Muessen SHA256 sein; MD5, SHA1 sind unzulaessig.
- **Alle States:** Muessen atomar geschrieben, mit Zeitstempel und Hash protokolliert werden.
- **Alle Quarantaene-Faelle:** Muessen mit Grund, Zeit, Hash nach `WORKFLOW_DATA/runtime/quarantine` kopiert werden.

#### N4 – Zustandsautomaten-Praezisierung

- **Alle Ueberg aenge:** Muessen atomar, mit Zeitstempel und Hash protokolliert werden.
- **Rueckwaerts-Ueberg aenge:** Nur bei Quarantaene zulaessig.
- **Blockierende Zustaende:** Muessen in Run-Summary als `blocking` gemeldet werden.
- **Pausierte Zustaende:** Muessen mit Zeitstempel, Grund und Hash protokolliert werden.

#### N5 – Kapitel-Querverweise

- **Alle Kapitel:** Muessen konsistent nummeriert sein (0–6).
- **Alle Anhaenge:** Muessen konsistent benannt sein (A–P).
- **Querverweise:** Muessen immer mit "siehe Abschnitt X.Y" oder "siehe Anhang X" erfolgen.
- **Keine impliziten Referenzen** (z. B. "siehe oben", "siehe unten", "wie beschrieben").

#### N6 – Glossar-Vervollstaendigung

- **Alle Begriffe:** Muessen im Glossar (Abschnitt 6.1) definiert sein.
- **Neue Begriffe:** Muessen bei Einfuehrung sofort im Glossar ergaenzt werden.
- **Begriffs aenderungen:** Muessen im CHANGELOG.md dokumentiert werden.

#### N7 – Anhang-Konsolidierung

- **Alle Anhaenge:** Muessen thematisch konsistent sein (kein Duplikat, keine Ueberlappung).
- **Anhang-Reihenfolge:** Alphabetisch nach Thema (A–P).
- **Anhang-Querverweise:** Muessen konsistent sein (z. B. "siehe Anhang H" statt "siehe Archivvertrag").

#### N8 – Stil- und Formatvereinheitlichung

- **Ueberschriften:** Immer Markdown-Header (`##`, `###`), nie fett gedruckt.
- **Listen:** Immer Bindestriche (`-`), nie Zahlen (ausser bei Reihenfolge).
- **Tabellen:** Immer mit Header-Zeile und Trennlinie, linksbuendig.
- **Code-Bl ocke:** Immer mit Sprachangabe (z. B. ` ```yaml`, ` ```json`, ` ```bash`).
- **Zitate:** Immer mit `> ` (Grossbuchstabe nach `>`).

---

### Anhang M — Mindesttestliste

- Konfigurationsvalidierung (alle Schluessel, Typen, Enums, Widersprueche).
- CLI-Hilfe (alle Befehle, Optionen, Exit-Codes).
- Unit-Tests (alle Module, APIs, Vertraege).
- Integrationstests (Phasen, WorkUnits, Recovery, State).
- Pfad-/ZIP-Sicherheit (Traversal, Symlink, Groessenlimit, Kompression).
- Dependency-Scan (keine unerlaubten Abhaengigkeiten, Lizenzkonformitaet).
- ARW-Archiv (vollstaendig, pruefbar, aktivierbar, Hash).
- Paralleler Scheduler (Lock, Race Conditions, Isolation).
- Abbruch vor/nach Phase-2-Transaktion (Resume, State, Quarantaene, Atomaritaet).
- Ressourcenverhalten auf Ziel-NAS (RAM, CPU, I/O, Zeitbudget).
- Face-Backend (Registry, Adapter, Cache-Fingerprint, Rebuild).
- MANUAL_KEEP (ResolutionAwareSimilarity, Threshold, Marge, inbox/used).
- Gewichtungsassistent (Audit, Rollback, Fingerprint).
- NAS-Pilot (vollstaendiger Lauf, Dokumentation, Abnahmebericht).

---

### Anhang N — Projektstruktur (GitHub-Repository)

#### Q1 – Repository-Uebersicht

Das GitHub-Repository `MaiTaiMa/synology-photo-workflow` enthaelt den vollstaendigen Code, die Dokumentation und die Konfiguration fuer den Synology Photo Workflow.

#### Q2 – Ordnerstruktur (Beispiel)

```text
synology-photo-workflow/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD-Pipeline (Tests, Lint, Security)
├── .gitignore                   # Git-Ignorierregeln (Python, Models, Secrets)
├── CHANGELOG.md                 # Versionshistorie, Aenderungen
├── Dockerfile                   # Container-Definition (Python, Dependencies)
├── README.md                    # Schnellstart, Ziel, Verweis auf MANUAL_DE
├── SECURITY.md                  # Sicherheitsrichtlinien, Kontakt
├── app/                         # Python-Quellcode (alle Module)
│   ├── __init__.py
│   ├── __main__.py
│   ├── archives.py              # ZIP-Archivierung, Hash, Aktivierung
│   ├── batch_state.py           # Batch-Zustaende, State-Management
│   ├── calibration.py           # Gewichtungsassistent, Kalibrierung
│   ├── cli.py                   # CLI-Argumente, Dispatch, Exit-Codes
│   ├── clip_taste_adapter.py    # CLIP-Geschmacksadapter
│   ├── configuration.py         # YAML-Konfiguration, Validierung
│   ├── culling.py               # Technisches Culling, Score, Serien
│   ├── face_adapter_yunet_sface_cpu.py  # Face-Backend-Adapter
│   ├── face_backend.py          # Face-Backend-Registry
│   ├── face_cache.py            # Face-Cache, Fingerprint
│   ├── family_recognition.py    # Familien-Erkennung (Fachlogik)
│   ├── inventory.py             # Batch-Inventar, WorkUnits
│   ├── locks.py                 # Globaler Lock, Race-Condition-Schutz
│   ├── manual_keep.py           # Manual Keep, ResolutionAwareSimilarity
│   ├── metadata.py              # Exiftool, Metadaten, Keywords
│   ├── phases.py                # Phase 1, Phase 2, Workflows
│   ├── photoworkflow.py         # Haupt-Entry-Point
│   ├── planning.py              # WorkUnit-Planung, Sortierung
│   ├── reporting.py             # Run-Summary, CSV, JSON, Logs
│   ├── result_contract.py       # Datenvertraege, Schema-Validierung
│   ├── runtime.py               # State, Lock, Recovery, Quarantaene
│   └── safety.py                # Pfadvalidierung, Security-Checks
├── config/
│   └── config.yaml              # Vollstaendige Konfiguration (YAML)
├── docker-compose.yml           # Docker-Compose (NAS-Mount, Volumes)
├── docs/                        # Dokumentation
│   ├── MANUAL_DE.md             # Benutzerhandbuch, Projektdokumentation
├── legacy/                      # Altlasten, DEPRECATED
│   ├── README.md                # Historie, Migration, Warum ersetzt
│   └── nas_photosort.sh         # Altes Bash-Skript (nicht mehr verwendet)
├── pyproject.toml               # Python-Projektmetadaten, Dependencies
├── pytest.ini                   # Pytest-Konfiguration
├── requirements-clip.txt        # CLIP-Abhaengigkeiten (optional)
├── requirements-dev.txt         # Entwicklungs-Abhaengigkeiten
├── requirements.txt             # Kern-Abhaengigkeiten
├── scripts/                     # Hilfskripte (Shell)
│   ├── README.md                # Skript-Uebersicht, Verwendung
│   ├── dsm-acceptance-preflight.sh
│   ├── preflight.sh
│   ├── run-phase1.sh
│   ├── run-phase2.sh
│   └── run-workflow.sh
└── tests/                       # Unit- und Integrationstests
    ├── README.md
    ├── __init__.py
    ├── conftest.py              # Pytest-Fixtures
    ├── integration/             # Integrationstests
    └── test_*.py                # Einzelne Testmodule
```

#### Q3 – Datenablage (Wo welche Daten abgelegt werden)

| Ordner/Datei | Zweck | Datenablage |
|--------------|-------|-------------|
| `config/config.yaml` | Konfiguration | Nur Konfiguration, keine Laufzeitdaten |
| `app/` | Quellcode | Nur Python-Code, keine Daten |
| `docs/` | Dokumentation | Nur Dokumente, keine Laufzeitdaten |
| `tests/` | Tests | Nur Testcode, keine Produktionsdaten |
| `scripts/` | Hilfskripte | Nur Skripte, keine Daten |
| `legacy/` | Altlasten | Nur historische Dateien, keine aktiven Daten |
| `.github/workflows/` | CI/CD | Nur Pipeline-Definitionen |
| NAS (extern) | Workflow-Daten | Alle Laufzeitdaten: `WORKFLOW_DATA/`, `TEMP_SD/`, `MANUAL_KEEP/`, `TEMP_IMAGES/`, `TEMP_DONE/`, `TEMP_ERROR/` |

#### Q4 – Wichtige Regeln

1. **Git enthaelt nie:**
   - Modellgewichte (`models/`)
   - Private Bilder, Referenzen, Face-Crops, Embeddings
   - Laufzeitdaten, Caches, Logs, Secrets, Konfiguration mit Produktionspfaden

2. **NAS enthaelt:**
   - Alle Workflow-Daten (`WORKFLOW_DATA/`, `TEMP_*`, `MANUAL_KEEP/`)
   - Konfiguration mit Produktionspfaden (lokal, nicht in Git)

3. **Docker-Container:**
   - Ent haelt nur Code (`app/`, `config/`, `scripts/`)
   - Mountet NAS-Pfade fuer `WORKFLOW_DATA/`, `TEMP_*`, `MANUAL_KEEP/`
   - Keine persistenten Daten im Container-Dateisystem

---

### Anhang O — Skript-Anforderungen (Struktur, Kommentare, Lesbarkeit)

#### R1 – Geltungsbereich

Diese Anforderung gilt fuer alle Skript-Dateien im Repository:

- Shell-Skripte (`.sh`) in `scripts/`
- Python-Skripte (`.py`) in `scripts/` oder anderen Verzeichnissen
- CI/CD-Skripte in `.github/workflows/`
- Hilfskripte fuer Tests oder Deployment

#### R2 – Struktur-Anforderungen

Jede Skript-Datei MUSS folgende Struktur aufweisen:

1. **Header-Kommentar** (obligatorisch, 6–10 Zeilen):
   - Skript-Name und Pfad
   - Zweck (1–2 Saetze)
   - Autor und Erstellungsdatum
   - Version (z. B. `Version: 1.0`)
   - Abhaengigkeiten (z. B. `Requires: bash, docker, exiftool`)
   - Verwendung (z. B. `Usage: ./run-phase1.sh <batch-id>`)

2. **Abschnitts-Kommentare** (obligatorisch, 2–3 Zeilen pro Abschnitt):
   - Jeder logische Abschnitt MUSS mit einem Kommentar ueberschrieben sein
   - Beispiel: `# === Phase 1: Inventar erstellen ===`
   - Beispiel: `# === Validierung: Pfade pruefen ===`

3. **Funktions-Kommentare** (obligatorisch, 3–5 Zeilen pro Funktion):
   - Jede Funktion MUSS mit einem Kommentar beschrieben sein
   - Zweck, Eingaben, Ausgaben, Rueckgabewert
   - Beispiel:
     ```bash
     # create_manifest()
     # Zweck: Erstellt Batch-Manifest mit Hashes
     # Eingabe: Pfad zum Batch-Ordner
     # Ausgabe: manifest.json im Batch-Ordner
     # Rueckgabe: 0 bei Erfolg, 1 bei Fehler
     ```

4. **Einzeiler-Kommentare** (empfohlen, bei komplexen Zeilen):
   - Komplexe Befehle oder Bedingungen Muessen kommentiert sein
   - Beispiel: `if [ -z "$BATCH_ID" ]; then  # BATCH_ID ist Pflichtargument`

#### R3 – Kommentar-Dichte und Lesbarkeit

1. **Mindestkommentierung:**
   - Jede Funktion: 3–5 Zeilen Kommentar
   - Jeder Abschnitt: 2–3 Zeilen Kommentar
   - Header: 6–10 Zeilen Kommentar
   - **Ca. 20 %** des Skript-Inhalts SOLLTEN Kommentare sein (ausreichend fuer Lesbarkeit)

2. **Selbsterklaerende Namen:**
   - Variablen, Funktionen und Konstanten Muessen sprechende Namen haben
   - Beispiel: `BATCH_ID` statt `id`, `create_manifest()` statt `do_it()`

3. **Konsistente Formatierung:**
   - Einrueckung: 2–4 Leerzeichen oder Tabs (konsistent im ganzen Skript)
   - Leerzeilen: Zwischen Abschnitten und Funktionen
   - Max. 80–100 Zeichen pro Zeile (fuer Lesbarkeit)

#### R4 – Beispiel-Header (Shell-Skript)

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

#### R5 – Beispiel-Abschnitt (Shell-Skript)

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

#### R6 – Beispiel-Funktion (Shell-Skript)

```bash
# create_manifest()
# Zweck: Erstellt Batch-Manifest mit Hashes fuer alle JPGs und ARWs
# Eingabe: $1 (Pfad zum Batch-Ordner)
# Ausgabe: manifest.json im Batch-Ordner (mit batchid, image_count, hashes)
# Rueckgabe: 0 bei Erfolg, 1 bei Fehler
# Abhaengigkeiten: jq, sha256sum
create_manifest() {
    local batch_path="$1"
    
    # Inventar: Alle JPGs und ARWs zaehlen
    local jpg_count=$(find "$batch_path" -name "*.jpg" | wc -l)
    local arw_count=$(find "$batch_path" -name "*.arw" | wc -l)
    
    # Manifest erstellen (JSON-Struktur)
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

Jede Skript-Datei MUSS vor der ersten Verwendung durch einen Validierungsschritt geprueft werden:

1. Header-Kommentar vorhanden (6–10 Zeilen)?
2. Abschnitts-Kommentare vorhanden (2–3 Zeilen pro Abschnitt)?
3. Funktions-Kommentare vorhanden (3–5 Zeilen pro Funktion)?
4. Ca. 20 % Kommentare im gesamten Skript (ausreichend fuer Lesbarkeit)?
5. Sprechennde Namen fuer Variablen, Funktionen, Konstanten?
6. Konsistente Formatierung (Einrueckung, Leerzeilen, Zeilenlaenge)?

Bei Fehlern: Skript als ungueltig markieren, im Log dokumentieren, manuelle Korrektur erforderlich.

#### R8 – Versionierung und Aenderungshistorie

- **Version:** Jede Skript-Datei MUSS eine Versionsnummer im Header enthalten (z. B. `Version: 1.0`)
- **Aenderungsprotokoll:** Jede Aenderung MUSS im Header dokumentiert werden (Datum, Autor, Kurzbeschreibung)
- **CHANGELOG.md:** Jede Aenderung MUSS zusaetzlich im CHANGELOG.md dokumentiert werden

---

### Anhang P — README-Anforderungen fuer Ordner

#### P4.1 Geltungsbereich

Diese Anforderung gilt fuer alle README-Dateien im NAS-Workflow-Bereich:

- `PHOTO_WORKFLOW/README.md`
- `TEMP_SD/README.md`, `TEMP_IMAGES/README.md`, `TEMP_DONE/README.md`, `TEMP_ERROR/README.md`
- `MANUAL_KEEP/README.md`, `MANUAL_KEEP/inbox/README.md`, `MANUAL_KEEP/used/README.md`
- `WORKFLOW_DATA/README.md` und alle direkten Unterordner (`runtime/`, `reports/`, `archives/`, `faces/`, `samples/`, `models/`, `config/`)

#### P4.2 Pflichtfelder pro README

Jede README-Datei MUSS die folgenden 8 Felder enthalten, in dieser Reihenfolge:

1. **Zweck** (1–2 Saetze): Wofuer ist dieser Ordner da? Welches Problem loest er im Workflow?
2. **Eingaben** (Aufzaehlung): Welche Daten/Dateien/Ordner duerfen hier abgelegt werden? Wer oder welcher Prozess legt sie ab?
3. **Prozess** (1–3 Saetze): Welcher Prozessschritt (Phase 1, Phase 2, Manual Keep, Mensch) verarbeitet diesen Ordner? Was passiert hier?
4. **Ausgaben** (Aufzaehlung): Wohin wandern die Daten als naechstes? Welcher Prozess oder welcher Ordner konsumiert sie?
5. **Manuelle Aktionen** (Aufzaehlung): Was darf der Mensch hier tun? Was ist ausdruecklich verboten?
6. **Lebenszyklus** (1–2 Saetze): Wann gilt ein Batch/Datei in diesem Ordner als abgeschlossen? Wann wird er bereinigt/verschoben?
7. **Fehlerfaelle** (Aufzaehlung): Was passiert bei Fehlern? Wo werden fehlerhafte Faelle abgelegt? Wer muss eingreifen?
8. **Konfiguration** (optional, falls relevant): Welche Config-Schluessel beeinflussen diesen Ordner? (z. B. `manual_keep.*` fuer `MANUAL_KEEP/inbox/`)

#### P4.3 Format und Umfang

- **Format:** Markdown, klare Ueberschriften (`##`, `###`), Aufzaehlungen mit Bindestrichen.
- **Umfang:** Mindestens 100 Woerter, maximal 500 Woerter (ausgenommen Code-Beispiele oder Pfadlisten).
- **Sprache:** Deutsch, technisch praezise, frei von Floskeln.
- **Beispiele:** Mindestens ein konkretes Beispiel fuer Eingabe/Ausgabe oder manuelle Aktion.
- **Verweise:** Keine externen URLs; nur interne Pfadverweise (z. B. `../TEMP_IMAGES/`).

#### P4.4 Validierung

Jede README-Datei MUSS vor der ersten Verwendung durch einen Validierungsschritt geprueft werden:

1. Alle 8 Pflichtfelder vorhanden?
2. Mindestens 100 Woerter, maximal 500 Woerter?
3. Mindestens ein konkretes Beispiel enthalten?
4. Keine externen URLs?
5. Technische Korrektheit (Pfade, Prozessnamen, Config-Schluessel)?

Bei Fehlern: README als ungueltig markieren, im Log dokumentieren, manuelle Korrektur erforderlich.

#### P4.5 Versionierung

- **Version:** Jede README-Datei MUSS eine Versionsnummer im Header enthalten (z. B. `Version: 1.0`).
- **Aenderungshistorie:** Jede Aenderung MUSS im CHANGELOG.md dokumentiert werden (Datum, Autor, Kurzbeschreibung).
- **Migration:** Bei Aenderung der Ordnerstruktur oder Prozesslogik MUSS die README entsprechend aktualisiert werden.

#### P5 – Beispiel-README fuer TEMP_SD (Muster)

```markdown
## TEMP_SD

### Zweck
Eingang fuer neue Kameraordner. Hier werden frische DCIM-Ordner (z. B. `100CANON`) abgelegt, bevor Phase 1 beginnt.

### Eingaben
- Nur frische Kameraordner (z. B. `DCIM/100CANON`, `DCIM/101CANON`)
- Nur JPGs und ARWs im Originalzustand (keine bearbeiteten Dateien)
- Abgelegt durch: Mensch (SD-Karte kopieren) oder automatischer Import (z. B. Synology Photo)

### Prozess
Phase 1 liest von hier, normalisiert Datum, lagert ARWs nach `ARW/` aus, erzeugt Batch-Struktur und bewertet JPGs.

### Ausgaben
- Nach Phase 1: Batch wird nach `TEMP_IMAGES/` ueberfuehrt (alle Unterordner: Hauptordner, `Review/`, `Rejected/`, `ARW/`, `SAVE/`)

### Manuelle Aktionen
- Neue Kameraordner ablegen (erlaubt)
- Bestehende Batches veraendern (verboten – fuehrt zu `review_state_invalid`)
- Dateien loeschen (verboten – fuehrt zu inkonsistentem State)

### Lebenszyklus
Ein Batch gilt als abgeschlossen, wenn Phase 1 erfolgreich nach `TEMP_IMAGES/` verschoben wurde. Danach wird `TEMP_SD/` fuer diesen Batch bereinigt.

### Fehlerfaelle
- Ungueltiger Ordnername (z. B. `Meine_Fotos`): Wird ignoriert, Log-Eintrag, manuelle Pruefung erforderlich
- Fehlende ARWs: Phase 1 setzt `failed_metadata`, Batch wandert nach `TEMP_ERROR/`
- Beschaedigte Dateien: Phase 1 setzt `analysis_error`, Batch wird quaraentaenisiert

### Konfiguration
- `paths.temp_sd` (Pfad zu diesem Ordner)
- `workflow.batch_sort` (Reihenfolge der Batch-Verarbeitung)
```

---

### Anhang T — Aenderungs-Historie und Versionierung (vollstaendig)

#### T1 – Versions-Historie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|----------|
| 9.9 | 2026-08-04 | MaiTaiMa + Perplexity AI | Harmonisierte Fassung (AP1–AP5): Begriffe, Regeln, Schutzgrenzen konsolidiert; Redundanzen entfernt; neue Struktur (6 Hauptkapitel + Anhaenge A–P). |
| 9.8 | 2026-08-03 | MaiTaiMa + Perplexity AI | Rechtschreib- und Formatkorrekturen, neuer Abschnitt "Architektur und Compliance", Aktualisierung der Aenderungs-Historie. |
| 9.7 | 2026-08-04 | MaiTaiMa + Perplexity AI | AP5-Umsetzung (Finalisierung, Konsolidierung, Querverweise, Beispiele, Fehlerfaelle, Konfigurations-Beispiel, Migration, Versionierung, Release-Checkliste, Abnahme-Protokoll, Aenderungs-Historie). |
| 9.6 | 2026-08-04 | MaiTaiMa + Perplexity AI | AP4-Umsetzung (Vollstaendigkeits- und Kohaerenzpruefung). |
| 9.5 | 2026-08-04 | MaiTaiMa + Perplexity AI | AP3-Umsetzung (Konsistenz- und Einheitlichkeitspruefung). |
| 9.4 | 2026-08-04 | MaiTaiMa + Perplexity AI | AP2-Umsetzung (Logik- und Plausibilitaetspruefung). |

#### T2 – Versionierungs-Regeln

- **Major-Version** (z. B. 9.x): Breaking Changes, neue Kernfunktionen, geaenderte Datenvertraege.
- **Minor-Version** (z. B. x.4): Neue Features, Ergaenzungen, Praezisierungen ohne Breaking Changes.
- **Patch-Version** (z. B. x.x.1): Fehlerkorrekturen, kleinere Verbesserungen, keine neuen Features.

#### T3 – Release-Checkliste

Vor jedem Release MUSS folgende Checkliste abgearbeitet werden:

1. Alle Header aktualisiert (Version, Datum, Status)?
2. CHANGELOG.md aktualisiert?
3. Alle Anhange konsistent (A–P)?
4. Alle Querverweise geprueft?
5. Glossar vollstaendig?
6. Config-Schema validiert?
7. Alle Tests bestanden (ACC-01 bis ACC-15)?
8. NAS-Pilot dokumentiert?

---

**Ende der Spezifikation v9.9 (mit allen Anhaengen A–P)**
