from __future__ import annotations

from .model import Event, H_CORR, Latency, Measurement, Phenotype, Trace


class TraceValidationError(ValueError):
    pass


def _validate_trace(trace: Trace) -> None:
    if not trace.records:
        raise TraceValidationError("trace must contain records")
    for index, record in enumerate(trace.records):
        if record.step != index:
            raise TraceValidationError("trace steps must be contiguous from zero")
        if index and trace.records[index - 1].state_after != record.state_before:
            raise TraceValidationError("trace state continuity violated")


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
        return Measurement(
            delta_emp=delta_emp,
            delta_def=delta_def,
            access=False,
            standing=None,
            effect=None,
            tau_defeat=None,
            tau_commit=tau_commit,
            latency=None,
            phenotype=Phenotype.ACCESS_FAIL,
        )

    if Event.ASSERT_ACCEPTED in events:
        standing = True
    elif Event.ASSERT_REJECTED in events:
        standing = False
    else:
        raise TraceValidationError("trace does not resolve STANDING")

    if not standing:
        return Measurement(
            delta_emp=delta_emp,
            delta_def=delta_def,
            access=True,
            standing=False,
            effect=None,
            tau_defeat=None,
            tau_commit=tau_commit,
            latency=None,
            phenotype=Phenotype.STANDING_FAIL,
        )

    effective_records = [record for record in trace.records if record.event is Event.APPLY_EFFECTIVE]
    no_effect_records = [record for record in trace.records if record.event is Event.APPLY_NO_EFFECT]
    if effective_records and no_effect_records:
        raise TraceValidationError("trace cannot contain both effective and ineffective APPLY outcomes")

    if no_effect_records:
        return Measurement(
            delta_emp=delta_emp,
            delta_def=delta_def,
            access=True,
            standing=True,
            effect=False,
            tau_defeat=None,
            tau_commit=tau_commit,
            latency=None,
            phenotype=Phenotype.EFFECT_FAIL,
        )

    if len(effective_records) != 1:
        raise TraceValidationError("trace does not resolve EFFECT")

    effective = effective_records[0]
    if not (
        effective.state_before.authority == 2
        and effective.state_after.authority == 1
    ):
        raise TraceValidationError("APPLY_EFFECTIVE must causally reduce authority 2 -> 1")

    tau_defeat = effective.state_after.t_corr
    timely = tau_defeat <= H_CORR and (
        tau_commit is None or tau_defeat < tau_commit
    )
    latency = Latency.PASS if timely else Latency.FAIL
    phenotype = Phenotype.CONTROL if timely else Phenotype.EFFECTIVE_LATE

    return Measurement(
        delta_emp=delta_emp,
        delta_def=delta_def,
        access=True,
        standing=True,
        effect=True,
        tau_defeat=tau_defeat,
        tau_commit=tau_commit,
        latency=latency,
        phenotype=phenotype,
    )
