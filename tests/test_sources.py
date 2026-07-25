"""Unit tests for sources acquisition and policy augmentations."""

import unittest
from pathlib import Path
from unittest.mock import patch

from okf_planning.sources import (
    POLICY_AND_GUIDANCE_AUGMENTATIONS,
    AcquisitionError,
    get_all_augmented_datasets,
    load_live_planning_datasets,
)

SOURCE = Path(__file__).resolve().parents[1] / "source"


class TestSources(unittest.TestCase):
    def test_augmented_datasets_loaded(self):
        datasets = get_all_augmented_datasets(str(SOURCE))
        self.assertGreaterEqual(len(datasets), len(POLICY_AND_GUIDANCE_AUGMENTATIONS))
        policy_ids = [d["dataset"] for d in POLICY_AND_GUIDANCE_AUGMENTATIONS]
        loaded_ids = [d["dataset"] for d in datasets]
        for pid in policy_ids:
            self.assertIn(pid, loaded_ids)

    def test_nppf_augmentation_fields(self):
        datasets = get_all_augmented_datasets(str(SOURCE))
        nppf = next(d for d in datasets if d["dataset"] == "nppf-framework-policy")
        self.assertEqual(nppf["typology"], "policy")
        self.assertIn("housing", nppf["themes"])
        self.assertEqual(nppf["source_adapter"], "gov-uk-mhclg")
        self.assertEqual(
            nppf["publisher_id"],
            "ministry-of-housing-communities-and-local-government",
        )

    def test_augmentations_keep_their_actual_publishers(self):
        datasets = get_all_augmented_datasets(str(SOURCE))
        legislation = next(
            dataset
            for dataset in datasets
            if dataset["dataset"] == "town-and-country-planning-act-1990"
        )
        historic_england = next(
            dataset
            for dataset in datasets
            if dataset["dataset"] == "historic-england-nhle-heritage"
        )
        self.assertEqual(legislation["publisher_id"], "the-national-archives")
        self.assertEqual(historic_england["publisher_id"], "historic-england")
        self.assertEqual(historic_england["licence"], "source-specific")
        self.assertEqual(historic_england["confidence"], "curated-unverified")

    def test_offline_failure_is_explicit_and_does_not_become_empty_data(self):
        with patch("okf_planning.sources.fetch_json", side_effect=OSError("offline")):
            with self.assertRaises(AcquisitionError):
                load_live_planning_datasets()

    def test_pinned_cache_never_requires_connectivity(self):
        with patch("okf_planning.sources.fetch_json", side_effect=OSError("offline")):
            payload = load_live_planning_datasets(str(SOURCE))
        self.assertEqual(len(payload["datasets"]), 220)


if __name__ == "__main__":
    unittest.main()
