from __future__ import annotations

import argparse
import json
from pathlib import Path

from .orchestrator import prepare_artifacts, run_pilot, run_readiness


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare and check thesis experiment-matrix readiness.")
    parser.add_argument(
        "--base",
        default=None,
        help="Project base containing TSEL and the independent testing projects. Defaults to the parent of this repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="Generate local frozen artifacts and manifests.")
    subparsers.add_parser("readiness", help="Run readiness gates.")
    subparsers.add_parser("pilot", help="Run readiness and local pilot dry-runs.")
    args = parser.parse_args(argv)

    base = Path(args.base).resolve() if args.base else None
    if args.command == "prepare":
        prepared = prepare_artifacts(base)
        print(json.dumps(prepared.to_record(), indent=2, sort_keys=True))
        return 0
    if args.command == "readiness":
        report = run_readiness(base)
        print(json.dumps(report.to_record(), indent=2, sort_keys=True))
        return 0 if report.ready else 1
    report = run_pilot(base)
    print(json.dumps(report.to_record(), indent=2, sort_keys=True))
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
