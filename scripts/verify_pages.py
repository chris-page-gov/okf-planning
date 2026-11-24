"""Compare every declared deployed file with the exact assured candidate identity."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from time import monotonic
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def safe_path(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or str(path) != value:
        raise ValueError("Unsafe declared publication path")
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--commit", required=True)
    p.add_argument("--manifest-sha256", required=True)
    a = p.parse_args()
    contract = json.loads((ROOT / "okf.publication.json").read_bytes())
    target = [t for t in contract["publication"]["targets"] if t["kind"] == "github-pages"]
    assert len(target) == 1
    base = target[0]["public_base_url"]
    deadline = monotonic() + 55

    def fetch(relative):
        if monotonic() >= deadline:
            raise TimeoutError("Public verification deadline")
        url = base + quote(safe_path(relative), safe="/")
        with urlopen(url, timeout=min(15, max(0.1, deadline - monotonic()))) as response:
            if response.status != 200 or response.url != url:
                raise ValueError("Unexpected public response: " + relative)
            raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError("Oversized publication file")
            return raw

    raw = fetch("publication.json")
    assert sha256(raw).hexdigest() == a.manifest_sha256, "Public candidate manifest differs"
    manifest = json.loads(raw)
    assert manifest["source_commit"] == a.commit and manifest["okf_version"] == "0.3"
    assert manifest["source_dirty"] is False and manifest["release_eligible"] is True
    assert len(manifest["files"]) <= 2000

    def check(item):
        name, digest = item
        body = fetch(name)
        if sha256(body).hexdigest() != digest:
            raise ValueError("Public bytes differ: " + name)
        return len(body)

    with ThreadPoolExecutor(max_workers=6) as executor:
        sizes = list(executor.map(check, manifest["files"].items()))
    assert sum(sizes) <= 128 * 1024 * 1024
    print(
        json.dumps(
            {
                "status": "passed",
                "commit": a.commit,
                "files": len(sizes) + 1,
                "bytes": sum(sizes) + len(raw),
                "manifest_sha256": a.manifest_sha256,
                "browser_journey": "separate mandatory release gate",
            }
        )
    )


if __name__ == "__main__":
    main()
