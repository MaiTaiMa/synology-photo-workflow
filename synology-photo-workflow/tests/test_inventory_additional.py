"""tests/test_inventory_additional.py

Spezifikation v10.2 - AP4
"""
from pathlib import Path
import pytest
from app.inventory import arw_bindings, assert_safe_batch, batch_id
from app.safety import SafetyError


def test_batch_id_changes_when_original_content_changes(tmp_path):
    batch = tmp_path / 'camera'; batch.mkdir(); image = batch / 'IMG_1.jpg'; image.write_bytes(b'a')
    before = batch_id(batch); image.write_bytes(b'b')
    assert batch_id(batch) != before


def test_review_jpg_is_not_active_and_does_not_protect_raw(tmp_path):
    batch = tmp_path / 'camera'; (batch / 'ARW').mkdir(parents=True); (batch / 'Review').mkdir()
    (batch / 'Review' / 'IMG_1.jpg').write_bytes(b'jpg'); raw = batch / 'ARW' / 'IMG_1.arw'; raw.write_bytes(b'raw')
    assert arw_bindings(batch)[raw] is False


def test_ambiguous_active_jpg_pairing_blocks_phase_two(tmp_path):
    batch = tmp_path / 'camera'; (batch / 'ARW').mkdir(parents=True)
    (batch / 'IMG_1.jpg').write_bytes(b'a'); (batch / 'IMG_1.jpeg').write_bytes(b'b'); (batch / 'ARW' / 'IMG_1.arw').write_bytes(b'r')
    with pytest.raises(SafetyError, match='ambiguous'):
        arw_bindings(batch)


def test_symlink_is_rejected_before_inventory(tmp_path):
    batch = tmp_path / 'camera'; batch.mkdir(); target = tmp_path / 'outside'; target.write_text('x')
    (batch / 'linked.jpg').symlink_to(target)
    with pytest.raises(SafetyError, match='symlink'):
        assert_safe_batch(batch)
