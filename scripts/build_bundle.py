#!/usr/bin/env python3
"""CLI build entrypoint for OKF Planning Bundle v0.2."""

import logging
import os
import sys

# Ensure src is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from okf_planning.build import build_bundle

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bundle_dir = os.path.join(root_dir, "bundle")
    source_dir = os.path.join(root_dir, "source")

    cache_dir = source_dir if os.path.exists(os.path.join(source_dir, "dataset.json")) else None

    logging.info("Starting OKF Planning Bundle build v0.2.0...")
    checksums = build_bundle(output_dir=bundle_dir, cache_dir=cache_dir)
    logging.info("OKF Planning Bundle build successful! Generated %d checksum entries in %s", len(checksums), bundle_dir)


if __name__ == "__main__":
    main()
