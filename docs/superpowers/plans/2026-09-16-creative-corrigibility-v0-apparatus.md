# Creative Corrigibility v0 Apparatus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the finite v0 calibration apparatus whose engine emits raw traces and whose frozen measurer derives typed answerability phenotypes without access to experimental intent.

**Architecture:** Standard-library Python package with immutable finite-state records, a deterministic reference interpreter, a trace-only measurement module, five semantic calibration configurations, and exhaustive apparatus tests. Calibration and prospective science remain separate; no substantive adaptive mechanism is implemented in this plan.

**Tech Stack:** Python 3.12+, `dataclasses`, `enum`, `typing`, `unittest`, GitHub Actions.

**Spec:** `docs/preregistration/CREATIVE_CORRIGIBILITY_V0.md`

## Global Constraints
- Implementation may expose inconsistency; it may not manufacture refinement.
- `Delta_emp A(T)=+1` in every calibration arm.
- Correction clock begins only after matched setup.
- `H_corr=3`; explicit commitment boundary `t_corr=4`.
- Engine writes states/events only, never phenotype labels.
- Measurement consumes trace records only and has no runtime dependency on calibration identity or prospective mechanism code.
- Upstream causal failure forces downstream fields to `NA`.
- Any calibration mismatch yields `UNSCORED` and forbids scientific interpretation.
- No prospective scientific result is produced by this plan.

## File map
- `src/creative_corrigibility/model.py`: finite records, enums, configs, typed outputs.
- `src/creative_corrigibility/engine.py`: deterministic interpreter and correction policy.
- `src/creative_corrigibility/measurement.py`: trace validator and frozen `measure(trace)`.
- `src/creative_corrigibility/calibration.py`: five configs, semantic diff, execution helper, gate.
- `tests/test_calibration_signatures.py`: exact five signatures and timing facts.
- `tests/test_measurement_contract.py`: NA semantics, metadata/copy invariance, malformed trace rejection.
- `tests/test_semantic_isolation.py`: one-family mutation and unaffected-rule identity.
- `tests/test_architecture.py`: dependency boundary and status/classification separation.
- `.github/workflows/ci.yml`: deterministic test gate.

## Task 1 — RED apparatus tests
- [ ] Add all four test modules before production code.
- [ ] Add CI using `PYTHONPATH=src python -m unittest discover -s tests -v`.
- [ ] Push and verify the tests fail because the production package is absent.
- [ ] Preserve this RED commit as provenance.

## Task 2 — Finite model
- [ ] Implement immutable `State`, `TraceRecord`, `Trace`, `CalibrationConfig`, measurement/result types and enums.
- [ ] Keep apparatus status and scientific phenotype as distinct types.
- [ ] Freeze `H_CORR=3` and `COMMIT_AT=4`.

## Task 3 — Reference interpreter
- [ ] Implement `BASE -> EMPOWERED` with authority `1 -> 2`.
- [ ] Implement matched setup with no correction-clock advance.
- [ ] Implement low-level SEND, ASSERT, APPLY, DELAY, and explicit COMMIT events.
- [ ] Ensure CONTROL defeats at `t_corr=3` and LATENCY commits at 4 then defeats at 5.
- [ ] Do not import measurement or scientific classification types.

## Task 4 — Frozen measurer
- [ ] Validate trace continuity.
- [ ] Derive ACCESS from successful SEND, STANDING from successful ASSERT, EFFECT from authority-reducing APPLY.
- [ ] Enforce typed downstream `NA` semantics.
- [ ] Derive latency only after effect, using `H_CORR` and explicit COMMIT time.
- [ ] Ignore metadata in classification.

## Task 5 — Calibration gate
- [ ] Encode CONTROL plus four exactly one-family mutants.
- [ ] Machine-check semantic diffs and unaffected-rule identity.
- [ ] Compare observed signatures against the preregistered dictionary.
- [ ] Return `CALIBRATION_FAIL` / `UNSCORED` on any mismatch.

## Task 6 — Close apparatus
- [ ] Run the complete test suite on Python 3.12.
- [ ] Verify copied/relabelled traces measure identically.
- [ ] Verify `measurement.py` has no calibration/prospective runtime dependency.
- [ ] Verify all five signatures and semantic-isolation controls.
- [ ] Record the green commit SHA and CI evidence.
- [ ] Stop: no substantive adaptive mechanism or prospective scientific claim.
