from __future__ import annotations

from .engine import run
from .measurement import measure
from .model import (
    ApparatusStatus,
    CalibrationConfig,
    CalibrationReport,
    InterpretationStatus,
    Latency,
    Phenotype,
    SemanticFamily,
)

CONTROL = CalibrationConfig(name="CONTROL")
ACCESS_CAPTURE = CalibrationConfig(name="ACCESS_CAPTURE", access_enabled=False)
STANDING_CAPTURE = CalibrationConfig(name="STANDING_CAPTURE", standing_enabled=False)
EFFECT_CAPTURE = CalibrationConfig(name="EFFECT_CAPTURE", effect_enabled=False)
LATENCY_CAPTURE = CalibrationConfig(name="LATENCY_CAPTURE", apply_delay_until=4)

CALIBRATION_CONFIGS = (
    CONTROL,
    ACCESS_CAPTURE,
    STANDING_CAPTURE,
    EFFECT_CAPTURE,
    LATENCY_CAPTURE,
)


def semantic_diff(left: CalibrationConfig, right: CalibrationConfig) -> set[SemanticFamily]:
    diff: set[SemanticFamily] = set()
    if left.access_enabled != right.access_enabled:
        diff.add(SemanticFamily.ACCESS)
    if left.standing_enabled != right.standing_enabled:
        diff.add(SemanticFamily.STANDING)
    if left.effect_enabled != right.effect_enabled:
        diff.add(SemanticFamily.EFFECT)
    if left.apply_delay_until != right.apply_delay_until:
        diff.add(SemanticFamily.LATENCY)
    return diff


def run_variant(config: CalibrationConfig):
    trace = run(config)
    return trace, measure(trace)


_EXPECTED = {
    "CONTROL": ((True, True, True, Latency.PASS), Phenotype.CONTROL, 3, None, 1, -1),
    "ACCESS_CAPTURE": ((False, None, None, None), Phenotype.ACCESS_FAIL, None, None, 1, 0),
    "STANDING_CAPTURE": ((True, False, None, None), Phenotype.STANDING_FAIL, None, None, 1, 0),
    "EFFECT_CAPTURE": ((True, True, False, None), Phenotype.EFFECT_FAIL, None, None, 1, 0),
    "LATENCY_CAPTURE": ((True, True, True, Latency.FAIL), Phenotype.EFFECTIVE_LATE, 5, 4, 1, -1),
}


def run_calibration() -> CalibrationReport:
    measurements = {}
    try:
        for config in CALIBRATION_CONFIGS:
            if config is not CONTROL and len(semantic_diff(config, CONTROL)) != 1:
                raise ValueError(f"semantic isolation failed for {config.name}")

            _, measured = run_variant(config)
            measurements[config.name] = measured
            observed = (
                measured.signature,
                measured.phenotype,
                measured.tau_defeat,
                measured.tau_commit,
                measured.delta_emp,
                measured.delta_def,
            )
            if observed != _EXPECTED[config.name]:
                raise ValueError(f"calibration signature mismatch for {config.name}")
    except Exception:
        return CalibrationReport(
            status=ApparatusStatus.CALIBRATION_FAIL,
            interpretation_status=InterpretationStatus.UNSCORED,
            measurements=measurements,
        )

    return CalibrationReport(
        status=ApparatusStatus.CALIBRATION_PASS,
        interpretation_status=InterpretationStatus.ELIGIBLE,
        measurements=measurements,
    )
