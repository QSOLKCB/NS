<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Problem Statement and Canonical Target

## Authority

The canonical Millennium Prize target for this repository is the Clay Mathematics Institute Navier-Stokes problem and Charles L. Fefferman's official problem description:

- https://www.claymath.org/millennium/Navier-Stokes-Equation/
- https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf

The machine-readable target lock is `research/clay_target.json`.

This repository does **not** replace, simplify, broaden or redefine that target.

## Working equations

For exploratory work we use the three-dimensional incompressible Navier-Stokes system

```text
partial_t u + (u dot grad)u = -grad p + nu Delta u + f
div u = 0
```

where `u` is velocity, `p` pressure, `nu > 0` viscosity and `f` forcing when present.

## The four official routes

The Fefferman description asks for proof of at least one of four statements. They are separate targets; their domains and forcing quantifiers may not be mixed silently.

### A — Global smoothness on `R^3`

For every admissible smooth divergence-free rapidly decaying initial datum, with `f = 0`, prove a global smooth solution satisfying the required energy bound.

### B — Global smoothness on `R^3/Z^3`

For every admissible smooth divergence-free spatially periodic initial datum, with `f = 0`, prove a global smooth spatially periodic solution.

### C — Breakdown on `R^3`

Exhibit admissible smooth divergence-free rapidly decaying initial data and admissible smooth rapidly decaying forcing for which there is no global physically reasonable smooth bounded-energy solution of the required kind. Zero forcing is permitted but is not required by the formulation.

### D — Breakdown on `R^3/Z^3`

Exhibit admissible smooth divergence-free periodic initial data and admissible smooth periodic/time-decaying forcing for which there is no global smooth periodic solution of the required kind. Zero forcing is permitted but is not required by the formulation.

## Official errata

The official PDF contains errata that are part of this repository's target lock.

- The periodic formulation requires explicit pressure periodicity `p(x+e_j,t)=p(x,t)`.
- A weak-form equation in the historical text is corrected in the errata; any proof-level reuse must follow the corrected form.

Agents must use `research/clay_target.json` rather than reconstructing these details from memory.

## Two-track program

The project explores both logically available directions:

1. **Global-regularity track:** establish estimates or structural results sufficient to prove A or B.
2. **Breakdown track:** construct or characterize admissible data sufficient to prove C or D.

No track receives evidentiary preference in advance.

## Exact-hypothesis rule

Before any result is described as relevant to a Millennium solution, it must explicitly record:

- selected official formulation: `A | B | C | D`;
- spatial domain;
- initial data class;
- smoothness/decay or periodicity conditions;
- incompressibility condition;
- viscosity;
- forcing assumptions and quantifier;
- solution concept;
- time interval;
- norm or regularity quantity controlled or shown to fail;
- every bridge from a restricted/modified/computational/formal setting to the official formulation.

A result for a modified equation, restricted ansatz, symmetry class, discretization, regularized model, averaged model or altered forcing may be mathematically valuable but is not automatically a result for the Clay problem.

## Canonical non-equivalences

```text
DISCRETE_BLOWUP != CONTINUUM_BLOWUP
REGULARIZED_MODEL_RESULT != NAVIER_STOKES_RESULT
SPECIAL_ANSATZ_RESULT != GENERAL_RESULT
SMALL_DATA_RESULT != ARBITRARY_DATA_RESULT
WEAK_EXISTENCE != GLOBAL_SMOOTHNESS
CONDITIONAL_REGULARITY != UNCONDITIONAL_APRIORI_BOUND
PARTIAL_REGULARITY != EMPTY_SINGULAR_SET
R3_RESULT != PERIODIC_RESULT
LARGE_NORM != SINGULARITY
SOLVER_FAILURE != SINGULARITY
FORMALIZED_SURROGATE != OFFICIAL_PROBLEM
```

## Change control

Any proposed modification to this document or `research/clay_target.json` that changes the target rather than clarifying it requires explicit human-operator review and comparison against the current CMI statement.
