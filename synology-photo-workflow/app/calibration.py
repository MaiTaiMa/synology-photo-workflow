"""Projekt: Synology Photo Workflow
Datei: app/calibration.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Unveränderliche Review-Records, rekonstruierbare Kennzahlen und konservative Automatikbereitschaft.
SICHERHEIT: Reports sind rekonstruierbar und schalten Automatik niemals selbst ein.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from .safety import atomic_json, canonical_hash, read_control_json, utcnow


def record(batch_id: str, manifest: dict[str, Any], decisions: dict[str, str], config_fingerprint: str, model_version: str, source: str = 'manual_review') -> dict[str, Any]:
    """Erzeugt vor jeder ARW-Aktion die fachliche Wahrheit eines manuell geprüften Batches."""
    images = []
    for item in manifest['images']:
        final = decisions[item['image_id']]
        predicted = item['predicted_decision']
        correction = 'confirmed' if predicted == final else ('manualkeep' if item.get('manual_keep') else 'promoted' if final == 'keep' else 'demoted')
        images.append({'image_id': item['image_id'], 'relative_phase1_path': item['relative_path'], 'predicted_decision': predicted, 'final_decision': final, 'correction_type': correction, 'final_score': item['final_score'], 'features': item['components'], 'final_path': item['final_path']})
    now = utcnow()
    return {'schema_version': 1, 'record_id': canonical_hash(images)[:16], 'batch_id': batch_id, 'handoff_source': source, 'phase1_at': manifest['created_at'], 'review_at': now, 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'config_fingerprint': config_fingerprint, 'model_version': model_version, 'integrity_hashes': [item['image_id'] for item in images], 'images': images}


def rebuild(records_dir: str | Path, out_path: str | Path, configuration: dict[str, Any] | None = None) -> dict[str, Any]:
    """Baut Kennzahlen ausschließlich aus validen, kompatiblen manuellen Batch-Records neu auf."""
    records = []
    for path in sorted(Path(records_dir).glob('*/review_decision_record.json')):
        value = read_control_json(path, 'batch_id')
        if value.get('handoff_source') == 'manual_review':
            records.append(value)
    active_fingerprint = records[-1]['config_fingerprint'] if records else None
    compatible = [record for record in records if record['config_fingerprint'] == active_fingerprint]
    images = [image for record in compatible for image in record['images']]
    direct = [image for image in images if image['predicted_decision'] in {'keep', 'reject'}]
    terminal_agreement = sum(image['predicted_decision'] == image['final_decision'] for image in direct) / len(direct) if direct else None
    reject_to_keep = sum(image['predicted_decision'] == 'reject' and image['final_decision'] == 'keep' for image in images) / len(images) if images else None
    reject_to_review = sum(image['predicted_decision'] == 'reject' and image['final_decision'] == 'review' for image in images) / len(images) if images else None
    keep_to_reject = sum(image['predicted_decision'] == 'keep' and image['final_decision'] == 'reject' for image in images) / len(images) if images else None
    review_rate = sum(image['predicted_decision'] == 'review' for image in images) / len(images) if images else None
    readiness = 'collecting'
    reason = 'Keine kompatiblen manuell bestätigten Batches.'
    if configuration and images:
        limits = configuration['calibration']
        eligible = len(compatible) >= limits['reviewed_batches_minimum'] and len(images) >= limits['reviewed_images_minimum'] and terminal_agreement is not None and terminal_agreement >= limits['terminal_agreement_minimum'] and reject_to_keep <= limits['reject_to_keep_rate_maximum']
        readiness = 'eligible_automatic_phase2' if eligible else 'learning'
        reason = 'Alle konfigurierten Referenz-Gates erfüllt; Aktivierung bleibt menschliche Entscheidung.' if eligible else 'Noch nicht alle Kalibrierungs-Gates erfüllt.'
    now = utcnow()
    payload = {'schema_version': 1, 'calibration_scope': 'global', 'created_at': now, 'updated_at': now, 'producer_version': '7.7.0', 'record_count': len(compatible), 'image_count': len(images), 'active_config_fingerprint': active_fingerprint, 'terminal_agreement': terminal_agreement, 'reject_to_keep_rate': reject_to_keep, 'reject_to_review_rate': reject_to_review, 'keep_to_reject_rate': keep_to_reject, 'review_rate': review_rate, 'trend': 'not_available', 'status': readiness, 'reason': reason, 'next_action': 'Review-Batches fortsetzen und Kennzahlen beobachten.', 'record_ids_hash': canonical_hash([record['record_id'] for record in compatible])}
    atomic_json(out_path, payload, 'calibration_scope')
    return payload
