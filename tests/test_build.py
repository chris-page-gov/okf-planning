"""Unit tests for OKF Planning bundle compilation engine."""

import json
import os
import tempfile
import unittest

from okf_planning.build import build_bundle


class TestBuild(unittest.TestCase):
    def test_build_bundle_output_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            checksums = build_bundle(output_dir=tmpdir)
            self.assertGreater(len(checksums), 0)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "okf-bundle.yamlld")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "okf-bundle.jsonld")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "okf-explorer.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "checksums.json")))

            with open(os.path.join(tmpdir, "okf-explorer.json"), encoding="utf-8") as f:
                desc = json.load(f)

            self.assertEqual(desc["schema"], "okf-explorer-large-corpus.v1")
            self.assertEqual(desc["profile"], "https://chris-page-gov.github.io/okf-explorer/profile/bundle-wiki/v1/")
            self.assertGreaterEqual(desc["counts"]["datasets"], 230)
            self.assertIn("authority", desc)
            self.assertTrue(desc["authority"]["notEndorsedBySource"])


if __name__ == "__main__":
    unittest.main()
