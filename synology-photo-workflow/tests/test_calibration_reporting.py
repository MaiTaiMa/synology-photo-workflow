"""tests/test_calibration_reporting.py

Spezifikation v10.2 - AP5
"""
from app.calibration import rebuild
from app.reporting import action, summary
from app.safety import atomic_json, utcnow


def valid_record(batch, fingerprint):
    now = utcnow()
    return {
        'schema_version': 1, 'batch_id': batch, 'record_id': batch,
        'created_at': now, 'updated_at': now, 'producer_version': '7.8.0',
        'handoff_source': 'manual_review', 'config_fingerprint': fingerprint,
        'images': [{'image_id': 'x', 'predicted_decision': 'reject', 'final_decision': 'keep'}],
    }


def test_rebuild_does_not_mix_config_fingerprints(tmp_path):
    for batch, fingerprint in [('a', 'old'), ('b', 'new')]:
        path = tmp_path / batch / 'review_decision_record.json'
        path.parent.mkdir()
        atomic_json(path, valid_record(batch, fingerprint), 'batch_id')
    result = rebuild(tmp_path, tmp_path / 'summary.json')
    assert result['active_config_fingerprint'] == 'new' and result['record_count'] == 1


def test_run_summary_has_modes_actions_and_required_scope(tmp_path):
    item = action('blocking', 'batch:a', 'Reviewzustand pruefen', 'docs/MANUAL_DE.md')
    result = summary(tmp_path, 'blocked', 'fingerprint', {}, [item])
    assert result['requested_automation_mode'] == 'assisted_review'
    assert result['user_actions_required'][0]['severity'] == 'blocking'
