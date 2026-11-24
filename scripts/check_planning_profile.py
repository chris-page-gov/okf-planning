#!/usr/bin/env python3
"""Check the declared inferred-link profile without acquiring source material."""

from __future__ import annotations
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "https://chris-page-gov.github.io/okf-planning/profile/planning-metadata/v1/"


def validate_relationships(relationships, records, schema):
    validator = Draft202012Validator(schema)
    ids = {"dataset/" + row["name"] for row in records}
    for row in relationships:
        validator.validate(row)
        if row["source"] not in ids or row["target"] not in ids:
            raise ValueError("A relationship endpoint has no catalogue record")


def check(root=ROOT):
    schema = json.loads(
        (root / "profiles/planning-metadata/v1/relationship.schema.json").read_bytes()
    )
    Draft202012Validator.check_schema(schema)
    descriptor = json.loads((root / "bundle/okf-explorer.json").read_bytes())
    semantic = json.loads((root / "okf.semantic.json").read_bytes())
    if semantic["semantic_layer"]["profile"] != PROFILE or descriptor["profile"] != PROFILE:
        raise ValueError("The domain profile differs from the reviewed declaration")
    records, relationships = [], []
    manifest = json.loads((root / "bundle/data/manifest.json").read_bytes())
    for path in sorted((root / "bundle/data").glob("datasets-*.json")):
        records.extend(json.loads(path.read_bytes()))
    for path in sorted((root / "bundle/data").glob("relationships-*.json")):
        relationships.extend(json.loads(path.read_bytes()))
    validate_relationships(relationships, records, schema)
    if len(records) != 230 or len(relationships) != 40:
        raise ValueError("Frozen catalogue coverage changed without a source review")
    if manifest["okf_version"] != "0.3":
        raise ValueError("The runtime manifest does not declare Core 0.3")
    return {
        "profile": PROFILE,
        "records": len(records),
        "inferred_relationships": len(relationships),
        "status": "passed",
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
