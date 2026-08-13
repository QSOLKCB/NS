# QSOL NS

**Private reproducible research workbench for the 3D incompressible Navier–Stokes existence and smoothness problem, and first reference domain for the QSOL Crucible architecture.**

QSOL NS is a two-track research program: global regularity and finite-time breakdown are treated as competing hypotheses until mathematics rules one out. Numerical experiments, symbolic work, formal verification, literature reconstruction, ML-assisted candidate generation and controlled cross-domain transfer are discovery/checking tools, never substitutes for proof.

## Research boundary

```text
NUMERICAL_BLOWUP_SIGNATURE != PROOF_OF_BLOWUP
NO_OBSERVED_BLOWUP != PROOF_OF_GLOBAL_REGULARITY
FORMAL_VERIFICATION != EMPIRICAL_TRUTH
CANDIDATE_LEMMA != VERIFIED_THEOREM
PRIVATE_EXPERIMENT != PUBLIC_CLAIM
KNOWN_THEOREM_SUMMARY != NOVEL_RESULT
NARRATIVE_PLAUSIBILITY != EVIDENTIARY_STATUS
PRECISION_AGREEMENT != CONTINUUM_PROOF
CRUCIBLE_SURVIVAL != PROOF
FAILURE_OF_ONE_CANDIDATE != PROOF_OF_A_COMPETITOR
VISUAL_RESEMBLANCE != PHYSICAL_MECHANISM
SHARED_OPERATOR != SHARED_DYNAMICS
STRUCTURAL_ANALOGY != DOMAIN_EQUIVALENCE
ANALOGY != DOMAIN_EVIDENCE
ANALOGY_CANNOT_PROMOTE_CLAIM
```

## Machine research boundary

The project carries machine-readable research boundaries and laboratory contracts:

- `research/clay_target.json` — exact official Clay A-D targets and errata;
- `research/source_registry.json` — source identities and authority classes;
- `research/theorem_registry.json` — known-result summaries with hypotheses and limitations;
- `research/proof_barriers.json` — invalid inference patterns and required bridge obligations;
- `research/baseline_identities.json` — analytic identities bound to Phase 2 diagnostics;
- `research/lab_contract.json` — reference-solver scope, evidence ceiling, determinism and diagnostics;
- `research/precision_referee_contract.json` — scope/nonclaims of the arbitrary-precision referee;
- `research/crucible_contract.json` — domain-neutral hypothesis/falsification orchestration contract;
- `research/ns_crucible_adapter.json` — NS epistemic adapter binding Crucible to Clay, proof barriers and claim authority;
- `research/analogy_firewall_contract.json` — authority limits for cross-domain analogy transfer;
- `research/cross_domain_transfer_registry.json` — provenance-bearing mapping classifications and negative controls;
- `research/ns_cross_domain_transfer_adapter.json` — NS intake/revalidation policy for analogy-derived candidates;
- `research/schemas/` — schemas for research, experiment, laboratory, referee, Crucible and transfer contracts;
- `tools/validate_boundary_map.py` — theorem/source boundary validation;
- `tools/validate_lab_contract.py` — solver/manifest/identity correspondence validation;
- `tools/validate_precision_referee.py` — precision-referee correspondence validation;
- `tools/validate_crucible_core.py` — Crucible/NS-adapter correspondence and hostile-mutation validation;
- `tools/validate_analogy_firewall.py` — transfer-registry/firewall/NS-intake authority validation.

Only official problem statements and primary research sources may authorize theorem-registry entries. Secondary sources may help discover literature but cannot establish the machine theorem boundary. Cross-domain analogies are even more tightly bounded: they may generate exploratory candidates but are not NS evidence.

## Deterministic PDE laboratory v0.1

PR #3 began Phase 2 with a deliberately narrow reference solver: a three-dimensional `[0,2π)^3` periodic cube, positive viscosity, zero forcing, deterministic Taylor–Green initial data, Fourier pseudo-spectral discretization, strict 2/3 de-aliasing, spectral divergence-free projection, classical fixed-step RK4, and `float64/complex128` arithmetic.

The laboratory binds all six Phase-1 baseline identities to executable checks, emits content-hashed diagnostics and raw final velocity, and provides deterministic timestep/resolution sensitivity helpers. Its machine evidence ceiling remains `reproduced_numerical`.

## Independent Precision Referee v0.1

PR #4 added a low-resolution arbitrary-precision referee for the `N=8` Taylor-Green reference family. It constructs Fourier coefficients analytically, evaluates the nonlinear term by direct modal convolution without NumPy FFTs, applies modal divergence-free projection and advances the same retained Fourier system with RK4 using `mpmath` arithmetic.

It is **not** a second spatial discretization and is not a scalable singularity-search backend. Agreement means the tested finite-dimensional computation survived another implementation/precision challenge; it does not establish a continuum theorem.

## Crucible Core v0.1

PR #5 extracts the reusable research machinery that PRs #1-#4 implicitly created.

`src/crucible_core/` manages candidate lineage, unresolved competing hypothesis sets, evidence provenance, domain-supplied constraint results, sealed holdout access, append-only failure records and a deterministic survivor frontier.

Crucible Core has **no authority to define truth, promote a claim, assign a winner or emit a universal confidence score**. Those powers belong to the domain adapter and existing human/research governance.

For NS, `research/ns_crucible_adapter.json` binds the two initial tracks:

- `NS_GLOBAL_REGULARITY` -> Clay A/B;
- `NS_FINITE_TIME_BREAKDOWN` -> Clay C/D.

All registered NS proof barriers remain hard screening obligations. The deterministic lab and precision referee remain numerical evaluators with their existing evidence ceilings.

The failure ledger is intended to make future ML search cumulative: dead candidate families preserve *why* they failed instead of being rediscovered in another chat or run.

## Analogy Firewall v0.1

PR #6 adds a controlled intake valve from other domains.

`src/crucible_core/analogy.py` classifies cross-domain mappings as:

- exact correspondence;
- operator correspondence;
- structural analogy;
- heuristic analogy;
- visual resemblance;
- explicit non-correspondence.

The first four may seed an **exploratory** candidate. The final two are negative-control-only.

No mapping class may automatically become NS evidence, raise a claim level, satisfy a proof barrier, select a winner, or assert whole-domain equivalence. Source-domain proof/evidence status is never inherited. Every accepted transfer must be revalidated under the NS adapter, Clay target and full proof-barrier set.

The initial registry is derived from a user-supplied fluid/diffusion technical reference. The source is retained as design provenance, not promoted to theorem authority.

## Repository map

- `AGENTS.md` / `AGENTS.schema.json` — machine-readable research constitution;
- `src/ns_lab/` — deterministic periodic reference laboratory and precision referee;
- `src/crucible_core/` — domain-neutral candidate/falsification and analogy-firewall machinery;
- `tests/` — replay, solver, manifest, referee, Crucible and analogy-firewall regressions;
- `docs/CRUCIBLE_CORE_V0_1.md` — generic Crucible design and nonclaims;
- `docs/NS_CRUCIBLE_ADAPTER.md` — NS-specific epistemic binding;
- `docs/ANALOGY_FIREWALL_V0_1.md` — controlled cross-domain transfer architecture;
- `docs/NS_CROSS_DOMAIN_TRANSFER_ADAPTER.md` — NS-specific analogy intake/revalidation rules;
- `docs/PDE_LAB_V0_1.md` / `docs/PRECISION_REFEREE_V0_1.md` — numerical architecture;
- `docs/PROBLEM_STATEMENT.md` / `docs/KNOWN_BOUNDARY.md` / `docs/PROOF_BARRIERS.md` — mathematical target and known boundary;
- `docs/CLAIM_LEVELS.md` — evidence/claim promotion ladder;
- `docs/ROADMAP.md` — staged research plan.

## Canonical external authority

The Millennium Prize target is the Clay Mathematics Institute Navier-Stokes problem and Charles L. Fefferman's official problem description. This repository does not redefine the prize problem. Any candidate solution must map its hypotheses and conclusion explicitly to one or more official A-D formulations before publication-grade status is possible.

## Current phase

**Phase 1 boundary reconstruction continues; Phase 2 laboratory engineering and Phase 2.5 Crucible/ML-search architecture are in progress.**

No solution, counterexample, proof of global regularity, proof of finite-time singularity, or new theorem is claimed by this repository at present.

## Licensing

Software, machine-readable policies, schemas, configuration, tests and tooling are Apache-2.0 unless a file states otherwise. Human-authored research prose and figures explicitly marked `CC-BY-4.0` are licensed under Creative Commons Attribution 4.0 International. See `LICENSES.md`.
