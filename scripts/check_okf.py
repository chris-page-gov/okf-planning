#!/usr/bin/env python3
"""Validate the checked-in normative OKF layer and generated integrity catalogue."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from okf_planning.build import validate_okf_v02_markdown
from okf_planning.evaluation import evaluate_metadata_completeness


def main() -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bundle = os.path.join(root, "bundle")
    conformance = validate_okf_v02_markdown(bundle)
    integrity = evaluate_metadata_completeness(bundle)
    print(json.dumps({"conformance": conformance, "integrity": integrity}, indent=2))
    return 0 if conformance["status"] == "conformant" and integrity["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
