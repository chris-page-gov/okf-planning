#!/usr/bin/env python3
"""Check the local, packaged GitHub Pages candidate entry points."""

from __future__ import annotations

import argparse
from hashlib import file_digest, sha256
import json
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


def identity_errors(bundle: Path, commit: str, manifest_sha256: str) -> list[str]:
    path = bundle / "publication.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        return ["missing or invalid Pages publication manifest"]
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != manifest_sha256:
        return ["Pages publication manifest SHA-256 differs from core validation"]
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["Pages publication manifest is not valid JSON"]
    if not isinstance(manifest, dict) or (
        manifest.get("schema") != "okf-planning-publication.v1"
        or manifest.get("source_commit") != commit
        or manifest.get("okf_version") != "0.3"
        or manifest.get("source_dirty") is not False
        or manifest.get("release_eligible") is not True
    ):
        return ["Pages publication manifest does not bind the expected clean OKF 0.3 candidate"]
    declared = manifest.get("files")
    required = set(REQUIRED_ENTRYPOINTS) | {".nojekyll"}
    if not isinstance(declared, dict) or not required <= declared.keys():
        return ["Pages publication manifest is missing required entry points"]

    actual = set()
    for member in bundle.rglob("*"):
        if member.is_symlink():
            return ["Pages candidate contains a symbolic link"]
        if member != path and member.is_file():
            actual.add(member.relative_to(bundle).as_posix())
    if actual != declared.keys():
        return ["Pages candidate file inventory differs from the publication manifest"]
    for relative, digest in sorted(declared.items()):
        with (bundle / relative).open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != digest:
                return [f"Pages candidate file SHA-256 differs: {relative}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "bundle")
    parser.add_argument("--require-nojekyll", action="store_true")
    parser.add_argument("--expected-commit")
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    if (args.expected_commit is None) != (args.manifest_sha256 is None):
        parser.error("--expected-commit and --manifest-sha256 must be supplied together")
    errors = candidate_errors(args.bundle, args.require_nojekyll)
    if not errors and args.expected_commit is not None:
        errors = identity_errors(args.bundle, args.expected_commit, args.manifest_sha256)
    if errors:
        print("Pages candidate validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.expected_commit is None:
        print("Pages candidate validated: required entry points are present")
    else:
        print("Pages candidate validated: exact source revision and all file digests match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
