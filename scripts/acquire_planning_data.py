#!/usr/bin/env python3
"""Acquire and cache raw metadata snapshots from planning.data.gov.uk."""

import json
import logging
import os
import sys
import tempfile

# Ensure src is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from okf_planning.sources import load_live_planning_datasets, load_live_planning_organisations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _write_json_atomically(path: str, payload: object) -> None:
    """Replace a snapshot only after a complete JSON document is on disk."""
    directory = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(
        "w", dir=directory, encoding="utf-8", delete=False
    ) as temporary:
        json.dump(payload, temporary, indent=2, ensure_ascii=False, sort_keys=True)
        temporary.write("\n")
        temporary_path = temporary.name
    os.replace(temporary_path, path)


def main() -> None:
    source_dir = os.path.join(os.path.dirname(__file__), "..", "source")
    os.makedirs(source_dir, exist_ok=True)

    logging.info("Acquiring both planning.data.gov.uk snapshots before replacing either...")
    datasets = load_live_planning_datasets()
    orgs = load_live_planning_organisations()
    if not isinstance(datasets.get("datasets"), list) or not datasets["datasets"]:
        raise ValueError("Refusing to replace dataset snapshot with an empty payload")
    if not isinstance(orgs.get("organisations"), dict) or not orgs["organisations"]:
        raise ValueError("Refusing to replace organisation snapshot with an empty payload")

    ds_path = os.path.join(source_dir, "dataset.json")
    org_path = os.path.join(source_dir, "organisation.json")
    _write_json_atomically(ds_path, datasets)
    _write_json_atomically(org_path, orgs)
    logging.info(
        "Saved dataset definitions to %s (%d datasets)",
        ds_path,
        len(datasets["datasets"]),
    )
    logging.info("Saved organisation definitions to %s", org_path)


if __name__ == "__main__":
    main()
