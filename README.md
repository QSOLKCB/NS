# QSOL NS

**Private reproducible research workbench for the 3D incompressible Navier-Stokes existence and smoothness problem.**

QSOL NS is a two-track research program: global regularity and finite-time breakdown are treated as competing hypotheses until mathematics rules one out. Numerical experiments, symbolic work, formal verification and literature reconstruction are used as discovery and checking tools, never as substitutes for proof.

## Research boundary

```text
NUMERICAL_BLOWUP_SIGNATURE != PROOF_OF_BLOWUP
NO_OBSERVED_BLOWUP != PROOF_OF_GLOBAL_REGULARITY
FORMAL_VERIFICATION != EMPIRICAL_TRUTH
CANDIDATE_LEMMA != VERIFIED_THEOREM
PRIVATE_EXPERIMENT != PUBLIC_CLAIM
KNOWN_THEOREM_SUMMARY != NOVEL_RESULT
```

## Machine research boundary

The project now carries a machine-readable Phase 1 boundary map:

- `research/clay_target.json` — exact official Clay A-D targets and errata;
- `research/source_registry.json` — source identities and authority classes;
- `research/theorem_registry.json` — known-result summaries with hypotheses and limitations;
- `research/proof_barriers.json` — invalid inference patterns and required bridge obligations;
- `research/baseline_identities.json` — analytic identities for future solver diagnostics;
- `research/schemas/` — JSON Schemas for all boundary registries;
- `tools/validate_boundary_map.py` — schema, reference-integrity and hostile-mutation validator.

Only official problem statements and primary research sources may authorize theorem-registry entries. Secondary sources may help discover literature but cannot establish the machine theorem boundary.

## Repository map

- `AGENTS.md` — authoritative machine-readable agent policy; file contents are strict JSON, not prose.
- `AGENTS.schema.json` — JSON Schema for the agent policy.
- `docs/PROBLEM_STATEMENT.md` — canonical target and exact A-D scope discipline.
- `docs/KNOWN_BOUNDARY.md` — human-readable reconstruction of the initial theorem landscape.
- `docs/PROOF_BARRIERS.md` — common invalid proof upgrades and bridge obligations.
- `docs/BASELINE_IDENTITIES.md` — analytic identities Phase 2 will turn into executable diagnostics.
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

The Millennium Prize target is the Clay Mathematics Institute Navier-Stokes problem and Charles L. Fefferman's official problem description. This repository does not redefine the prize problem. Any candidate solution must map its hypotheses and conclusion explicitly to one or more of the official A-D formulations before publication-grade status is possible.

## Current phase

**Phase 1 — Known-boundary reconstruction.**

The initial boundary map establishes a conservative theorem spine, proof-barrier registry and exact source-authority policy. It is intentionally incomplete and is expected to expand as primary literature is checked.

No solution, counterexample, proof of global regularity, proof of finite-time singularity, or new theorem is claimed by this repository at present.

## Licensing

Software, machine-readable policies, schemas, configuration, tests and tooling are Apache-2.0 unless a file states otherwise. Human-authored research prose and figures explicitly marked `CC-BY-4.0` are licensed under Creative Commons Attribution 4.0 International. See `LICENSES.md`.
