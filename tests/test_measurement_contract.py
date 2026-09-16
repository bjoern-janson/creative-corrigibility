import copy
import unittest
from dataclasses import replace

from creative_corrigibility.calibration import ACCESS_CAPTURE, CONTROL, STANDING_CAPTURE, run_variant
from creative_corrigibility.measurement import TraceValidationError, measure
from creative_corrigibility.model import Latency, Measurement, Phenotype


class MeasurementContractTests(unittest.TestCase):
    def test_upstream_access_failure_forces_downstream_na(self):
        _, m = run_variant(ACCESS_CAPTURE)
        self.assertEqual(m.signature, (False, None, None, None))

    def test_standing_failure_forces_effect_and_latency_na(self):
        _, m = run_variant(STANDING_CAPTURE)
        self.assertEqual(m.signature, (True, False, None, None))

    def test_invalid_causal_measurement_is_rejected(self):
        with self.assertRaises(ValueError):
            Measurement(
                delta_emp=1,
                delta_def=-1,
                access=False,
                standing=True,
                effect=True,
                tau_defeat=3,
                tau_commit=None,
                latency=Latency.PASS,
                phenotype=Phenotype.CONTROL,
            )

    def test_metadata_relabeling_does_not_change_measurement(self):
        trace, original = run_variant(CONTROL)
        relabeled = replace(trace, metadata={"variant": "AMAZING_RESULT", "expected": "ACCESS_FAIL"})
        self.assertEqual(measure(relabeled), original)

    def test_copy_does_not_change_measurement(self):
        trace, original = run_variant(CONTROL)
        self.assertEqual(measure(copy.deepcopy(trace)), original)

    def test_discontinuous_trace_is_rejected(self):
        trace, _ = run_variant(CONTROL)
        records = list(trace.records)
        records[1] = replace(records[1], state_before=records[0].state_before)
        bad = replace(trace, records=tuple(records))
        with self.assertRaises(TraceValidationError):
            measure(bad)


if __name__ == "__main__":
    unittest.main()
