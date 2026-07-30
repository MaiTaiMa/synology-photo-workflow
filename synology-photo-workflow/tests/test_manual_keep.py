"""Projekt: Synology Photo Workflow
Datei: tests/test_manual_keep.py
Mitentwickler: MaiTai
Erstellt: 2026-07-30
Projektversion: 7.7.0
Funktion: Prüft Mehrkandidaten-Bestmatch, Marge und Nichtbewegung bei unsicherer Zuordnung.
SICHERHEIT: Manual Keep bleibt konservativ; keine Datei wird ohne eindeutigen Vergleich verschoben.
"""
from app.manual_keep import process_inbox


def test_manual_keep_moves_only_clear_best_of_multiple_candidates(tmp_path):
    inbox, used = tmp_path / 'inbox', tmp_path / 'used'
    inbox.mkdir()
    source = inbox / 'keep.jpg'
    source.write_bytes(b's')
    first, second = tmp_path / 'first.jpg', tmp_path / 'second.jpg'
    first.write_bytes(b'a')
    second.write_bytes(b'b')
    scores = {first.name: .97, second.name: .91}
    result = process_inbox(inbox, used, [first, second], lambda _source, candidate: scores[candidate.name])
    assert result[0]['status'] == 'matched' and (used / 'keep.jpg').exists()


def test_manual_keep_keeps_ambiguous_source_in_inbox(tmp_path):
    inbox, used = tmp_path / 'inbox', tmp_path / 'used'
    inbox.mkdir()
    (inbox / 'keep.jpg').write_bytes(b's')
    first, second = tmp_path / 'first.jpg', tmp_path / 'second.jpg'
    first.write_bytes(b'a')
    second.write_bytes(b'b')
    result = process_inbox(inbox, used, [first, second], lambda _source, _candidate: .97)
    assert result[0]['status'] == 'unmatched' and (inbox / 'keep.jpg').exists()
