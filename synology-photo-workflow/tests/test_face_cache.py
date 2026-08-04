"""tests/test_face_cache.py

Spezifikation v10.2 - AP7
"""
from pathlib import Path
from app.face_backend import FaceBackendDiagnosis, MatchMetric
from app.face_cache import rebuild_plan, write_cache_manifest
from app.safety import sha256, read_control_json


def diagnosis():
    return FaceBackendDiagnosis(
        True, 'opencv_yunet_sface_cpu', 'ready', '1',
        MatchMetric('cosine_similarity', 'higher_is_better', .95, .03),
        'CPUExecutionProvider', ('modelhash',),
    )


def test_cache_plan_uses_only_active_hashed_references(tmp_path):
    reference = tmp_path / 'reference' / 'a.jpg'
    reference.parent.mkdir()
    reference.write_bytes(b'image')
    selection = {
        'person_slug': 'ada',
        'files': [
            {'relative_path': 'reference/a.jpg', 'sha256': sha256(reference), 'status': 'active'},
            {'relative_path': 'newfaces/no.jpg', 'sha256': 'ignored', 'status': 'active'},
        ],
    }
    plan = rebuild_plan(tmp_path, 'ada', selection, diagnosis())
    assert plan['reference_count'] == 1 and plan['status'] == 'ready'


def test_cache_manifest_never_persists_vectors(tmp_path):
    reference = tmp_path / 'reference' / 'a.jpg'
    reference.parent.mkdir()
    reference.write_bytes(b'image')
    selection = {
        'person_slug': 'ada',
        'files': [{'relative_path': 'reference/a.jpg', 'sha256': sha256(reference), 'status': 'active'}],
    }
    plan = rebuild_plan(tmp_path, 'ada', selection, diagnosis())
    write_cache_manifest(tmp_path / 'cache.json', plan, diagnosis(), [])
    assert read_control_json(tmp_path / 'cache.json', 'cache_fingerprint')['vector_storage'] == 'none'
