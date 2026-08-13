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
```

## Repository map

- `AGENTS.md` — authoritative machine-readable agent policy; file contents are strict JSON, not prose.
- `AGENTS.schema.json` — JSON Schema for the agent policy.
- `docs/PROBLEM_STATEMENT.md` — canonical target and scope discipline.
- `docs/RESEARCH_CHARTER.md` — research method and governance.
- `docs/CLAIM_LEVELS.md` — evidence/claim promotion ladder.
- `docs/EXPERIMENT_CONTRACT.md` — minimum metadata for computational experiments.
- `docs/REPRODUCIBILITY.md` — deterministic/replay requirements.
- `docs/NUMERICAL_EVIDENCE_POLICY.md` — what computation may and may not establish.
- `docs/FORMAL_VERIFICATION_POLICY.md` — machine-proof scope and nonclaims.
- `docs/PUBLICATION_GATE.md` — conditions for promotion beyond the private workspace.
- `docs/LITERATURE_MAP.md` — controlled literature intake and prior-art map.
- `docs/ROADMAP.md` — staged research plan.
- `docs/DECISION_LOG.md` — durable architectural/research decisions.
- `CONTRIBUTING.md` — contribution rules.
- `SECURITY.md` — vulnerability and research-integrity reporting.
- `LICENSES.md` / `NOTICE` — licensing scope and attribution.
- `CITATION.cff` — citation metadata for the project.

## Canonical external authority

The Millennium Prize target is the Clay Mathematics Institute Navier–Stokes problem and Charles L. Fefferman's official problem description. This repository does not redefine the prize problem. Any candidate solution must map its hypotheses and conclusion explicitly to an allowed official formulation before publication-grade status is possible.

## Current status

**Private exploratory research.** No solution, counterexample, proof of global regularity, proof of finite-time singularity, or new theorem is claimed by this repository at present.

## Licensing

Software, machine-readable policies, schemas, configuration, tests and tooling are Apache-2.0 unless a file states otherwise. Human-authored research prose and figures explicitly marked `CC-BY-4.0` are licensed under Creative Commons Attribution 4.0 International. See `LICENSES.md`.
