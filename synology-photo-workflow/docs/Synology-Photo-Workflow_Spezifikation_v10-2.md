<!--
Synology Photo Workflow – Spezifikation v10.2
Datei: docs/Synology-Photo-Workflow_Spezifikation_v10-2_Teil1.md
Mitentwickler: MaiTaiMa (in Zusammenarbeit mit Perplexity AI)
Erstellt: 2026-08-04
Projektversion: 10.2
Status: Vollstaendige, bereinigte und konsolidierte Fassung, erweitert um optionale PHASE3 (Finalisierung) und optionale Synology-Photos-API-Integration
-->

# Synology Photo Workflow – Spezifikation v10.2

**Status:** Verbindliche, alleinstehende Spezifikation fuer den sicheren, wiederaufnehmbaren Synology Photo Workflow (vollstaendig bereinigte und konsolidierte Fassung, erweitert um optionale PHASE3).

**Zielsetzung:** Dieses Dokument ist die alleinige normative Quelle fuer Entwicklung, Betrieb, Test und Aenderungen. Es enthaelt alle Informationen aus der vorherigen harmonisierten Fassung, erweitert um die Referenzpool-Verwaltung, Face-Crops, dynamisches Ranking, vollstaendige Anhaenge und eine optionale PHASE3 (Finalisierung und Synology-Photos-Integration).

**Ergaenzung v10.2:** Diese Fassung ergaenzt die vollstaendige Spezifikation v10.1 um eine optionale PHASE3. PHASE3 kann fertig verarbeitete Batches optional aus `03_TEMP_DONE` in einen Synology-Photos-indexierten Zielpfad uebertragen und danach optional Metadaten ueber einen gekapselten API-Adapter setzen. Bei deaktivierter PHASE3 bleibt der Ablauf der v10.1 unveraendert.

---

## 0. Metadaten und Geltungsbereich

### 0.1 Dokumentenmetadaten

| Feld | Wert |
|------|------|
| Version | 10.2 |
| Datum | 2026-08-04 |
| Status | Vollstaendig bereinigt und konsolidiert, erweitert um optionale PHASE3 |
| Vorgaenger | 10.1 |
| Aenderungs-Historie | Siehe Kapitel 6.4 und Anhang T (v10.1) sowie Anhang W (v10.2) |

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

Der Workflow verarbeitet Foto-Batches auf einem Synology-NAS in drei Phasen:

- **Phase 1** analysiert, bewertet und bereitet die menschliche Pruefung vor.
- **Phase 2** archiviert und bereinigt ARWs erst nach einer nachweislich sicheren Endentscheidung.
- **Phase 3 (optional)** prueft einen erfolgreich abgeschlossenen Phase-2-Batch und kann ihn – nur bei aktivierter Veroeffentlichungsoption – aus `03_TEMP_DONE` in einen konfigurierten, von Synology Photos indexierten Zielpfad uebertragen. Nach erfolgreicher Indexierung KANN sie Ratings, kontrollierte Tags und optional Beschreibungen ueber einen Synology-Photos-API-Adapter anwenden.

Original-JPGs und ARWs duerfen weder still ueberschrieben noch geloescht werden. Bekannte Gesichtserkennung verarbeitet nur bewusst gepflegte bekannte Personen. Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt, als Kandidat protokolliert oder als Referenz aktiviert werden. Ein Gesichtstreffer darf technische Mindestqualitaet, Manual Keep oder Schutzregeln niemals ueberstimmen.

PHASE3 ist vollstaendig nachgelagert. Sie DARF nur fuer Batches mit `phase2_completed` starten. Sie DARF keine ARWs, ZIP-Archive, Review-Records, Referenzpools oder Kalibrierungsdaten veraendern. Ein Fehler in PHASE3 darf eine erfolgreiche PHASE2 weder zuruecksetzen noch Bilddaten loeschen.

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
- PHASE3 darf nur Quell- und Zielpfade verwenden, die innerhalb von `paths.basedir` liegen und die bestehende Pfadvalidierung bestehen.
- Ein aktivierter Transfer muss vollstaendig, nachvollziehbar und wiederaufnehmbar sein. Teiluebertragene Batches duerfen nicht als erfolgreich veroeffentlicht gelten.
- Bei deaktiviertem Transfer darf PHASE3 keine Bilddatei aus `03_TEMP_DONE` verschieben, kopieren, loeschen oder umbenennen.
- API-Credentials, Session-Token und vergleichbare Geheimnisse duerfen weder in Git noch in Batch-Manifests, CSVs, Logs oder Run-Summaries gespeichert werden.
- Die API-Schicht darf nur bereits vorhandene lokale Workflow-Metadaten uebertragen. Bildbytes, Face-Crops, Embeddings und Referenzbilder duerfen nicht an die API uebermittelt werden.
- API-Fehler duerfen niemals eine Loeschung, ein Ueberschreiben, einen Ruecktransfer oder eine sonstige unkontrollierte Datei aenderung ausloesen.

---

## 2. Architektur, Verzeichnisse, Datenfluesse

### 2.1 Systemuebersicht

Das Projekt trennt Betriebsschnittstelle, CLI, Fachmodule und den persistenten NAS-Datenbereich. Shell-Skripte pruefen nur Umgebung und starten den Workflow; sie enthalten keine Geschaeftslogik. Die Python-CLI laedt `config/config.yaml`, validiert die Konfiguration und delegiert an spezialisierte Module. Die Fachmodule erzeugen testbare Ergebnisobjekte und kapseln Dateisystemmutationen.

### 2.2 Projektstruktur

- `NAS_EXAMPLE/`: Beispiel fuer den persistenten NAS-Bereich.
  - `01_TEMP_SD/`: Neue Eingangsbatches.
  - `02_TEMP_IMAGES/`: Phase-1-Review-Ausgabe.
  - `03_TEMP_DONE/`: Menschlich freigegebene Uebergabe.
  - `00_TEMP_ERROR/`: Quarantaene und Fehlerfaelle.
  - `WORKFLOW_DATA/`: States, Logs, Summaries, Caches, Referenzen, Modelle.
  - `MANUAL_KEEP/inbox/`: Manuelle Keep-Eingaenge.
  - `MANUAL_KEEP/used/`: Bereits zugeordnete Keep-Dateien.
  - `04_TEMP_FINAL/` (optional): Lokaler Finalisierungsbereich, falls der veroeffentlichte Zielpfad nicht direkt verwendet wird.
- `synology-photo-workflow/`
  - `app/`: Python-Fachmodule und CLI.
  - `config/config.yaml`: Zentrale kommentierte Konfiguration.
  - `scripts/`: DSM-/Docker-Start- und Vorpruefungsskripte.
  - `tests/`: Unit- und Vertragspruefungen.
  - `docs/`: Handbuch, Architektur, Testdokumentation.
  - `app/finalization.py` (optional): PHASE3-Planung, Transfer, Resume und Reporting.
  - `app/synology_photos_adapter.py` (optional): Gekapselte Synology-Photos-Authentisierung, Capability-Pruefung, Item-Aufloesung und Metadatenoperationen.

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
- `app.finalization` verwaltet PHASE3: Auswahl von Phase-2-abgeschlossenen Batches, Konfigurationspruefung, Transferplan, Move/Copy, Hashpruefung, Resume und PHASE3-Reporting.
- `app.synology_photos_adapter` kapselt die konkrete Synology-Photos-Integration: Authentisierung, API-Discovery, Capability-Pruefung, sichere Item-Aufloesung, Lesen und Schreiben von Metadaten sowie Ruecklesepruefung.

**Wichtig:** Diese Trennung ist der vorgesehene Erweiterungspunkt: Ein neues Face-Backend gehoert in Adapter/Registry, eine neue Bewertungsregel in `culling`, ein anderes Archivformat in `archives` und keine dieser Aenderungen in Shell-Skripte. Eine Synology-Photos-Integration gehoert ausschliesslich in `app.synology_photos_adapter`; Dateioperationen und PHASE3-Zustaende gehoeren in `app.finalization`. Shell-Skripte sowie Culling-, Archiv- und Face-Module duerfen keine API-spezifische Geschaeftslogik enthalten.

### 2.4 Datenquellen und Wirkungen

- Die Inventarisierung bezieht Daten direkt aus `01_TEMP_SD`; sie erzeugt Manifeste und Paarbindungen.
- `culling` bezieht Bilddaten und Gewichte aus `config.culling`; seine Scores wirken auf Sterne, Vorschlaege und Review-Listen.
- `metadata` bezieht Entscheidungen und erlaubte Schluessel aus den Batch-Ergebnissen; es wirkt ausschliesslich bei aktiviertem Schreibmodus auf Bildmetadaten.
- `archives` beziehen nur validierte Phase-2-Kandidaten und erzeugen verifizierte ZIPs im persistenten Bereich.
- Die Loeschlogik bezieht sich auf Archivmanifest, Hash und State; ohne diese Quellen wird kein ARW geloescht.
- Face-Erkennung bezieht Modelle aus dem gewaehlten Backend, Referenzen und Caches aus `WORKFLOW_DATA`. Ihre Wirkung ist auf Match-Ergebnis, Familien-Score und gegebenenfalls Personentags begrenzt; bei deaktivierter Funktion entstehen keine Face-Artefakte.
- Kalibrierung bezieht bestaetigte Review-Records und wirkt auf Reports und Empfehlungen, niemals selbst aendert auf Automatikflags.
- `finalization` bezieht ausschliesslich Batches mit dem validen State `phase2_completed`, ihre bestehenden Manifeste und die freigegebenen sichtbaren Bilddateien. Bei deaktivierter Veroeffentlichungsoption erzeugt es ausschliesslich Plan-/Reportartefakte und veraendert keine Bilddateien.
- Bei aktivierter Veroeffentlichungsoption uebertraegt `finalization` den Batch nach `target_folder` und prueft die vollstaendige Uebertragung per Dateiliste, Groesse und SHA256.
- `synology_photos_adapter` bezieht ausschliesslich bereits vorhandene Ratings und erlaubte Workflow-Tags. Er darf nur nach verifiziertem Transfer und zuverlaessiger Aufloesung der Zielbilder als indexierte Synology-Photos-Items schreiben.

### 2.5 Kanonische Arbeitsordner

| Ordner | Zweck |
|--------|-------|
| `PHOTO_WORKFLOW/README.md` | Gesamtdokument fuer den Workflow, beschreibt Gesamtfluss, manuelle Aktionen und Lebenszyklus. |
| `01_TEMP_SD` | Eingang fuer neue Kameraordner. |
| `02_TEMP_IMAGES` | Ergebnis aus Phase 1 zur manuellen Sichtung. |
| `03_TEMP_DONE` | Manuell freigegebene Ordner fuer Phase 2. |
| `00_TEMP_ERROR` | Quarantaene fuer fehlerhafte oder unsichere Faelle. |
| `WORKFLOW_DATA` | Zentrale Daten (faces, models, runtime, samples, reports, archives, config). |
| `MANUAL_KEEP` | Vorab ausgewaehlte, extern erhaltene JPGs (inbox, used). |
| `04_TEMP_FINAL` (optional) | Kontrollierter lokaler Bereich fuer erfolgreich finalisierte Batches, sofern kein Direkttransfer nach `target_folder` genutzt wird. |
| `finalization.publish_to_synology_photos.target_folder` | Optionaler Veroeffentlichungszielpfad. Er liegt innerhalb von `paths.basedir` und wird von Synology Photos indexiert. |

Die tatsaechlichen Pfade sind konfigurierbar, muessen aber innerhalb eines erlaubten Basisverzeichnisses liegen.

`03_TEMP_DONE` bleibt der Arbeits- und Uebergabebereich nach manueller Freigabe und waehrend PHASE2. Ein Batch bleibt dort, wenn die optionale Veroeffentlichung deaktiviert ist. `target_folder` ist der Zielpfad der tatsaechlichen Veroeffentlichung, nicht lediglich ein Parameter fuer API-Aufrufe.

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

Die unveraenderliche `batchid` lautet `source-folder-name+fingerprint(8)` und bleibt beim Wechsel zwischen allen Arbeitsordnern gleich. Pro Batch gibt es genau eine zentrale Zustandsdatei `WORKFLOW_DATA/runtime/state/{batchid}.json`; globale Zustandsdateien sind unzulaessig.

**Batch-ID-Bildung:** Die `batchid` wird bei Erstkontakt mit dem Batch aus dem Ordnernamen und einem 8-stelligen Fingerprint (SHA256, gekuerzt) gebildet. Sie bleibt ueber alle Ordnerwechsel hinweg unveraendert.

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
8. Atomare Uebergabe nach `02_TEMP_IMAGES`.

### 3.3 Phase 2

Phase 2 MUSS zuerst Phase-1-Manifest und Endentscheidungen validieren, bei manueller Freigabe den unveraenderlichen Review-Record schreiben und erst danach archivieren. Ein ARW darf nur geloescht werden, nachdem ein vollstaendiges Archiv erzeugt, geprueft, auf demselben Dateisystem atomar aktiviert und mit Hash protokolliert wurde.

Bei jedem Fehler bleibt das ARW erhalten; ARW darf erst nach vollstaendig dokumentierter Bereinigung entfernt werden.

**Phase-2-Start:** Phase 2 beginnt erst nach manueller Freigabe (Move nach `03_TEMP_DONE`) oder nach explizit zugelassener automatischer Uebergabe (`automatic_handoff`).

**Beispiel:** Ein Batch in `02_TEMP_IMAGES` wird vom Menschen gesichtet. Nach der Sichtung wird der gesamte Batch nach `03_TEMP_DONE` verschoben. Dies ist das alleinige Freigabesignal fuer Phase 2.

### 3.4 Zustandsautomat (manuell und automatisch)

Fuer manuell freigegebene Batches lautet der Zustandsautomat zwingend:

```text
phase1_started → phase1_completed → review_comparison_pending → review_record_committed → calibration_index_committed → phase2_archiving → phase2_completed
```

Der manuelle Move nach `03_TEMP_DONE` ist das alleinige Freigabesignal.

Bei einer explizit zugelassenen automatischen Uebergabe lautet er:

```text
phase1_completed → automatic_handoff → phase2_archiving → phase2_completed
```

Es entsteht kein Trainingslabel.

**Blockierender Zustand:** `review_state_invalid` (bei mehrdeutigen Paarungen, mehreren wirksamen JPG-Kopien, fehlenden Quellhashes oder widerspruechlichen Ordnerzustaenden) blockiert Phase 2; es darf keine ARW-Aktion stattfinden. Der Batch wird in `00_TEMP_ERROR` verschoben und in der Run-Summary als `blocking` gemeldet.

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
    "hash": "a3f7c2e1...",
    "reason": null,
    "producer_version": "10.2"
}
```

### 3.4.1 PHASE3 Finalisierung, Veroeffentlichung und Synology-Photos-API

- **Status:** Optional.
- **Zweck:** Erlaubt es, einen bereits erfolgreich durch PHASE2 verarbeiteten Batch kontrolliert zu veroeffentlichen. Der Batch kann optional aus `03_TEMP_DONE` in einen von Synology Photos indexierten Zielpfad verschoben oder kopiert werden. Nach bestaetigter Indexierung koennen vorhandene Workflow-Metadaten optional ueber einen gekapselten Synology-Photos-API-Adapter auf die indexierten Bilder uebertragen werden.
- **Ablauf:**
  1. PHASE3 beruecksichtigt ausschliesslich Batches mit dem validen State `phase2_completed`.
  2. `finalization.enabled: false` beendet PHASE3 ohne Datei- oder API-Aktion; der Batch bleibt unveraendert in `03_TEMP_DONE`.
  3. Bei `finalization.enabled: true` und `publish_to_synology_photos.enabled: false` validiert PHASE3 Konfiguration, State und Pfade und erzeugt nur Plan-/Reportartefakte; der Batch bleibt unveraendert in `03_TEMP_DONE`.
  4. Bei `publish_to_synology_photos.enabled: true` schreibt PHASE3 zuerst ein atomar validiertes `finalization_manifest.json` mit Quelle, Ziel, Modus, Dateiliste, Groessen und SHA256-Hashes.
  5. `mode: move` verschiebt den Batch erst nach erfolgreichem Zielabgleich; `mode: copy` kopiert den Batch und erhaelt die Quelle in `03_TEMP_DONE`.
  6. Nach dem Transfer prueft PHASE3 die Vollstaendigkeit aller Zieldateien per Dateiliste, Groesse und SHA256. Erst dann wird `phase3_transferred_to_target` gesetzt.
  7. PHASE3 wartet mindestens `wait_for_index_seconds` und loest anschliessend jedes Zielbild als Synology-Photos-Item auf. Nicht aufgeloes te oder mehrdeutige Items werden nicht beschrieben.
  8. Nur bei `synology_api.enabled: true` und nach erfolgreicher Item-Aufloesung uebertraegt der API-Adapter die erlaubten Metadaten. Die Werte werden aus bereits vorhandenen Workflow-Metadaten uebernommen, nicht neu berechnet.
  9. Bei aktivierter Ruecklesepruefung liest PHASE3 die geschriebenen Werte erneut und bestaetigt Rating, Tags und optionale Beschreibung.
  10. Jeder Zustandsuebergang, Transfer und API-Versuch wird atomar mit Zeitstempel, Konfigurationsfingerprint und Ergebnis protokolliert.

**PHASE3-Vertrag:** PHASE3 MUSS `batchid`, `source_batch_path`, `target_batch_path` (falls Transfer aktiv), `publish_enabled`, `transfer_mode` (falls Transfer aktiv), `state`, `timestamp`, `config_fingerprint`, `producer_version` und `finalization_manifest_hash` enthalten. Bei API-Nutzung MUSS zusaetzlich pro Bild ein lokaler Korrelationsrecord mit `relative_path`, `resolved_item_status`, `metadata_status`, `attempt_count` und `last_error` (optional, secrets-frei) gefuehrt werden.

**Beispiel ohne Veroeffentlichung:** Bei `finalization.enabled: true` und `publish_to_synology_photos.enabled: false` wird ein Batch `2024-08-15_Geburtstag+a3f7c2e1` mit `phase2_completed` geprueft und in der Run-Summary als `finalization_skipped_publish_disabled` gemeldet. Er verbleibt vollstaendig in `03_TEMP_DONE`; keine Datei wird verschoben oder kopiert und keine API wird aufgerufen.

**Beispiel mit Copy:** Bei `finalization.enabled: true`, `publish_to_synology_photos.enabled: true` und `mode: copy` wird der Batch von `/photo/03_TEMP_DONE/2024-08-15_Geburtstag` nach `/volume1/photo/Workflow/2024-08-15_Geburtstag` kopiert. Erst wenn alle Dateien im Ziel hashgleich vorliegen, wird `phase3_transferred_to_target` gesetzt. Die Quelle bleibt in `03_TEMP_DONE` erhalten.

**Beispiel mit Move:** Bei `mode: move` wird zunaechst der vollstaendige Zielbestand aufgebaut und geprueft. Erst nach erfolgreichem Abgleich darf die Quelle als Move-Abschluss entfernt werden. Scheitert ein Schritt, bleibt ein sicherer, wiederaufnehmbarer Zustand erhalten; es darf kein Bild verloren gehen.

### 3.4.2 PHASE3-Zustandsautomat

Fuer einen Batch mit aktivierter Veroeffentlichung lautet der optionale Zustandszweig:

```text
phase2_completed
  → phase3_finalization_planned
  → phase3_transfer_in_progress
  → phase3_transferred_to_target
  → phase3_index_waiting
  → phase3_item_resolution_pending
  → phase3_api_metadata_pending
  → phase3_api_metadata_completed
```

Fuer einen Batch mit aktiver PHASE3, aber deaktivierter Veroeffentlichung lautet der Abschluss:

```text
phase2_completed → phase3_finalization_planned → phase3_publish_disabled
```

`phase3_publish_disabled` ist kein Fehlerzustand. Er dokumentiert, dass PHASE3 bewusst keine Datei- oder API-Aktion ausfuehren durfte.

Zusaetzliche Fehlerzustaende sind:

- `phase3_transfer_failed`
- `phase3_indexing_timeout`
- `phase3_item_resolution_failed`
- `phase3_api_metadata_partial`
- `phase3_api_metadata_failed`
- `finalization_state_invalid`

Ein PHASE3-Fehler darf keinen automatischen Rueckwaerts-Move ausloesen. Ein bereits vollstaendig und hashgleich veroeffentlichter Batch bleibt im Zielpfad; ein Folgejob setzt nur die noch fehlende Pruefung oder API-Metadatenoperation fort.

### 3.5 WorkUnits (Bildmengenmodus, Resume)

- **Status:** Pflicht.
- **Zweck:** Erlaubt es, auch sehr grosse physische Ordner in ueberschaubaren, sicher fortsetzbaren Portionen zu verarbeiten, ohne die sichtbare Ordnerstruktur zu veraendern.
- **Ablauf:**
  1. `workflow.workunit_mode: source_batch` (Default, ganzer Ordner Einheit) oder `imagecount` (interne, unsichtbare Portionierung).
  2. Der physische Batch wird erst verschoben, wenn alle WorkUnits abgeschlossen sind.
  3. Angefangene oder wiederherzustellende Arbeit hat immer Vorrang vor neuen Ordnern.
  4. Vor jedem sichtbaren Dateimove wird ein Uebergangsstate `phase1_moving` geschrieben, erst danach der Abschluss `phase1_completed`.

**WorkUnit-Vertrag:** Eine WorkUnit MUSS `workunit_id`, `batch_id`, `image_range` (Start, Ende), `state` (pending, in_progress, completed, failed, paused), `timestamp`, `hash`, `error_reason` (optional) enthalten.

**Beispiel imagecount:** Bei `workflow.workunit_mode: imagecount` und `workflow.images_per_workunit: 200` wird ein physischer Batch mit 800 Bildern in 4 WorkUnits aufgeteilt. Jede WorkUnit wird separat verarbeitet, aber der Batch wird erst nach Abschluss aller 4 WorkUnits nach `02_TEMP_IMAGES` verschoben.

### 3.5.1 PHASE3-Resume

- **Status:** Pflicht, wenn PHASE3 aktiviert ist.
- **Zweck:** Erlaubt es, einen unterbrochenen Finalisierungs-, Transfer-, Indexierungs- oder API-Lauf ohne doppelten Transfer, Datenverlust oder doppelte Tags sicher fortzusetzen.
- **Ablauf:**
  1. Vor einer Dateiaktion erzeugt PHASE3 ein atomar validiertes `finalization_manifest.json`.
  2. Ist die Veroeffentlichung deaktiviert, wird `phase3_publish_disabled` gesetzt; bei spaeterer Aktivierung wird kein alter Plan blind wiederverwendet, sondern mit dem aktuellen Konfigurationsfingerprint neu geprueft.
  3. Ist die Quelle vollstaendig und das Ziel nicht vorhanden, wird der Transfer nach dem gespeicherten Modus fortgesetzt oder neu geplant.
  4. Ist das Ziel vollstaendig und hashgleich, wird kein zweiter Transfer ausgefuehrt; PHASE3 setzt bei Indexierung, Item-Aufloesung oder API-Metadaten fort.
  5. Sind Quelle und Ziel gleichzeitig vorhanden, entscheidet das Manifest: Bei `copy` ist dies erwartbar; bei `move` wird geprueft, ob der Move noch nicht finalisiert wurde.
  6. Bei abweichenden Hashes, unklarer Teiluebertragung oder einer Kollision wird der Batch blockiert und in der Run-Summary als `blocking` gemeldet.

**Finalization-Manifest-Vertrag:** `finalization_manifest.json` MUSS `schema_version`, `batch_id`, `created_at`, `updated_at`, `producer_version`, `source_batch_path`, `target_batch_path` (optional, wenn Veroeffentlichung deaktiviert), `publish_enabled`, `mode` (optional), `entries` (relative_path, size, hash), `config_fingerprint`, `state` und `hash` enthalten.

**Beispiel Resume:** Ein Copy-Lauf mit 800 Bildern wird nach 600 Dateien unterbrochen. Beim naechsten Start vergleicht PHASE3 Quelle, Ziel und Transfermanifest. Bereits vollstaendig hashgleiche Zieldateien werden nicht erneut kopiert; fehlende Dateien werden ergaenzt. Erst nach vollstaendigem Hashabgleich folgt die Indexierungs- und API-Phase.

### 3.6 Archivvertrag

- **ZIP:** Lesbarkeit, Traversal, Groessenlimit, Kompressionsverhaeltnis pruefen.
- **Kollision:** `...EXTRAn.zip` statt Ueberschreibung.
- **Hash:** SHA256 fuer ZIP, Manifest, State; Hash vor/nach Aktivierung pruefen.
- **Aktivierung:** Vollstaendiges Archiv erzeugt, geprueft, auf gleichem Dateisystem atomar aktiviert, mit Hash protokolliert.
- **Loeschung:** ARW erst nach vollstaendig dokumentierter Bereinigung entfernen.

**Archiv-Vertrag-Kohaerenz:** Jeder Archiveintrag MUSS folgende Felder enthalten:
- `relative_path` (string, relativ zum Batch)
- `size` (int, Bytes)
- `hash` (string, SHA256)
- `archived_at` (string, ISO8601)

**Archivplan-Details:** Der Archivplan MUSS folgende Felder enthalten:
- `batch_id` (Batch-ID)
- `created_at` (ISO8601-Zeitstempel)
- `archive_path` (relativer Pfad zur ZIP)
- `entry_count` (Anzahl der Eintraege)
- `total_size` (Gesamtgroesse in Bytes)
- `entries` (Liste aller Eintraege mit Pfad, Groesse, SHA256)
- `config_fingerprint` (SHA256 der effektiven Konfiguration)
- `producer_version` (Versionskennung)

### 3.7 Fehler- und Recovery-Vertrag

- **Fehlende oder ungueltige Steuerdaten:** Nach `WORKFLOW_DATA/runtime/quarantine` kopieren, mit Grund, Zeit, Hash melden; sichere Neuerstellung oder menschliche Pruefung erforderlich.
- **Atomaritaet:** Inhalt erzeugen, validieren, temporaer auf gleichem Dateisystem schreiben, erneut validieren, atomar ersetzen; vorherige Version bis Aktivierung erhalten.
- **Lock:** Globaler Lock verhindert parallele produktive Laeufe; Lock vor/nach Lauf pruefen.
- **Quarantaene:** Fehlerhafte Artefakte nach `WORKFLOW_DATA/runtime/quarantine` mit Manifest blockierend melden; menschliche Pruefung erforderlich.

---

## 4. Scoring, Serien, Metadaten, Manual Keep, Face-Backend, Kalibrierung

### 4.1 Technisches Culling (basescore)

- **Status:** Pflicht.
- **Zweck:** Ressourcenschonende Basisbewertung ohne Pflicht-KI-Modell. Bewertet Schaerfe, Belichtung und einfache aesthetische Merkmale. Ergebnis ist `base_score`.
- **Ablauf:**
  1. Kleine technische Vorschau erzeugen (256–512 Pixel laengste Kante).
  2. Teilscores fuer Schaerfe (Kantenvarianz), Belichtung (Clipping), Helligkeitsbalance und Aesthetik (Kontrast, Saettigung, Bildbalance) berechnen.
  3. Teilscores mit konfigurierbaren Gewichten (`culling.base_weights`) zu `base_score` kombinieren.
  4. Nicht lesbare oder fehlerhafte Bilder erhalten `analysis_error`, aber keinen stillen Ersatzscore.

**Score-Vertrag:** `base_score` ist eine Fliesskommazahl im Bereich [0,0 bis 1,0]. `analysis_error` wird als `null` oder spezieller Wert `-1` repraesentiert, nie als 0.0.

### 4.2 Persoenlicher Geschmack (lokales CLIP, personal_score)

- **Status:** Pflicht.
- **Zweck:** Ergaenzt die technische Bewertung um eine gelernte, persoenliche Praeferenz. Bewertet Bilder gegen positive/negative Text-Prompts oder aktive Referenzbilder.
- **Ablauf:**
  1. CLIP-Modell laedt nur bei aktiviertem Adapter.
  2. Bild wird gegen aktive Referenzen aus `samples/reference` oder gegen Prompt-Listen bewertet.
  3. Ergebnis ist ausschliesslich `personal_score`; es wird nicht in `base_score` gemischt.
  4. Bilder, die `keep` sind, hoechste Sternklasse erreichen und die aktive Auswahl messbar erweitern, werden automatisch nach `samples/new_refs` vorgeschlagen.
  5. Nur ein manuelles Kopieren nach `samples/reference` aktiviert sie und loest ein Retraining aus.

**Score-Vertrag:** `personal_score` ist eine Fliesskommazahl im Bereich [0,0 bis 1,0] oder `None` bei deaktiviertem/fehlerhaftem Adapter.

### 4.3 Serienerkennung (series_id, series_rank, series_best)

- **Status:** Pflicht.
- **Zweck:** Verhindert, dass mehrere technisch aehnliche Aufnahmen alle gleich behandelt werden. Hebt das beste Bild einer Serie hervor.
- **Ablauf:**
  1. Gruppierung ueber Aufnahmezeit, Bild-Embedding, visuelle Aehnlichkeit oder deterministische Dateinamenlogik als Fallback.
  2. Pro Bild werden Serien-ID, -Groesse, -Rang, `series_best`-Flag und Abstand zum Besten gespeichert.
  3. Das Bestbild darf hoechstens um eine Klasse aufgewertet werden.
  4. Andere Bilder duerfen nur mit dokumentierter Distanz zum Bestbild abgewertet werden.

**Serien-Vertrag:** `series_id` ist eine eindeutige Zeichenkette pro Serie innerhalb eines Batches. `series_rank` ist 1-basiert (1 = bestes Bild). `series_best` ist ein boolescher Wert.

### 4.4 Eye-Score (geschlossene Augen)

- **Status:** Pflicht.
- **Zweck:** Erkennt geschlossene Augen als leichtes Korrektursignal.
- **Ablauf:**
  1. Nur bei genau einem ausreichend grossem Gesicht im Bild.
  2. ONNX-Zweiklassen-Modell liefert `P(offen)`.
  3. Ergebnis ist `eye_score` (eigene Komponente, nicht Teil von `base_score`).

**Score-Vertrag:** `eye_score` ist eine Fliesskommazahl im Bereich [0,0 bis 1,0] (Wahrscheinlichkeit fuer offene Augen) oder `None`.

### 4.5 Bekannte Gesichtserkennung (Familie, family_score)

- **Status:** Pflicht.
- **Zweck:** Liefert ein moderates positives Signal fuer bewusst gepflegte, bekannte Personen. Keine allgemeine Gesichtserkennung, kein Clustering unbekannter Gesichter.
- **Ablauf:**
  1. Backend (Registry-basiert, Standard: `opencv_yunets_face_cpu`) erzeugt Embedding.
  2. Vergleich gegen aktive Referenzen einer Person (`faces/<slug>/reference` mit `selection.json` Status `active`).
  3. Nur bei eindeutigem Match (Schwelle + Sicherheitsmarge zum Zweitbesten) wird `family_score` gesetzt und ein Personentag vergeben.
  4. Klare Treffer erzeugen Vorschlaege in `faces/<slug>/new_faces`, die ein Mensch durch Kopieren nach `reference` bestaetigt.

**Schutzgrenzen:** Bilder, Bildbytes, Face-Crops, Referenzbilder sowie Bild-Face-CLIP-Embeddings sind ausschliesslich fluechtig im RAM zulaessig und duerfen nie in JSON, Cache, Log, Manifest, CSV, Metadaten oder Report persistiert werden.

**Face-Backend-Vertrag:** Jedes Backend MUSS eine Registry-ID, einen Adapter-Namen, einen Modellhash, einen Provider-Namen, eine Vorverarbeitungs-Pipeline, eine Metrik und einen Auswahlfingerprint bereitstellen.

**Score-Vertrag:** `family_score` ist eine Fliesskommazahl im Bereich [0,0 bis 1,0] oder `None`.

### 4.6 Manual Keep (manual_keep, manual_keep_match)

- **Status:** Pflicht.
- **Zweck:** Ordnet extern (z. B. per WhatsApp) vorab ausgewaehlte, oft komprimierte/kleine Bilder ihrem Original im aktuellen Batch zu und erzwingt fuer dieses `keep`.
- **Ablauf:**
  1. Zweistufig: schneller aufloesungsrobuster Vorfilter (Seitenverhaeltnis, Perceptual Hash).
  2. Danach strenge normalisierte Endpruefung (Verifikationsscore auf EXIF-korrigierten, gleich skalierten Bildern).
  3. Match nur bei Schwelle und ausreichendem Abstand zum Zweitbesten.
  4. Ergebnis erzwingt `keep` mit Grund `manual_keep_match`.
  5. Danach durchlaeuft das Bild normales Scoring; erst nach Zuordnung wird die Quelldatei nach `used` verschoben.

**Manual-Keep-Vertrag:** `manual_keep` ist ein boolescher Wert (`true` bei Match, `false` oder `null` sonst). `manual_keep_match` wird in der Run-Summary als Zaehler gefuehrt.

### 4.7 Metadaten (Rating, Tags, Beschreibung)

- **Status:** Pflicht.
- **Zweck:** Macht Bewertungen und Personentreffer in gaengigen Fotoprogrammen sichtbar.
- **Ablauf:**
  1. Sternrating aus Score-Band bestimmen.
  2. Namespaced Keywords einbetten (`workflow:ai_cull`, `decision:final`, `series:`, `family:match`, `person:<slug>`, `manual_keep:true`).
  3. Per `exiftool` (shell=False) in Bild schreiben.
  4. Nach dem Schreiben zuruecklesen und abgleichen.

**Metadaten-Vertrag:** Metadaten MUessen namespaced sein (Praefix `workflow:`). `failed_metadata` ist ein boolescher Wert. `exiftool_status` ist einer von `success`, `disabled`, `failed`, `sidecar`.

### 4.8 Kalibrierung und Gewichtungsassistent

- **Status:** Pflicht.
- **Zweck:** Lernt aus bestaetigten menschlichen Endentscheidungen, ob die vorhandenen Score-Komponenten anders gewichtet werden sollten. Ersetzt nie die Komponenten selbst.
- **Ablauf:**
  1. Pro manuell freigegebenem Batch entsteht ein unveraenderliches `review_decision_record.json`.
  2. Daraus werden Kennzahlen (terminale Uebereinstimmung, `reject_to_keep_rate` etc.) berechnet.
  3. Optional wird ein Gewichtsvorschlag im Schattenmodus erzeugt.
  4. Eine Aktivierung erfordert bewusste Nutzerfreigabe, erfuellte Gates und bleibt jederzeit rollbackfaehig.

**Kalibrierungs-Vertrag:** `review_decision_record.json` MUSS `batch_id`, `timestamp`, `human_decision`, `predicted_decision`, `agreement`, `config_fingerprint`, `producer_version` enthalten.

---

## 5. Referenzpool-Verwaltung, Rebuild und Nutzen-Ranking

### 5.1 Ziel

Die Referenzpool-Verwaltung ist die gemeinsame Regel fuer Geschmack und bekannte Gesichter. Sie stellt sicher, dass aktive Referenzen klein, qualitativ sinnvoll und divers bleiben. Sie trennt Vorschlagsdateien von aktiven Referenzen, erzwingt menschliche Freigabe, aktualisiert Wahrheitsdateien und baut bei jeder aktiven Aenderung die Referenzbasis neu auf.

### 5.2 Geltungsbereich

Diese Regeln gelten fuer:
- Face-Referenzpools: `WORKFLOW_DATA/faces/<slug>` (je bekannte Person)
- Geschmacks-Referenzpool: `WORKFLOW_DATA/samples`

Nicht Gegenstand dieser Regel sind Manual Keep, technische Culling-Bilder (ausserhalb der speziell konfigurierten Modellbasis) und unbekannte Gesichter.

### 5.3 Ordnerstruktur

Jeder Pool MUSS folgende Struktur haben:

```text
pool_root/
  reference/          # Aktive Referenzen (max. max_active)
  new/                # Vorschlaege (max. max_new, max. max_new_per_batch pro Batch)
  selection.json      # EINZIGE Wahrheit fuer diesen Pool
```

- Face: `pool_root = WORKFLOW_DATA/faces/<slug>`, `new = new_faces`, Dateien = Face-Crops.
- Geschmack: `pool_root = WORKFLOW_DATA/samples`, `new = new_refs`, Dateien = Ganzbilder.

### 5.4 Wahrheitsdatei (selection.json)

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

### 5.5 Bild-Metadaten (in selection.json)

Jeder Eintrag in `images` MUSS folgende Felder enthalten:
- `source_id`
- `batch_id`
- `path` (oder `crop_source`)
- `status` (`active` oder `new`)
- `quality_score`
- `pool_utility_score` (oder `candidate_utility_score`)
- `pool_rank` (nur `active`)
- `approved_at` (nur `active`)

**Face-spezifisch:** `bounding_box`, `face_confidence`, `original_path`.
**Geschmack-spezifisch:** `base_score`.

### 5.6 Kapazitaetsgrenzen

| Grenze | Typ | Wirkung |
|--------|-----|---------|
| `max_active` | Hard Limit | Darf nicht ueberschritten werden; weitere Aktivierungen blockiert. |
| `max_new` | Hard Limit | Darf nicht ueberschritten werden; weitere Vorschlaege blockiert. |
| `max_new_per_batch` | Hard Limit | Pro `batch_id` darf diese Grenze nicht ueberschritten werden. |
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

**Schritte:**
1. Anzahl aktiver Dateien zaehlen.
2. `rank_digits` berechnen.
3. Nutzenranking berechnen.
4. Temporaere Dateien erzeugen.
5. Finale Namen setzen.
6. Neue `selection.json` validieren.
7. `selection.json` atomar ersetzen.
8. `rank_digits` und `pool_build_id` schreiben.

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


## 6. Konfiguration, Deployment, Qualitaet, Aenderungshistorie

### 6.1 Konfiguration (v10.1)

[HIER DIE BESTEHENDEN KONFIGURATIONSBLOECKE AUS V10.1 EINFUEGEN, UNVERAENDERT]

### 6.1.1 Konfiguration PHASE3, Veroeffentlichung und Synology-Photos-API

```yaml
finalization:
  enabled: false
  source_root: "/photo/03_TEMP_DONE"

  publish_to_synology_photos:
    enabled: false
    mode: "move"                  # move | copy
    target_folder: "/volume1/photo/Workflow"
    space: "shared"               # shared | personal
    wait_for_index_seconds: 30
    index_timeout_seconds: 900
    verify_transfer_hashes: true

  synology_api:
    enabled: false
    adapter: "synology_photos"
    auth_profile: "photo_workflow"
    timeout_seconds: 10
    retry_count: 3
    retry_backoff_seconds: 3

    write_rating: true
    write_tags: true
    write_description: false
    write_person_mapping: false

    tag_namespace_prefixes:
      - "workflow:"
      - "decision:"
      - "series:"
      - "family:"
      - "manual_keep:"
    person_tag_prefix: "person:"

    dry_run: false
    require_readback: true
```

**Konfigurationsvertrag:**

- `finalization.enabled` ist standardmaessig `false`.
- `publish_to_synology_photos.enabled` ist standardmaessig `false`; damit ist der Transfer aus `03_TEMP_DONE` standardmaessig deaktiviert.
- Ist `publish_to_synology_photos.enabled: false`, MUSS PHASE3 alle Dateioperationen und jeden API-Aufruf unterlassen.
- Ist `synology_api.enabled: true`, MUESSEN `finalization.enabled` und `publish_to_synology_photos.enabled` ebenfalls `true` sein. Andernfalls ist die Konfiguration unguedltig.
- `mode` MUSS `move` oder `copy` sein; andere Werte sind ein Konfigurationsfehler.
- `source_root` und `target_folder` MUESSEN innerhalb von `paths.basedir` liegen.
- `target_folder` MUSS als von Synology Photos indexierter Bereich dokumentiert und vor produktiver Aktivierung im Pilotbetrieb geprueft sein.
- `write_person_mapping` MUSS standardmaessig `false` bleiben und darf nur nach expliziter Capability-Pruefung und Datenschutzfreigabe verwendet werden.
- `dry_run: true` darf weder Dateien uebertragen noch API-Schreiboperationen ausfuehren.

### 6.1.2 API-Adapterprinzip (Vorschlag)

Ein konkreter Synology-Photos-Endpunkt, dessen Verfuegbarkeit und Schreibmoeglichkeiten nicht vorab nachgewiesen sind, darf nicht als harte Annahme in die Fachlogik eingebaut werden. Deshalb wird die Integration ueber einen Capability-gesteuerten Adapter umgesetzt.

```python
class SynologyPhotosAdapter(Protocol):
    def healthcheck(self) -> ApiCapabilityReport: ...
    def resolve_item(self, target_path: str, space: str) -> ResolvedPhotoItem: ...
    def get_metadata(self, item_id: str) -> PublishedMetadata: ...
    def set_rating(self, item_id: str, rating: int) -> ApiWriteResult: ...
    def ensure_tags(self, item_id: str, tags: list[str]) -> ApiWriteResult: ...
    def set_description(self, item_id: str, description: str) -> ApiWriteResult: ...
```

Die API-Schicht darf keine Culling-Entscheidungen treffen und keine Dateimoves ausfuehren. Sie erhaelt nur ein bereits aufgeloestes Item und ein lokal erzeugtes, erlaubtes Metadaten-Payload.

**Capability-Gate:** Vor jeder schreibenden Operation prueft und dokumentiert der Adapter:

- Authentisierung erfolgreich.
- Gewuenschter Bereich (`shared` oder `personal`) erreichbar.
- Bild im Zielpfad eindeutig als Synology-Photos-Item aufloesbar.
- Rating-Schreiben unterstuetzt.
- Tag-Operationen unterstuetzt.
- Beschreibungsschreiben unterstuetzt.
- Optionale Personen-Zuordnung unterstuetzt.

Eine nicht nachgewiesene Fae higkeit gilt als `unsupported`. Sie darf nicht ueber nicht dokumentierte private Endpunkte produktiv erzwungen werden.

**Sicheres Item-Matching:** Die API darf ein Bild nicht allein anhand seines Dateinamens finden. Die empfohlene Reihenfolge ist:

1. Serverseitiger Pfad bzw. API-Pfad, sofern verfuegbar.
2. Exakter relativer Pfad unter dem veroeffentlichten Batch-Zielpfad.
3. Dateiname plus Batch-Zielpfad.
4. Unterstuetzte eindeutige Dateieigenschaft.

Mehrdeutige Treffer fuehren zu `item_ambiguous`. In diesem Fall werden keine Metadaten geschrieben.

**Metadaten-Mapping:**

| Workflow-Quelle | API-Ziel | Regel |
|-----------------|----------|-------|
| Lokales Sternrating | Rating | Wert 0–5 unveraendert uebertragen. |
| `workflow:ai_cull` | Tag | Nur bei aktivierter Tag-Synchronisierung. |
| `decision:<final>` | Tag | Z. B. `decision:keep`. |
| `series:best` bzw. Serien-Tag | Tag | Nur bereits vorhandene, erlaubte Tags. |
| `family:match` | Tag | Kein unbekannter Personenbezug. |
| `manual_keep:true` | Tag | Nur bei vorhandenem Manual-Keep-Ergebnis. |
| `person:<slug>` | Kontrollierter Tag oder Personen-Zuordnung | Standard: kein Personen-Mapping; echte Zuordnung nur bei expliziter Freigabe. |
| Freigegebener Beschreibungstext | Beschreibung | Nur bei `write_description: true`. |

**Nicht an die API uebertragen werden:**

- Bildbytes, Face-Crops, Embeddings, Referenzbilder.
- Interne Hashes, Caches, Fehlerursachen, lokale Dateisystempfade.
- Unbekannte Personen, unbekannte Gesichter und Gesichtskandidaten.
- Zugangsdaten, Tokens oder Sessioninformationen.

**Idempotenz und Ruecklesepruefung:**

- Bereits vorhandene Tags duerfen nicht dupliziert werden.
- Ein bereits korrektes Rating ist ein Erfolg, kein Fehler.
- Fehlende oder abweichende Werte duerfen gezielt nachgezogen werden.
- Ist `require_readback: true`, wird nach dem Schreiben erneut gelesen und mit dem erwarteten Payload verglichen.
- Ein Schreibvorgang ohne bestaetigbare Ruecklesepruefung hat den Status `partial`, nicht `success`.

**Fehlerklassen:**

| Fehlerklasse | Wirkung |
|--------------|---------|
| `auth_failed` | API-Teil blockieren; Transfer nicht zurueckrollen. |
| `capability_unsupported` | Nur betroffene Funktion ueberspringen und melden. |
| `item_not_found` | Bis Timeout warten/retry; kein Schreiben. |
| `item_ambiguous` | Benutzeraktion erforderlich; kein Schreiben. |
| `transient_api_error` | Begrenzt retry mit Backoff. |
| `validation_error` | Mapping/Konfiguration korrigieren; Batch blockieren. |
| `readback_mismatch` | Status `phase3_api_metadata_partial`; spaeter fortsetzen. |

### 6.2 Deployment

[HIER DIE BESTEHENDEN DEPLOYMENT-REGELN AUS V10.1 EINFUEGEN, UNVERAENDERT]

### 6.3 Qualitaet und CI

[HIER DIE BESTEHENDEN QUALITAETS- UND CI-REGELN AUS V10.1 EINFUEGEN, UNVERAENDERT]

### 6.4 Aenderungshistorie

| Version | Datum | Autor | Beschreibung |
|---------|-------|-------|--------------|
| 10.0 | 2026-08-03 | MaiTaiMa, Perplexity AI | Erste harmonisierte Vollfassung |
| 10.1 | 2026-08-04 | MaiTaiMa, Perplexity AI | Vollstaendige, bereinigte und konsolidierte Fassung mit Referenzpool-Verwaltung, Face-Crops, dynamischem Ranking und vollstaendigen Anhaengen |
| 10.2 | 2026-08-04 | MaiTaiMa, Perplexity AI | Additive Erweiterung um optionale PHASE3: konfigurierbarer Transfer aus 03_TEMP_DONE in einen Synology-Photos-indexierten Zielpfad (Move/Copy), expliziter Publish-disabled-Betrieb ohne Datei aenderungen, optionaler capability-gesteuerter API-Adapter fuer Rating/Tags/Beschreibung, Resume, Reporting und Anhaenge U–W. PHASE1, PHASE2 und alle v10.1-Vertraege bleiben unveraendert. |

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

#### L1 – Begriffskonsistenz

- **Batch-ID:** Immer `batchid`.
- **WorkUnit:** Immer `WorkUnit`.
- **Face-Backend:** Immer `Face-Backend`.
- **Manual Keep:** Immer `Manual Keep`.
- **Review-Record:** Immer `Review-Record`.
- **Calibration-Index:** Immer `Calibration-Index`.

#### L2 – Referenzintegritaet

- **Anhang-Referenzen:** Immer mit `Anhang X`.
- **Kapitel-Referenzen:** Immer mit `Kapitel X`.
- **Abschnitts-Referenzen:** Immer mit `Abschnitt X.Y`.
- **Keine relativen Pfadverweise.**

#### L3 – Datenvertragskohaerenz

- **Alle Artefakte:** `schema_version`, `created_at`, `updated_at`, `producer_version`.
- **Alle Hashes:** SHA256.
- **Alle States:** Atomar, mit Zeitstempel und Hash.
- **Alle Quarantaene-Faelle:** Mit Grund, Zeit, Hash nach `WORKFLOW_DATA/runtime/quarantine` kopieren.

#### L4 – Zustandsautomaten-Praezisierung

- Alle Ueberg aenge atomar und protokolliert.
- Rueckwaerts-Ueberg aenge nur bei Quarantaene.
- Blockierende Zustaende in Run-Summary melden.
- Pausierte Zustaende mit Zeitstempel, Grund und Hash protokollieren.

#### L5 – Kapitel-Querverweise

- Alle Kapitel konsistent nummeriert.
- Alle Anhaenge konsistent benannt.
- Querverweise immer mit Abschnitt/Anhang.
- Keine impliziten Referenzen.

#### L6 – Glossar-Vervollstaendigung

- Alle Begriffe im Glossar definiert.
- Neue Begriffe sofort ergaenzen.
- Begriffs aenderungen in CHANGELOG.md dokumentieren.

#### L7 – Anhang-Konsolidierung

- Thematisch konsistent, kein Duplikat.
- Alphabetische Reihenfolge.
- Konsistente Querverweise.

#### L8 – Stil- und Formatvereinheitlichung

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

#### N1 – Repository-Uebersicht

Das GitHub-Repository enthaelt den vollstaendigen Code, die Dokumentation und die Konfiguration fuer den Synology Photo Workflow.

#### N2 – Ordnerstruktur (Beispiel)

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

#### N3 – Datenablage

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

#### N4 – Wichtige Regeln

1. Git enthaelt nie Modellgewichte, private Bilder, Referenzen, Face-Crops, Embeddings, Laufzeitdaten, Caches, Logs oder Secrets.
2. NAS enthaelt alle Workflow-Daten und Konfiguration mit Produktionspfaden.
3. Docker-Container enthaelt nur Code und mountet NAS-Pfade.

---

### Anhang O — Skript-Anforderungen

#### O1 – Geltungsbereich

Diese Anforderung gilt fuer alle Skript-Dateien im Repository.

#### O2 – Struktur-Anforderungen

Jede Skript-Datei MUSS eine feste Struktur haben:

1. Header-Kommentar (6–10 Zeilen).
2. Abschnitts-Kommentare (2–3 Zeilen pro Abschnitt).
3. Funktions-Kommentare (3–5 Zeilen pro Funktion).
4. Einzeiler-Kommentare fuer komplexe Bedingungen.

#### O3 – Kommentar-Dichte und Lesbarkeit

- Header: 6–10 Zeilen.
- Jede Funktion: 3–5 Zeilen Kommentar.
- Jeder Abschnitt: 2–3 Zeilen Kommentar.
- Ca. 20 % Kommentare im Skript.
- Sprechende Namen, konsistente Formatierung, max. 80–100 Zeichen pro Zeile.

#### O4 – Beispiel-Header

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

#### O5 – Beispiel-Abschnitt

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

#### O6 – Beispiel-Funktion

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

#### O7 – Validierung und Abnahme

- Header-Kommentar vorhanden?
- Abschnitts-Kommentare vorhanden?
- Funktions-Kommentare vorhanden?
- Ca. 20 % Kommentare?
- Sprechende Namen?
- Konsistente Formatierung?

Bei Fehlern: Skript ungueltig markieren, loggen, manuelle Korrektur.

#### O8 – Versionierung und Aenderungshistorie

- Jede Skript-Datei braucht Versionsnummer im Header.
- Jede Aenderung muss im Header dokumentiert werden.
- Jede Aenderung muss zusaetzlich im CHANGELOG.md dokumentiert werden.

---

### Anhang P — README-Anforderungen fuer Ordner

#### P1 Geltungsbereich

Gilt fuer alle README-Dateien im NAS-Workflow-Bereich:

- `PHOTO_WORKFLOW/README.md`
- `TEMP_SD/README.md`, `TEMP_IMAGES/README.md`, `TEMP_DONE/README.md`, `TEMP_ERROR/README.md`
- `MANUAL_KEEP/README.md`, `MANUAL_KEEP/inbox/README.md`, `MANUAL_KEEP/used/README.md`
- `WORKFLOW_DATA/README.md` und alle direkten Unterordner

#### P2 Pflichtfelder pro README

1. Zweck
2. Eingaben
3. Prozess
4. Ausgaben
5. Manuelle Aktionen
6. Lebenszyklus
7. Fehlerfaelle
8. Konfiguration (optional, falls relevant)

#### P3 Format und Umfang

- Markdown, klare Ueberschriften, Aufzaehlungen mit Bindestrichen.
- Mindestens 100, maximal 500 Woerter.
- Deutsch, technisch praezise, frei von Floskeln.
- Mindestens ein konkretes Beispiel.
- Keine externen URLs.

#### P4 Validierung

- Alle 8 Pflichtfelder vorhanden?
- Wortumfang eingehalten?
- Ein Beispiel enthalten?
- Keine externen URLs?
- Technische Korrektheit?

#### P5 Versionierung

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

## Anhang U – PHASE3-Finalisierungsvertrag

### U1 Geltungsbereich

PHASE3 gilt nur für JPG-Batches, die alle bestehenden PHASE1- und PHASE2-Verträge erfüllt haben und `phase2_completed` besitzen. PHASE3 ist optional und lässt bei deaktivierter Veröffentlichung alle Bilddateien in `03_TEMP_DONE` unverändert.

### U2 Transfervertrag

Ein Transfer beginnt nur mit `publish_to_synology_photos.enabled: true`. Vor einer Dateiaktion wird ein atomar validiertes `finalization_manifest.json` geschrieben. Das Manifest enthält mindestens `batch_id`, Zeitstempel, Quelle, Ziel, Transfermodus, Konfigurationsfingerprint sowie für jede Datei relativen Pfad, Größe und SHA256.

Ein `move` gilt erst als abgeschlossen, wenn der Zielbestand vollständig hashgleich geprüft wurde. Ein `copy` verändert die Quelle nicht. Kollidierende Zielbatches dürfen nie überschrieben werden.

### U3 Publish-disabled-Vertrag

Ist `finalization.enabled: true`, aber `publish_to_synology_photos.enabled: false`, muss PHASE3:

- den Phase-2-State, die Konfiguration und Pfade prüfen.
- einen klaren Reporteintrag erzeugen.
- optional den State `phase3_publish_disabled` schreiben.
- keine Bilddatei kopieren, verschieben, umbenennen oder löschen.
- keinen API-Aufruf ausführen.

### U4 Indexierungs- und API-Vertrag

Eine feste Wartezeit allein beweist keine Synology-Indexierung. Nach Ablauf der Mindestwartezeit müssen die Zielbilder eindeutig als Synology-Photos-Items auflösbar sein. Erst danach darf die API Metadaten schreiben.

### U5 Verbotene Wirkungen

PHASE3 darf keine ARWs, ZIP-Archive, Culling-Werte, Review-Records, Referenzpools oder Kalibrierungsdaten verändern. Sie darf niemals unbekannte Gesichter persistieren oder veröffentlichen.

---

## Anhang V – Synology-Photos-API-Adaptervertrag

### V1 Authentisierung und Secrets

Secrets liegen außerhalb von Git. Das Auth-Profil ist nur eine Referenz. Tokens, Cookies, Passwörter und vollständige Antwortpayloads dürfen nie geloggt werden. HTTPS und Zertifikatsprüfung sind standardmäßig verpflichtend.

### V2 API-Fähigkeiten

Der vollständige Originaltext der v10.1 ist enthalten. Kein bestehender Anhang A–T wurde gekürzt, entfernt oder umnummeriert. Der Transfer aus `03_TEMP_DONE` ist mit `publish_to_synology_photos.enabled` ausdrücklich optional und standardmäßig deaktiviert. Deaktivierter Transfer führt zu keiner Dateiänderung und keinem API-Aufruf. API ist nur bei aktiviertem und erfolgreich abgeschlossenem Transfer möglich. PHASE3 ist im Stil der bestehenden v10.1 als Status, Zweck, Ablauf, Vertrag und Beispiel beschrieben. `move` und `copy` sind beide eindeutig beschrieben und resume-fähig. `target_folder` ist als indexierter Veröffentlichungszielpfad, nicht nur als API-Konfiguration, definiert. API-Fähigkeiten werden über einen Adapter geprüft; nicht verifizierte Funktionen werden nicht versprochen. PHASE3 kann keine ARWs, Archive, Scores, Referenzpools oder Datenschutzgrenzen verletzen.

### V3 Datenschutz

Die API erhält nur freigegebene Metadaten. Sie erhält niemals Bildbytes, Face-Crops, Embeddings oder Referenzbilder. Personenzuordnungen bleiben standardmäßig deaktiviert.

### V4 Rücklesen

Nach API-Schreiben wird bei aktivierter Rückleseprüfung der Zustand erneut gelesen. Abweichungen sind `partial` und müssen wiederaufnehmbar protokolliert werden.

---

## Anhang W – Abnahmefälle

Die bestehenden ACC-01 bis ACC-15 bleiben unverändert. Ergänzend:

- **ACC-16 (Publish disabled):** `finalization.enabled: true` und `publish_to_synology_photos.enabled: false` verändern keine Bilddatei und rufen keine API auf.
- **ACC-17 (Copy-Transfer):** Ein `phase2_completed`-Batch wird vollständig hashgleich in `target_folder` kopiert; Quelle bleibt vollständig erhalten.
- **ACC-18 (Move-Transfer und Resume):** Ein abgebrochener Move erzeugt keinen Datenverlust; ein Resume kopiert/verschiebt keine bereits hashgleichen Dateien erneut.
- **ACC-19 (Indexierung):** Vor der eindeutigen Item-Auflösung findet kein API-Schreiben statt; mehrdeutige Treffer werden blockiert.
- **ACC-20 (Mapping):** Ratings und nur erlaubte Tag-Präfixe werden korrekt übertragen; interne Daten und unbekannte Personen werden nicht übertragen.
- **ACC-21 (Idempotenz):** Wiederholte Läufe erzeugen keine doppelten Tags und verändern korrekte Ratings nicht unnötig.
- **ACC-22 (API-Fehler):** Auth-, Timeout- und Rücklesefehler führen weder zu Datenverlust noch zu einem Rücktransfer.

---

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
