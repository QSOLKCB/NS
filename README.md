# QSOL NS

**Private research workbench for the 3D incompressible Navier–Stokes existence and smoothness problem.**

QSOL NS is intended to support a disciplined two-track investigation of the Navier–Stokes Millennium Prize Problem while keeping numerical evidence, mathematical proof, and physical interpretation rigorously separated.

## Core problem

For the 3D incompressible Navier–Stokes equations

```text
∂ₜu + (u·∇)u = -∇p + νΔu
∇·u = 0
```

with velocity field `u`, pressure `p`, and viscosity `ν > 0`, the project studies the global existence/smoothness question from both admissible directions:

1. **Global-regularity track** — seek rigorous estimates, invariants, continuation criteria, monotonic quantities, or exclusions of concentration mechanisms that could establish global smoothness.
2. **Finite-time singularity track** — seek admissible smooth divergence-free initial data and a rigorously characterizable mechanism capable of forcing loss of regularity in finite time.

Neither track is privileged in advance. The mathematics decides.

## Governing research boundary

```text
NUMERICAL BLOW-UP SIGNATURE != PROOF OF BLOW-UP
NO OBSERVED BLOW-UP != PROOF OF GLOBAL REGULARITY
FORMAL VERIFICATION != PHYSICAL TRUTH
```

Numerical experiments may discover conjectures, candidate mechanisms, counterexample families, scaling laws, or proof obligations. They do not settle the Millennium problem by themselves.

## Planned repository structure

```text
docs/        exact problem statement, theorem boundary, literature map, research notes
experiments/ deterministic numerical experiments and singularity diagnostics
formal/      machine-checked lemmas and proof-support material where useful
src/         reusable numerical, symbolic, and verification tooling
tests/       regression, determinism, and invariant tests
```

## Reproducibility principles

- freeze initial conditions and numerical parameters;
- record solver, compiler, dependency, and runtime identities;
- separate exploratory runs from evidentiary runs;
- retain negative and null results;
- distinguish numerical instability from mathematical singularity;
- state every theorem claim with explicit hypotheses and dependencies;
- preserve exact commit identity for any result promoted into a paper or archival record;
- never promote computational consistency into mathematical proof without a valid argument bridging the two.

## Current status

Early **private research stage**. No claim of a solution, counterexample, proof, or new theorem is made by the existence of this repository.

## Private-repository access test

This README was intentionally updated through the connected GitHub integration while `QSOLKCB/NS` was private. See [`docs/PRIVATE_REPO_SMOKE_TEST.md`](docs/PRIVATE_REPO_SMOKE_TEST.md) for the companion nested-file write/read test.

## License

Source code is licensed under the **Apache License 2.0**; see [`LICENSE`](LICENSE).

Research papers, figures, and selected documentation may later be released under **CC BY 4.0** when appropriate. Any such material will be explicitly marked rather than assumed to inherit a different license from the repository root.
