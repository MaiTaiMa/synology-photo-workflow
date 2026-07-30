<!--
Projekt: Synology Photo Workflow
Datei: scripts/README.md
Rolle: Betriebs- und Container-Schnittstelle.
Funktion: Beschreibt die Startskripte für Vorprüfung, Phase 1, Phase 2 und Gesamtworkflow.
-->

# Scripts

Die Skripte in diesem Ordner sind die Betriebsschnittstelle für Docker und DSM.
Sie starten Vorprüfungen oder Workflow-Läufe, enthalten aber keine Fachlogik des Foto-Workflows selbst.

## Abgrenzung

- `preflight.sh` prüft nur die Umgebung.
- `run-phase1.sh` und `run-phase2.sh` starten jeweils genau eine Phase.
- `run-workflow.sh` startet den kanonischen Gesamtfluss, ohne die Freigabelogik zu umgehen.
