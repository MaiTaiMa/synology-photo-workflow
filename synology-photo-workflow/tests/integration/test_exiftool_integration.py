"""Projekt: Synology Photo Workflow
Datei: tests/integration/test_exiftool_integration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Optionaler Exiftool-Integrationstest für tatsächliches Schreiben und Rücklesen verwalteter XMP-Tags.
SICHERHEIT: Integrationstests sind optional und führen nur kontrollierte, lokale Testartefakte aus.
"""
import shutil
from pathlib import Path
import pytest
from app.metadata import write_metadata

pytestmark = pytest.mark.integration


def test_exiftool_writes_and_verifies_xmp_tags(tmp_path):
    if not shutil.which('exiftool'):
        pytest.skip('exiftool not installed')
    image = tmp_path/'fixture.jpg'
    image.write_bytes(bytes.fromhex('ffd8ffe000104a46494600010100000100010000ffdb004300' + '08'*64 + 'ffc00011080001000103012200021101031101ffc40014000100000000000000000000000000000000ffda0008010100003f00ffd9'))
    config = {'metadata': {'write_mode': 'exiftool', 'verify_after_write': True}}
    assert write_metadata(image, {'rating': 4, 'keywords': ['workflow:ai-cull', 'workflow:decision-keep']}, config) == 'written_verified'
