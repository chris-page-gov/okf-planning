"""Unit tests for sources acquisition and policy augmentations."""

import unittest
from okf_planning.sources import get_all_augmented_datasets, POLICY_AND_GUIDANCE_AUGMENTATIONS


class TestSources(unittest.TestCase):
    def test_augmented_datasets_loaded(self):
        datasets = get_all_augmented_datasets()
        self.assertGreaterEqual(len(datasets), len(POLICY_AND_GUIDANCE_AUGMENTATIONS))
        policy_ids = [d["dataset"] for d in POLICY_AND_GUIDANCE_AUGMENTATIONS]
        loaded_ids = [d["dataset"] for d in datasets]
        for pid in policy_ids:
            self.assertIn(pid, loaded_ids)

    def test_nppf_augmentation_fields(self):
        datasets = get_all_augmented_datasets()
        nppf = next(d for d in datasets if d["dataset"] == "nppf-framework-policy")
        self.assertEqual(nppf["typology"], "policy")
        self.assertIn("housing", nppf["themes"])
        self.assertEqual(nppf["source_adapter"], "gov-uk-planning-policy")


if __name__ == "__main__":
    unittest.main()
