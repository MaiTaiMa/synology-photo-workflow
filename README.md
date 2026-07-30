# Synology Photo Workflow

Dieses Repository enthält einen konservativen Zwei-Phasen-Workflow für Kamera- und Foto-Batches auf Synology NAS und in Docker-Umgebungen. Das Projekt inventarisiert Eingänge, bereitet eine manuelle Sichtprüfung vor und führt freigegebene Batches erst danach in eine kontrollierte Archiv- und Bereinigungsphase über.

## Einstieg

- [Benutzerhandbuch](synology-photo-workflow/docs/MANUAL_DE.md)
- [Architektur und Compliance](synology-photo-workflow/docs/ARCHITEKTUR_UND_COMPLIANCE.md)
- [Testing und Abnahme](synology-photo-workflow/docs/TESTING.md)
- [Konfiguration](synology-photo-workflow/config/config.yaml)
- [Skripte](synology-photo-workflow/scripts/README.md)

## Inhalte des Repos

- `synology-photo-workflow/app/` enthält die Python-Fachmodule und die CLI.
- `synology-photo-workflow/scripts/` enthält die Bash-Start- und Vorprüfungsskripte.
- `synology-photo-workflow/tests/` enthält die automatisierten Prüfungen.
- `synology-photo-workflow/docs/` enthält die ausführliche Dokumentation.
- `NAS_EXAMPLE/` zeigt die persistente Zielstruktur für den NAS-Betrieb.

## Was das Projekt macht

Der Workflow trennt Eingang, Review, Freigabe und endgültige Archivierung. Phase 1 erzeugt aus Eingangsbatches prüfbare Ergebnisse, Phase 2 verarbeitet nur manuell freigegebene Batches weiter. Optional können Face- und Referenzfunktionen aktiv werden, solange die Konfiguration, die Modelle und die Abnahme dazu passen.

## Wichtige Hinweise

- Der Repository-Root ist nur der Einstiegspunkt; die operative NAS-Struktur liegt in `NAS_EXAMPLE/`.
- Die aktive Konfiguration ist `synology-photo-workflow/config/config.yaml`.
- Die Shell-Skripte prüfen und starten nur; die fachliche Logik liegt in Python.
- Für die ausführliche Inbetriebnahme und Nutzung nutze das Handbuch.
