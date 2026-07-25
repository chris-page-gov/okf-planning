"""Unit tests for domain models and OKF 0.2 serialization."""

import unittest

from okf_planning.model import OKFPlanningRecord


class TestModel(unittest.TestCase):
    def test_record_to_explorer_dict(self):
        rec = OKFPlanningRecord(
            id="conservation-area",
            route="dataset/conservation-area",
            title="Conservation Area",
            description="Statutory conservation area boundaries",
            record_type="geography",
            collection="planning-data",
            typology="geography",
            phase="live",
            themes=["heritage"],
            entity_count=3400,
            licence="ogl3",
            licence_text="Open Government Licence v3.0",
            attribution="crown-copyright",
            attribution_text="© Crown copyright",
            source_url="https://www.planning.data.gov.uk/dataset/conservation-area",
            documentation_url="https://www.planning.data.gov.uk/dataset/conservation-area",
            source_adapter="planning-data-gov-uk",
            publisher="https://www.planning.data.gov.uk/",
            publisher_id="planning-data-england",
            publisher_name="MHCLG",
        )

        exp_dict = rec.to_explorer_dict("https://example.gov/okf-planning/")
        self.assertEqual(exp_dict["id"], "conservation-area")
        self.assertEqual(exp_dict["route"], "dataset/conservation-area")
        self.assertEqual(exp_dict["record_type"], "geography")
        self.assertIn("node_json", exp_dict)
        self.assertEqual(exp_dict["node_json"]["@type"], "dcat:Dataset")
        self.assertEqual(exp_dict["open"], "dataset/conservation-area")
        self.assertEqual(exp_dict["generated"]["by"], "okf-planning/0.2.0")
        self.assertEqual(exp_dict["trust_tier"], "unverified")


if __name__ == "__main__":
    unittest.main()
