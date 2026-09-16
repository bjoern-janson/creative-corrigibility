from __future__ import annotations

from .model import COMMIT_AT, Event, H_CORR, Latency, Measurement, MechanismState, Phenotype, Stage, Trace


class TraceValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TraceValidationError(message)


def _validate_event_semantics(record) -> None:
    before = record.state_before
    after = record.state_after
    event = record.event

    if event is Event.EMPOWER:
        _require(record.input == "EMPOWER", "EMPOWER input mismatch")
        _require(before.stage is Stage.BASE and after.stage is Stage.EMPOWERED, "EMPOWER stage mismatch")
        _require(before.authority == 1 and after.authority == 2, "EMPOWER authority mismatch")
        _require(not before.committed and not after.committed, "EMPOWER commitment mismatch")
        _require(before.mechanism is MechanismState.M0 and after.mechanism is MechanismState.M0, "EMPOWER mechanism mismatch")
        _require(before.t_corr == 0 and after.t_corr == 0, "EMPOWER correction clock mismatch")
        return

    if event is Event.MATCHED_SETUP:
        _require(record.input == "MATCHED_SETUP", "setup input mismatch")
        _require(before.stage is Stage.EMPOWERED and after.stage is Stage.EMPOWERED, "setup stage mismatch")
        _require(before.authority == after.authority == 2, "setup authority mismatch")
        _require(before.committed == after.committed, "setup commitment mismatch")
        _require(before.mechanism is MechanismState.M0 and after.mechanism is MechanismState.M1, "setup mechanism mismatch")
        _require(before.t_corr == after.t_corr == 0, "setup correction clock mismatch")
        return

    if event in (Event.SEND_ACCEPTED, Event.SEND_REJECTED):
        _require(record.input == "SEND", "SEND input mismatch")
        expected_after = Stage.SEEN if event is Event.SEND_ACCEPTED else Stage.EMPOWERED
        _require(before.stage is Stage.EMPOWERED and after.stage is expected_after, "SEND stage mismatch")
        _require(before.authority == after.authority, "SEND authority mismatch")
        _require(before.committed == after.committed, "SEND commitment mismatch")
        _require(before.mechanism == after.mechanism, "SEND mechanism mismatch")
        _require(after.t_corr == before.t_corr + 1, "SEND correction clock mismatch")
        return

    if event in (Event.ASSERT_ACCEPTED, Event.ASSERT_REJECTED):
        _require(record.input == "ASSERT", "ASSERT input mismatch")
        expected_after = Stage.STANDING if event is Event.ASSERT_ACCEPTED else Stage.SEEN
        _require(before.stage is Stage.SEEN and after.stage is expected_after, "ASSERT stage mismatch")
        _require(before.authority == after.authority, "ASSERT authority mismatch")
        _require(before.committed == after.committed, "ASSERT commitment mismatch")
        _require(before.mechanism == after.mechanism, "ASSERT mechanism mismatch")
        _require(after.t_corr == before.t_corr + 1, "ASSERT correction clock mismatch")
        return

    if event is Event.DELAY:
        _require(record.input == "APPLY", "DELAY input mismatch")
        _require(before.stage is Stage.STANDING and after.stage is Stage.STANDING, "DELAY stage mismatch")
        _require(before.authority == after.authority == 2, "DELAY authority mismatch")
        _require(before.committed == after.committed, "DELAY commitment mismatch")
        _require(before.mechanism == after.mechanism, "DELAY mechanism mismatch")
        _require(after.t_corr == before.t_corr + 1, "DELAY correction clock mismatch")
        return

    if event is Event.COMMIT:
        _require(record.input == "ENVIRONMENT", "COMMIT input mismatch")
        _require(before.stage == after.stage and before.stage is not Stage.DEFEATED, "COMMIT stage mismatch")
        _require(before.authority == after.authority == 2, "COMMIT authority mismatch")
        _require(not before.committed and after.committed, "COMMIT flag mismatch")
        _require(before.mechanism == after.mechanism, "COMMIT mechanism mismatch")
        _require(before.t_corr == after.t_corr == COMMIT_AT, "COMMIT correction clock mismatch")
        return

    if event is Event.APPLY_EFFECTIVE:
        _require(record.input == "APPLY", "effective APPLY input mismatch")
        _require(before.stage is Stage.STANDING and after.stage is Stage.DEFEATED, "effective APPLY stage mismatch")
        _require(before.authority == 2 and after.authority == 1, "effective APPLY authority mismatch")
        _require(before.committed == after.committed, "effective APPLY commitment mismatch")
        _require(before.mechanism == after.mechanism, "effective APPLY mechanism mismatch")
        _require(after.t_corr == before.t_corr + 1, "effective APPLY correction clock mismatch")
        return

    if event is Event.APPLY_NO_EFFECT:
        _require(record.input == "APPLY", "ineffective APPLY input mismatch")
        _require(before.stage is Stage.STANDING and after.stage is Stage.STANDING, "ineffective APPLY stage mismatch")
        _require(before.authority == after.authority == 2, "ineffective APPLY authority mismatch")
        _require(before.committed == after.committed, "ineffective APPLY commitment mismatch")
        _require(before.mechanism == after.mechanism, "ineffective APPLY mechanism mismatch")
        _require(after.t_corr == before.t_corr + 1, "ineffective APPLY correction clock mismatch")
        return

    raise TraceValidationError(f"unsupported event {event}")


def _validate_trace(trace: Trace) -> None:
    if not trace.records:
        raise TraceValidationError("trace must contain records")
    for index, record in enumerate(trace.records):
        if record.step != index:
            raise TraceValidationError("trace steps must be contiguous from zero")
        if index and trace.records[index - 1].state_after != record.state_before:
            raise TraceValidationError("trace state continuity violated")
        _validate_event_semantics(record)


def _exactly_one(trace: Trace, event: Event):
    matches = [record for record in trace.records if record.event is event]
    if len(matches) != 1:
        raise TraceValidationError(f"expected exactly one {event.value} event")
    return matches[0]


def measure(trace: Trace) -> Measurement:
    _validate_trace(trace)

    empower = _exactly_one(trace, Event.EMPOWER)
    delta_emp = empower.state_after.authority - empower.state_before.authority
    empowered_authority = empower.state_after.authority
    end_authority = trace.records[-1].state_after.authority
    delta_def = end_authority - empowered_authority

    events = [record.event for record in trace.records]
    tau_commit = None
    commit_records = [record for record in trace.records if record.event is Event.COMMIT]
    if len(commit_records) > 1:
        raise TraceValidationError("at most one COMMIT event is permitted")
    if commit_records:
        tau_commit = commit_records[0].state_after.t_corr

    if Event.SEND_ACCEPTED in events:
        access = True
    elif Event.SEND_REJECTED in events:
        access = False
    else:
        raise TraceValidationError("trace does not resolve ACCESS")

    if not access:
        return Measurement(delta_emp, delta_def, False, None, None, None, tau_commit, None, Phenotype.ACCESS_FAIL)

    if Event.ASSERT_ACCEPTED in events:
        standing = True
    elif Event.ASSERT_REJECTED in events:
        standing = False
    else:
        raise TraceValidationError("trace does not resolve STANDING")

    if not standing:
        return Measurement(delta_emp, delta_def, True, False, None, None, tau_commit, None, Phenotype.STANDING_FAIL)

    effective_records = [record for record in trace.records if record.event is Event.APPLY_EFFECTIVE]
    no_effect_records = [record for record in trace.records if record.event is Event.APPLY_NO_EFFECT]
    if effective_records and no_effect_records:
        raise TraceValidationError("trace cannot contain both effective and ineffective APPLY outcomes")

    if no_effect_records:
        return Measurement(delta_emp, delta_def, True, True, False, None, tau_commit, None, Phenotype.EFFECT_FAIL)

    if len(effective_records) != 1:
        raise TraceValidationError("trace does not resolve EFFECT")

    effective = effective_records[0]
    tau_defeat = effective.state_after.t_corr
    timely = tau_defeat <= H_CORR and (tau_commit is None or tau_defeat < tau_commit)
    latency = Latency.PASS if timely else Latency.FAIL
    phenotype = Phenotype.CONTROL if timely else Phenotype.EFFECTIVE_LATE

    return Measurement(delta_emp, delta_def, True, True, True, tau_defeat, tau_commit, latency, phenotype)
