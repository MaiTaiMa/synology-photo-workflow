"""Projekt: Synology Photo Workflow
Datei: app/model_download.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Explizite, verwaltete Modellinstallation ueber einen lokalen Katalog erlaubter Modell-IDs
          mit HTTPS-Zwang, Host-Allowlist, Groessenlimit, SHA256-Pruefung und atomarer Aktivierung.
SICHERHEIT: Workflow-Phasen laden oder installieren nie selbst Modelle; Installation ist eine
            bewusste Verwaltungsaktion, niemals ein Nebenprodukt eines normalen Laufs.
HINWEIS: Neu, noch nicht an ein CLI-Kommando angebunden (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from .safety import SafetyError, sha256


class ModelInstallError(SafetyError):
    pass


def _validate_https_host(url: str, allow_hosts: set[str]) -> None:
    if not url.startswith('https://'):
        raise ModelInstallError('model_download_requires_https')
    host = url.split('/')[2]
    if host not in allow_hosts:
        raise ModelInstallError(f'model_download_host_not_allowed:{host}')


def _download_to_staging(url: str, staging: Path, max_bytes: int, connect_timeout: int, read_timeout: int) -> Path:
    staging.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(request, timeout=connect_timeout) as response:
        if response.status != 200:
            raise ModelInstallError(f'model_download_http_status:{response.status}')
        written = 0
        with staging.open('wb') as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise ModelInstallError('model_download_size_exceeded')
                handle.write(chunk)
    return staging


def _safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    opener = zipfile.ZipFile if archive.suffix == '.zip' else tarfile.open
    with opener(archive) as bundle:
        members = bundle.namelist() if isinstance(bundle, zipfile.ZipFile) else bundle.getnames()
        for member in members:
            if member.startswith('/') or '..' in Path(member).parts:
                raise ModelInstallError('model_archive_path_traversal')
        bundle.extractall(destination)


def install_model(model_id: str, catalog: dict[str, dict[str, Any]], models_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    if model_id not in catalog:
        raise ModelInstallError(f'model_id_not_in_catalog:{model_id}')
    entry = catalog[model_id]
    allow_hosts = set(config['models']['download']['allow_hosts'])
    _validate_https_host(entry['url'], allow_hosts)
    max_bytes = int(config['models']['download']['maximum_artifact_size_mb']) * 1024 * 1024
    staging = models_root / '.staging' / f'{model_id}.download'
    try:
        _download_to_staging(entry['url'], staging, max_bytes, config['models']['download']['connect_timeout_seconds'], config['models']['download']['read_timeout_seconds'])
        if sha256(staging) != entry['sha256']:
            raise ModelInstallError('model_download_hash_mismatch')
        destination = models_root / entry['install_dir']
        if staging.suffix in {'.zip', '.tar', '.tgz'}:
            _safe_extract(staging, destination)
        else:
            destination.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staging), str(destination / staging.name))
        return {'model_id': model_id, 'status': 'installed', 'destination': str(destination)}
    finally:
        if staging.exists():
            staging.unlink()
