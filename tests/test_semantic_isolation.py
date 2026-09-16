import unittest

from creative_corrigibility.calibration import ACCESS_CAPTURE, CONTROL, EFFECT_CAPTURE, LATENCY_CAPTURE, STANDING_CAPTURE, semantic_diff
from creative_corrigibility.model import SemanticFamily


class SemanticIsolationTests(unittest.TestCase):
    def test_each_mutant_changes_exactly_one_family(self):
        expected = {
            ACCESS_CAPTURE.name: {SemanticFamily.ACCESS},
            STANDING_CAPTURE.name: {SemanticFamily.STANDING},
            EFFECT_CAPTURE.name: {SemanticFamily.EFFECT},
            LATENCY_CAPTURE.name: {SemanticFamily.LATENCY},
        }
        for config in (ACCESS_CAPTURE, STANDING_CAPTURE, EFFECT_CAPTURE, LATENCY_CAPTURE):
            with self.subTest(config=config.name):
                self.assertEqual(semantic_diff(config, CONTROL), expected[config.name])
                self.assertEqual(len(semantic_diff(config, CONTROL)), 1)

    def test_control_has_no_semantic_diff_from_itself(self):
        self.assertEqual(semantic_diff(CONTROL, CONTROL), set())


if __name__ == "__main__":
    unittest.main()
