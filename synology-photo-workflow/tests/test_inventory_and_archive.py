"""tests/test_inventory_and_archive.py

Spezifikation v10.2 - AP1, AP4
"""
import zipfile
import pytest
from app.inventory import arw_bindings
from app.safety import SafetyError, validate_zip


def test_active_jpg_protects_exact_matching_arw(tmp_path):
    (tmp_path / 'ARW').mkdir()
    (tmp_path / 'IMG_0001.jpg').write_bytes(b'jpg')
    (tmp_path / 'ARW' / 'IMG_0001.arw').write_bytes(b'arw')
    assert list(arw_bindings(tmp_path).values()) == [True]


def test_non_matching_jpg_does_not_protect_arw(tmp_path):
    (tmp_path / 'ARW').mkdir()
    (tmp_path / 'IMG_0002.jpg').write_bytes(b'jpg')
    (tmp_path / 'ARW' / 'IMG_0001.arw').write_bytes(b'arw')
    assert list(arw_bindings(tmp_path).values()) == [False]


def test_zip_path_traversal_is_rejected(tmp_path):
    archive = tmp_path / 'bad.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('../escape', 'x')
    with pytest.raises(SafetyError, match='zip_path_traversal'):
        validate_zip(archive)
