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
- [x] create a machine-readable theorem-boundary registry;
- [x] create a machine-readable proof-barrier registry;
- [x] define baseline analytic identities for Phase 2 diagnostics;
- [x] add schemas, cross-registry validation and hostile mutation probes;
- [x] make AI agents load the boundary map before research work;
- [ ] continue expanding the theorem landscape with primary-source verification;
- [ ] map geometric/vorticity depletion criteria in detail;
- [ ] map concentration/compactness and refined blow-up exclusions;
- [ ] map rigorous/computer-assisted PDE verification methods;
- [ ] maintain a queue of unresolved source checks and errata.

Phase 1 remains iterative while Phase 2 engineering continues. The initial registry is a conservative spine, not an exhaustive literature claim.

## Phase 2 — Deterministic PDE laboratory — IN PROGRESS

PR #3 v0.1 foundation:

- [x] implement a narrow periodic pseudo-spectral reference solver;
- [x] use deterministic Taylor-Green initial data;
- [x] add strict 2/3 de-aliasing and spectral divergence-free projection;
- [x] use fixed-step RK4 with explicit solver/version identity;
- [x] turn all six baseline identities into executable diagnostic bindings;
- [x] emit exact experiment manifests and content hashes;
- [x] preserve deterministic raw velocity output;
- [x] add identical-input replay tests;
- [x] add timestep and resolution comparison helpers;
- [x] add numerical-failure and sweep policies;
- [x] machine-disable singularity-oriented promotion while validation remains insufficient for mechanism-search claims;
- [x] add Python 3.11/3.13 CI for contract, tests and reference smoke run.

PR #4 precision-referee foundation:

- [x] add an independent arbitrary-precision arithmetic path for the `N=8` Taylor-Green reference family;
- [x] construct referee initial Fourier coefficients analytically rather than by FFT;
- [x] evaluate the nonlinear term by direct retained-mode convolution;
- [x] add a 50-to-80-decimal-digit precision ladder;
- [x] compare retained coefficients, kinetic energy and enstrophy against the NumPy/FFT reference path;
- [x] machine-lock the distinction between independent arithmetic/evaluation and independent spatial discretization;
- [x] keep singularity-oriented promotion disabled despite successful low-resolution precision comparison;
- [x] add hostile-mutation validation and Python 3.11/3.13 precision-referee CI;
- [ ] scale independent precision checks beyond the low-resolution reference family;
- [ ] add alternate initial-data families with exact admissibility records;
- [ ] add an independent solver implementation using a genuinely different spatial/numerical method for cross-method comparison;
- [ ] add spectral-transfer and scale-local diagnostics beyond the v0.1 baseline;
- [ ] add longer-run checkpoint/restart with content-addressed state identity.

The laboratory and referee are exploratory/reproducibility instruments, not proof engines.

## Phase 3 — Competing mechanism search

### Regularity track

Search for sharpened a priori bounds, monotone/coercive quantities, geometric depletion mechanisms, continuation criteria or concentration exclusions. Every candidate must be checked against `research/theorem_registry.json` and `research/proof_barriers.json` before novelty language is permitted.

### Breakdown track

Search for admissible initial-data/forcing families, concentration mechanisms, scaling scenarios or rigorous reductions capable of satisfying Clay C or D. Numerical blow-up signatures remain exploratory until a continuum bridge is proved.

## Phase 4 — Proof extraction

Promote only precise candidate lemmas. Attempt analytic proof, symbolic checking, interval methods or proof-assistant formalization where appropriate. Preserve correspondence between any formal object and the exact mathematical statement.

## Phase 5 — Adversarial review

Try to break every promoted result with edge cases, scaling checks, hidden assumptions, known theorems, alternate discretizations, proof-barrier matching and independent reviewers.

## Phase 6 — Publication/archive

Only after the publication gate: freeze exact commit/tag, generate citation metadata, archive artifacts, and publish wording that matches the actual claim level.
