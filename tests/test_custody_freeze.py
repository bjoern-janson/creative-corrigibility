from __future__ import annotations

import json
import unittest
from pathlib import Path

from creative_corrigibility.custody import (
    APPARATUS_PARENT_COMMIT,
    FREEZE_ID,
    FreezeVerificationError,
    load_manifest,
    verify_freeze,
    verify_manifest_signature,
)


ROOT = Path(__file__).resolve().parents[1]


class CustodyFreezeTests(unittest.TestCase):
    def test_current_tree_verifies_as_frozen_apparatus(self):
        report = verify_freeze(ROOT)
        self.assertTrue(report.ok)
        self.assertEqual(report.status, "FROZEN_APPARATUS")
        self.assertEqual(report.freeze_id, FREEZE_ID)
        self.assertEqual(report.parent_commit, APPARATUS_PARENT_COMMIT)
        self.assertEqual(report.cube_coverage, "16/16")
        self.assertEqual(report.ci_tests, 17)
        self.assertEqual(report.correction_horizon, 3)

    def test_manifest_binds_the_calibrated_parent_commit(self):
        manifest = load_manifest(ROOT)
        self.assertEqual(manifest["freeze_id"], FREEZE_ID)
        self.assertEqual(manifest["apparatus_parent_commit"], APPARATUS_PARENT_COMMIT)
        self.assertEqual(manifest["status"], "FROZEN_APPARATUS")

    def test_manifest_signature_is_valid(self):
        self.assertTrue(verify_manifest_signature(ROOT))

    def test_manifest_signature_rejects_tampered_payload(self):
        manifest_path = ROOT / "custody" / "FREEZE_V0.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["correction_horizon"] = 999
        tampered = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        with self.assertRaises(FreezeVerificationError):
            verify_manifest_signature(ROOT, manifest_bytes=tampered)

    def test_hash_mismatch_invalidates_frozen_apparatus(self):
        manifest = load_manifest(ROOT)
        target = "src/creative_corrigibility/measurement.py"
        original = (ROOT / target).read_bytes()
        with self.assertRaises(FreezeVerificationError):
            verify_freeze(ROOT, content_overrides={target: original + b"\n# mutation\n"})

    def test_prospective_additions_do_not_change_frozen_hash_set(self):
        manifest = load_manifest(ROOT)
        frozen_paths = set(manifest["frozen_files"])
        self.assertFalse(any(path.startswith("prospective/") for path in frozen_paths))
        self.assertIn("src/creative_corrigibility/measurement.py", frozen_paths)
        self.assertIn("tests/test_exhaustive_finite_validation.py", frozen_paths)
        self.assertIn(".github/workflows/ci.yml", frozen_paths)


if __name__ == "__main__":
    unittest.main()
