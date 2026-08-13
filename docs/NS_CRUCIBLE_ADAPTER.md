<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Navier-Stokes Crucible Adapter v0.1

## Role

The NS adapter binds the generic Crucible Core to the existing QSOL NS research constitution. It does not replace any existing authority. It points the core back to the exact Clay target, theorem registry, proof barriers, deterministic lab, precision referee, and existing claim policy.

## Primary competition

The initial hypothesis set is unresolved:

- `NS_GLOBAL_REGULARITY` -> Clay A/B routes;
- `NS_FINITE_TIME_BREAKDOWN` -> Clay C/D routes.

Neither receives a prior preference. The purpose of the Crucible is not to vote between them. It is to let proposed mechanisms on both sides face the same provenance, theorem-boundary, proof-barrier and reproducibility pressure.

## Proof barriers as screening obligations

All registered proof barriers are bound into the adapter. Crossing one requires the same response already required by the NS project: provide a rigorous bridge theorem or weaken the claim.

This makes the generic failure ledger useful without changing the mathematics. A candidate can be remembered as failing `NUMERICAL_CONTINUUM_GAP`, `CIRCULAR_REGULARITY`, `SMALL_DATA_NOT_ARBITRARY_DATA`, and so on.

## Numerical evaluators

The deterministic PDE laboratory and precision referee are available as domain evaluators. Their existing ceilings remain unchanged:

```text
NUMERICAL_EVIDENCE <= reproduced_numerical
PRECISION_AGREEMENT != CONTINUUM_PROOF
SOLVER_FAILURE != MATHEMATICAL_SINGULARITY
```

Crucible Core cannot reinterpret those results into a stronger claim.

## Holdouts in NS

Holdouts may be useful for ML candidate generation and adversarial numerical screening, but they are not a substitute for mathematical proof and are not required as part of the Clay proof standard. A successful holdout therefore changes no claim level by itself.

## Why extract the core now?

PRs #1-#4 already created the ingredients of a generic falsification architecture: exact targets, theorem boundaries, proof barriers, provenance, claim levels, deterministic evaluators and independent checking.

PR #5 names and formalizes the reusable machinery while keeping NS as the first reference domain. This lets later ML search operate against an explicit survivor frontier and failure ledger rather than repeatedly rediscovering the same dead ends.
