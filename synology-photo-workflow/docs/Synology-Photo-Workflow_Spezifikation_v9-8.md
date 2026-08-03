<!--
Synology Photo Workflow – Spezifikation v9.8
Datei: docs/Synology-Photo-Workflow_Spezifikation_v9-8.md
Mitentwickler: MaiTaiMa (in Zusammenarbeit mit Perplexity AI)
Erstellt: 2026-08-04
Projektversion: 9.8
Funktion: Vollstaendige, alleinstehende Spezifikation ohne Verweise auf alte Versionen.
Aenderungen in v9.8: Rechtschreib- und Formatkorrekturen, neuer Abschnitt "Architektur und Compliance" (Systemuebersicht, Projektstruktur, Abstraktionsschichten, Datenquellen und Wirkungen, Betriebsskripte, Sicherheits- und Compliance-Grenzen), Aktualisierung der Aenderungs-Historie.
-->

# Synology Photo Workflow – Spezifikation v9.8

**Status:** Verbindliche, alleinstehende Spezifikation fuer den sicheren, wiederaufnehmbaren Synology Photo Workflow.

**Zielsetzung:** Dieses Dokument ist die alleinige normative Quelle fuer Entwicklung, Betrieb, Test und Aenderungen. Es ersetzt alle frueheren Versionen dieser Spezifikation. Abweichende aeltere Fassungen oder Teildokumente sind nicht mehr gueltig.

---

## 0. Lesart und Vorrang

### 0.1 Normative Schluesselwoerter

Die Schluesselwoerter **MUSS**, **DARF NICHT**, **SOLL** und **KANN** sind normativ.

- **MUSS** kennzeichnet eine zwingende Anforderung.
- **DARF NICHT** kennzeichnet ein ausdrueckliches Verbot.
- **SOLL** kennzeichnet eine empfohlene Praxis.
- **KANN** kennzeichnet eine optionale Moeglichkeit.

### 0.2 Abwaegungslogik

Bei Zielkonflikten gilt **zuerst** und **vorrangig vor allen anderen Regeln** folgende Abwaegungslogik:

1. **Sicherheit:** Keine unkontrollierten Datei aenderungen, Datenverluste, Modell-Downloads oder Daten uebertragungen. Bilder, Referenzen, Gesichts-Crops und Vektoren verlassen nie die NAS.
2. **Stabilitaet:** Ein einzelnes fehlerhaftes Foto, ein Modellfehler oder ein defekter Ordner stoppt nicht den ueblichen Lauf.
3. **Nutzen:** Jede Funktion muss Fotos besser vorsortieren, Nachvollziehbarkeit oder Betriebssicherheit erhoe hen.
4. **Einfachheit:** Wenige verstaendliche Optionen; keine technische Doppelstruktur ohne nachgewiesenen Nutzen.
5. **NAS-Performance:** Ein langsamer, begrenzter und ueber mehrere Tage fortsetzbarer Betrieb ist akzeptabel.

**Richtwert NAS-Performance:** Auf einer typischen NAS (z. B. 2–4 Kerne, 4–8 GB RAM) sind ca. 500–1000 Bilder pro Tag realistisch. Bei groesseren Batches ist der Betrieb ueber mehrere Tage fortsetzbar.

Diese Reihenfolge ist **verbindlich** und darf durch keine andere Regel, keine Konfiguration und keine Implementierungsentscheidung ueberstimmt werden. Sie gilt projektweit, fuer Fachlogik, Architektur, Konfiguration, Betrieb und Tests.

### 0.3 Sekundaere Vorranghierarchie

Erst **nach** Anwendung der Abwaegungslogik aus 0.2 gilt in dieser Reihenfolge:

1. Datenintegritaet, Schutz von Originalen, Datenschutz und Sicherheitsgrenzen.
2. Ausdrueckliche Verbote.
3. Haupttext der Spezifikation.
4. Normative Anhaenge.
5. Nichtnormative Referenzwerte.

Ein Entwickler darf interne Algorithmen austauschen, wenn alle externen Vertraege, Artefaktformate, Sicherheitsgrenzen und Abnahmekriterien erhalten bleiben und die Abwaegungslogik aus 0.2 nicht verletzt wird.

### 0.4 Geltungsbereich und Zielsetzung

Diese Spezifikation definiert den kleinen, produktiv sinnvollen Kern des Synology Photo Workflow. Die Implementierung soll eine vorhandene Codebasis gezielt pruefen und nur die hier beschriebenen Funktionen ergaenzen oder reparieren. Sie soll nicht zu einer grossen allgemeinen Foto- oder Gesichtsdatenplattform ausgebaut werden.

Der Workflow verfolgt drei gleichrangige Ziele:

1. Originaldaten vor Verlust schuetzen.
2. Den wiederkehrenden manuellen Aufwand klein halten.
3. Die Qualitaet der Entscheidungen ueber nachvollziehbare Lernbeispiele verbessern.

Bei Zielkonflikten gilt die Abwaegungslogik aus 0.2.

---

## 1. Architektur und Compliance

### 1.1 Systemuebersicht

Das Projekt trennt Betriebsschnittstelle, CLI, Fachmodule und den persistenten NAS-Datenbereich. Shell-Skripte pruefen nur Umgebung und starten den Workflow; sie enthalten keine Geschaeftslogik. Die Python-CLI laedt `config/config.yaml`, validiert die Konfiguration und delegiert an spezialisierte Module. Die Fachmodule erzeugen testbare Ergebnisobjekte und kapseln Dateisystemmutationen.

### 1.2 Projektstruktur

- `NAS_EXAMPLE/`: Beispiel fuer den persistenten NAS-Bereich.
  - `TEMP/`: Arbeitsbereich aus `config.paths.basedir`.
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

### 1.3 Abstraktionsschichten

`app.cli` verarbeitet Argumente, laedt Konfiguration und uebersetzt Ergebnisse in Exit-Codes. `app.configuration` validiert YAML, Pfade und Fingerprints. `app.inventory` prueft Eingangsstabilitaet, Endungen und exakte JPG-/ARW-Paarbildung. `app.phases` orchestriert die Phasen, ohne Bewertungs- oder Archivdetails zu duplizieren. `app.culling` berechnet Merkmale, Komponentenscores, Sterne und Vorschlaege. `app.metadata` kapselt Exiftool, Keyword-Merge und Ruecklesepruefung. `app.archives` kapselt Archivplan, ZIP-Erstellung, Validierung, Hashes, Kollisionen und Aktivierung.

`app.batchstate` haelt den Zustandsautomaten und atomare Updates. `app.locks` schuetzt parallele Laeufe. `app.calibration` erzeugt Records, Indizes und Readiness-Auswertung. `app.facebackend` definiert modellneutrale Protokolle und die Backend-Registry. `app.familyrecognition` verarbeitet Referenzen, Caches und Matchlogik, ohne Fachlogik in Adapter zu verlagern. `app.reporting` erzeugt Logs, Scheduler-Ausgabe und Run-Summaries. Diese Trennung ist der vorgesehene Erweiterungspunkt: Ein neues Face-Backend gehoert in Adapter/Registry, eine neue Bewertungsregel in `culling`, ein anderes Archivformat in `archives` und keine dieser Aenderungen in Shell-Skripte.

### 1.4 Datenquellen und Wirkungen

Die Inventarisierung bezieht Daten direkt aus `TEMP_SD`; sie erzeugt Manifeste und Paarbindungen. `culling` bezieht Bilddaten und Gewichte aus `config.culling`; seine Scores wirken auf Sterne, Vorschlaege und Review-Listen. `metadata` bezieht Entscheidungen und erlaubte Schluessel aus den Batch-Ergebnissen; es wirkt ausschliesslich bei aktiviertem Schreibmodus auf Bildmetadaten. `archives` beziehen nur validierte Phase-2-Kandidaten und erzeugen verifizierte ZIPs im persistenten Bereich. Die Loeschlogik bezieht sich auf Archivmanifest, Hash und State; ohne diese Quellen wird kein ARW geloescht.

Face-Erkennung bezieht Modelle aus dem gewaehlten Backend, Referenzen und Caches aus `WORKFLOW_DATA`. Ihre Wirkung ist auf Match-Ergebnis, Familien-Score und gegebenenfalls Personentags begrenzt; bei deaktivierter Funktion entstehen keine Face-Artefakte. Kalibrierung bezieht bestaetigte Review-Records und wirkt auf Reports und Empfehlungen, niemals selbst aendig auf Automatikflags.

### 1.5 Betriebsskripte

`preflight.sh` validiert Mount, Docker und Konfiguration ohne Bildverarbeitung. `dsm-acceptance-preflight.sh` ist die DSM-orientierte Variante. `run-phase1.sh` und `run-phase2.sh` rufen jeweils nur den gleichnamigen CLI-Befehl auf. `run-workflow.sh` startet den kanonischen `run`-Befehl. Alle Skripte verwenden `set -Eeuo pipefail`, klare Pfadvariablen und einen Abbruch bei unsicherer Umgebung.

### 1.6 Sicherheits- und Compliance-Grenzen

Alle Pfade muessen innerhalb von `paths.basedir` liegen. Phase 2 benoetigt valide Freigabe, Locks, konsistenten Batch-State und ein verifiziertes Archiv. Archive werden nicht ueberschrieben; unsichere Kollisionen erzeugen neue Namen. Persistente Daten liegen ausserhalb des Container-Images. Private Bilder, Laufzeitdaten, lokale Secrets und Caches gehoeren nicht in Git. Die zentrale `config.yaml` ist eine bewusste Projektabweichung von einer separaten Beispielvorlage und muss daher secrets-frei bleiben.

---

## 2. Zielbild und Schutzgrenzen

### 2.1 Zielbild

Der Workflow verarbeitet Foto-Batches auf einem Synology-NAS in zwei Phasen:

- **Phase 1** analysiert, bewertet und bereitet die menschliche Pruefung vor.
- **Phase 2** archiviert und bereinigt ARWs erst nach einer nachweislich sicheren Endentscheidung.

Original-JPGs und ARWs duerfen weder still ueberschrieben noch geloescht werden. Bekannte Gesichtserkennung verarbeitet nur bewusst gepflegte bekannte Personen. Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt, als Kandidat protokolliert oder als Referenz aktiviert werden. Ein Gesichtstreffer darf technische Mindestqualitaet, Manual Keep oder Schutzregeln niemals ueberstimmen.

### 2.2 Schutzgrenzen

Folgende Datenklassen unterliegen unterschiedlichen Schutzregeln:

| Klasse | Inhalt | Schutzregel |
|--------|--------|-------------|
| Originale | Kamera-JPGs und ARWs | Nur im geregelten Phasenablauf veraenderbar. |
| Abgeleitete Medien | Crops, ZIPs, Vorschauen, Kopien | Nur mit Herkunft, Hash und dokumentierter Aktion. |
| Steuerdaten | Manifeste, Zustaende, Logs, Indizes, Caches | Schema-validiert, atomar, rekonstruierbar. |

### 2.3 Datenklassen

Es gibt drei Datenklassen mit unterschiedlichen Regeln:

1. **Originaldaten (Kamera-JPGs, ARWs):** Duerrfen nie still ueberschrieben oder geloescht werden.
2. **Abgeleitete Medien (Crops, ZIPs, Vorschauen, Kopien):** Duerrfen nach dokumentierten Regeln verwaltet werden.
3. **Steuerdaten (Manifeste, Zustaende, Logs, Indizes, Caches):** Muessen schema-validiert, atomar und rekonstruierbar sein.

Kein abgeleitetes Artefakt darf eine Aktion an einem Original ausloesen, die nicht bereits durch die aktive-JPG-Regel und die jeweilige Automatikstufe erlaubt ist.

---

## 3. Ordner, Namen und Datenklassen

### 3.1 Kanonische Arbeitsordner (ergaenzt)

Folgende Arbeitsordner sind kanonisch:

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

### 3.2 Batch-Struktur

Ein Batch enthaelt verbindlich die Unterordner:

- `ARW` (fuer ausgelagerte ARWs)
- `SAVE` (fuer JPG-Archiv und Scores)
- `Review` (fuer zur Pruefung vorgemerkte Bilder)
- `Rejected` (fuer abgelehnte Bilder)

Nur JPGs im Batch-Hauptordner gelten als aktiv. Ein aus `Review` oder `Rejected` in den Hauptordner zurueckgelegtes JPG ist wieder aktiv und schuetzt sein passendes ARW.

### 3.3 Aktive JPGs und ARW-Schutz

Ein ARW ist geschuetzt, wenn ein aktives JPG mit demselben eindeutig normalisierten Basename existiert. Mehrdeutige Paarungen, mehrere wirksame JPG-Kopien, fehlende Quellhashes oder widerspruechliche Ordnerzustaende blockieren Phase 2 mit `review_state_invalid`; es darf keine ARW-Aktion stattfinden.

Die Endentscheidung wird ohne Neuberechnung von Scores ausschliesslich aus dem vorgefundenen Batch-Zustand abgeleitet:

1. Ein valides Manual-Keep-Signal ergibt `keep`.
2. `Rejected` ergibt `reject`.
3. `Review` ergibt `review`.
4. Hauptordner ergibt `keep`.

Fehlt ein Bild oder ist die Zuordnung nicht eindeutig, ist der ganze Batch blockiert.

**Beispiel:** Ein Batch mit 100 JPGs und 80 ARWs wird wie folgt verarbeitet:
- 90 JPGs bleiben im Hauptordner (`keep`)
- 5 JPGs wandern nach `Review`
- 5 JPGs wandern nach `Rejected`
- Alle 80 ARWs mit passendem JPG im Hauptordner oder `Review` sind geschuetzt
- ARWs zu den 5 JPGs in `Rejected` koennen nach Phase-2-Archivierung geloescht werden

### 3.4 Manual Keep, inbox, used (vollstaendig ersetzt)

**MANUAL_KEEP** ist der kontrollierte Eingang fuer externe, vorab ausgewaehlte JPGs (z. B. per WhatsApp erhalten). Die Zuordnung erfolgt streng getrennt vom Culling, Serienlogik und persoenlichen Geschmack.

#### 3.4.1 Ordnerstruktur

```text
MANUAL_KEEP/
├── README.md
├── inbox/
│   └── README.md
└── used/
    └── README.md
```

#### 3.4.2 Zuordnungslogik

Manual Keep liest `MANUAL_KEEP/inbox/` nur fuer den aktuellen Batch. Die Standardmetrik ist Kosinus aehnlichkeit (higher_is_better, Bereich 0 bis 1) mit Schwelle 0,95 und Mindestmarge 0,03 zum zweitbesten Treffer; ein eindeutiger Treffer erzwingt `keep` mit Grund `manual_keep_match`.

1. **Vorfilter:** Schneller, aufloesungsrobuster Abgleich (Seitenverhaeltnis, Perceptual Hash).
2. **Endpruefung:** Strenge, normalisierte Verifikation auf EXIF-korrigierten, gleich skalierten Bildern.
3. **Match:** Nur bei Schwelle **und** ausreichendem Abstand zum Zweitbesten.
4. **Zuordnung:** Ergebnis erzwingt `keep` mit Grund `manual_keep_match`.
5. **Verschobene Datei:** Nach erfolgreicher Zuordnung wird die Quelldatei nach `MANUAL_KEEP/used/` verschoben.

#### 3.4.3 Fehlerfaelle

- **Mehrdeutige Zuordnung:** Datei bleibt in `inbox/`, wird geloggt und in der Run-Summary gez aehlt.
- **Nicht lesbare Datei:** Datei bleibt in `inbox/`, wird geloggt und in der Run-Summary gez aehlt.
- **Nicht zuordenbare Datei:** Datei bleibt in `inbox/`, wird geloggt und in der Run-Summary gez aehlt.

**Beispiel:** Ein Batch enthaelt 3 Manual-Keep-Bilder in `inbox/`:
- Bild A: Eindeutiger Match (Schwelle 0,97, Marge 0,05) → `keep`, Datei wandert nach `used/`
- Bild B: Mehrdeutig (Schwelle 0,96, Marge 0,01) → bleibt in `inbox/`, Log-Eintrag, Summary-Zaehler
- Bild C: Nicht zuordenbar (kein Match ueber 0,90) → bleibt in `inbox/`, Log-Eintrag, Summary-Zaehler

#### 3.4.4 Konfiguration

- `manual_keep.similarity_backend`
- `manual_keep.comparison_long_edge`, `manual_keep.aspect_ratio_tolerance`, `manual_keep.perceptual_hash_max_distance`
- `manual_keep.verification_threshold`, `manual_keep.minimum_best_second_margin`, `manual_keep.allow_automatic_move`

#### 3.4.5 Implementierung

- `app.manual_keep` (Orchestrierung)
- `app.manual_keep_similarity` (`ResolutionAwareSimilarity`)
- Gemeinsam genutzter `app.image_features` (`ImageFeatureService`)

---

## 4. Batch, Phasen und Transaktionsvertrag

### 4.1 Batch-ID und Zustandsdatei

Die unver aenderliche `batchid` lautet `source-folder-name+fingerprint(8)` und bleibt beim Wechsel zwischen allen Arbeitsordnern gleich. Pro Batch gibt es genau eine zentrale Zustandsdatei `WORKFLOW_DATA/runtime/state/{batchid}.json`; globale Zustandsdateien sind unzulaessig.

**Batch-ID-Bildung:** Die `batchid` wird bei Erstkontakt mit dem Batch aus dem Ordnernamen und einem 8-stelligen Fingerprint (SHA256, gekuerzt) gebildet. Sie bleibt ueber alle Ordnerwechsel hinweg unver aendert.

**Beispiel:** Ein Ordner `2024-08-15_Geburtstag` erhaelt die `batchid` `2024-08-15_Geburtstag+a3f7c2e1`.

### 4.2 Phase 1

Phase 1 MUSS in dieser Reihenfolge arbeiten:

1. Stabilitaets-, Namens-, Lock- und Symlink-Pruefung.
2. Datumsnormalisierung.
3. ARW-Ablage nach `ARW`.
4. Validiertes JPG-Archiv.
5. Feature- und Score-Ermittlung einschliesslich Manual Keep und Serienlogik.
6. Eingebettete Metadaten, CSV und Phase-1-Manifest.
7. Sichtbare Ablage in Hauptordner, `Review` oder `Rejected`.
8. Atomare Uebergabe nach `TEMP_IMAGES`.

### 4.3 Phase 2

Phase 2 MUSS zuerst Phase-1-Manifest und Endentscheidungen validieren, bei manueller Freigabe den unver aenderlichen Review-Record schreiben und erst danach archivieren. Ein ARW darf nur geloescht werden, nachdem ein vollstaendiges Archiv erzeugt, geprueft, auf demselben Dateisystem atomar aktiviert und mit Hash protokolliert wurde.

Bei jedem Fehler bleibt das ARW erhalten; ARW darf erst nach vollstaendig dokumentierter Bereinigung entfernt werden.

**Phase-2-Start:** Phase 2 beginnt erst nach manueller Freigabe (Move nach `TEMP_DONE`) oder nach explizit zugelassener automatischer Uebergabe (`automatic_handoff`).

**Beispiel:** Ein Batch in `TEMP_IMAGES` wird vom Menschen gesichtet. Nach der Sichtung wird der gesamte Batch nach `TEMP_DONE` verschoben. Dies ist das alleinige Freigabesignal fuer Phase 2.

### 4.4 Zustandsautomat (manuell und automatisch)

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
- `state` (Zustandsname)
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
    "producer_version": "9.8"
}
```

### 4.5 ARW-Loeschung und Archivvertrag

Vor der Bereinigung erzeugt Phase 2 einen unver aenderlichen Archivplan. Das temporaere ARW-Archiv enthaelt fuer jeden Eintrag relativen Pfad, Groesse und SHA-256. Vor Aktivierung werden ZIP-Lesbarkeit, sichere Memberpfade, erwartete Dateiliste, Groesse und Hash jedes Eintrags geprueft. Erst dann wird das Archiv atomar aktiviert und `archive_manifest.json` persistiert.

Existiert ein Zielarchiv mit exakt passendem Plan, Entry-Hashes und Konfigurationsfingerprint, darf es wiederverwendet werden. Existiert es, ist aber abweichend oder nicht vertrauenswuerdig, folgt der erste freie Kollisionsname `..._EXTRA<n>.zip`; `zip_target_collision` ist dann in Log, Summary und Konfliktliste Pflicht. Fremde oder unsichere ZIPs duerfen weder ersetzt noch entfernt werden.

**Querverweis:** Siehe Anhang H (Archivvertrag) fuer detaillierte Anforderungen an ZIP, Kollision, Hash, Aktivierung und Loeschung.

**Archivplan-Details:** Der Archivplan MUSS folgende Felder enthalten:
- `batchid` (Batch-ID)
- `created_at` (ISO8601-Zeitstempel)
- `archive_path` (relativer Pfad zur ZIP)
- `entry_count` (Anzahl der Eintr aeg)
- `total_size` (Gesamtgr oesse in Bytes)
- `entries` (Liste aller Eintr aeg mit Pfad, Groesse, SHA256)
- `config_fingerprint` (SHA256 der effektiven Konfiguration)
- `producer_version` (Versionskennung)

**Beispiel-Archivplan:**
```json
{
    "batchid": "2024-08-15_Geburtstag+a3f7c2e1",
    "created_at": "2024-08-15T16:00:00Z",
    "archive_path": "WORKFLOW_DATA/archives/2024-08-15_Geburtstag+a3f7c2e1_ARW.zip",
    "entry_count": 80,
    "total_size": 2147483648,
    "entries": [
        {
            "relative_path": "ARW/IMG_0001.ARW",
            "size": 26843545,
            "hash": "a3f7c2e1b5d8f9e0c4a6b7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
        }
    ],
    "config_fingerprint": "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
    "producer_version": "9.8"
}
```

---

## 5. Funktionskatalog

Fuer jede Kernfunktion werden definiert:

- **Status:** Pflicht (immer verfuegbar).
- **Zweck:** Kurze fachliche Beschreibung, wozu die Funktion dient.
- **Ablauf:** Wie die Funktion arbeitet (Schrittfolge, Eingaben, Ausgaben).
- **Zusammenspiel:** Wie die Funktion mit anderen Funktionen interagiert; welche Scores/Entscheidungen sie beeinflusst.
- **Sicherheits- und Datenschutzgrenzen:** Was die Funktion explizit nicht darf; welche Daten fluechtig vs. persistent sind.
- **Fehlerverhalten:** Wie die Funktion bei Fehlern, Unsicherheit oder deaktiviertem Zustand reagiert.
- **Konfiguration:** Wo die Funktion konfiguriert wird (YAML-Schluessel, erlaubte Werte, Defaults).
- **Implementierung:** Welche Module zust aendig sind (fachliche Zuordnung, keine Code-Zeilen).

---

### 5.1 Technisches Culling

- **Status:** Pflicht.
- **Zweck:** Ressourcenschonende Basisbewertung ohne Pflicht-KI-Modell. Bewertet Schaerfe, Belichtung und einfache aesthetische Merkmale. Ergebnis ist `base_score`.
- **Ablauf:**
  1. Kleine technische Vorschau erzeugen (256–512 Pixel laengste Kante).
  2. Teilscores fuer Schaerfe (Kantenvarianz), Belichtung (Clipping, Helligkeitsbalance) und Aesthetik (Kontrast, Saettigung, Bildbalance) berechnen.
  3. Teilscores mit konfigurierbaren Gewichten (`culling.base_weights`) zu `base_score` kombinieren.
  4. Nicht lesbare oder fehlerhafte Bilder erhalten `analysis_error`, aber keinen stillen Ersatzscore.
- **Zusammenspiel:**
  - `base_score` ist Pflichtkomponente von `final_score`.
  - Ein Analysefehler betrifft nur das eine Bild (`analysis_error`), nie den ganzen Batch.
  - Ohne KI-Funktionen bleibt die technische Bewertung allein massgeblich.
- **Sicherheits- und Datenschutzgrenzen:**
  - Keine externen Modelle, keine Daten uebertragung.
  - Alle Berechnungen lokal auf der NAS.
- **Fehlerverhalten:**
  - Nicht lesbare Bilder erhalten `analysis_error`, werden aber nicht als `0.0` bewertet.
  - Ein einzelner Fehler stoppt nicht den gesamten Batch.
- **Konfiguration:**
  - `culling.base_weights.sharpness`, `culling.base_weights.aesthetic`, `culling.base_weights.exposure` (nichtnegative Werte, Summe 1,0).
  - `culling.keep_threshold`, `culling.reject_threshold`, `culling.star_rating_bands`.
- **Implementierung:**
  - `app.culling` (`technical_components()`, `final_score()`, `stars()`).

**Score-Vertrag:** `base_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0. `analysis_error` wird als `null` oder spezieller Wert `-1` repraesentiert, nie als `0.0`.

**Beispiel:** Ein Bild mit hoher Schaerfe (0,9), guter Belichtung (0,8) und maessiger Aesthetik (0,5) erhaelt bei Gewichten (0,5, 0,3, 0,2) einen `base_score` von `0,9*0,5 + 0,8*0,3 + 0,5*0,2 = 0,45 + 0,24 + 0,10 = 0,79`.

---

### 5.2 Persoenlicher Geschmack (lokales CLIP)

- **Status:** Pflicht.
- **Zweck:** Ergaenzt die technische Bewertung um eine gelernte, persoenliche Praeferenz. Bewertet Bilder gegen positive/negative Text-Prompts oder aktive Referenzbilder.
- **Ablauf:**
  1. CLIP-Modell laedt (nur bei aktiviertem Adapter).
  2. Bild wird gegen aktive Referenzen aus `samples/reference/` oder gegen Prompt-Listen bewertet.
  3. Ergebnis ist ausschliesslich `personal_score`; es wird nicht in `base_score` gemischt.
  4. Bilder, die `keep` sind, hoechste Sternklasse erreichen und die aktive Auswahl messbar erweitern, werden automatisch nach `samples/new_refs/` vorgeschlagen.
  5. Nur ein manuelles Kopieren nach `samples/reference/` aktiviert sie und loest ein Retraining aus.
- **Zusammenspiel:**
  - `personal_score` ist optionale Komponente von `final_score`.
  - Fehlender oder fehlerhafter Adapter erzeugt `None`, nicht `0.0`.
  - Retraining erfolgt nur bei Aenderung des aktiven Pools (`selection.json`).
- **Sicherheits- und Datenschutzgrenzen:**
  - Modellartefakte, private Bilder, Caches und Logs duerfen nie in Git eingecheckt werden.
  - Modellinstallation ist eine bewusste, separate Verwaltungsaktion (HTTPS, Host-Allowlist, Groessenlimit, SHA256-Pruefung).
  - Bilder und Embeddings sind nur fluechtig im RAM; keine Persistenz in JSON, CSV, Logs oder Manifesten.
- **Fehlerverhalten:**
  - Fehlender oder fehlerhafter Adapter erzeugt `None` (neutral), nicht `0.0`.
  - Ein Modellfehler betrifft nur das eine Bild, nie den gesamten Batch.
- **Konfiguration:**
  - `culling.final_component_weights.personal_score`.
  - Sample-Kapazitaeten (`samples.min_active`, `samples.target_active`, `samples.max_active`, `samples.max_not_used`).
  - Prompt-Listen (`taste.positive_prompts`, `taste.negative_prompts`).
- **Implementierung:**
  - `app.clip_adapter` (neu, ML-Adapter), `app.clip_taste_adapter` (fachlicher Wrapper).
  - Modelle unter `models/taste/`.

**Score-Vertrag:** `personal_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 oder `None` (bei deaktiviertem/fehlerhaftem Adapter).

---

### 5.3 Serienerkennung

- **Status:** Pflicht.
- **Zweck:** Verhindert, dass mehrere technisch aehnliche Aufnahmen alle gleich behandelt werden. Hebt das beste Bild einer Serie hervor.
- **Ablauf:**
  1. Gruppierungueber Aufnahmezeit + Bild-Embedding (visuelle Aehnlichkeit) oder deterministische Dateinamenlogik als Fallback.
  2. Pro Bild werden Serien-ID, -Groesse, -Rang, `series_best`-Flag und Abstand zum Besten gespeichert.
  3. Das Bestbild darf hoechstens um eine Klasse aufgewertet werden.
  4. Andere Bilder duerfen nur mit dokumentierter Distanz zum Bestbild abgewertet werden.
- **Zusammenspiel:**
  - Entscheidet **nie** direkt Keep/Review/Reject.
  - Bei deaktiviertem oder fehlerhaftem Modell bleibt die vorhandene deterministische Serienlogik (Dateinamen, Aufnahmezeit) aktiv.
  - Im Bildmengenmodus darf eine visuelle Serie erst endgueltig geschlossen werden, wenn der gesamte physische Batch analysiert wurde.
- **Sicherheits- und Datenschutzgrenzen:**
  - Serien-Embeddings sind fluechtig im RAM; keine Persistenz.
  - Keine externen Modelle, keine Daten uebertragung.
- **Fehlerverhalten:**
  - Fehlerhafte Serienlogik fuehrt zu neutralem Verhalten (keine Auf-/Abwertung).
  - Ein einzelner Fehler stoppt nicht den gesamten Batch.
- **Konfiguration:**
  - `culling.enable_series_logic` (bool).
  - Zeitfenster fuer Serien (z. B. 60 Sekunden).
  - Mindestclustergroesse (z. B. 3 Bilder).
- **Implementierung:**
  - `app.clip_series_adapter` (Modell, optional).
  - Bestehende `apply_series()` in `app.culling` als Fallback.

**Serien-Vertrag:** `series_id` ist eine eindeutige Zeichenkette pro Serie innerhalb eines Batches. `series_rank` ist 1-basiert (1 = bestes Bild). `series_best` ist ein boolescher Wert.

---

### 5.4 Bekannte Gesichtserkennung / Familie

- **Status:** Pflicht.
- **Zweck:** Liefert ein moderates positives Signal fuer bewusst gepflegte, bekannte Personen. **Keine** allgemeine Gesichtserkennung, kein Clustering unbekannter Gesichter.
- **Ablauf:**
  1. Backend (Registry-basiert, Standard `opencv_yunet_sface_cpu`) erzeugt Embedding.
  2. Vergleich gegen aktive Referenzen einer Person (`faces/<slug>/reference/` mit `selection.json` Status `active`).
  3. Nur bei eindeutigem Match (Schwelle + Sicherheitsmarge zum Zweitbesten) wird `family_score` gesetzt und ein Personentag vergeben.
  4. Klare Treffer erzeugen Vorschlaeg in `faces/<slug>/new_faces/`, die ein Mensch durch Kopieren nach `reference/` bestaetigt.
- **Zusammenspiel:**
  - Ein eindeutiger Match darf `reject` hoechstens auf `review` anheben, nie technische Mindestqualitaet oder Manual Keepueberstimmen.
  - Face-Crops, Embeddings und Referenzbilder duerfen weder in Git, Logs, CSVs noch Manifeste geschrieben werden.
  - Unbekannte Gesichter werden nicht gespeichert, geclustert, indexiert oder getaggt.
- **Sicherheits- und Datenschutzgrenzen:**
  - Bilder, Bildbytes, Face-Crops, Referenzbilder sowie Bild-/Face-/CLIP-Embeddings sind ausschliesslich fluechtig im RAM zul aessig und duerfen nie in JSON, Cache, Log, Manifest, CSV, Metadaten oder Report persistiert werden.
  - Unbekannte Gesichter duerfen nicht gespeichert, geclustert, indexiert, getaggt oder als Referenz aktiviert werden.
  - Modellgewichte, private Bilder, Caches, Logs, Laufzeitdaten und Secrets duerfen nie in Git eingecheckt werden.
- **Fehlerverhalten:**
  - Fehlender oder fehlerhafter Adapter erzeugt `None` (neutral), nicht `0.0`.
  - Ein einzelner Fehler stoppt nicht den gesamten Batch.
- **Konfiguration:**
  - `family_recognition.enabled`, `family_recognition.backend`.
  - `family_recognition.match_threshold` (Default `null` = kein automatischer Match).
  - `family_recognition.min_best_second_margin`.
  - Pool-Richtwerte (`faces.min_active: 30`, `faces.target_active: 40`, `faces.max_active: 50`, `faces.max_not_used: 100`).
- **Implementierung:**
  - `app.face_backend*` (Registry/Adapter, modellneutral).
  - `app.family_recognition` (Fachlogik, **darf keine ML-Bibliothek direkt importieren**).

**Face-Backend-Vertrag:** Jedes Backend MUSS eine Registry-ID, einen Adapter-Namen, einen Modellhash, einen Provider-Namen, eine Vorverarbeitungs-Pipeline, eine Metrik und einen Auswahlfingerprint bereitstellen. `family_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 oder `None`.

---

### 5.5 Eye-Score

- **Status:** Pflicht.
- **Zweck:** Erkennt geschlossene Augen als leichtes Korrektursignal.
- **Ablauf:**
  1. Nur bei genau einem ausreichend grossem Gesicht im Bild.
  2. ONNX-Zweiklassen-Modell liefert `P(offen)`.
  3. Ergebnis ist `eye_score` (eigene Komponente, nicht Teil von `base_score`).
- **Zusammenspiel:**
  - Eigene finale Komponente, niemals Teil von `base_score`.
  - Fuehrt allein nie zu automatischem Reject.
  - Bei Unsicherheit, mehreren oder keinem Gesicht → `None`.
- **Sicherheits- und Datenschutzgrenzen:**
  - Modellartefakte und Embeddings sind fluechtig im RAM; keine Persistenz.
  - Keine externen Modelle, keine Daten uebertragung.
- **Fehlerverhalten:**
  - Bei Unsicherheit, mehreren oder keinem Gesicht → `None`.
  - Ein einzelner Fehler stoppt nicht den gesamten Batch.
- **Konfiguration:**
  - `culling.final_component_weights.eye_score`.
  - Mindestgesichtsgroesse, Mindestkonfidenz.
- **Implementierung:**
  - `app.eye_state_adapter_onnx`.

**Score-Vertrag:** `eye_score` ist eine Fliesskommazahl im Bereich 0,0 bis 1,0 (Wahrscheinlichkeit fuer offene Augen) oder `None`.

---

### 5.6 Manual Keep (aufloesungsunabhaengiger Abgleich)

- **Status:** Pflicht.
- **Zweck:** Ordnet extern (z. B. per WhatsApp) vorab ausgewaehlte, oft komprimierte/kleine Bilder ihrem Original im aktuellen Batch zu und erzwingt fuer dieses `keep`.
- **Ablauf:**
  1. Zweistufig: schneller aufloesungsrobuster Vorfilter (Seitenverhaeltnis, Perceptual Hash).
  2. Danach strenge normalisierte Endpruefung (Verifikationsscore auf EXIF-korrigierten, gleich skalierten Bildern).
  3. Match nur bei Schwelle **und** ausreichendem Abstand zum Zweitbesten.
  4. Ergebnis erzwingt `keep` mit Grund `manual_keep_match`.
  5. Danach durchlaeuft das Bild normales Scoring; erst nach Zuordnung wird die Quelldatei nach `used/` verschoben.
- **Zusammenspiel:**
  - Bewusst **fachlich getrennt** von Culling/Serien/Geschmack.
  - Diese duerfen hoechstens als Kandidaten-Vorfilter dienen, nie allein einen Move best aetigen.
- **Sicherheits- und Datenschutzgrenzen:**
  - Manual-Keep-Bilder (oft komprimierte WhatsApp-JPGs) werden nur im RAM verarbeitet; keine Persistenz von Embeddings.
  - Keine externen Modelle, keine Daten uebertragung.
- **Fehlerverhalten:**
  - Mehrdeutige, nicht lesbare oder nicht zuordenbare Dateien bleiben in `inbox`, werden geloggt und in der Run-Summary gez aehlt.
  - Ein einzelner Fehler stoppt nicht den gesamten Batch.
- **Konfiguration:**
  - `manual_keep.similarity_backend`.
  - `manual_keep.comparison_long_edge`, `manual_keep.aspect_ratio_tolerance`, `manual_keep.perceptual_hash_max_distance`.
  - `manual_keep.verification_threshold`, `manual_keep.minimum_best_second_margin`, `manual_keep.allow_automatic_move`.
- **Implementierung:**
  - `app.manual_keep` (Orchestrierung).
  - `app.manual_keep_similarity` (`ResolutionAwareSimilarity`).
  - Gemeinsam genutzter `app.image_features` (`ImageFeatureService`).

**Manual-Keep-Vertrag:** `manual_keep` ist ein boolescher Wert (`true` bei Match, `false` oder `null` sonst). `manual_keep_match` wird in der Run-Summary als Zaehler gefuehrt.

---

### 5.7 Metadaten

- **Status:** Pflicht.
- **Zweck:** Macht Bewertungen und Personentreffer in gaengigen Fotoprogrammen sichtbar.
- **Ablauf:**
  1. Sternrating aus Score-Band bestimmen.
  2. Namespaced Keywords einbetten (`workflow:ai_cull`, `decision:<final>`, `series:*`, `family:match`, `person:<slug>`, `manual_keep:true`).
  3. Per `exiftool` (`shell=False`) in Bild schreiben.
  4. Nach dem Schreiben zuruecklesen und abgleichen.
- **Zusammenspiel:**
  - Rohscores bleiben primaer in `SAVE/culling_scores.csv` und der Run-Summary, nicht in den Bildmetadaten selbst.
  - Fehlt Exiftool, bleibt der Kernworkflow lauff aehig; der Status wird als `disabled`/`failed` berichtet.
  - Bei erfolgreichem Manual-Keep-Match (5.6) wird zwingend `manual_keep:true` als Keyword gesetzt.
- **Sicherheits- und Datenschutzgrenzen:**
  - Exiftool wird nur argumentbasiert mit `shell=False` gestartet.
  - Keine externen Dienste, keine Daten uebertragung.
- **Fehlerverhalten:**
  - Fehlendes Exiftool blockiert den Kernworkflow nicht, muss aber als `disabled` oder `failed` berichtet werden.
  - Ein Mismatch zwischen geschriebenen und zurueckgelesenen Metadaten setzt `failed_metadata` und blockiert den Metadatenabschluss.
  - **Fallback:** Bei `failed_metadata` wird der Sidecar-Modus (`metadata.sidecar_recovery_enabled=true`) aktiviert; Metadaten werden als `.xmp`-Sidecar geschrieben.
- **Konfiguration:**
  - `metadata.write_mode` (embedded, sidecar, none).
  - `metadata.verify_after_write` (bool).
  - `metadata.sidecar_recovery_enabled` (bool).
- **Implementierung:**
  - `app.metadata`.

**Metadaten-Vertrag:** Metadaten MUessen namespaced sein (Praefix `workflow:`). `failed_metadata` ist ein boolescher Wert. `exiftool_status` ist einer von `success`, `disabled`, `failed`, `sidecar`.

---

### 5.8 Kalibrierung und Gewichtungsassistent

- **Status:** Pflicht.
- **Zweck:** Lernt aus best aetigten menschlichen Endentscheidungen, ob die vorhandenen Score-Komponenten anders gewichtet werden sollten. Ersetzt nie die Komponenten selbst.
- **Ablauf:**
  1. Pro manuell freigegebenem Batch entsteht ein unver aenderliches `review_decision_record.json`.
  2. Daraus werden Kennzahlen (terminale Uebereinstimmung, `reject_to_keep_rate` etc.) berechnet.
  3. Optional wird ein Gewichtsvorschlag im Schattenmodus erzeugt.
  4. Eine Aktivierung erfordert bewusste Nutzerfreigabe, erfuellte Gates und bleibt jederzeit rollbackf aehig.
- **Zusammenspiel:**
  - Die YAML-Basisgewichte bleiben sichtbar und unver aendert.
  - Das System schaltet nie selbst einen hoehern Automatikmodus ein.
- **Sicherheits- und Datenschutzgrenzen:**
  - Review-Record darf keine Bilddateien, Vorschaubilder, Roh-Embeddings oder absolute NAS-Pfade enthalten.
  - Modellgewichte, private Bilder, Caches, Logs, Laufzeitdaten und Secrets duerfen nie in Git eingecheckt werden.
- **Fehlerverhalten:**
  - Fehlende oder ungueltige Steuerdaten werden mit Grund, Zeit und Hash nach `WORKFLOW_DATA/runtime/quarantine` kopiert, als blockierend gemeldet und erfordern sichere Neuerstellung oder menschliche Pruefung.
  - Ein Fehler stoppt den betroffenen Batch, aber nicht den gesamten Lauf.
- **Konfiguration:**
  - `calibration.enabled`, `calibration.min_decisions`, `calibration.retrain_frequency`.
  - `calibration.audit_log` (Pfad).
  - `automation.mode` (assisted_review, automatic_phase2, automatic_candidates, reference_activation).
- **Implementierung:**
  - `app.calibration`, `app.weight_assistant` (Proposal-Gates, Rollback).
  - `app.reporting`.

**Kalibrierungs-Vertrag:** `review_decision_record.json` MUSS `batchid`, `timestamp`, `human_decision`, `predicted_decision`, `agreement`, `config_fingerprint`, `producer_version` enthalten.

---

### 5.9 WorkUnits / Bildmengenmodus / Resume

- **Status:** Pflicht.
- **Zweck:** Erlaubt es, auch sehr grosse physische Ordner in ueberschaubaren, sicher fortsetzbaren Portionen zu verarbeiten, ohne die sichtbare Ordnerstruktur zu ver aendern.
- **Ablauf:**
  1. `workflow.work_unit_mode: source_batch` (Default, ganzer Ordner = Einheit) oder `image_count` (interne, unsichtbare Portionierung).
  2. Der physische Batch wird erst verschoben, wenn alle WorkUnits abgeschlossen sind.
  3. Angefangene oder wiederherzustellende Arbeit hat immer Vorrang vor neuen Ordnern.
  4. Vor jedem sichtbaren Dateimove wird ein Uebergangsstate (`phase1_moving`) geschrieben, erst danach der Abschluss (`phase1_completed`).
- **Zusammenspiel:**
  - `resume_incomplete_batches=true` hat immer Vorrang vor `batch_sort`.
  - Macht jeden Abbruchpunkt eindeutig wiederherstellbar.
- **Sicherheits- und Datenschutzgrenzen:**
  - Alle produktiven Pfade muessen innerhalb des erlaubten Basisverzeichnisses liegen; Path Traversal und Symlink-Ausbrueche werden abgelehnt.
  - Ein globaler Lock verhindert parallele produktive Laeufe.
- **Fehlerverhalten:**
  - Bei Zeitbudget oder SIGTERM wird kein neuer teurer Schritt begonnen; der sichere aktuelle Schritt wird abgeschlossen, der Status `paused` atomar geschrieben und kontrolliert beendet.
  - Unvollstaendige Schritte werden anhand von Quelle, Ziel, Hash, Groesse und Marker sicher fortgesetzt oder neu ausgefuehrt; bei Widerspruch wird quaraentaenisiert.
- **Konfiguration:**
  - `workflow.work_unit_mode` (source_batch, image_count).
  - `workflow.images_per_work_unit` (positive Ganzzahl).
  - `workflow.batch_sort` (oldest_first, newest_first).
  - `workflow.max_run_hours`, `workflow.max_images_per_run`.
- **Implementierung:**
  - `app.work_units` (Inventar, WorkUnit-States).
  - `app.planning` (`select_next_work_units`).
  - `app.phases` (Verdrahtung inkl. Move-Reihenfolge).

**WorkUnit-Vertrag:** Eine WorkUnit MUSS `work_unit_id`, `batchid`, `image_range` (Start, Ende), `state` (pending, in_progress, completed, failed, paused), `timestamp`, `hash`, `error_reason` (optional) enthalten.

**Beispiel image_count:** Bei `workflow.work_unit_mode: image_count` und `workflow.images_per_work_unit: 200` wird ein physischer Batch mit 800 Bildern in 4 WorkUnits aufgeteilt. Jede WorkUnit wird separat verarbeitet, aber der Batch wird erst nach Abschluss aller 4 WorkUnits nach `TEMP_IMAGES` verschoben.

---

### 5.10 Archivierung und Bereinigung (Phase 2)

- **Status:** Pflicht.
- **Zweck:** Stellt sicher, dass ARWs erst nach nachweislich sicherer Archivierung geloescht werden.
- **Ablauf:**
  1. Archivplan mit Hash je Datei erstellen.
  2. Tempor aeres ZIP schreiben.
  3. Pruefung (Lesbarkeit, Dateiliste, Hash).
  4. Atomare Aktivierung.
  5. Erst dann Loeschung; jede Loeschung protokolliert.
- **Zusammenspiel:**
  - Bei jedem Fehler bleibt das ARW erhalten.
  - `ARW/` wird erst nach vollstaendig dokumentierter Bereinigung entfernt.
- **Sicherheits- und Datenschutzgrenzen:**
  - Originaldaten (Kamera-JPGs, ARWs) duerfen nie still ueberschrieben oder geloescht werden.
  - ZIPs werden vor Nutzung auf Lesbarkeit, Traversal, Groessenlimit und Kompressionsverhaeltnis geprueft; Kollisionen erzeugen `..._EXTRA<n>.zip` statt Ueberschreibung.
  - Alle produktiven Pfade muessen innerhalb des erlaubten Basisverzeichnisses liegen; Path Traversal und Symlink-Ausbrueche werden abgelehnt.
- **Fehlerverhalten:**
  - Bei jedem Fehler bleibt das ARW erhalten.
  - Ein Fehler stoppt den betroffenen Batch, aber nicht den gesamten Lauf.
- **Konfiguration:**
  - `phase2.delete_unneeded_arws_after_verified_archive` (bool).
  - `phase2.allow_automatic_handoff` (bool).
- **Implementierung:**
  - `app.archives`, `app.batch_state`.

**Archiv-Vertrag:** Jede Archivierung MUSS `archive_id`, `batchid`, `zip_path`, `zip_hash`, `entry_count`, `total_size`, `activation_timestamp`, `activation_hash`, `config_fingerprint`, `producer_version` enthalten.

---

### 5.11 Reporting

- **Status:** Pflicht.
- **Zweck:** Macht jedem Lauf auf einen Blick klar, was passiert ist und was der Mensch tun muss.
- **Ablauf:**
  1. JSON-Run-Summary erzeugen.
  2. Kurze Scheduler-Ausgabe schreiben.
  3. `SAVE/culling_scores.csv` erstellen.
  4. Persistente Logs fuehren.
  5. Priorisierte `user_actions_required` mit Severity `info`/`warning`/`blocking` ausgeben.
- **Zusammenspiel:**
  - Inhalt ist normativ (siehe Anhang J).
  - Keine spezifischen Konfigurationsschalter.
- **Sicherheits- und Datenschutzgrenzen:**
  - Die Summary enthaelt keine Secrets, keine Produktionspfade, keine Bilder, keine Embeddings.
  - Alle Logs und Summaries liegen auf der NAS, nicht im beschreibbaren Container-Dateisystem.
- **Fehlerverhalten:**
  - Kritische Fehler (ungueltige Steuerdaten, fehlender Pflicht-Rebuild, unaufl oesbarer Dateikonflikt, Integritaets- oder Sicherheitsfehler) stoppen den Batch.
  - Bereits erfolgreich atomare Aktionen werden nicht rueckgaengig gemacht.
- **Konfiguration:**
  - Keine spezifischen Schalter, Inhalt ist normativ.
- **Implementierung:**
  - `app.reporting`.

**Reporting-Vertrag:** Die Run-Summary MUSS `run_id`, `timestamp`, `config_fingerprint`, `automation_mode`, `batch_count`, `image_count`, `keep_count`, `review_count`, `reject_count`, `error_count`, `blocking_count`, `user_actions_required` enthalten.

---

### 5.12 Betrieb: Scheduler, Docker, Lock, Fehlerisolation

- **Status:** Pflicht.
- **Zweck:** Sicherer, wiederaufnehmbarer Dauerbetrieb ueber Synology Task Scheduler.
- **Ablauf:**
  1. Container mit persistentem NAS-Mount starten.
  2. Globaler Lock verhindert parallele Laeufe.
  3. Ein defekter Batch wird quaraentaenisiert statt den ganzen Lauf zu stoppen.
  4. Alle Zustaende, Logs, Konfigurationen, Caches und Summaries liegen auf der NAS.
- **Zusammenspiel:**
  - `quarantine_batch()` muss in `phases.py` tats aechlich aufgerufen werden.
  - Lock und Zustandsdateien werden zuerst geprueft; der aelteste pausierte Batch hat Vorrang.
- **Sicherheits- und Datenschutzgrenzen:**
  - Alle produktiven Pfade muessen innerhalb des erlaubten Basisverzeichnisses liegen; Path Traversal und Symlink-Ausbrueche werden abgelehnt.
  - Modellgewichte, private Bilder, Caches, Logs, Laufzeitdaten und Secrets duerfen nie in Git eingecheckt werden.
  - Container und DSM Task Scheduler verwenden einen persistent gemounteten `basedir`, einen dedizierten Least-Privilege-Benutzer und nachvollziehbare UID/GID.
- **Fehlerverhalten:**
  - Ein defekter Batch wird quaraentaenisiert statt den ganzen Lauf zu stoppen.
  - Bei Zeitbudget oder SIGTERM wird kein neuer teurer Schritt begonnen; der sichere aktuelle Schritt wird abgeschlossen, der Status `paused` atomar geschrieben und kontrolliert beendet.
- **Konfiguration:**
  - `paths.basedir` und Unterpfade.
  - `workflow.resume_incomplete_batches` (bool).
- **Implementierung:**
  - `app.locks`, `app.runtime` (`quarantine_batch()`).
  - `app.phases` (muss `quarantine_batch()` aufrufen).

**Lock-Vertrag:** Der Lock MUSS `lock_id`, `timestamp`, `hostname`, `pid`, `producer_version` enthalten. Ein Lock aelter als 24 Stunden gilt als verwaist und darf ueberschrieben werden.

---

## 6. Konfiguration

### 6.1 Schema und Validierung

Die Konfiguration ist eine YAML-Datei mit strikter Validierung. Unbekannte Schluessel sind Fehler, ausser sie liegen in einem explizit dokumentierten `extensions`-Block.

### 6.2 Effektive Konfiguration und Fingerprint

Die effektive Konfiguration wird mit SHA256-Fingerprint im Run dokumentiert. Geheimnisse und Produktionspfade gelangen nicht in Git.

### 6.3 Config-Kommentierung

Jede Variable in der Beispielkonfiguration MUSS kommentiert sein mit:

1. Zweck der Variable.
2. Typ bzw. Wertebereich.
3. Standardverhalten.
4. Sicherheits- und Performancewirkung.
5. Mindestens eine sinnvolle Alternative oder ein typischer Wertebereich.

Jeder Logikblock MUSS einen einleitenden Block-Kommentar besitzen, der:

1. Den fachlichen Zweck des Blocks beschreibt.
2. Die typische Nutzung erklaert.
3. Die Auswirkungen auf den Workflow nennt.
4. Sicherheits- oder performancekritische Aspekte benennt.

Der Umfang soll mindestens 3–6 Zeilen pro Block betragen, menschenlesbar und technisch praezise.

**Konfigurations-Vertrag:** Die effektive Konfiguration MUSS `config_fingerprint` (SHA256), `schema_version`, `created_at`, `updated_at`, `producer_version` enthalten.

**Beispiel-Konfiguration (Auszug):**
```yaml
# ============================================================
# Workflow-Konfiguration
# Zweck: Steuert den Gesamtfluss, Batch-Verarbeitung und Recovery
# Typ: YAML mit strikter Validierung
# Standard: source_batch (ganzer Ordner = Einheit)
# Sicherheit: Pfadvalidierung, Lock-Schutz, Quarantaene bei Fehlern
# Alternative: image_count (interne Portionierung fuer grosse Batches)
# ============================================================
workflow:
  phase_execution: phase1_then_phase2  # phase1_only, phase2_only, phase1_then_phase2
  batch_sort: oldest_first  # oldest_first, newest_first
  resume_incomplete_batches: true  # true, false
  work_unit_mode: source_batch  # source_batch, image_count
  images_per_work_unit: 200  # positive Ganzzahl, nur bei image_count
  max_run_hours: 4  # positive Ganzzahl, Zeitbudget pro Lauf
  max_images_per_run: 1000  # positive Ganzzahl, Bilder-Budget pro Lauf
```

---

## 7. Dokumentation

### 7.1 Pflichtdokumente

Die Anzahl der Pflichtdokumente wird auf ein Minimum reduziert:

1. `README.md` (Schnelleinstieg, Ziel, Installation in Kurzfassung, Verweis auf MANUAL_DE).
2. `docs/MANUAL_DE.md` (vollstaendiges Benutzerhandbuch und Projektdokumentation).
3. `CHANGELOG.md` (Versionshistorie, Aenderungsprotokoll).

Alle anderen bisher geforderten Dokumente (`CONFIGURATION.md`, `INSTALLATION.md`, `BETRIEB.md`, `TESTING.md`, `ARCHITEKTUR.md`, `SECURITY.md`) sind nicht mehr als separate Pflichtdokumente erforderlich, sofern ihre Inhalte in `MANUAL_DE.md` vollstaendig enthalten oder per stabilem Querverweis eindeutig abgedeckt sind.

### 7.2 MANUAL_DE-Struktur

`docs/MANUAL_DE.md` ist das wichtigste Dokument des Projekts. Es MUSS als vollstaendiges Benutzerhandbuch und Projektdokumentation dienen und folgende 11 Kapitel abbilden:

1. Schnellstart
2. Zielbild und Abwaegungslogik
3. Ordner, Namen und Datenklassen
4. Phasen, Batches, WorkUnits und Recovery
5. Scoring, Serien, Metadaten und Manual Keep
6. Gesichter, Familie und Face-Backends
7. Gewichtungsassistent, Kalibrierung und Lernen
8. Betrieb, Sicherheit, Scheduler und Deployment
9. Reporting, Konfiguration und Dokumentation
10. Automatikstufen und Abnahme
11. Altlasten, Migration, Glossar und Referenzen

### 7.3 Ordnung und Sauberkeit

Das Repository MUSS klar, konsistent und wartbar strukturiert sein. Altlasten, tote Dateien, ungenutzte Ordner, ungenutzte Module und veraltete Pfade muessen entfernt werden. Wenn sie bewusst erhalten bleiben, MUessen sie als `DEPRECATED` oder `LEGACY` markiert sein, mit Header-Kommentar (Zweck, Entstehung, Migration) und in `MANUAL_DE.md` Kapitel 11 dokumentiert sein.

---

## 8. Automatikstufen und Abnahme

### 8.1 Automatikstufen

| Stufe | Modus | System darf | Mensch muss |
|-------|-------|-------------|-------------|
| 1 | `assisted_review` | Phase 1, Reporting, Vorschlaeg | Phase-2-Uebergabe und Referenzaktivierung freigeben |
| 2 | `automatic_phase2` | Phase 2 nach expliziten Gates | Referenzaktivierung freigeben |
| 3 | `automatic_candidates` | Kandidaten priorisieren/verwalten | Referenzaktivierung freigeben |
| 4 | `reference_activation` | Nur spaeterer Erweiterungspunkt | Audit und explizite Freigabe |

Stufe 1 ist Standard. Stufe 2 erfordert gleichzeitig: `automation.mode`, `automatic_phase2_enabled=true`, `workflow.phase_execution=phase1_then_phase2` sowie dokumentierte NAS-Abnahme und Kalibrierungsbereitschaft. Stufe 3 erfordert zusaetzlich `automatic_candidates_enabled=true`. Stufe 4 ist experimental, standardmaessig verboten und braucht eine eigene spaetere Anforderung.

### 8.2 Abnahme

Die Abnahme ist erst erfuellt, wenn alle Faelle in Anhang E automatisiert reproduzierbar bestehen und der Ziel-NAS-Pilot dokumentiert ist. Unit- oder Containertests ersetzen den NAS-Piloten nicht.

---

## 9. Ordnung und Sauberkeit

### 9.1 Altlasten, tote Dateien, ungenutzte Ordner/Module

Altlasten, tote Dateien, ungenutzte Ordner, ungenutzte Module und veraltete Pfade muessen entfernt werden. Wenn sie bewusst erhalten bleiben, MUessen sie als `DEPRECATED` oder `LEGACY` markiert sein, mit Header-Kommentar (Zweck, Entstehung, Migration) und in `MANUAL_DE.md` Kapitel 11 dokumentiert sein.

### 9.2 Doppelstrukturen

Doppelstrukturen (parallele Implementierungen, mehrere Config-Varianten ohne klaren Zweck, mehrere Doku-Pfade) sind unzulaessig, es sei denn, sie haben einen dokumentierten fachlichen oder technischen Zweck. Zweck, Abgrenzung und Lebenszyklus muessen in `MANUAL_DE.md` Kapitel 11 dokumentiert sein.

### 9.3 DEPRECATED/LEGACY-Markierung und Dokumentation

Wenn alte Pfade, Module, Config-Bl ocke oder Doku-Inhalte bewusst erhalten bleiben, muessen sie klar von der aktiven Logik abgegrenzt sein (z. B. `legacy/`, `deprecated/`, `experimental/`), mit Header-Kommentaren versehen sein und in `MANUAL_DE.md` Kapitel 11 dokumentiert sein.

---

## 10. Glossar und Begriffe

| Begriff | Bedeutung |
|---------|-----------|
| Batch | Kameraordner mit unveraenderlicher `batchid`, Eingangsmanifest und zentraler Zustandsdatei. |
| Aktives JPG | JPG im Hauptordner; nur dieses schuetzt ein ARW mit gleichem Basename. |
| Score-Entscheidung | Phase-1-Klasse `keep`, `review` oder `reject` vor manueller Sichtung. |
| Finale Entscheidung | Deterministisch aus dem Phase-2-Ordnerzustand abgeleitete Endentscheidung. |
| Family-Backend | Explizit registrierter Adapter fuer bekannte Gesichter. |
| Face-Cache-Fingerprint | Fingerprint aus Backend, Adapter, Modellen, Provider, Preprocessing, Metrik, Auswahl und Parametern. |
| Archivaktivierung | Atomarer Wechsel einer vollstaendig validierten temporaeren ZIP zur finalen ZIP. |
| Wiederaufnahme | Idempotentes Fortsetzen anhand von Zustand, Manifesten, Hashes und Artefaktpruefung. |
| Blockierender Fehler | Fehler, der sicherheitsrelevante Batch-Aktionen verhindert. |

---

## Anhaenge

### Anhang A – Normative Datenvertraege

- Artefakte: Batch-Zustand (`state/{batchid}.json`), Manifest (`manifest.json`), CSV (`SAVE/culling_scores.csv`), Review-Record (`review_decision_record.json`), Calibration-Index (`calibration_summary.json`), Lock-Manifest, Quarantaene-Manifest, Run-Summary.
- Pfadvertrag: Alle produktiven Pfade unterhalb des erlaubten Basisverzeichnisses; keine Symlink-Ausbrueche; relative Pfade innerhalb Batch.
- Hashvertrag: SHA256 fuer ARW, JPG, ZIP, Manifest, State; Hash vor/nach Operation pruefen.
- Namensvertrag: `batchid = source-folder-name + Fingerprint(8)`; unver aenderlich ueber alle Ordnerwechsel.
- JSON-Schema: `schema_version`, `created_at`, `updated_at`, `producer_version`, Bereichskennung, Pflichtfelder je Artefakt.
- Fehlervertrag: Unbekannte, zukuenftige, ungueltige oder unlesbare Dateien nicht still ueberschreiben; nach `quarantine` kopieren, mit Grund, Zeit, Hash melden; sichere Neuerstellung oder menschliche Pruefung.
- Atomaritaetsvertrag: Inhalt erzeugen, validieren, temporaer auf gleichem Dateisystem schreiben, erneut validieren, atomar ersetzen; vorherige Version bis Aktivierung erhalten.
- Lockvertrag: Globaler Lock verhindert parallele produktive Laeufe; Lock vor/nach Lauf pruefen.
- Batch-Lebenszyklus: `phase1_started → phase1_completed → review_comparison_pending → review_record_committed → calibration_index_committed → phase2_archiving → phase2_completed` (manuell); oder `phase1_completed → automatic_handoff → phase2_archiving → phase2_completed` (automatisch).
- Quarantaenevertrag: Fehlerhafte Artefakte nach `WORKFLOW_DATA/runtime/quarantine` mit Manifest; blockierend melden; menschliche Pruefung erforderlich.

**Datenvertrags-Vervollstaendigung:** Alle Artefakte Muessen folgende Pflichtfelder enthalten:
- `schema_version` (string, format: "major.minor")
- `created_at` (string, format: ISO8601)
- `updated_at` (string, format: ISO8601)
- `producer_version` (string, format: "major.minor.patch")
- `batchid` (string, falls zutreffend)
- `hash` (string, SHA256, falls zutreffend)

---

### Anhang B – Metadaten, CSV und Manifest

- CSV: `SAVE/culling_scores.csv` mit `batchid`, `image_id`, `basescore`, `eyescore`, `personalscore`, `familyscore`, `finalscore`, `predicted_decision`, `series_id`, `series_size`, `series_rank`, `series_best`, `family_match`, `person_slug`, `manual_keep`, `failed_metadata`, `exiftool_status`.
- JSON-Manifest: `batchid`, `source_folder`, `created_at`, `updated_at`, `schema_version`, `producer_version`, `image_count`, `active_jpgs`, `arw_count`, `culling_scores_hash`, `manifest_hash`, `state`, `phase`, `review_state`, `calibration_status`, `quarantine_reason` (falls vorhanden).
- Metadaten: Inventarisierung vor Schreiben; Exiftool-Argumente; Zuruecklesen und Abgleich; `failed_metadata` bei Mismatch; Sidecar nur als Recovery-Modus.
- Mindest-Tag-Satz: Sternrating, `workflow_ai_cull`, `decision`, optional `series_best`, `family_match`, `person_slug`, `manual_keep`.
- Run-Summary: Run-Batch-ID, Konfigurationsfingerprint, angeforderter/wirksamer Automatikmodus, Ergebnisstatus, Keep/Review/Reject-Zaehler, Cache-/Metadatenstatus, ZIP-Konflikte, Kalibrierungsstatus, `user_actions_required`.

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

### Anhang C – Face-Backend-Vertrag

- Registry: Backends ausschliesslich durch explizite Registry und Adapter ausgewaehlt.
- Adapter: Jedes Backend implementiert festgelegte Schnittstellen (Laden, Vorverarbeitung, Merkmalsextraktion, Metrik, Cache-Fingerprint).
- Modellhash: Jedes Modell hat SHA256-Hash; Hash Teil des Cache-Fingerprints.
- Provider: Backend-Provider klar dokumentiert (z. B. facenet, arcface).
- Vorverarbeitung: Normalisierung, Skalierung, Zuschneiden einheitlich; Teil des Fingerprints.
- Metrik: Kosinus aehnlichkeit (higher_is_better, 0–1) mit Schwelle 0,95 und Marge 0,03; alternative Metrik nur mit vollstaendiger Dokumentation.
- Auswahlfingerprint: `selection.json`-Fingerprint Teil des Cache-Fingerprints; unterschiedliche Fingerprints nie mischen.
- Face-Crop: Nur fuer sicheren, bekannten Personenmatch; Vorschlag in `newfaces` mit Herkunft, Hash, Bounding Box, Qualitaet, Neuheit, Konfidenz, Status.

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

### Anhang D – Referenzkonfiguration

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

### Anhang E – Abnahme ACC-01 bis ACC-15

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

### Anhang F – CLI, Exit-Codes, Module

- CLI: `app/cli` nur fuer Argumente, Dispatch, Exit-Codes; keine Fachlogik.
- Exit-Codes: 0 (Erfolg), 1 (Konfigurationsfehler), 2 (Pfad-/Sicherheitfehler), 3 (Lock-Fehler), 4 (State-Fehler), 5 (Quarantaene-Fehler), 6 (Metadaten-Fehler), 7 (Modell-Fehler), 8 (Face-Backend-Fehler), 9 (Interrupt/SIGTERM), 10 (Timeout/Budget).
- Module: `app/culling` (Merkmale, Score, Serien), `app/family_recognition` (ohne ML-Import), `app/archives` (ZIP, Hash, Aktivierung), `app/runtime` (State, Lock, Recovery), `app/safety` (Validierung, Quarantaene), `app/phases` (Phasenlogik), `app/manualkeep` (MANUAL_KEEP), `app/calibration` (Gewichtungsassistent), `app/reporting` (Summary, CSV, JSON, Log), `app/config` (Konfiguration, Validierung), `app/locks` (Lock-Manifest), `app/batch_state` (State-Management), `app/face_cache` (Face-Cache), `app/inference` (Worker, Parallelitaet).

---

### Anhang G – Konfigurationsvertrag

- Schema: YAML mit strikter Validierung; unbekannte Schluessel Fehler (ausser `extensions`).
- Fingerprint: Effektive Konfiguration mit SHA256-Fingerprint im Run dokumentieren.
- Sicherheit: Keine Geheimnisse, keine Produktionspfade in Git.
- Status: `stable`, `advanced`, `experimental` je Variable.
- Migration: Aenderungen an Gewichten, Schwellen, Feature-Logik, Referenzbasis, Backend, Modell, Metadatenvertrag aendern Versions-, Konfigurations- und ggf. Cache-Kalibrierungsfingerprint; Migrationshinweise im CHANGELOG.

---

### Anhang H – Archivvertrag

- ZIP: Lesbarkeit, Traversal, Groessenlimit, Kompressionsverhaeltnis pruefen.
- Kollision: `..._EXTRA_n.zip` statt Ueberschreibung.
- Hash: SHA256 fuer ZIP, Manifest, State; Hash vor/nach Aktivierung pruefen.
- Aktivierung: Vollstaendiges Archiv erzeugt, geprueft, auf gleichem Dateisystem atomar aktiviert, mit Hash protokolliert.
- Loeschung: ARW erst nach vollstaendig dokumentierter Bereinigung entfernen.

**Archiv-Vertrag-Kohaerenz:** Jeder Archiveintrag MUSS folgende Felder enthalten:
- `relative_path` (string, relativ zum Batch)
- `size` (int, Bytes)
- `hash` (string, SHA256)
- `archived_at` (string, ISO8601)

---

### Anhang I – Sample-Kapazitaetsvertrag

- Kleine NAS: ARWs werden im MVP nicht dekodiert; technische Vorschauen 256–512 Pixel laengste Kante; Aehnlichkeitsvektoren 32–64 Pixel; Standard-Worker 1; Bilder unmittelbar schliessen; kein Vollbatch im RAM.
- Referenzprofile, Geschmacksmodell, Face-Merkmale persistent cachen; nur bei Eingabe aenderung neu aufbauen.
- Fehler/Timeouts eines Bildes duerfen Batch nicht abstuerzen lassen.
- Werte konfigurierbar; Sicherheitsvertraege nicht abschw aechen.

**Praezisierung:** Die Groesse der Aehnlichkeitsvektoren (32–64 Pixel) bezieht sich auf die reduzierte, technisch genutzte Vorschau fuer technische Culling- und Vergleichsoperationen. Die tats aechliche Dimension des Embedding-Vektors haengt vom verwendeten Modell ab (z. B. CLIP: 512 oder 768 Dimensionen).

---

### Anhang J – Reporting, Deployment

- Reporting: Kurze Scheduler-Ausgabe, strukturierte JSON-Run-Summary, Batch-CSV, persistente Logs.
- Deployment: Container mit NAS-Mount; alle Zustaende, Logs, Konfigurationen, Caches, Summaries auf NAS; nicht im beschreibbaren Container-Dateisystem.
- Docker/GPU: Separate Images; Dokumentation; not-root-Ausfuehrung anstreben.

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

### Anhang K – Qualitaet, CI

- CI prueft: Header, Pflichtfelder, Versionskonsistenz, Konfigurationsschema, Konfigurationsfingerprint, Secrets, Python-Compile, Unit-/Integrationstests, Abnahmetests.
- Qualitaetsmetriken: Testabdeckung, Fehlerquote, Quarantaenerate, Resume-Rate, Automatisierungsgrad, Performance auf Ziel-NAS.

---

### Anhang L – Glossar, Migration

- Glossar: Batch, WorkUnit, Run, Phase 1, Phase 2, State, Manifest, Lock, Quarantaene, Review-Record, Calibration-Index, Fingerprint, Hash, Face-Crop, Referenzpool, Manual Keep, Inbox, Used, Archiv, ZIP, Sidecar, Exiftool, Worker, Adapter, Backend, Metrik, Schwelle, Marge, Score, Serie, Bestbild, Gewichtungsassistent, Audit, Rollback.
- Migration: Alte Pfade, Module, Config-Blocke, Doku-Inhalte klar von aktiver Logik abgrenzen; DEPRECATED/LEGACY markieren; in MANUAL_DE.md Kapitel 11 dokumentieren.

---

### Anhang M – Mindesttestliste

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

### Anhang N – Konsistenz- und Einheitlichkeitsregeln

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

- **Alle Kapitel:** Muessen konsistent nummeriert sein (0–9).
- **Alle Anhaenge:** Muessen konsistent benannt sein (A–N).
- **Querverweise:** Muessen immer mit "siehe Abschnitt X.Y" oder "siehe Anhang X" erfolgen.
- **Keine impliziten Referenzen** (z. B. "siehe oben", "siehe unten", "wie beschrieben").

#### N6 – Glossar-Vervollstaendigung

- **Alle Begriffe:** Muessen im Glossar (Abschnitt 10) definiert sein.
- **Neue Begriffe:** Muessen bei Einfuehrung sofort im Glossar ergaenzt werden.
- **Begriffs aenderungen:** Muessen im CHANGELOG.md dokumentiert werden.

#### N7 – Anhang-Konsolidierung

- **Alle Anhaenge:** Muessen thematisch konsistent sein (kein Duplikat, keine Ueberlappung).
- **Anhang-Reihenfolge:** Alphabetisch nach Thema (A–N).
- **Anhang-Querverweise:** Muessen konsistent sein (z. B. "siehe Anhang H" statt "siehe Archivvertrag").

#### N8 – Stil- und Formatvereinheitlichung

- **Ueberschriften:** Immer Markdown-Header (`##`, `###`), nie fett gedruckt.
- **Listen:** Immer Bindestriche (`-`), nie Zahlen (ausser bei Reihenfolge).
- **Tabellen:** Immer mit Header-Zeile und Trennlinie, linksbuendig.
- **Code-Bl ocke:** Immer mit Sprachangabe (z. B. ` ```yaml`, ` ```json`, ` ```bash`).
- **Zitate:** Immer mit `> ` (Grossbuchstabe nach `>`).

---

### Anhang P – Ausfuehrliche Beschreibung Config-Kommentierung und MANUAL_DE-Struktur

#### P1. Konfiguration: Konkrete Anforderungen an Kommentare

##### P1.1 Variablen-Kommentierung (REQ-CFG-011 bis REQ-CFG-013)

Jede Variable MUSS mit folgenden 5 Punkten kommentiert sein:

1. **Zweck:** Was bewirkt diese Variable fachlich?
2. **Typ/Wertebereich:** Welcher Datentyp (string, int, bool, enum)? Welche Werte sind erlaubt?
3. **Standardverhalten:** Was passiert, wenn ich nichts aendere?
4. **Sicherheits-/Performance-Wirkung:** Welche Auswirkungen hat diese Variable auf Sicherheit, Datenschutz, Geschwindigkeit oder Ressourcen?
5. **Mindestens eine sinnvolle Alternative oder typischer Wertebereich:** Welche anderen Werte sind praktikabel und wann waehle ich sie?

##### P1.2 Logikblock-Kommentierung (REQ-CFG-014)

Jeder Logikblock MUSS einen einleitenden Block-Kommentar besitzen mit:

1. **Fachlicher Zweck:** Welches Problem loest dieser Block?
2. **Typische Nutzung:** Wann und wie wird dieser Block verwendet?
3. **Auswirkungen auf Workflow:** Was aendert sich im Ablauf bei Aenderungen?
4. **Sicherheits-/Performance-Aspekte:** Welche Risiken oder Vorteile gibt es?
5. **Umfang:** 3–6 Zeilen pro Block, menschenlesbar, technisch praezise, frei von Floskeln.

#### P2. MANUAL_DE: Konkretisierte Inhaltsbeschreibung (11-Kapitel-Struktur)

REQ-DOC-010, REQ-DOC-016, REQ-DOC-017, REQ-DOC-018 verlangen eine vollstaendige, menschenlesbare Struktur. Die 11 Kapitel sind wie folgt festgehalten:

1. **Schnellstart:** Ziel des Projekts, Installation in Kurzfassung, Verweis auf vollstaendige Kapitel.
2. **Zielbild und Abwaegungslogik:** Zielbild, Abwaegungslogik, Geltungsbereich.
3. **Ordner, Namen und Datenklassen:** Kanonische Arbeitsordner, Batch-Struktur, Aktive JPGs, ARW-Schutz, Manual Keep.
4. **Phasen, Batches, WorkUnits und Recovery:** Phase 1 und Phase 2, Batch-Lebenszyklus, WorkUnits, Recovery.
5. **Scoring, Serien, Metadaten und Manual Keep:** Score-Komponenten, Serienlogik, Metadaten, Manual Keep.
6. **Gesichter, Familie und Face-Backends:** Bekannte Gesichter, Referenzpool, Face-Crop, Backend-Registry.
7. **Gewichtungsassistent, Kalibrierung und Lernen:** Gewichtungsassistent, Nutzung, Aktivierung, Kein automatisches Einschalten.
8. **Betrieb, Sicherheit, Scheduler und Deployment:** Lock, Pfade, Dry Run, ZIP-Sicherheit, Container, Restore, Abbruchtest.
9. **Reporting, Konfiguration und Dokumentation:** Run-Summary, CSV, JSON, Logs, Konfigurationsfingerprint, Beispielkonfiguration, Pflichtdokumente.
10. **Automatikstufen und Abnahme:** Stufe 1–4, Gates, Abnahme (ACC-01 bis ACC-15).
11. **Altlasten, Migration, Glossar und Referenzen:** DEPRECATED/LEGACY, Migration, Glossar, REQ-IDs, GitHub-Realitaetsabgleich, Rueckverfolgbarkeit.

#### P3. Zusammenfassung

- **Config-Kommentierung:** Jede Variable braucht 5 Punkte (Zweck, Typ, Standard, Sicherheit/Performance, Alternative); jeder Logikblock braucht 5 Punkte (Zweck, Nutzung, Auswirkungen, Sicherheit/Performance, 3–6 Zeilen).
- **MANUAL_DE-Struktur:** 11 Kapitel (Schnellstart, Zielbild/Abwaegung, Ordner, Phasen/WorkUnits, Scoring/Metadaten, Gesichter, Gewichtungsassistent, Betrieb, Reporting, Automatikstufen, Altlasten/Glossar).
- **MANUAL_DE-Inhalt:** Vollstaendiges Benutzerhandbuch UND wartbare Projektdokumentation; fuer Menschen (klare Sprache, Beispiele) und KI (strukturierte Ueberschriften, konsistente Begriffe, stabile Referenzen) lesbar.

#### P4 – Mindestanforderung an README-Dateien (verbindlich)

##### P4.1 Geltungsbereich

Diese Anforderung gilt fuer alle README-Dateien im NAS-Workflow-Bereich:

- `PHOTO_WORKFLOW/README.md`
- `TEMP_SD/README.md`, `TEMP_IMAGES/README.md`, `TEMP_DONE/README.md`, `TEMP_ERROR/README.md`
- `MANUAL_KEEP/README.md`, `MANUAL_KEEP/inbox/README.md`, `MANUAL_KEEP/used/README.md`
- `WORKFLOW_DATA/README.md` und alle direkten Unterordner (`runtime/`, `reports/`, `archives/`, `faces/`, `samples/`, `models/`, `config/`)

##### P4.2 Pflichtfelder pro README

Jede README-Datei MUSS die folgenden 8 Felder enthalten, in dieser Reihenfolge:

1. **Zweck** (1–2 Saetze): Wofuer ist dieser Ordner da? Welches Problem loest er im Workflow?
2. **Eingaben** (Aufzaehlung): Welche Daten/Dateien/Ordner duerfen hier abgelegt werden? Wer oder welcher Prozess legt sie ab?
3. **Prozess** (1–3 Saetze): Welcher Prozessschritt (Phase 1, Phase 2, Manual Keep, Mensch) verarbeitet diesen Ordner? Was passiert hier?
4. **Ausgaben** (Aufzaehlung): Wohin wandern die Daten als naechstes? Welcher Prozess oder welcher Ordner konsumiert sie?
5. **Manuelle Aktionen** (Aufzaehlung): Was darf der Mensch hier tun? Was ist ausdruecklich verboten?
6. **Lebenszyklus** (1–2 Saetze): Wann gilt ein Batch/Datei in diesem Ordner als abgeschlossen? Wann wird er bereinigt/verschoben?
7. **Fehlerfaelle** (Aufzaehlung): Was passiert bei Fehlern? Wo werden fehlerhafte Faelle abgelegt? Wer muss eingreifen?
8. **Konfiguration** (optional, falls relevant): Welche Config-Schluessel beeinflussen diesen Ordner? (z. B. `manual_keep.*` fuer `MANUAL_KEEP/inbox/`)

##### P4.3 Format und Umfang

- **Format:** Markdown, klare Ueberschriften (`##`, `###`), Aufzaehlungen mit Bindestrichen.
- **Umfang:** Mindestens 100 Woerter, maximal 500 Woerter (ausgenommen Code-Beispiele oder Pfadlisten).
- **Sprache:** Deutsch, technisch praezise, frei von Floskeln.
- **Beispiele:** Mindestens ein konkretes Beispiel fuer Eingabe/Ausgabe oder manuelle Aktion.
- **Verweise:** Keine externen URLs; nur interne Pfadverweise (z. B. `../TEMP_IMAGES/`).

##### P4.4 Validierung

Jede README-Datei MUSS vor der ersten Verwendung durch einen Validierungsschritt geprueft werden:

1. Alle 8 Pflichtfelder vorhanden?
2. Mindestens 100 Woerter, maximal 500 Woerter?
3. Mindestens ein konkretes Beispiel enthalten?
4. Keine externen URLs?
5. Technische Korrektheit (Pfade, Prozessnamen, Config-Schluessel)?

Bei Fehlern: README als ungueltig markieren, im Log dokumentieren, manuelle Korrektur erforderlich.

##### P4.5 Versionierung

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

### Anhang Q – Projektstruktur (GitHub-Repository)

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

### Anhang R – Skript-Anforderungen (Struktur, Kommentare, Lesbarkeit)

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

### Anhang S – Begriffs- und Referenzindex

#### S1 – Begriffindex

| Begriff | Erste Erwaehnung | Glossar | Relevante Abschnitte |
|---------|------------------|---------|---------------------|
| Batch | 3.2 | Ja | 3.1, 3.2, 3.3, 3.4, 3.5, Anhang A, B, F, L |
| WorkUnit | 5.9 | Ja | 3.4, 5.9, Anhang A, F, L |
| Manual Keep | 3.4 | Ja | 3.4, 5.6, Anhang B, D, E, L |
| Face-Backend | 5.4 | Ja | 5.4, Anhang C, D, E, F, L |
| Review-Record | 3.3, 5.8 | Ja | 3.3, 3.4, 5.8, Anhang A, B, L |
| Calibration-Index | 5.8 | Ja | 3.4, 5.8, Anhang A, B, E, L |
| Archivvertrag | 3.5 | Ja | 3.5, Anhang A, B, H, L |
| Zustandsautomat | 3.4 | Ja | 3.4, Anhang A, L |
| Quarantaene | 3.4, 5.12 | Ja | 3.4, 5.8, 5.12, Anhang A, F, L |
| Fingerprint | 3.1, 3.5, 5.4, 5.8 | Ja | 3.1, 3.5, 5.4, 5.8, Anhang A, C, D, G, L |

#### S2 – Referenzindex

| Referenz | Typ | Ziel | Erste Erwaehnung |
|----------|-----|------|------------------|
| Anhang A | Anhang | Normative Datenvertraege | 3.5 |
| Anhang B | Anhang | Metadaten, CSV und Manifest | 5.7 |
| Anhang C | Anhang | Face-Backend-Vertrag | 5.4 |
| Anhang D | Anhang | Referenzkonfiguration | 6.3 |
| Anhang E | Anhang | Abnahme ACC-01 bis ACC-15 | 8.2 |
| Anhang F | Anhang | CLI, Exit-Codes, Module | 5.12 |
| Anhang G | Anhang | Konfigurationsvertrag | 6.1 |
| Anhang H | Anhang | Archivvertrag | 3.5 |
| Anhang I | Anhang | Sample-Kapazitaetsvertrag | 5.2 |
| Anhang J | Anhang | Reporting, Deployment | 5.11 |
| Anhang K | Anhang | Qualitaet, CI | 7.3 |
| Anhang L | Anhang | Glossar, Migration | 10 |
| Anhang M | Anhang | Mindesttestliste | 8.2 |
| Anhang N | Anhang | Konsistenz- und Einheitlichkeitsregeln | 7.3 |
| Anhang P | Anhang | Config-Kommentierung, MANUAL_DE-Struktur | 7.2 |
| Anhang Q | Anhang | Projektstruktur | Q1 |
| Anhang R | Anhang | Skript-Anforderungen | R1 |
| Anhang S | Anhang | Begriffs- und Referenzindex | S1 |

---

### Anhang T – Aenderungs-Historie und Versionierung

#### T1 – Versions-Historie

| Version | Datum | Autor | Aenderung |
|---------|-------|-------|----------|
| 9.8 | 2026-08-03 | MaiTaiMa + Perplexity AI | Rechtschreib- und Formatkorrekturen, neuer Abschnitt "Architektur und Compliance" (Systemuebersicht, Projektstruktur, Abstraktionsschichten, Datenquellen und Wirkungen, Betriebsskripte, Sicherheits- und Compliance-Grenzen), Aktualisierung der Aenderungs-Historie. |
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

1. **Spezifikation aktuell?** (dieses Dokument, Version x.y.z)
2. **CHANGELOG.md aktuell?** (alle Aenderungen dokumentiert)
3. **MANUAL_DE.md aktuell?** (alle Kapitel konsistent)
4. **Config-Kommentierung vollstaendig?** (alle Variablen, alle Logikbl oecke)
5. **README-Dateien vollstaendig?** (alle Ordner, alle 8 Pflichtfelder)
6. **Skript-Kommentierung vollstaendig?** (alle Header, alle Abschnitte, alle Funktionen)
7. **Tests bestanden?** (ACC-01 bis ACC-15)
8. **NAS-Pilot bestanden?** (vollstaendiger Lauf auf Ziel-NAS)
9. **Git-Clean?** (keine Secrets, keine Produktionspfade, keine Modelle, keine privaten Bilder)
10. **Docker-Image aktuell?** (alle Dependencies, alle Pfade korrekt)

#### T4 – Abnahme-Protokoll

Jede Abnahme MUSS dokumentiert werden mit:

- **Datum:** (ISO8601)
- **Tester:** (Name, Rolle)
- **Version:** (x.y.z)
- **ACC-Tests:** (bestanden/fehlgeschlagen, Details)
- **NAS-Pilot:** (bestanden/fehlgeschlagen, Details)
- **Freigabe:** (ja/nein, Bemerkung)

**Beispiel-Abnahme-Protokoll:**
```json
{
    "datum": "2026-08-04T18:00:00Z",
    "tester": "MaiTaiMa, Entwickler",
    "version": "9.8",
    "acc_tests": {
        "bestanden": 15,
        "fehlgeschlagen": 0,
        "details": "Alle ACC-01 bis ACC-15 bestanden"
    },
    "nas_pilot": {
        "bestanden": true,
        "details": "Vollstaendiger Lauf auf Ziel-NAS, 1000 Bilder, 2 Stunden, keine Fehler"
    },
    "freigabe": {
        "ja": true,
        "bemerkung": "Freigegeben fuer Produktion"
    }
}
```
