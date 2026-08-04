"""app/cli.py — CLI-Einstiegspunkt, validate_config, phase1, recover_batch.

Spezifikation v10.2 - AP6
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .configuration import load_config
from .safety import utcnow
from .batch_state import state_path, read_state


EXIT = {
    "success": 0,
    "recoverable": 1,
    "error": 2,
}


def main(argv: list[str] | None = None) -> int:
    """CLI-Main (Stub)."""
    parser = argparse.ArgumentParser(prog="photoworkflow")
    parser.add_argument("--config", required=True, type=Path)
    sub = parser.add_subparsers(dest="command")
    
    # validate_config
    sub.add_parser("validate_config")
    
    # phase1
    p1 = sub.add_parser("phase1")
    p1.add_argument("--dry_run", action="store_true")
    
    # recover_batch
    rec = sub.add_parser("recover_batch")
    rec.add_argument("batch_id")
    
    args = parser.parse_args(argv)
    config = load_config(args.config)
    
    if args.command == "validate_config":
        print(json.dumps({"valid": True, "config": config}))
        return EXIT["success"]
    
    elif args.command == "phase1":
        if args.dry_run:
            print(json.dumps({"dry_run": True, "batches": []}))
            return EXIT["success"]
        return EXIT["success"]
    
    elif args.command == "recover_batch":
        runtime = Path(config["paths"]["workflow_data"]) / "runtime"
        sp = state_path(runtime, args.batch_id)
        state = read_state(sp)
        print(json.dumps({
            "batch_id": args.batch_id,
            "state": state,
            "safe_to_auto_resume": False,
        }))
        return EXIT["recoverable"]
    
    return EXIT["error"]


if __name__ == "__main__":
    sys.exit(main())
