from __future__ import annotations

from dataclasses import replace

from .model import (
    COMMIT_AT,
    CalibrationConfig,
    EdgeFamily,
    Event,
    MechanismState,
    Stage,
    State,
    Trace,
    TraceRecord,
)


def correction_action(stage: Stage) -> str:
    if stage is Stage.EMPOWERED:
        return "SEND"
    if stage is Stage.SEEN:
        return "ASSERT"
    if stage is Stage.STANDING:
        return "APPLY"
    return "NOOP"


def run(config: CalibrationConfig) -> Trace:
    records: list[TraceRecord] = []
    step = 0
    state = State(Stage.BASE, 1, False, MechanismState.M0, 0)

    def emit(input_name: str, event: Event, after: State, family: EdgeFamily) -> None:
        nonlocal state, step
        records.append(
            TraceRecord(
                step=step,
                state_before=state,
                input=input_name,
                event=event,
                state_after=after,
                edge_family=family,
            )
        )
        state = after
        step += 1

    emit(
        "EMPOWER",
        Event.EMPOWER,
        State(Stage.EMPOWERED, 2, False, MechanismState.M0, 0),
        EdgeFamily.EMPOWERMENT,
    )
    emit(
        "MATCHED_SETUP",
        Event.MATCHED_SETUP,
        replace(state, mechanism=MechanismState.M1),
        EdgeFamily.SETUP,
    )

    for _ in range(32):
        if (
            state.t_corr == COMMIT_AT
            and state.authority == 2
            and not state.committed
            and state.stage is not Stage.DEFEATED
        ):
            emit(
                "ENVIRONMENT",
                Event.COMMIT,
                replace(state, committed=True),
                EdgeFamily.COMMITMENT,
            )
            continue

        action = correction_action(state.stage)
        if action == "SEND":
            if config.access_enabled:
                after = replace(state, stage=Stage.SEEN, t_corr=state.t_corr + 1)
                emit("SEND", Event.SEND_ACCEPTED, after, EdgeFamily.ACCESS)
            else:
                after = replace(state, t_corr=state.t_corr + 1)
                emit("SEND", Event.SEND_REJECTED, after, EdgeFamily.ACCESS)
                break
            continue

        if action == "ASSERT":
            if config.standing_enabled:
                after = replace(state, stage=Stage.STANDING, t_corr=state.t_corr + 1)
                emit("ASSERT", Event.ASSERT_ACCEPTED, after, EdgeFamily.STANDING)
            else:
                after = replace(state, t_corr=state.t_corr + 1)
                emit("ASSERT", Event.ASSERT_REJECTED, after, EdgeFamily.STANDING)
                break
            continue

        if action == "APPLY":
            if state.t_corr < config.apply_delay_until:
                after = replace(state, t_corr=state.t_corr + 1)
                emit("APPLY", Event.DELAY, after, EdgeFamily.LATENCY)
                continue

            if config.effect_enabled:
                after = replace(
                    state,
                    stage=Stage.DEFEATED,
                    authority=1,
                    t_corr=state.t_corr + 1,
                )
                emit("APPLY", Event.APPLY_EFFECTIVE, after, EdgeFamily.EFFECT)
            else:
                after = replace(state, t_corr=state.t_corr + 1)
                emit("APPLY", Event.APPLY_NO_EFFECT, after, EdgeFamily.EFFECT)
            break

        break
    else:
        raise RuntimeError("finite interpreter exceeded execution bound")

    return Trace(records=tuple(records), metadata={"variant": config.name})
