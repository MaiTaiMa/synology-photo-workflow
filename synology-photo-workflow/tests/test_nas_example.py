"""Projekt: Synology Photo Workflow
Datei: app/tests/test_nas_example.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Automatisierte Prüfung der Projektlogik, Skripte und Verträge.
"""

from pathlib import Path


def test_top_level_nas_example_structure_exists():
    root = Path(__file__).parents[2] / 'NAS_EXAMPLE' / 'TEMP'
    required = [
        'MANUAL_KEEP/inbox', 'MANUAL_KEEP/used', 'TEMP_DONE', 'TEMP_ERROR', 'TEMP_IMAGES', 'TEMP_SD',
        'WORKFLOW_DATA/faces', 'WORKFLOW_DATA/models/family', 'WORKFLOW_DATA/models/taste',
        'WORKFLOW_DATA/runtime/calibration/batches', 'WORKFLOW_DATA/runtime/locks',
        'WORKFLOW_DATA/runtime/logs', 'WORKFLOW_DATA/runtime/quarantine',
        'WORKFLOW_DATA/runtime/runsummaries', 'WORKFLOW_DATA/runtime/state',
        'WORKFLOW_DATA/samples/newrefs', 'WORKFLOW_DATA/samples/notused', 'WORKFLOW_DATA/samples/reference'
    ]
    assert all((root / item / 'README.md').is_file() for item in required)
