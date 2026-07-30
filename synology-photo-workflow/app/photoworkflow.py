"""Projekt: Synology Photo Workflow
Datei: app/photoworkflow.py
Mitentwickler: MaiTai
Erstellt: 2026-07-29
Projektversion: 7.7.0
Funktion: Kanonischer CLI-Kompatibilitätseinstieg nach Spezifikation Anhang F.
SICHERHEIT: Delegiert ausschließlich an die zentrale CLI-Implementierung.
"""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
