#!/usr/bin/env python3
"""Validate the checked-in normative OKF layer and generated integrity catalogue."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from okf_planning.build import CORE_ROLE_IRI, CORE_VERSION, PLANNING_PROFILE, validate_okf_v03_markdown
from okf_planning.evaluation import evaluate_metadata_completeness


def main() -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bundle = os.path.join(root, "bundle")
    conformance = validate_okf_v03_markdown(bundle)
    integrity = evaluate_metadata_completeness(bundle)
    descriptor = _load_json(os.path.join(bundle, "okf-explorer.json"))
    manifest = _load_json(os.path.join(bundle, "data/manifest.json"))
    semantic = _load_json(os.path.join(bundle, "okf-bundle.jsonld"))
    roles = {"errors": [], "counts": {}}

    if descriptor.get("okf_version") != CORE_VERSION:
        roles["errors"].append("descriptor does not declare OKF core 0.3")
    if descriptor.get("profile") != PLANNING_PROFILE:
        roles["errors"].append("descriptor does not identify the Planning metadata profile")
    datasets = _load_chunks(bundle, manifest.get("chunks", {}).get("datasets", []))
    publishers = _load_chunks(bundle, manifest.get("chunks", {}).get("publishers", []))
    resources = _load_chunks(bundle, manifest.get("chunks", {}).get("resources", []))
    graph_records = semantic.get("record", [])
    roles["counts"] = {
        "core_concepts": len(datasets),
        "metadata_publishers": len(publishers),
        "metadata_resources": len(resources),
        "semantic_concepts": len(graph_records),
    }
    if len(datasets) != conformance["checked_concepts"]:
        roles["errors"].append("typed Markdown and runtime concept counts differ")
    if any(row.get("core_role") != "concept" for row in datasets):
        roles["errors"].append("a typed Markdown concept lacks the concept runtime role")
    if any(row.get("core_role") != "extension" for row in publishers + resources):
        roles["errors"].append("a metadata support record lacks the extension runtime role")
    if any(row.get(CORE_ROLE_IRI) != "concept" for row in graph_records):
        roles["errors"].append("semantic concept graph lacks the explicit core role")
    if len(graph_records) != len(datasets):
        roles["errors"].append("semantic and runtime concept counts differ")
    if semantic.get("okfVersion") != CORE_VERSION:
        roles["errors"].append("semantic graph does not declare OKF core 0.3")
    roles["status"] = "passed" if not roles["errors"] else "failed"
    print(json.dumps({"conformance": conformance, "integrity": integrity, "roles": roles}, indent=2))
    return 0 if conformance["status"] == "conformant" and integrity["status"] == "passed" and roles["status"] == "passed" else 1


def _load_json(path: str):
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def _load_chunks(bundle: str, paths: list[str]):
    return [row for relative in paths for row in _load_json(os.path.join(bundle, relative))]


if __name__ == "__main__":
    raise SystemExit(main())
