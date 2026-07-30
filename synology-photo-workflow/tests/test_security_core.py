"""Projekt: Synology Photo Workflow
Datei: tests/test_security_core_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Regressionstests für atomare Steuerdaten, Archivhashes, Kollisionen und Löschjournal.
SICHERHEIT: Originale werden nur durch verifizierte Transaktionen verändert.
"""
from pathlib import Path
import pytest
from app.archives import archive_unneeded
from app.safety import SafetyError, atomic_json, read_control_json, validate_zip, utcnow


def payload():
    now = utcnow()
    return {'schema_version': 1, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'batch_id': 'b'}


def test_control_record_requires_schema_fields(tmp_path):
    with pytest.raises(SafetyError, match='missing'):
        atomic_json(tmp_path / 'x.json', {'schema_version': 1})


def test_archive_collision_and_deletion_journal(tmp_path):
    batch = tmp_path / 'batch'; (batch / 'ARW').mkdir(parents=True); (batch / 'SAVE').mkdir()
    (batch / 'IMG_1.jpg').write_bytes(b'jpg')
    raw = batch / 'ARW' / 'IMG_2.arw'; raw.write_bytes(b'raw')
    (batch / 'SAVE' / 'batch_SORTARW.zip').write_bytes(b'foreign')
    result = archive_unneeded(batch, {'phase2': {'delete_unneeded_arws_after_verified_archive': True}})
    assert result['zip_target_collision'] == 'batch_SORTARW.zip'
    assert len(result['deletions']) == 1 and not raw.exists()
    validate_zip(batch / result['archive_path'], result['entry_hashes'])


def test_state_file_is_rejectable_when_tampered(tmp_path):
    path = tmp_path / 'state.json'; atomic_json(path, payload(), 'batch_id')
    path.write_text('{bad', encoding='utf-8')
    with pytest.raises(SafetyError, match='unreadable'):
        read_control_json(path, 'batch_id')
