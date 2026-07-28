# Paket 0 – Baseline

Erstellt: 2026-07-27T14:07:45Z

## Prüfergebnis

- Syntax: **bestanden** (`python -m compileall -q app`)
- Tests: **fehlgeschlagen** (`python -m pytest -q tests`)
- Testbestand: 23 versionierte Projektdateien im Inventar; der vollständige Dateibaum und SHA-256-Fingerprints stehen in `PACKAGE_0_BASELINE.json`.

## Reproduzierbarer Blocker

`tests/test_v7.py::test_manual_flow` scheitert bei der ersten State-Anlage. In `app/state.py:transition` wird bei einem neuen Batch `old.get(...)` aufgerufen, obwohl `old` noch `None` ist. Der Fehler ist lokal reproduzierbar und keine NAS-/Docker-Ausnahme.

## Umgebungsabhängige Abnahmen

ExifTool-Rücklesevalidierung, YuNet/SFace-ONNX-Inferenz sowie DSM-Scheduler-/Bind-Mount-Prüfungen bleiben ausdrücklich für Paket 11 reserviert.

## Nächster Schritt

Paket 1 repariert und testet den atomaren Zustandsautomaten sowie die JSON-Datenverträge.
