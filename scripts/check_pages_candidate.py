#!/usr/bin/env python3
"""Check the local, packaged GitHub Pages candidate entry points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENTRYPOINTS = (
    "index.html",
    "index.md",
    "concepts/index.md",
    "okf-explorer.json",
    "okf-bundle.yamlld",
    "okf-bundle.jsonld",
    "checksums.json",
)


def candidate_errors(bundle: Path, require_nojekyll: bool = False) -> list[str]:
    errors = [
        f"missing Pages entry point: {relative}"
        for relative in REQUIRED_ENTRYPOINTS
        if not (bundle / relative).is_file()
    ]
    if require_nojekyll and not (bundle / ".nojekyll").is_file():
        errors.append("missing Pages packaging marker: .nojekyll")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "bundle")
    parser.add_argument("--require-nojekyll", action="store_true")
    args = parser.parse_args()
    errors = candidate_errors(args.bundle, args.require_nojekyll)
    if errors:
        print("Pages candidate validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Pages candidate validated: required entry points are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
