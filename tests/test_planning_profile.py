"""Protect the inferred-link boundary and endpoint closure."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "planning_profile", ROOT / "scripts/check_planning_profile.py"
)
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class PlanningProfileTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(
            (ROOT / "profiles/planning-metadata/v1/relationship.schema.json").read_bytes()
        )
        self.records = [{"name": "a"}, {"name": "b"}]
        self.link = {
            "source": "dataset/a",
            "target": "dataset/b",
            "kind": "governed-by",
            "confidence": "inferred",
            "evidence_type": "deterministic-collection-rule",
        }

    def test_migration_cannot_promote_an_inferred_link_to_official_evidence(self):
        for key, value in [("confidence", "official"), ("evidence_type", "human-verified")]:
            changed = copy.deepcopy(self.link)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValidationError):
                profile.validate_relationships([changed], self.records, self.schema)
        profile.validate_relationships(
            [{**self.link, "extension_note": "Retain unknown fields"}], self.records, self.schema
        )

    def test_missing_endpoint_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "endpoint"):
            profile.validate_relationships([self.link], self.records[:1], self.schema)


if __name__ == "__main__":
    unittest.main()
