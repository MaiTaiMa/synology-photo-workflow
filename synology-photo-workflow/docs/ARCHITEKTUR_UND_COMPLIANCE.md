# Architektur und Compliance

## Systemübersicht

Das Projekt trennt Betriebsschnittstelle, CLI, Fachmodule und persistenten NAS-Datenbereich. Shell-Skripte prüfen und starten; sie enthalten keine Geschäftslogik. Die Python-CLI lädt `config/config.yaml`, validiert sie und delegiert an spezialisierte Module. Die Fachmodule erzeugen testbare Ergebnisobjekte und kapseln Dateisystemmutationen.

## Projektstruktur

```text
NAS_EXAMPLE/                 Beispiel für den persistenten NAS-Bereich
  TEMP/                      Arbeitsbereich aus config.paths.basedir
    TEMP_SD/                 neue Eingangsbatches
    TEMP_IMAGES/             Phase-1-Review-Ausgabe
    TEMP_DONE/               menschlich freigegebene Übergabe
    TEMP_ERROR/              Quarantäne und Fehlerfälle
    WORKFLOW_DATA/           States, Logs, Summaries, Caches, Referenzen, Modelle
    MANUAL_KEEP/inbox/       manuelle Keep-Eingänge
    MANUAL_KEEP/used/        bereits zugeordnete Keep-Dateien
synology-photo-workflow/
  app/                       Python-Fachmodule und CLI
  config/config.yaml         zentrale kommentierte Konfiguration
  scripts/                   DSM-/Docker-Start- und Vorprüfungsskripte
  tests/                     Unit- und Vertragsprüfungen
  docs/                      Handbuch, Architektur, Testdokumentation
```

## Abstraktionsschichten

`app.cli` verarbeitet Argumente, lädt Konfiguration und übersetzt Ergebnisse in Exit-Codes. `app.configuration` validiert YAML, Pfade und Fingerprints. `app.inventory` prüft Eingangsstabilität, Endungen und exakte JPG-/ARW-Paarbildung. `app.phases` orchestriert die Phasen, ohne Bewertungs- oder Archivdetails zu duplizieren. `app.culling` berechnet Merkmale, Komponentenscores, Sterne und Vorschläge. `app.metadata` kapselt Exiftool, Keyword-Merge und Rückleseprüfung. `app.archives` kapselt Archivplan, ZIP-Erstellung, Validierung, Hashes, Kollision und Aktivierung.

`app.batchstate` hält den Zustandsautomaten und atomare Updates. `app.locks` schützt parallele Läufe. `app.calibration` erzeugt Records, Indizes und Readiness-Auswertung. `app.facebackend` definiert modellneutrale Protokolle und die Backend-Registry. `app.familyrecognition` verarbeitet Referenzen, Caches und Matchlogik ohne Fachlogik in Adapter zu verlagern. `app.reporting` erzeugt Logs, Scheduler-Ausgabe und Run-Summaries. Diese Trennung ist der vorgesehene Erweiterungspunkt: Ein neues Face-Backend gehört in Adapter/Registry, eine neue Bewertungsregel in `culling`, ein anderes Archivformat in `archives` und keine dieser Änderungen in Shell-Skripte.

## Datenquellen und Wirkungen

Die Inventarisierung bezieht Daten direkt aus `TEMP_SD`; sie erzeugt Manifeste und Paarbindungen. Culling bezieht Bilddaten und die Gewichte aus `config.culling`; seine Scores wirken auf Sterne, Vorschläge und Review-Listen. Metadaten bezieht Entscheidungen und erlaubte Schlüssel aus den Batch-Ergebnissen; sie wirkt ausschließlich bei aktiviertem Schreibmodus auf Bildmetadaten. Archive beziehen nur validierte Phase-2-Kandidaten und erzeugen verifizierte ZIPs im persistenten Bereich. Die Löschlogik bezieht sich auf Archivmanifest, Hash und State; ohne diese Quellen wird kein ARW gelöscht.

Face-Erkennung bezieht Modelle aus dem gewählten Backend, Referenzen und Caches aus `WORKFLOW_DATA`. Ihre Wirkung ist auf Match-Ergebnis, Familien-Score und gegebenenfalls Personentags begrenzt; bei deaktivierter Funktion entstehen keine Face-Artefakte. Kalibrierung bezieht bestätigte Review-Records und wirkt auf Reports und Empfehlungen, niemals selbständig auf Automatikflags.

## Betriebsskripte

`preflight.sh` validiert Mount, Docker und Konfiguration ohne Bildverarbeitung. `dsm-acceptance-preflight.sh` ist die DSM-orientierte Variante. `run-phase1.sh` und `run-phase2.sh` rufen jeweils nur den gleichnamigen CLI-Befehl auf. `run-workflow.sh` startet den kanonischen `run`-Befehl. Alle Skripte verwenden `set -Eeuo pipefail`, klare Pfadvariablen und einen Abbruch bei unsicherer Umgebung.

## Sicherheits- und Compliance-Grenzen

Alle Pfade müssen innerhalb von `paths.basedir` liegen. Phase 2 benötigt valide Freigabe, Locks, konsistenten Batch-State und ein verifiziertes Archiv. Archive werden nicht überschrieben; unsichere Kollisionen erzeugen neue Namen. Persistente Daten liegen außerhalb des Container-Images. Private Bilder, Laufzeitdaten, lokale Secrets und Caches gehören nicht in Git. Die zentrale `config.yaml` ist eine bewusste Projektabweichung von einer separaten Beispielvorlage und muss daher secrets-frei bleiben.
