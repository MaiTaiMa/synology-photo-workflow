"""Projekt: Synology Photo Workflow
Datei: app/metadata.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Exiftool-Metadatenvertrag mit argumentbasiertem Aufruf, verwalteten Keywords und Rückleseprüfung.
SICHERHEIT: Bildanalyse ist optional, lokal und darf keine Originale verändern.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

MANAGED_PREFIX = 'workflow:'


def build_tags(image: dict[str, Any]) -> dict[str, Any]:
    """Erzeugt ausschließlich den normativen Minimal-Tag-Satz ohne Rohscores oder unbekannte Personen."""
    keywords = [f'{MANAGED_PREFIX}ai-cull', f'{MANAGED_PREFIX}decision-{image["predicted_decision"]}']
    if image.get('series_best'):
        keywords.append(f'{MANAGED_PREFIX}series-best')
    if image.get('manual_keep'):
        keywords.append(f'{MANAGED_PREFIX}manual-keep')
    if image.get('family_match') and image.get('person_slug'):
        keywords.extend([f'{MANAGED_PREFIX}family-match', f'{MANAGED_PREFIX}person-{image["person_slug"]}'])
    return {'rating': image.get('star_rating'), 'keywords': keywords}


def write_metadata(image: str | Path, tags: dict[str, Any], config: dict[str, Any]) -> str:
    """Schreibt Metadaten ohne Shell; fehlendes Exiftool bleibt sichtbar und blockiert den Kern nicht."""
    metadata = config['metadata']
    if metadata['write_mode'] == 'disabled':
        return 'disabled'
    executable = shutil.which('exiftool')
    if not executable:
        return 'failed_exiftool_unavailable'
    args = [executable, '-overwrite_original']
    if tags['rating'] is not None:
        args.append(f'-XMP:Rating={tags["rating"]}')
    args.extend(f'-XMP-dc:Subject+={keyword}' for keyword in tags['keywords'])
    result = subprocess.run(args + [str(image)], shell=False, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return 'failed_exiftool_write'
    if not metadata.get('verify_after_write', True):
        return 'written_unverified'
    readback = subprocess.run([executable, '-s3', '-XMP:Rating', '-XMP-dc:Subject', str(image)], shell=False, capture_output=True, text=True, check=False)
    required = [str(tags['rating'])] if tags['rating'] is not None else []
    required += tags['keywords']
    if readback.returncode or any(value not in readback.stdout for value in required):
        return 'failed_metadata_verification'
    return 'written_verified'
