"""Projekt: Synology Photo Workflow
Datei: tests/test_archive_resume_v77.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft sichere Archivwiederaufnahme ohne neues ZIP und Blockade bei verändertem Archiv.
SICHERHEIT: Wiederaufnahme validiert stets das vorhandene Archiv und löscht nur nachweislich archivierte Quellen.
"""
import pytest
from app.archives import archive_unneeded, resume_archive
from app.safety import SafetyError


def config(delete=True):
    return {'phase2': {'delete_unneeded_arws_after_verified_archive': delete}}


def prepare(batch):
    (batch/'ARW').mkdir(parents=True)
    (batch/'ARW'/'IMG.ARW').write_bytes(b'raw-content')


def test_resume_uses_existing_archive_and_finishes_missing_deletions(tmp_path):
    batch = tmp_path/'batch'; prepare(batch)
    manifest = archive_unneeded(batch, config(False))
    assert (batch/'ARW'/'IMG.ARW').exists()
    resumed = resume_archive(batch, config(True))
    assert not (batch/'ARW'/'IMG.ARW').exists()
    assert resumed['archive_hash'] == manifest['archive_hash'] and len(resumed['deletions']) == 1


def test_resume_blocks_changed_archive(tmp_path):
    batch = tmp_path/'batch'; prepare(batch)
    manifest = archive_unneeded(batch, config(False))
    (batch/manifest['archive_path']).write_bytes(b'changed')
    with pytest.raises(SafetyError, match='archive'):
        resume_archive(batch, config(True))
