# Testing und Abnahme

## Testschichten

- Unit-Tests: Konfiguration, Sicherheit, Archivierung, Recovery, Reporting, Result-Verträge, NAS-Beispielstruktur
- Integrationstests: Exiftool und Signalverhalten, nur optional
- Abnahme: echter NAS-Pilot mit realen Bedingungen

## Ausführung

```sh
python -m pytest -q
python -m pytest -q -m integration
```

## Was muss vor der Freigabe geprüft werden?

1. Phase 1 mit repräsentativen Batches.
2. Manuelle Sichtprüfung vor Phase 2.
3. Verifiziertes Archiv und korrekte Löschung.
4. Reale Wiederaufnahme nach Unterbrechung.
5. Mount-Ausfall, Speichergrenze und SIGTERM im echten Betrieb.

## Wichtige Warnung

Die Standardsuite ersetzt keinen NAS-Pilot. Besonders Archivierung und Wiederaufnahme müssen auf dem Zielsystem noch einmal real beobachtet werden.
