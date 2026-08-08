"""Projekt: Synology Photo Workflow
Datei: tests/test_safety.py
Mitentwickler: MaiTai
Erstellt: 2026-08-08
Projektversion: 7.9.0
Funktion: Prüft AP-01 Pfadgrenzen, Traversal-Schutz und Symlink-Blockade.
"""

from app.safety import is_within_base, validate_path


def test_validate_path_allows_paths_within_base(tmp_path):
    allowed = validate_path(str(tmp_path / 'inside'), str(tmp_path))
    assert allowed.allowed is True


def test_validate_path_blocks_paths_outside_base(tmp_path):
    outside = tmp_path.parent / 'outside'
    blocked = validate_path(str(outside), str(tmp_path))
    assert blocked.allowed is False
    assert blocked.reason == 'path_outside_base'


def test_validate_path_blocks_dotdot_traversal(tmp_path):
    blocked = validate_path('../escape', str(tmp_path))
    assert blocked.allowed is False
    assert blocked.reason == 'path_traversal'


def test_is_within_base_blocks_symlink_outside(tmp_path):
    outside_dir = tmp_path.parent / 'outside'
    outside_dir.mkdir()
    outside_file = outside_dir / 'x.txt'
    outside_file.write_text('x', encoding='utf-8')
    link = tmp_path / 'link.txt'
    link.symlink_to(outside_file)
    assert is_within_base(link, tmp_path) is False


def test_publish_root_can_be_validated_separately(tmp_path):
    publish_root = tmp_path / 'publish'
    publish_root.mkdir()
    valid_target = validate_path(str(publish_root / 'albumA'), str(publish_root))
    invalid_target = validate_path(str(tmp_path.parent / 'other' / 'albumA'), str(publish_root))
    assert valid_target.allowed is True
    assert invalid_target.allowed is False
