<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenAI 2026 C/D exact statement correspondence

## Status

**Phase 3A Gate 1: statement correspondence confirmed.**

This document records a field-by-field audit of the *target statements* for OpenAI's 2026 Navier–Stokes claims against Charles Fefferman's official Clay formulations C and D.

It does **not** claim that the analytical proof has been independently checked, that the Lean project has been clean-room replayed by QSOL, or that the Millennium problem has been accepted as solved. Those are later gates.

The machine-readable authority for this audit is:

- `research/openai_2026_correspondence.json`
- `research/schemas/openai_2026_correspondence.schema.json`
- `tools/validate_openai_2026_correspondence.py`

The prior intake boundary remains authoritative for claim status:

- `research/external_claim_registry.json`

C and D remain `external_claim_pending_independent_verification`.

## Pinned formal statement artifacts

The correspondence audit is pinned to OpenAI repository commit:

`8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`

and to exact blob identities for:

| Artifact | Blob SHA |
|---|---|
| `NavierStokes/ComparatorSolution.lean` | `cc232068cd384dbbddce2753b1fc4a4017c0f2d7` |
| `NavierStokes/ComparatorDefinitions.lean` | `d92c81ac99c1139e54c181c97d9021e975e23b7a` |
| `ComparatorChallenges/NavierStokes.lean` | `673fb19e26e60818d446363afd953f618719f99b` |
| `formalization.yaml` | `01270e9f666b0400b60d032204e02e6d684cee98` |

The final comparator submission exposes:

- `NavierStokes.Comparator.navier_stokes_breakdown_R3`
- `NavierStokes.Comparator.navier_stokes_breakdown_periodic`

The independent challenge file presents the same theorem shapes as alternatives C and D.

## Why Gate 1 can close without claiming proof validity

There are three separate questions:

1. **Does the final statement match Fefferman C/D?**
2. **Does the analytical construction actually establish that statement?**
3. **Does the Lean proof correctly and independently certify the encoded statement?**

Gate 1 addresses only question 1.

Questions 2 and 3 remain open work in Gates 2–6.

That separation is intentional. A statement can be perfectly encoded while its proof is wrong; a proof assistant can successfully check an encoded theorem while the encoding differs from the intended prose target; and a special constructed witness can satisfy the target assumptions only if all bridge arguments are actually valid.

## Formulation C — whole space

OpenAI's final Lean declaration has the form:

```text
for every nu > 0,
there exist u0 and f such that
  InitialVelocityConditionDecay u0
  and ForceConditionDecay f
  and there do not exist v,p satisfying
      NavierStokesExistenceAndSmoothnessRn nu u0 f v p
```

### Field map

| Fefferman requirement | Pinned Lean encoding | Gate 1 disposition |
|---|---|---|
| 3 spatial dimensions | `ℝ³ := EuclideanSpace ℝ (Fin 3)` | exact statement match |
| `nu > 0` | `(nu : ℝ) (hnu : nu > 0)` | exact statement match |
| domain `R^3` | `u₀ : ℝ³ → ℝ³`, `f : ℝ³ → ℝ → ℝ³` | exact statement match |
| smooth divergence-free rapidly decaying initial data | `InitialVelocityConditionDecay` | exact target-class match |
| smooth rapidly decaying forcing | `ForceConditionDecay` | exact target-class match |
| Navier–Stokes momentum equation | `NavierStokesExistenceAndSmoothness.navier_stokes` | exact statement match |
| incompressibility | `.div_free` | exact statement match |
| initial condition | `.initial_condition` | exact statement match |
| global smooth velocity and pressure | `.velocity_smooth`, `.pressure_smooth` on `[0,∞)` | exact statement match |
| finite and uniformly bounded kinetic energy | `MemLp` plus `.globally_bounded_energy` | exact statement match |
| no global physically reasonable solution | negated existence of `NavierStokesExistenceAndSmoothnessRn` | exact statement match |

The analytical paper uses the stronger special initial datum `u0 = 0` and describes smooth compactly supported forcing. Those are admissible special cases of the C data classes **if the construction and bridge arguments are correct**. Gate 1 records that logical relationship but does not prove those construction facts.

## Formulation D — periodic torus

OpenAI's final Lean declaration has the form:

```text
for every nu > 0,
there exist u0 and f such that
  InitialVelocityConditionPeriodic u0
  and ForceConditionPeriodic f
  and there do not exist v,p satisfying
      NavierStokesExistenceAndSmoothnessPeriodic nu u0 f v p
```

### Field map

| Fefferman requirement | Pinned Lean encoding | Gate 1 disposition |
|---|---|---|
| 3 spatial dimensions | `ℝ³ := EuclideanSpace ℝ (Fin 3)` | exact statement match |
| `nu > 0` | `(nu : ℝ) (hnu : nu > 0)` | exact statement match |
| domain `R^3/Z^3` | `IsOnePeriodic` in each coordinate | exact statement match |
| smooth divergence-free periodic initial data | `InitialVelocityConditionPeriodic` | exact target-class match |
| smooth periodic forcing with time decay | `ForceConditionPeriodic` | exact target-class match |
| Navier–Stokes momentum equation | `NavierStokesExistenceAndSmoothness.navier_stokes` | exact statement match |
| incompressibility | `.div_free` | exact statement match |
| initial condition | `.initial_condition` | exact statement match |
| global smooth velocity and pressure | base smoothness fields on `[0,∞)` | exact statement match |
| velocity periodicity | `.isOnePeriodic_velocity` | exact statement match |
| **pressure periodicity erratum** | `.isOnePeriodic_pressure` | exact erratum match |
| no global smooth periodic solution | negated existence of `NavierStokesExistenceAndSmoothnessPeriodic` | exact statement match |

The pressure condition matters. QSOL's Clay target explicitly records the official periodic-pressure erratum, and the pinned comparator definition includes it directly.

## Important construction-versus-target distinction

The final comparator theorems are existential target statements. They do **not** by themselves expose every construction-specific fact from the analytical paper, such as:

- zero initial velocity;
- compact support of the force;
- the concentrating profile;
- stress and pulse construction;
- residual cancellation;
- localization;
- the uniqueness/continuation argument;
- periodicization of the whole-space construction.

Those are proof-side obligations.

They are the subject of Gate 2 (dependency graph) and Gate 3 (local proof reconstruction), not reasons to inflate Gate 1.

## Machine invariants

```text
STATEMENT_CORRESPONDENCE != PROOF_VALIDITY
LEAN_STATEMENT_MATCH != CLEAN_ROOM_REPLAY
SPECIAL_CASE_ADMISSIBILITY != PROOF_OF_CONSTRUCTION
C_CORRESPONDENCE != A_RESOLUTION
D_CORRESPONDENCE != B_RESOLUTION
PERIODIC_PRESSURE_ERRATUM_REQUIRED
GATE1_PASS != INDEPENDENT_VERIFICATION_COMPLETE
```

## Next gate

**Gate 2 — analytical dependency graph** is now the next priority.

The next work should root a machine-readable DAG at:

- Theorem 1.1 → C
- Corollary 10.6 → D

and descend through the proof-critical construction, localization, energy, uniqueness/continuation, and periodicization dependencies without allowing narrative shorthand to stand in for an explicit edge.
