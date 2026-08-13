<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Problem Statement and Canonical Target

## Authority

The canonical Millennium Prize target for this repository is the Clay Mathematics Institute Navier–Stokes problem, together with Charles L. Fefferman's official problem description referenced by CMI:

- https://www.claymath.org/millennium/Navier-Stokes-Equation/

This repository does **not** replace, simplify, broaden or redefine that target.

## Working equations

For exploratory work we use the three-dimensional incompressible Navier–Stokes system in the conventional form

```text
∂ₜu + (u·∇)u = -∇p + νΔu + f
∇·u = 0
```

where `u` is velocity, `p` pressure, `ν > 0` viscosity and `f` forcing when present.

## Two-track program

The project explores both logically available directions:

1. **Global-regularity track:** establish estimates or structural results sufficient to rule out finite-time loss of smoothness under an official admissible formulation.
2. **Breakdown track:** construct or characterize admissible data producing the type of breakdown required by an official admissible formulation.

No track receives evidentiary preference in advance.

## Exact-hypothesis rule

Before any result is described as relevant to a Millennium solution, it must explicitly record:

- spatial domain;
- initial data class;
- smoothness/decay or periodicity conditions;
- incompressibility condition;
- viscosity;
- forcing assumptions;
- solution concept;
- time interval;
- norm or regularity quantity controlled or shown to fail;
- the exact official formulation to which the result is claimed to map.

A result for a modified equation, restricted ansatz, symmetry class, discretization, regularized model, averaged model or altered forcing may be mathematically valuable but is not automatically a result for the Clay problem.

## Canonical non-equivalences

```text
DISCRETE_BLOWUP != CONTINUUM_BLOWUP
REGULARIZED_MODEL_RESULT != NAVIER_STOKES_RESULT
SPECIAL_ANSATZ_RESULT != GENERAL_RESULT
LARGE_NORM != SINGULARITY
SOLVER_FAILURE != SINGULARITY
FORMALIZED_SURROGATE != OFFICIAL_PROBLEM
```

## Change control

Any proposed modification to this document that changes the target rather than clarifying it requires explicit human-operator review and comparison against the current CMI statement.
