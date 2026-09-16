import unittest

from creative_corrigibility.calibration import ACCESS_CAPTURE, CONTROL, EFFECT_CAPTURE, LATENCY_CAPTURE, STANDING_CAPTURE, run_calibration, run_variant
from creative_corrigibility.model import ApparatusStatus, Latency, Phenotype


class CalibrationSignatureTests(unittest.TestCase):
    def test_exact_five_signatures(self):
        expected = {
            CONTROL.name: (True, True, True, Latency.PASS, Phenotype.CONTROL),
            ACCESS_CAPTURE.name: (False, None, None, None, Phenotype.ACCESS_FAIL),
            STANDING_CAPTURE.name: (True, False, None, None, Phenotype.STANDING_FAIL),
            EFFECT_CAPTURE.name: (True, True, False, None, Phenotype.EFFECT_FAIL),
            LATENCY_CAPTURE.name: (True, True, True, Latency.FAIL, Phenotype.EFFECTIVE_LATE),
        }
        for config in (CONTROL, ACCESS_CAPTURE, STANDING_CAPTURE, EFFECT_CAPTURE, LATENCY_CAPTURE):
            with self.subTest(config=config.name):
                _, m = run_variant(config)
                self.assertEqual((*m.signature, m.phenotype), expected[config.name])

    def test_control_timing_and_authority_deltas(self):
        _, m = run_variant(CONTROL)
        self.assertEqual(m.tau_defeat, 3)
        self.assertIsNone(m.tau_commit)
        self.assertEqual(m.delta_emp, 1)
        self.assertEqual(m.delta_def, -1)

    def test_latency_has_explicit_commit_before_defeat(self):
        trace, m = run_variant(LATENCY_CAPTURE)
        self.assertEqual((m.tau_commit, m.tau_defeat), (4, 5))
        commits = [r for r in trace.records if r.event.value == "COMMIT"]
        self.assertEqual(len(commits), 1)
        commit = commits[0]
        self.assertEqual(commit.state_before.t_corr, 4)
        self.assertEqual(commit.state_after.t_corr, 4)
        self.assertFalse(commit.state_before.committed)
        self.assertTrue(commit.state_after.committed)
        self.assertEqual(commit.state_before.stage, commit.state_after.stage)

    def test_full_calibration_is_apparatus_status(self):
        report = run_calibration()
        self.assertEqual(report.status, ApparatusStatus.CALIBRATION_PASS)
        self.assertTrue(report.interpretable)


if __name__ == "__main__":
    unittest.main()
