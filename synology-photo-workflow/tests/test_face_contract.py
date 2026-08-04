"""tests/test_face_contract.py

Spezifikation v10.2 - AP6, AP7
"""
from app.face_backend import MatchMetric, cache_fingerprint, diagnose, match_valid
from app.family_recognition import candidate_allowed, forbidden_unknown_artifact, selection_fingerprint


def test_metric_margin_is_direction_aware():
    assert match_valid(.97, .92, MatchMetric('cosine_similarity', 'higher_is_better', .95, .03))
    assert match_valid(.20, .25, MatchMetric('distance', 'lower_is_better', .21, .03))
    assert not match_valid(.97, None, MatchMetric('cosine_similarity', 'higher_is_better', .95, .03))


def test_registry_rejects_profile_mismatch_without_fallback():
    result = diagnose('onnx_face_cuda', 'cpu')
    assert not result.ready and result.message == 'execution_profile_mismatch'


def test_selection_fingerprint_uses_only_active_references():
    selection = {
        'person_slug': 'person-1',
        'files': [
            {'relative_path': 'reference/a.jpg', 'sha256': 'a', 'status': 'active'},
            {'relative_path': 'newfaces/b.jpg', 'sha256': 'b', 'status': 'active'},
        ],
    }
    assert selection_fingerprint(selection, 'person-1')


def test_unknown_face_can_never_become_candidate():
    assert forbidden_unknown_artifact({'status': 'unmatched', 'person_slug': 'unknown'})
    assert not candidate_allowed('unmatched', 'keep', .9, False)
