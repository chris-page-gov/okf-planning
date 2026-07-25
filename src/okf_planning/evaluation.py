"""Measured metadata and integrity evaluation for an OKF Planning bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from okf_planning.build import compute_sha256


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def evaluate_metadata_completeness(bundle_dir: str) -> dict[str, Any]:
    """Audit the generated records, manifest counts, and checksum catalogue."""
    root = Path(bundle_dir).resolve()
    manifest_path = root / "data/manifest.json"
    checksums_path = root / "checksums.json"
    if not manifest_path.exists():
        return {"status": "error", "message": "data/manifest.json not found"}
    if not checksums_path.exists():
        return {"status": "error", "message": "checksums.json not found"}

    manifest = _load_json(manifest_path)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for relative in manifest.get("chunks", {}).get("datasets", []):
        path = (root / relative).resolve()
        if root not in path.parents:
            errors.append(f"dataset shard escapes bundle: {relative}")
            continue
        payload = _load_json(path)
        if not isinstance(payload, list):
            errors.append(f"dataset shard is not a top-level array: {relative}")
            continue
        records.extend(payload)

    fields = ("title", "description", "publisher", "source_url", "resources")
    field_counts = {
        field: sum(1 for record in records if record.get(field)) for field in fields
    }
    possible = len(records) * len(fields)
    present = sum(field_counts.values())

    expected_records = manifest.get("counts", {}).get("records")
    if expected_records != len(records):
        errors.append(
            f"manifest records={expected_records!r}, hydrated records={len(records)}"
        )

    checksums = _load_json(checksums_path)
    verified_files = 0
    for relative, expected_digest in sorted(checksums.items()):
        path = (root / relative).resolve()
        if root not in path.parents:
            errors.append(f"checksum path escapes bundle: {relative}")
        elif not path.is_file():
            errors.append(f"checksummed file missing: {relative}")
        elif compute_sha256(path) != expected_digest:
            errors.append(f"checksum mismatch: {relative}")
        else:
            verified_files += 1

    return {
        "checksum_files": len(checksums),
        "completeness_score": round(present / possible, 4) if possible else 0,
        "errors": errors,
        "field_counts": field_counts,
        "status": "passed" if not errors else "failed",
        "total_entities": manifest.get("counts", {}).get("entities", 0),
        "total_records": len(records),
        "total_relationships": manifest.get("counts", {}).get("relationships", 0),
        "verified_files": verified_files,
        "warning": (
            "Completeness measures metadata-field presence only; it does not "
            "certify source accuracy or fitness for use."
        ),
    }
