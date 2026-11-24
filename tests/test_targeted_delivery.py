"""Verify that every canonical record route resolves to its exact original row."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from okf_planning.build import build_bundle, fnv1a_32

ROOT = Path(__file__).resolve().parents[1]


def test_all_records_resolve_through_reviewed_locator_contract():
    with TemporaryDirectory(prefix="okf-planning-locator-") as directory:
        check_locator(Path(directory))


def check_locator(tmp_path):
    build_bundle(output_dir=str(tmp_path), cache_dir=str(ROOT / "source"))
    read = lambda name: json.loads((tmp_path / name).read_bytes())
    descriptor = read("okf-explorer.json")
    manifest = read("data/manifest.json")
    assert descriptor["entrypoints"]["record_locator"] == manifest["indexes"]["record_locator"]
    locator = read(descriptor["entrypoints"]["record_locator"])
    assert (
        locator["schema"] == "okf-record-locator-sharded.v1"
        and locator["algorithm"] == "fnv1a32-prefix-2"
    )
    assert locator["records"] == 230 and locator["snapshot"] == descriptor["snapshot"]
    rows = [row for chunk in locator["record_chunks"] for row in read(chunk)]
    locations = {
        route: position
        for ref in locator["buckets"].values()
        for route, position in read(ref).items()
    }
    assert set(locations) == {row["route"] for row in rows} and len(locations) == 230
    for row in rows:
        bucket = f"{fnv1a_32(row['route']) >> 24:02x}"
        chunk, index = read(locator["buckets"][bucket])[row["route"]]
        assert read(locator["record_chunks"][chunk])[index] == row
        assert row["url"] == row["source_url"] and row["notes"] == row["description"]
        assert row["license_id"] == row["licence_id"] and row["lifecycle_status"] == "draft"
        assert (
            row["metadata_modified"] == row["generated"]["at"] == row["provenance"]["generated_at"]
        )
        assert row["metadata_modified"] == "2026-07-25T11:25:00Z"
    assert sum(row["count"] for row in read("data/facets.json")["typology"]) == 230
    adjacency = read(manifest["indexes"]["relationship_adjacency"])
    edges = [row for p in manifest["chunks"]["relationships"] for row in read(p)]
    for route in locations:
        bucket = f"{fnv1a_32(route) >> 24:02x}"
        incident = (
            read(adjacency["buckets"][bucket]).get(route, [])
            if bucket in adjacency["buckets"]
            else []
        )
        expected = [e for e in edges if route in (e["source"], e["target"])]
        assert incident == [
            {
                **e,
                "authority": "derived",
                "derivation": e["evidence_type"],
                "rule": e.get("note", "deterministic collection rule"),
            }
            for e in expected
        ]
    assert set(read("data/standards/evaluation.json")["conformance"]) == {
        "okf_0_3",
        "dcat_3",
        "prov_o",
        "skos",
    }
