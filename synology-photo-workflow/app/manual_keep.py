"""app/manual_keep.py — Manual-Keep-Workflow, process_inbox.

Spezifikation v10.2 - AP8
"""
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any, Callable


def process_inbox(
    inbox: Path | str,
    used: Path | str,
    candidates: list[Path],
    score_fn: Callable[[Path, Path], float],
) -> list[dict[str, Any]]:
    """Verarbeitet Inbox: verschiebt nur bei Margin >= 0.04.

    score_fn(source, candidate) -> float (0-1)
    """
    inbox_path = Path(inbox)
    used_path = Path(used)
    used_path.mkdir(parents=True, exist_ok=True)
    
    results: list[dict[str, Any]] = []
    
    for source_file in inbox_path.glob("*"):
        if not source_file.is_file():
            continue
        
        scores = {c: score_fn(source_file, c) for c in candidates}
        sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_candidates) < 2:
            results.append({"source": source_file.name, "status": "unmatched", "reason": "only_one_candidate"})
            continue
        
        best_score = sorted_candidates[0][1]
        second_score = sorted_candidates[1][1]
        margin = best_score - second_score
        
        if margin >= 0.04:
            # Verschieben nach used/
            shutil.move(str(source_file), str(used_path / source_file.name))
            results.append({
                "source": source_file.name,
                "status": "matched",
                "best_candidate": sorted_candidates[0][0].name,
                "score": best_score,
                "margin": margin,
            })
        else:
            results.append({
                "source": source_file.name,
                "status": "unmatched",
                "reason": "ambiguous",
                "best_score": best_score,
                "second_score": second_score,
                "margin": margin,
            })
    
    return results
