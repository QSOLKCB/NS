# Contributing

QSOL NS is currently a private research workspace. Contributions are welcome only when they preserve the distinction between exploration, reproducible evidence and proof.

## Before changing anything

1. Read `AGENTS.md` as JSON and obey its contract.
2. Read `docs/PROBLEM_STATEMENT.md` and `docs/CLAIM_LEVELS.md`.
3. Work on a branch; do not write directly to `main`.
4. State whether the change is documentation, tooling, numerical evidence, a candidate lemma, or a proof artifact.

## Mathematical contributions

A mathematical claim must state:

- exact hypotheses;
- domain and boundary conditions;
- regularity assumptions;
- viscosity and forcing assumptions;
- dependencies on external theorems;
- whether any limiting, compactness, approximation or regularization argument is used;
- the exact claim level requested.

Do not describe a result as a theorem merely because symbolic algebra, numerical evidence or a proof assistant accepts a different encoded statement.

## Numerical contributions

Every evidentiary run must satisfy `docs/EXPERIMENT_CONTRACT.md`. Preserve configuration, source commit, environment identity, hashes and termination reason. Resolution studies and precision sensitivity are required before a singularity-like numerical signature can be promoted beyond exploratory status.

## Novelty

Before claiming novelty, search the relevant mathematical literature. A derivation that reproduces a known criterion is still useful, but must be labelled as reconstruction rather than a new theorem.

## Pull requests

PRs should state:

- what changed;
- why it changed;
- claim level affected;
- validation performed;
- unresolved mathematical or numerical risks;
- whether licensing/provenance changed.

Research criticism is expected to be adversarial toward arguments, not people.
