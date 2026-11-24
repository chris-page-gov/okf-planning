"""Package an exact-commit Pages candidate without changing generated bundle bytes."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def package(output: Path, *, allow_dirty: bool = False) -> dict:
    if output.exists():
        raise ValueError("Use a fresh output path; candidates are not overwritten")
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    )
    if dirty and not allow_dirty:
        raise ValueError(
            "Publication requires a clean exact source revision; local diagnostics must explicitly use --allow-dirty"
        )
    source = ROOT / "bundle"
    files = {}
    descriptor = json.loads((source / "okf-explorer.json").read_bytes())
    if descriptor["okf_version"] != "0.3":
        raise ValueError("Wrong Core version")
    for p in sorted(source.rglob("*")):
        if p.is_symlink():
            raise ValueError("Symlink in bundle")
        if not p.is_file():
            continue
        name = p.relative_to(source).as_posix()
        if name == "publication.json":
            raise ValueError("Publication identity must be created only during packaging")
        raw = p.read_bytes()
        files[name] = sha256(raw).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    shutil.copytree(source, output)
    marker = output / ".nojekyll"
    marker.write_bytes(b"")
    files[".nojekyll"] = sha256(b"").hexdigest()
    report = {
        "schema": "okf-planning-publication.v1",
        "source_commit": commit,
        "source_dirty": dirty,
        "release_eligible": not dirty,
        "okf_version": "0.3",
        "product_version": descriptor["version"],
        "snapshot": descriptor["snapshot"],
        "files": files,
    }
    (output / "publication.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return {
        "files": len(files) + 1,
        "commit": commit,
        "manifest_sha256": sha256((output / "publication.json").read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--allow-dirty", action="store_true", help="Local non-promotable diagnostic only"
    )
    a = p.parse_args()
    print(json.dumps(package(a.output, allow_dirty=a.allow_dirty)))
