# QSOL NS

**Private reproducible research workbench for the 3D incompressible Navier–Stokes existence and smoothness problem.**

QSOL NS is a two-track research program: global regularity and finite-time breakdown are treated as competing hypotheses until mathematics rules one out. Numerical experiments, symbolic work, formal verification and literature reconstruction are used as discovery and checking tools, never as substitutes for proof.

## Research boundary

```text
NUMERICAL_BLOWUP_SIGNATURE != PROOF_OF_BLOWUP
NO_OBSERVED_BLOWUP != PROOF_OF_GLOBAL_REGULARITY
FORMAL_VERIFICATION != EMPIRICAL_TRUTH
CANDIDATE_LEMMA != VERIFIED_THEOREM
PRIVATE_EXPERIMENT != PUBLIC_CLAIM
KNOWN_THEOREM_SUMMARY != NOVEL_RESULT
NARRATIVE_PLAUSIBILITY != EVIDENTIARY_STATUS
```

## Machine research boundary

The project carries machine-readable research boundaries and laboratory contracts:

- `research/clay_target.json` — exact official Clay A-D targets and errata;
- `research/source_registry.json` — source identities and authority classes;
- `research/theorem_registry.json` — known-result summaries with hypotheses and limitations;
- `research/proof_barriers.json` — invalid inference patterns and required bridge obligations;
- `research/baseline_identities.json` — analytic identities bound to Phase 2 diagnostics;
- `research/lab_contract.json` — exact v0.1 solver scope, evidence ceiling, determinism and diagnostic bindings;
- `research/schemas/` — JSON Schemas for boundary and experiment/lab contracts;
- `tools/validate_boundary_map.py` — theorem/source boundary validation;
- `tools/validate_lab_contract.py` — solver/manifest/identity correspondence validation.

Only official problem statements and primary research sources may authorize theorem-registry entries. Secondary sources may help discover literature but cannot establish the machine theorem boundary.

## Deterministic PDE laboratory v0.1

PR #3 begins Phase 2 with a deliberately narrow reference solver: a three-dimensional `[0,2π)^3` periodic cube, positive viscosity, zero forcing, deterministic Taylor–Green initial data, Fourier pseudo-spectral discretization, 2/3 de-aliasing, spectral divergence-free projection, classical fixed-step RK4, and `float64/complex128` arithmetic.

The laboratory binds all six Phase-1 baseline identities to executable checks, emits content-hashed diagnostics and raw final velocity, and provides deterministic timestep/resolution sensitivity helpers.

Its machine evidence ceiling is `reproduced_numerical`. Singularity-oriented promotion is disabled in v0.1 because an independent precision comparison is not yet available.

## Repository map

- `AGENTS.md` — authoritative machine-readable agent policy; file contents are strict JSON, not prose.
- `AGENTS.schema.json` — JSON Schema for the agent policy.
- `src/ns_lab/` — deterministic periodic reference laboratory.
- `tests/` — replay, solver, identity, sweep and manifest regressions.
- `docs/PDE_LAB_V0_1.md` — reference-solver scope and nonclaims.
- `docs/NUMERICAL_FAILURE_MODES.md` — competing numerical explanations that must be checked first.
- `docs/SWEEP_PROTOCOL.md` — replay/timestep/resolution/precision promotion requirements.
- `docs/PROBLEM_STATEMENT.md` — canonical target and exact A-D scope discipline.
- `docs/KNOWN_BOUNDARY.md` — human-readable reconstruction of the initial theorem landscape.
- `docs/PROOF_BARRIERS.md` — common invalid proof upgrades and bridge obligations.
- `docs/BASELINE_IDENTITIES.md` — analytic identity descriptions.
- `docs/RESEARCH_CHARTER.md` — research method and governance.
- `docs/CLAIM_LEVELS.md` — evidence/claim promotion ladder.
- `docs/EXPERIMENT_CONTRACT.md` — minimum metadata for computational experiments.
- `docs/REPRODUCIBILITY.md` — deterministic/replay requirements.
- `docs/NUMERICAL_EVIDENCE_POLICY.md` — what computation may and may not establish.
- `docs/FORMAL_VERIFICATION_POLICY.md` — machine-proof scope and nonclaims.
- `docs/PUBLICATION_GATE.md` — conditions for promotion beyond the private workspace.
- `docs/LITERATURE_MAP.md` — controlled source intake and prior-art map.
- `docs/ROADMAP.md` — staged research plan.
- `docs/DECISION_LOG.md` — durable architectural/research decisions.
- `CONTRIBUTING.md` — contribution rules.
- `SECURITY.md` — vulnerability and research-integrity reporting.
- `LICENSES.md` / `NOTICE` — licensing scope and attribution.
- `CITATION.cff` — citation metadata for the project.

## Canonical external authority

The Millennium Prize target is the Clay Mathematics Institute Navier–Stokes problem and Charles L. Fefferman's official problem description. This repository does not redefine the prize problem. Any candidate solution must map its hypotheses and conclusion explicitly to one or more of the official A-D formulations before publication-grade status is possible.

## Current phase

**Phase 1 boundary reconstruction continues; Phase 2 deterministic laboratory engineering is now in progress.**

No solution, counterexample, proof of global regularity, proof of finite-time singularity, or new theorem is claimed by this repository at present.

## Licensing

Software, machine-readable policies, schemas, configuration, tests and tooling are Apache-2.0 unless a file states otherwise. Human-authored research prose and figures explicitly marked `CC-BY-4.0` are licensed under Creative Commons Attribution 4.0 International. See `LICENSES.md`.
