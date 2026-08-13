<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Roadmap

## Phase 0 — Governance and target lock — COMPLETE

- [x] freeze canonical problem authority;
- [x] establish claim levels;
- [x] establish experiment/reproducibility contracts;
- [x] establish machine-readable agent rules;
- [x] establish licensing and citation metadata.

## Phase 1 — Known-boundary reconstruction — IN PROGRESS

Initial PR #2 foundation:

- [x] encode the exact official A-D Clay target and errata;
- [x] establish primary/official source authority rules;
- [x] create machine-readable theorem and proof-barrier registries;
- [x] define baseline analytic identities for Phase 2 diagnostics;
- [x] add schemas, cross-registry validation and hostile mutation probes;
- [x] make AI agents load the boundary map before research work;
- [ ] continue expanding the theorem landscape with primary-source verification;
- [ ] map geometric/vorticity depletion criteria in detail;
- [ ] map concentration/compactness and refined blow-up exclusions;
- [ ] map rigorous/computer-assisted PDE verification methods;
- [ ] maintain a queue of unresolved source checks and errata.

Phase 1 remains iterative. The initial registry is a conservative spine, not an exhaustive literature claim.

## Phase 2 — Deterministic PDE laboratory — IN PROGRESS

PR #3 reference-lab foundation:

- [x] implement periodic pseudo-spectral reference solver and Taylor-Green baseline;
- [x] add strict 2/3 de-aliasing and spectral divergence-free projection;
- [x] use fixed-step RK4 with explicit solver/version identity;
- [x] bind all six baseline identities to executable diagnostics;
- [x] emit exact experiment manifests/content hashes and deterministic raw output;
- [x] add replay, timestep and resolution sensitivity helpers;
- [x] preserve numerical failures and keep singularity-oriented promotion disabled.

PR #4 precision-referee foundation:

- [x] add independent arbitrary-precision arithmetic for the `N=8` Taylor-Green reference family;
- [x] construct referee Fourier coefficients analytically and evaluate direct modal convolution;
- [x] add 50-to-80-decimal-digit precision ladder;
- [x] compare retained coefficients, kinetic energy and enstrophy with the NumPy/FFT path;
- [x] preserve failed float64 executions while continuing the referee path when possible;
- [x] emit provenance-complete referee evidence bundles;
- [x] machine-lock that the referee is not an independent spatial discretization or proof engine;
- [ ] scale precision checking beyond the low-resolution reference family;
- [ ] add alternate initial-data families with exact admissibility records;
- [ ] add a genuinely different numerical method for cross-method comparison;
- [ ] add spectral-transfer and scale-local diagnostics;
- [ ] add longer-run checkpoint/restart with content-addressed state identity.

## Phase 2.5 — Crucible Core and ML-search architecture — IN PROGRESS

PR #5 v0.1 foundation:

- [x] extract domain-neutral candidate/evidence/constraint/failure objects;
- [x] make competing hypothesis sets first-class and unresolved by default;
- [x] preserve candidate parentage and generation method;
- [x] add training/development/holdout evidence stages;
- [x] require candidate freeze before holdout access;
- [x] add append-only failure records with reusable lessons;
- [x] expose a deterministic survivor frontier without a universal confidence score;
- [x] forbid Crucible Core from defining domain truth, promoting claims or selecting a winner;
- [x] add NS domain adapter mapping regularity to Clay A/B and breakdown to C/D;
- [x] bind every registered NS proof barrier into Crucible screening;
- [x] retain existing numerical evidence ceilings and Clay correspondence requirements;
- [x] add agent boot requirements, hostile-mutation validation and Python 3.11/3.13 CI;
- [ ] add persistent content-addressed candidate/evidence/failure stores;
- [ ] add ML generator interfaces that emit schema-valid candidates only;
- [ ] add duplicate/dead-family detection against the accumulated failure ledger;
- [ ] add controlled candidate mutation/crossover provenance;
- [ ] add sealed holdout materialization with auditable release events;
- [ ] extract the generic Crucible package into its own repository only after the NS reference implementation stabilizes.

Crucible Core is an orchestration/falsification engine, not a truth engine. Each future domain adapter must define its own epistemic standard.

## Phase 3 — Competing mechanism search

### Regularity track

Use the Crucible frontier to search for sharpened a priori bounds, monotone/coercive quantities, geometric depletion mechanisms, continuation criteria or concentration exclusions. Every candidate must be checked against the theorem registry and proof barriers before novelty language is permitted.

### Breakdown track

Use the same machinery to search for admissible initial-data/forcing families, concentration mechanisms, scaling scenarios or rigorous reductions capable of satisfying Clay C or D. Numerical blow-up signatures remain exploratory until a continuum bridge is proved.

Future ML search should generate candidates on both tracks, preserve failed families, and use the failure ledger to reduce repeated exploration of already-rejected mechanisms.

## Phase 4 — Proof extraction

Promote only precise candidate lemmas. Attempt analytic proof, symbolic checking, interval methods or proof-assistant formalization where appropriate. Preserve correspondence between any formal object and the exact mathematical statement.

## Phase 5 — Adversarial review

Try to break every promoted result with edge cases, scaling checks, hidden assumptions, known theorems, alternate discretizations, proof-barrier matching and independent reviewers.

## Phase 6 — Publication/archive

Only after the publication gate: freeze exact commit/tag, generate citation metadata, archive artifacts, and publish wording that matches the actual claim level.
