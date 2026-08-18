from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_documentation_lockstep as lockstep  # noqa: E402
import check_pages_candidate as pages  # noqa: E402
import check_publication_contract as contract_check  # noqa: E402


class PublicationMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "okf.publication.json").read_text(encoding="utf-8")
        )

    def test_contract_has_valid_local_references(self) -> None:
        self.assertEqual([], contract_check.validate_document(self.contract))

    def test_unknown_command_fails_closed(self) -> None:
        document = copy.deepcopy(self.contract)
        document["planes"][0]["command_ids"].append("not-declared")
        self.assertTrue(
            any(
                "unknown command" in error
                for error in contract_check.validate_document(document)
            )
        )

    def test_plane_cycle_is_rejected(self) -> None:
        document = copy.deepcopy(self.contract)
        document["planes"][0]["depends_on"] = [document["planes"][-1]["id"]]
        self.assertTrue(
            any("cycle" in error for error in contract_check.validate_document(document))
        )

    def test_controlled_change_requires_documentation_and_changelog(self) -> None:
        errors, controlled, documentation = lockstep.lockstep_errors(
            self.contract, {"src/okf_planning/build.py"}
        )
        self.assertEqual(["src/okf_planning/build.py"], controlled)
        self.assertEqual([], documentation)
        self.assertEqual(2, len(errors))

    def test_documentation_and_changelog_satisfy_lockstep(self) -> None:
        errors, _, documentation = lockstep.lockstep_errors(
            self.contract,
            {
                "src/okf_planning/build.py",
                "docs/publication-method.md",
                "CHANGELOG.md",
            },
        )
        self.assertEqual([], errors)
        self.assertEqual(["docs/publication-method.md"], documentation)

    def test_pages_candidate_reports_missing_entrypoint_and_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors = pages.candidate_errors(Path(temporary), require_nojekyll=True)
        self.assertTrue(any("index.html" in error for error in errors))
        self.assertTrue(any(".nojekyll" in error for error in errors))

    def test_checked_in_pages_entrypoints_exist(self) -> None:
        self.assertEqual([], pages.candidate_errors(ROOT / "bundle"))

    def test_contract_is_named_in_lockstep_surfaces(self) -> None:
        for path in ("README.md", "AGENTS.md", "CHANGELOG.md"):
            self.assertIn(
                "okf.publication.json",
                (ROOT / path).read_text(encoding="utf-8"),
                path,
            )

    def test_pages_workflow_builds_bundle_once_and_promotes_that_candidate(self) -> None:
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertEqual(1, workflow.count("python scripts/build_bundle.py"))
        self.assertLess(
            workflow.index("python scripts/build_bundle.py"),
            workflow.index("git diff --exit-code"),
        )
        self.assertIn("group: pages-publication", workflow)
        self.assertIn("cancel-in-progress: ${{ github.event_name == 'pull_request' }}", workflow)
        self.assertGreaterEqual(workflow.count("timeout-minutes:"), 2)
        actions = re.findall(r"uses: ([^\s]+)", workflow)
        self.assertTrue(actions)
        for action in actions:
            self.assertRegex(action, r"@[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
