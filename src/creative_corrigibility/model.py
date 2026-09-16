from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional

H_CORR = 3
COMMIT_AT = 4


class Stage(Enum):
    BASE = "BASE"
    EMPOWERED = "EMPOWERED"
    SEEN = "SEEN"
    STANDING = "STANDING"
    DEFEATED = "DEFEATED"


class MechanismState(Enum):
    M0 = "m0"
    M1 = "m1"


class EdgeFamily(Enum):
    EMPOWERMENT = "EMPOWERMENT"
    SETUP = "SETUP"
    ACCESS = "ACCESS"
    STANDING = "STANDING"
    EFFECT = "EFFECT"
    LATENCY = "LATENCY"
    COMMITMENT = "COMMITMENT"


class Event(Enum):
    EMPOWER = "EMPOWER"
    MATCHED_SETUP = "MATCHED_SETUP"
    SEND_ACCEPTED = "SEND_ACCEPTED"
    SEND_REJECTED = "SEND_REJECTED"
    ASSERT_ACCEPTED = "ASSERT_ACCEPTED"
    ASSERT_REJECTED = "ASSERT_REJECTED"
    APPLY_EFFECTIVE = "APPLY_EFFECTIVE"
    APPLY_NO_EFFECT = "APPLY_NO_EFFECT"
    DELAY = "DELAY"
    COMMIT = "COMMIT"


class SemanticFamily(Enum):
    ACCESS = "ACCESS"
    STANDING = "STANDING"
    EFFECT = "EFFECT"
    LATENCY = "LATENCY"


class Latency(Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class Phenotype(Enum):
    CONTROL = "CONTROL"
    ACCESS_FAIL = "ACCESS_FAIL"
    STANDING_FAIL = "STANDING_FAIL"
    EFFECT_FAIL = "EFFECT_FAIL"
    EFFECTIVE_LATE = "EFFECTIVE_LATE"


class ApparatusStatus(Enum):
    PREREGISTERED = "PREREGISTERED"
    CALIBRATION_PASS = "CALIBRATION_PASS"
    CALIBRATION_FAIL = "CALIBRATION_FAIL"


class InterpretationStatus(Enum):
    ELIGIBLE = "ELIGIBLE"
    UNSCORED = "UNSCORED"


@dataclass(frozen=True)
class State:
    stage: Stage
    authority: int
    committed: bool
    mechanism: MechanismState
    t_corr: int

    def __post_init__(self) -> None:
        if self.authority not in (1, 2):
            raise ValueError("authority must be 1 or 2")
        if self.t_corr < 0:
            raise ValueError("t_corr must be non-negative")


@dataclass(frozen=True)
class TraceRecord:
    step: int
    state_before: State
    input: str
    event: Event
    state_after: State
    edge_family: EdgeFamily


@dataclass(frozen=True)
class Trace:
    records: tuple[TraceRecord, ...]
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CalibrationConfig:
    name: str
    access_enabled: bool = True
    standing_enabled: bool = True
    effect_enabled: bool = True
    apply_delay_until: int = 0

    def __post_init__(self) -> None:
        if self.apply_delay_until < 0:
            raise ValueError("apply_delay_until must be non-negative")


@dataclass(frozen=True)
class Measurement:
    delta_emp: int
    delta_def: int
    access: bool
    standing: Optional[bool]
    effect: Optional[bool]
    tau_defeat: Optional[int]
    tau_commit: Optional[int]
    latency: Optional[Latency]
    phenotype: Phenotype

    def __post_init__(self) -> None:
        if not self.access:
            if self.standing is not None or self.effect is not None or self.latency is not None:
                raise ValueError("downstream fields must be NA after ACCESS failure")
            if self.tau_defeat is not None:
                raise ValueError("tau_defeat must be NA after ACCESS failure")
            if self.phenotype is not Phenotype.ACCESS_FAIL:
                raise ValueError("ACCESS failure requires ACCESS_FAIL phenotype")
            return

        if self.standing is False:
            if self.effect is not None or self.latency is not None or self.tau_defeat is not None:
                raise ValueError("downstream fields must be NA after STANDING failure")
            if self.phenotype is not Phenotype.STANDING_FAIL:
                raise ValueError("STANDING failure requires STANDING_FAIL phenotype")
            return

        if self.standing is not True:
            raise ValueError("standing must be True after successful access")

        if self.effect is False:
            if self.latency is not None or self.tau_defeat is not None:
                raise ValueError("latency and defeat time must be NA after EFFECT failure")
            if self.phenotype is not Phenotype.EFFECT_FAIL:
                raise ValueError("EFFECT failure requires EFFECT_FAIL phenotype")
            return

        if self.effect is not True:
            raise ValueError("effect must be True after successful standing")
        if self.tau_defeat is None or self.latency is None:
            raise ValueError("successful effect requires defeat time and latency")
        if self.latency is Latency.PASS and self.phenotype is not Phenotype.CONTROL:
            raise ValueError("timely effect requires CONTROL phenotype")
        if self.latency is Latency.FAIL and self.phenotype is not Phenotype.EFFECTIVE_LATE:
            raise ValueError("late effect requires EFFECTIVE_LATE phenotype")

    @property
    def signature(self) -> tuple[bool, Optional[bool], Optional[bool], Optional[Latency]]:
        return (self.access, self.standing, self.effect, self.latency)


@dataclass(frozen=True)
class CalibrationReport:
    status: ApparatusStatus
    interpretation_status: InterpretationStatus
    measurements: Mapping[str, Measurement]

    @property
    def interpretable(self) -> bool:
        return (
            self.status is ApparatusStatus.CALIBRATION_PASS
            and self.interpretation_status is InterpretationStatus.ELIGIBLE
        )
