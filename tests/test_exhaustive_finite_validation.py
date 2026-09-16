import itertools
import unittest
from dataclasses import replace

from creative_corrigibility.engine import run
from creative_corrigibility.measurement import TraceValidationError, measure
from creative_corrigibility.model import CalibrationConfig, Event


class ExhaustiveFiniteValidationTests(unittest.TestCase):
    def test_complete_declared_semantic_cube_is_deterministic_and_typed(self):
        for access, standing, effect, delay_until in itertools.product(
            (False, True), (False, True), (False, True), (0, 4)
        ):
            config = CalibrationConfig(
                name=f"cube-{access}-{standing}-{effect}-{delay_until}",
                access_enabled=access,
                standing_enabled=standing,
                effect_enabled=effect,
                apply_delay_until=delay_until,
            )
            with self.subTest(config=config.name):
                trace_a = run(config)
                trace_b = run(config)
                self.assertEqual(trace_a.records, trace_b.records)
                measured = measure(trace_a)
                self.assertEqual(measured.access, access)
                if not access:
                    self.assertIsNone(measured.standing)
                    self.assertIsNone(measured.effect)
                    self.assertIsNone(measured.latency)
                elif not standing:
                    self.assertFalse(measured.standing)
                    self.assertIsNone(measured.effect)
                    self.assertIsNone(measured.latency)
                elif not effect:
                    self.assertTrue(measured.standing)
                    self.assertFalse(measured.effect)
                    self.assertIsNone(measured.latency)
                else:
                    self.assertTrue(measured.standing)
                    self.assertTrue(measured.effect)
                    self.assertIsNotNone(measured.latency)

    def test_measurer_rejects_event_label_that_lies_about_state_transition(self):
        trace = run(CalibrationConfig(name="control"))
        records = list(trace.records)
        send_index = next(i for i, r in enumerate(records) if r.event is Event.SEND_ACCEPTED)
        records[send_index] = replace(records[send_index], event=Event.SEND_REJECTED)
        lying_trace = replace(trace, records=tuple(records))
        with self.assertRaises(TraceValidationError):
            measure(lying_trace)


if __name__ == "__main__":
    unittest.main()
