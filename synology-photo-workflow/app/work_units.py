"""Projekt: Synology Photo Workflow
Datei: app/work_units.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Bildet physische Batches in logische WorkUnits ab, verwaltet deren Zustand und liefert
          die naechste zulaessige Arbeit gemaess Resume-Prioritaet und batch_sort.
SICHERHEIT: Ein geaendertes Inventar eines bereits begonnenen Batches wird niemals still fortgesetzt;
            Ergebnis ist stets `source_inventory_changed`.
HINWEIS: Diese Datei ist neu und noch NICHT in phases.py/planning.py verdrahtet (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from . import VERSION
from .inventory import IMG, RAW, assert_safe_batch, batch_fingerprint, files
from .safety import SafetyError, atomic_json, canonical_hash, read_control_json, utcnow


@dataclass(frozen=True)
class InventoryItem:
    image_id: str
    relative_path: str
    size_bytes: int
    mtime_ns: int


@dataclass(frozen=True)
class BatchInventory:
    batch_id: str
    source_fingerprint: str
    inventory_fingerprint: str
    items: tuple[InventoryItem, ...]


@dataclass(frozen=True)
class WorkUnit:
    work_unit_id: str
    parent_batch_id: str
    phase: Literal['phase1', 'phase2']
    ordinal: int
    image_ids: tuple[str, ...]
    inventory_fingerprint: str


@dataclass(frozen=True)
class WorkUnitPlan:
    work_unit: WorkUnit
    batch_path: Path
    image_paths: tuple[Path, ...]
    resume: bool


def build_inventory(batch_path: Path, basedir: Path) -> BatchInventory:
    batch = assert_safe_batch(batch_path)
    items: list[InventoryItem] = []
    for image in sorted(files(batch, IMG | RAW), key=lambda path: path.relative_to(batch).as_posix()):
        stat = image.stat()
        relative = image.relative_to(batch).as_posix()
        image_id = canonical_hash({'path': relative, 'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns})[:16]
        items.append(InventoryItem(image_id, relative, stat.st_size, stat.st_mtime_ns))
    inventory_fingerprint = canonical_hash([(item.relative_path, item.size_bytes, item.mtime_ns) for item in items])
    return BatchInventory(batch.name, batch_fingerprint(batch), inventory_fingerprint, tuple(items))


def create_work_units(inventory: BatchInventory, phase: str, mode: str, images_per_work_unit: int | None) -> list[WorkUnit]:
    if mode == 'source_batch' or not inventory.items:
        image_ids = tuple(item.image_id for item in inventory.items)
        return [WorkUnit(f'{inventory.batch_id}__{phase}__0', inventory.batch_id, phase, 0, image_ids, inventory.inventory_fingerprint)]
    size = images_per_work_unit or len(inventory.items)
    units = []
    for ordinal, start in enumerate(range(0, len(inventory.items), size)):
        chunk = inventory.items[start:start + size]
        image_ids = tuple(item.image_id for item in chunk)
        units.append(WorkUnit(f'{inventory.batch_id}__{phase}__{ordinal}', inventory.batch_id, phase, ordinal, image_ids, inventory.inventory_fingerprint))
    return units


def _unit_state_path(runtime: str | Path, unit: WorkUnit) -> Path:
    return Path(runtime) / 'work_units' / unit.parent_batch_id / unit.phase / f'{unit.work_unit_id}.json'


def load_work_unit_state(runtime: str | Path, unit: WorkUnit) -> dict[str, Any] | None:
    path = _unit_state_path(runtime, unit)
    if not path.exists():
        return None
    return read_control_json(path, 'work_unit_id')


def write_work_unit_state(runtime: str | Path, unit: WorkUnit, status: str, **extra: Any) -> dict[str, Any]:
    path = _unit_state_path(runtime, unit)
    old = load_work_unit_state(runtime, unit) or {}
    now = utcnow()
    data = {
        **old,
        'schema_version': 1,
        'producer_version': VERSION,
        'work_unit_id': unit.work_unit_id,
        'parent_batch_id': unit.parent_batch_id,
        'phase': unit.phase,
        'ordinal': unit.ordinal,
        'inventory_fingerprint': unit.inventory_fingerprint,
        'status': status,
        'image_ids': list(unit.image_ids),
        'completed_image_ids': old.get('completed_image_ids', []),
        'created_at': old.get('created_at', now),
        'updated_at': now,
        'pending_mutation': extra.pop('pending_mutation', old.get('pending_mutation')),
        **extra,
    }
    atomic_json(path, data, 'work_unit_id')
    return data


def recover_pending_mutation(state: dict[str, Any], batch_path: Path) -> dict[str, Any]:
    mutation = state.get('pending_mutation')
    if not mutation:
        return state
    source = batch_path / mutation['source_relative_path']
    target = batch_path / mutation['target_relative_path']
    target_exists, source_exists = target.exists(), source.exists()
    if target_exists == mutation['expected_target_exists'] and source_exists == mutation['expected_source_exists']:
        completed = set(state.get('completed_image_ids', [])) | {mutation['image_id']}
        return {**state, 'pending_mutation': None, 'completed_image_ids': sorted(completed)}
    if source_exists and not target_exists and not mutation['expected_source_exists']:
        return {**state, 'status': 'recovery_required', 'recovery_reason': 'pending_mutation_retry_required'}
    raise SafetyError('recovery_required:pending_mutation_unresolvable')


def select_next_work_units(config: dict[str, Any], phase: str) -> list[WorkUnitPlan]:
    paths = config['paths']
    runtime = Path(paths['workflow_data']) / 'runtime'
    source_root = Path(paths['temp_sd'] if phase == 'phase1' else paths['temp_done'])
    mode = config['workflow'].get('work_unit_mode', 'source_batch')
    unit_size = config['workflow'].get('images_per_work_unit')
    sort_order = config['workflow'].get('batch_sort', 'oldest_first')

    candidates = sorted(p for p in source_root.iterdir() if p.is_dir() and not p.is_symlink()) if source_root.is_dir() else []
    priority_order = {'recovery_required': 0, 'paused_runtime': 1, 'paused_budget': 1, 'in_progress': 1}
    in_progress: list[tuple[int, WorkUnitPlan]] = []
    fresh: list[WorkUnitPlan] = []

    for batch_path in candidates:
        inventory = build_inventory(batch_path, paths['basedir'])
        for unit in create_work_units(inventory, phase, mode, unit_size):
            state = load_work_unit_state(runtime, unit)
            if state and state.get('inventory_fingerprint') != unit.inventory_fingerprint:
                raise SafetyError('source_inventory_changed')
            image_paths = tuple(batch_path / item.relative_path for item in inventory.items if item.image_id in unit.image_ids)
            plan = WorkUnitPlan(unit, batch_path, image_paths, resume=bool(state))
            status = state.get('status') if state else None
            if status in priority_order:
                in_progress.append((priority_order[status], plan))
            elif not state:
                fresh.append(plan)

    in_progress.sort(key=lambda pair: pair[0])
    fresh.sort(key=lambda plan: plan.batch_path.stat().st_mtime, reverse=(sort_order == 'newest_first'))
    plans = [plan for _, plan in in_progress] + fresh

    limit = config['workflow']['batch_limit']
    if mode != 'source_batch':
        return plans[:limit]
    selected: list[WorkUnitPlan] = []
    seen_batches: set[str] = set()
    for plan in plans:
        batch_id = plan.work_unit.parent_batch_id
        if batch_id not in seen_batches and len(seen_batches) >= limit:
            continue
        seen_batches.add(batch_id)
        selected.append(plan)
    return selected
