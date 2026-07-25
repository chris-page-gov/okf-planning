"""Tests for the normative OKF layer and deterministic Explorer projection."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from okf_planning.build import build_bundle, validate_okf_v02_markdown
from okf_planning.evaluation import evaluate_metadata_completeness
from okf_planning.mcp_broker import PlanningMCPBroker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"


def load_json(path: Path):
    with open(path, encoding="utf-8") as source:
        return json.load(source)


class TestBuild(unittest.TestCase):
    def build_into(self, output: Path):
        return build_bundle(output_dir=str(output), cache_dir=str(SOURCE))

    def test_build_bundle_output_structure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            checksums = self.build_into(output)
            self.assertGreater(len(checksums), 250)
            for relative in (
                "index.md",
                "okf-bundle.yamlld",
                "okf-bundle.jsonld",
                "okf-explorer.json",
                "checksums.json",
                "data/manifest.json",
            ):
                self.assertTrue((output / relative).exists(), relative)

            descriptor = load_json(output / "okf-explorer.json")
            self.assertEqual(descriptor["schema"], "okf-explorer-large-corpus.v1")
            self.assertEqual(descriptor["okf_version"], "0.2")
            self.assertEqual(
                descriptor["core_conformance"],
                "OKF v0.2 Markdown concept layer",
            )
            self.assertEqual(descriptor["generated"]["by"], "okf-planning/0.2.0")
            self.assertEqual(descriptor["counts"]["datasets"], 230)
            self.assertTrue(descriptor["authority"]["notEndorsedBySource"])
            self.assertEqual(
                descriptor["extensions"]["okf-core.v0.2"]["status"],
                "conformant",
            )
            semantic = load_json(output / "okf-bundle.jsonld")
            self.assertEqual(semantic["okfVersion"], "0.2")
            self.assertEqual(semantic["okfEntrypoint"], "index.md")

    def test_markdown_layer_is_v02_conformant(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            self.build_into(output)
            result = validate_okf_v02_markdown(output)
            self.assertEqual(result["status"], "conformant")
            self.assertEqual(result["checked_concepts"], 230)
            concept = (
                output / "concepts/policy/nppf-framework-policy.md"
            ).read_text(encoding="utf-8")
            self.assertIn('type: "Planning Policy"', concept)
            self.assertIn("generated:", concept)
            self.assertIn("sources:", concept)
            self.assertNotIn("verified:", concept)
            self.assertNotIn('"author":"team:', concept)
            governance = load_json(output / "data/governance/release.json")
            self.assertEqual(
                governance["freshness_policy"]["stale_after"],
                "2026-10-25",
            )

    def test_manifest_uses_top_level_array_shards(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            self.build_into(output)
            manifest = load_json(output / "data/manifest.json")
            for kind in ("datasets", "resources", "publishers", "relationships"):
                self.assertTrue(manifest["chunks"][kind], kind)
                for relative in manifest["chunks"][kind]:
                    self.assertIsInstance(load_json(output / relative), list)

            hydrated = sum(
                (
                    load_json(output / relative)
                    for relative in manifest["chunks"]["datasets"]
                ),
                [],
            )
            self.assertEqual(len(hydrated), manifest["counts"]["datasets"])

    def test_search_open_is_record_route(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            self.build_into(output)
            docs = load_json(output / "data/search/docs-0.json")
            self.assertTrue(all(document["open"] == document["route"] for document in docs))

    def test_curated_sources_do_not_get_synthetic_planning_endpoints(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            self.build_into(output)
            manifest = load_json(output / "data/manifest.json")
            resources = sum(
                (
                    load_json(output / relative)
                    for relative in manifest["chunks"]["resources"]
                ),
                [],
            )
            nppf = [
                resource
                for resource in resources
                if resource["dataset"] == "nppf-framework-policy"
            ]
            self.assertTrue(nppf)
            self.assertTrue(
                all("planning.data.gov.uk/dataset/" not in item["url"] for item in nppf)
            )
            self.assertTrue(all(item["format"] == "html" for item in nppf))

    def test_build_is_deterministic_and_removes_only_generated_stale_files(self):
        with (
            tempfile.TemporaryDirectory() as first,
            tempfile.TemporaryDirectory() as second,
        ):
            first_path = Path(first)
            second_path = Path(second)
            (first_path / "data/obsolete").mkdir(parents=True)
            (first_path / "data/obsolete/stale.json").write_text(
                "{}", encoding="utf-8"
            )
            (first_path / "app.js").write_text("hand authored", encoding="utf-8")
            (first_path / ".DS_Store").write_text("junk", encoding="utf-8")
            first_checksums = self.build_into(first_path)
            second_checksums = self.build_into(second_path)
            self.assertEqual(first_checksums, second_checksums)
            self.assertFalse((first_path / "data/obsolete/stale.json").exists())
            self.assertEqual(
                (first_path / "app.js").read_text(encoding="utf-8"), "hand authored"
            )
            self.assertNotIn(".DS_Store", first_checksums)

    def test_build_is_stable_across_python_hash_seeds(self):
        script = (
            "from okf_planning.build import build_bundle;"
            "import sys;"
            "build_bundle(sys.argv[1], cache_dir=sys.argv[2])"
        )
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for seed, output in (("1", first), ("8675309", second)):
                subprocess.run(
                    [sys.executable, "-c", script, output, str(SOURCE)],
                    check=True,
                    env={**os.environ, "PYTHONHASHSEED": seed},
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(
                (Path(first) / "checksums.json").read_bytes(),
                (Path(second) / "checksums.json").read_bytes(),
            )

    def test_measured_evaluation_and_discovery_only_broker(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            self.build_into(output)
            report = evaluate_metadata_completeness(str(output))
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["total_records"], 230)
            self.assertEqual(report["checksum_files"], report["verified_files"])

            broker = PlanningMCPBroker(str(output))
            plan = broker.prepare_selection_plan("nppf-framework-policy")
            self.assertEqual(plan["status"], "metadata_only_no_executable_binding")
            self.assertEqual(plan["executable_resources"], [])
            self.assertNotIn("live_endpoint", plan)

    def test_cache_is_required_for_offline_safe_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "pinned source cache"):
                build_bundle(output_dir=temporary)

    def test_v02_validation_rejects_invented_actor_conventions(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "index.md").write_text(
                '---\nokf_version: "0.2"\n---\n\n# Test\n',
                encoding="utf-8",
            )
            (output / "invalid.md").write_text(
                """---
type: "Reference"
generated: {"by":"team:publisher","at":"2026-07-25T11:25:00Z"}
sources: [{"resource":"scope","author":"team:publisher"}]
---

# Invalid actor
""",
                encoding="utf-8",
            )
            result = validate_okf_v02_markdown(output)
            self.assertEqual(result["status"], "non-conformant")
            self.assertTrue(
                any("actor convention" in error for error in result["errors"])
            )
            self.assertTrue(
                any("sources[0].author" in error for error in result["errors"])
            )

    def test_standalone_ui_loads_manifest_shards_without_html_interpolation(self):
        script = (ROOT / "bundle/app.js").read_text(encoding="utf-8")
        self.assertIn("manifest.chunks?.datasets", script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML", script)


if __name__ == "__main__":
    unittest.main()
