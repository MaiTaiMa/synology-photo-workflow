"""Projekt: Synology Photo Workflow
Datei: scripts/scan_producer_version_literals.py
Mitentwickler: MaiTai
Erstellt: 2026-08-02
Projektversion: 7.9.0
Funktion: Rein lesendes Hilfsskript, das das Repository nach hartkodierten Versions-Literalen
          durchsucht (statt Referenzen auf app.VERSION), um Drift bei zukuenftigen Releases zu
          erkennen. Fuehrt keine Aenderungen am Code durch.
SICHERHEIT: Das Skript oeffnet Dateien ausschliesslich im Lesemodus und schreibt niemals in das
            durchsuchte Repository; Ausgabe erfolgt nur auf stdout.
HINWEIS: Neu, eigenstaendiges Diagnosewerkzeug (siehe FEATURE_BRANCH_V7_9_0_TODO.md).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r"\b\d+\.\d+\.\d+\b")
EXCLUDED_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}


def scan(root: Path) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in root.rglob('*.py'):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if 'VERSION' in line:
                continue
            if VERSION_PATTERN.search(line):
                findings.append((path, line_number, line.strip()))
    return findings


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    findings = scan(root)
    if not findings:
        print('no_hardcoded_version_literals_found')
        return 0
    for path, line_number, line in findings:
        print(f'{path}:{line_number}: {line}')
    print(f'total_findings={len(findings)}')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
