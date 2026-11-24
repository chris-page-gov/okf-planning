"""Replay this producer's journey manifest with its exact reviewed Reader."""

import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=ROOT / "release-assurance/tmp/native.json")
    p.add_argument("--bundle", type=Path, default=ROOT / "bundle")
    a = p.parse_args()
    consumer = Path(os.environ["OKF_EXPLORER_ROOT"])
    assert consumer.is_absolute()
    pin = json.loads((ROOT / "walkthroughs/explorer-consumer.json").read_bytes())
    assert (
        subprocess.check_output(
            ["git", "-C", str(consumer), "rev-parse", "HEAD"], text=True
        ).strip()
        == pin["commit"]
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "pnpm",
            "--dir",
            str(consumer / "apps/okf-explorer"),
            "acceptance:bundle",
            "--",
            "--bundle-root",
            str(a.bundle.resolve()),
            "--journeys",
            str((a.bundle / "reader-journeys.json").resolve()),
            "--output",
            str(a.output.resolve()),
            "--port",
            "4293",
        ],
        check=True,
        timeout=900,
    )


if __name__ == "__main__":
    main()
