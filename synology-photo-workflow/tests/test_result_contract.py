"""Projekt: Synology Photo Workflow
Datei: tests/test_result_contract.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft kanonische Entscheidungszähler, Statusaggregation und Phase-2-ZIP-Konfliktweitergabe.
SICHERHEIT: Ergebnisdaten sind vollständig, aber enthalten keine Bildbytes oder biometrischen Vektoren.
"""
from app.result_contract import decision_counts, phase2_result, status_summary


def test_result_contract_counts_only_canonical_decisions():
    assert decision_counts([
        {'predicted_decision': 'keep'},
        {'predicted_decision': 'review'},
        {'predicted_decision': 'other'},
    ]) == {'keep': 1, 'review': 1, 'reject': 0}


def test_status_summary_and_zip_conflict_are_preserved():
    archive = {'archive_path': 'SAVE/a.zip', 'archive_hash': 'x', 'zip_target_collision': 'old.zip'}
    result = phase2_result('b', [{'final_decision': 'reject'}], archive)
    assert status_summary(['disabled', 'disabled', 'written']) == {'disabled': 2, 'written': 1}
    assert result['decision_counts']['reject'] == 1 and result['zip_conflicts'] == ['old.zip']
