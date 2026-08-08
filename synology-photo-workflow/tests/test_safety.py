"""Projekt: Synology Photo Workflow
Datei: tests/test_safety.py
Mitentwickler: MaiTai
Erstellt: 2026-08-08
Projektversion: 7.9.0
Funktion: Prueft den 01AP-Safety-Vertrag fuer Basisgrenzen,
          Traversal-Blockade und Symlink-Schutz.
SICHERHEIT: Pfade ausserhalb der erlaubten Wurzel duerfen nie still akzeptiert werden.

Aenderungsprotokoll:
  2026-08-08 | 7.9.0 | Neue 01AP-Tests fuer validate_path, is_within_base
                       und block_traversal hinzugefuegt.
"""
from __future__ import annotations

from app.safety import block_traversal, is_within_base, validate_path


def test_validate_path_accepts_path_within_base(tmp_path):
    base = tmp_path / 'base'
    target = base / 'folder' / 'image.jpg'
    target.parent.mkdir(parents=True)
    target.write_text('ok', encoding='utf-8')

    result = validate_path(str(target), str(base))

    assert result.allowed is True
    assert result.reason is None


def test_validate_path_blocks_path_outside_base(tmp_path):
    base = tmp_path / 'base'
    outside = tmp_path / 'outside' / 'image.jpg'
    base.mkdir()
    outside.parent.mkdir(parents=True)
    outside.write_text('x', encoding='utf-8')

    result = validate_path(str(outside), str(base))

    assert result.allowed is False
    assert result.reason == 'outside_base'


def test_block_traversal_rejects_dotdot_segments():
    result = block_traversal('../outside/file.jpg')

    assert result.allowed is False
    assert result.reason == 'path_traversal'


def test_is_within_base_blocks_symlink_to_outside(tmp_path):
    base = tmp_path / 'base'
    outside = tmp_path / 'outside'
    base.mkdir()
    outside.mkdir()
    (outside / 'foreign.txt').write_text('blocked', encoding='utf-8')
    (base / 'link').symlink_to(outside, target_is_directory=True)

    assert is_within_base(base / 'link' / 'foreign.txt', base) is False


def test_publish_root_validation_is_separate(tmp_path):
    publish_root = tmp_path / 'publish'
    album = publish_root / 'album'
    publish_root.mkdir()
    album.mkdir()
    allowed = validate_path(str(album), str(publish_root))
    blocked = validate_path(str(tmp_path / 'foreign' / 'album'), str(publish_root))

    assert allowed.allowed is True
    assert blocked.allowed is False
    assert blocked.reason == 'outside_base'
