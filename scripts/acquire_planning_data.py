#!/usr/bin/env python3
"""Acquire and cache raw metadata snapshots from planning.data.gov.uk."""

import json
import logging
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from okf_planning.sources import load_live_planning_datasets, load_live_planning_organisations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    source_dir = os.path.join(os.path.dirname(__file__), "..", "source")
    os.makedirs(source_dir, exist_ok=True)

    logging.info("Acquiring planning.data.gov.uk dataset definitions...")
    datasets = load_live_planning_datasets()
    ds_path = os.path.join(source_dir, "dataset.json")
    with open(ds_path, "w", encoding="utf-8") as f:
        json.dump(datasets, f, indent=2)
    logging.info("Saved dataset definitions to %s (%d datasets)", ds_path, len(datasets.get("datasets", [])))

    logging.info("Acquiring planning.data.gov.uk organisation definitions...")
    orgs = load_live_planning_organisations()
    org_path = os.path.join(source_dir, "organisation.json")
    with open(org_path, "w", encoding="utf-8") as f:
        json.dump(orgs, f, indent=2)
    logging.info("Saved organisation definitions to %s", org_path)


if __name__ == "__main__":
    main()
