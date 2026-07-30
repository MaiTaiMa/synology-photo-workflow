# Synology Photo Workflow

Empfohlene Struktur:

- `NAS_EXAMPLE/` auf oberster Ebene als NAS-Zielstruktur
- `synology-photo-workflow/` als eigentlicher Quellcode- und Testbereich

## Einstieg

```sh
cd synology-photo-workflow
cp config/config.yaml config/config.local.yaml
python -m app.photoworkflow --config config/config.local.yaml validate_config
python -m app.photoworkflow --config config/config.local.yaml phase1
```

## Dokumentation

- [Benutzerhandbuch](docs/MANUAL_DE.md)
- [Architektur und Compliance](docs/ARCHITEKTUR_UND_COMPLIANCE.md)
- [Testing und Abnahme](docs/TESTING.md)
- [v7.7 Spezifikation](docs/Synology-Photo-Workflow_Spezifikation_v7-7.md)
- [v7.2 Spezifikation](docs/Synology-Photo-Workflow_Spezifikation_v7-2.md)
