<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenAI 2026 analytical dependency DAG — Phase 3A Gate 2

## Purpose

This document records the Gate 2 / WP2 dependency graph for QSOL's independent review of OpenAI's 2026 *Finite time blowup for Navier-Stokes* claim.

Gate 1 established only that the pinned final C/D statements line up with Fefferman alternatives C and D. Gate 2 asks a different question:

> What proof-critical construction and comparison obligations must all survive before those final statements can be accepted?

The machine-readable answer is `research/openai_2026_dependency_dag.json`.

The graph is **not a proof** and is not a claim that QSOL has independently re-derived any local estimate. Every node is deliberately marked `indexed_not_reconstructed`. Gate 3 is where the local arguments are independently rebuilt and attacked.

## Frozen source surface

The graph inherits the paper and Lean pins already established by PRs #12–#13:

- analytical PDF SHA-256: `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`;
- Lean repository: `openai/NavierStokesAndEuler`;
- pinned Lean commit: `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`;
- PR #13 merge baseline: `52fcdb1b4ec0eb561fd80e3dbdfab3f0e87465cf`.

Gate 2 additionally pins sixteen high-value formal modules whose comments and import structure expose the candidate/bridge spine. These include the two comparator bridges, whole-space and periodic comparison layers, candidate assembly/correction layers, residual limits, stress-cone algebra, curl realization, covariance construction, and exponent ledger.

A formal module path is an **anchor**, not an assertion that its proof has been independently checked.

## Graph semantics

Each edge means:

```text
FROM_NODE depends on TO_NODE
```

The two roots are:

```text
G2_ROOT_C  = Theorem 1.1 -> Fefferman C
G2_ROOT_D  = Corollary 10.6 -> Fefferman D
```

The validator requires that:

- every edge points to a registered node;
- the graph is acyclic;
- no non-root node is orphaned;
- every node is reachable from C, D, or both;
- all twelve Gate 2 dependency classes are represented;
- the complete reviewed node and edge semantics remain unchanged unless the validator is deliberately updated.

## C path

The C branch has the following top-level shape:

```text
Theorem 1.1 / C target
  -> whole-space candidate-to-C bridge
     -> compact whole-space candidate
        -> spatial localization / compact smooth force
        -> bounded-energy controls
        -> literal candidate assembly
     -> whole-space finite-energy uniqueness/comparison
        -> bounded-energy controls
        -> localization/support controls
```

The pinned OpenAI bridge `ComparatorR3Theorem.lean` makes this separation unusually explicit. It takes a compact candidate, proves the zero initial datum and viscosity-rescaled force satisfy the comparator decay classes, and then excludes a hypothetical global comparator solution through `R3FiniteEnergyComparison`.

QSOL therefore treats **construction** and **comparison/non-existence** as separate Gate 3 attack surfaces.

## D path

The D branch is:

```text
Corollary 10.6 / D target
  -> periodic candidate-to-D bridge
     -> periodic candidate
        -> periodicization and force decay
        -> literal candidate assembly
     -> periodic uniqueness / maximal lifespan
        -> periodic candidate
```

`ComparatorTheorem.lean` uses the selected periodic candidate, rescaling in viscosity and the maximal-lifespan exclusion. `CandidateConsequences.lean` is separately responsible for deriving the future-jet decay needed by the comparator from smoothness, periodicity and compact future-time support.

That means the D argument is not merely “copy the R3 fields onto a torus.” Periodic velocity, periodic pressure, force decay and the continuation/uniqueness contradiction remain distinct obligations.

## Shared construction spine

Both C and D ultimately depend on the same selected candidate assembly. The shared spine is broken into the twelve Gate 2 classes required by the verification programme.

### 1. Concentrating axisymmetric leading profile

Tracked by `G2_LEADING_PROFILE`.

Formal anchors include `FinalSlowBase.lean`, `PreparedOutgoing.lean`, and `ReferenceBounds.lean`.

Gate 3 must check the actual profile equations, support, signs, axis behavior, and the hypotheses later used by the stress cone and correction stages.

### 2. Self-similar scaling and velocity growth

Tracked by `G2_SCALING`.

`ExponentLedger.lean` explicitly says it checks the arithmetic of Proposition 10.3's assigned exponents **conditional on the analytic estimates being valid**. It also identifies the manuscript's parameter choices in sections 8.1 and 10.2.

This distinction is important: correct exponent arithmetic is not proof of the estimates carrying those exponents.

### 3. Annular residual stress

Tracked by `G2_ANNULAR_STRESS`.

This node keeps the residual-stress support/sign/orientation problem separate from both cone admissibility and the later covariance realization. Gate 3 should attack all three separately.

### 4. Admissible stress cone

Tracked by `G2_STRESS_CONE`.

`ConeAlgebra.lean` explicitly identifies the square-root criterion with manuscript Lemma 3.5 and the normalized factorization with equation (11). It also explicitly says it does **not** construct a stress profile.

The DAG therefore places profile construction and cone algebra in separate nodes.

### 5. Oscillatory pulse covariance

Tracked by `G2_PULSE_COVARIANCE`.

Formal anchors include `PulseCovariance.lean`, `PartitionedCovariance.lean`, `SignedCovariance.lean`, and `ActualPrimaryCovariance.lean`.

The review obligation includes slot separation, covariance realization, cross-copy suppression and the signed-square bookkeeping that is intentionally not folded into the linear covariance identity.

### 6. Exact divergence-free curl realization

Tracked by `G2_DIVERGENCE_FREE_CURL`.

`CurlGeometry.lean` identifies its algebra with manuscript Lemma 8.8 and explicitly limits its own scope: principal-symbol and algebraic divergence cancellation only, not regularity, differentiated-amplitude bounds or descent from the lift.

That scope boundary becomes a Gate 3 checklist item rather than being silently treated as a finished construction.

### 7. Correction cycle

Tracked by `G2_CORRECTION_CYCLE`.

`ActualCandidateConstruction.lean` defines the actual recurrence using fixed cycle parameters and retains the carrier, coefficient, base-error and pressure-reconstruction structure through iteration.

Gate 3 must independently verify that every claimed improvement follows from the actual estimates rather than from the recurrence bookkeeping alone.

### 8. Residual flatness and summation

Tracked by `G2_RESIDUAL_FLATNESS`.

`JointResidualLimits.lean` and `PeriodicResidualLimits.lean` distinguish actual one-sided smooth extensions and joint jet vanishing from assumptions about an already-smooth terminal residual. This is one of the most important anti-circularity boundaries in the graph.

### 9. Spatial localization and smooth force

Tracked by `G2_LOCALIZATION` and the compact-candidate extraction node.

The obligation is to prove that cutoffs and periodization preserve the necessary local PDE identities while all derivative-generated cutoff terms are genuinely captured in the residual/force. For C, the second outer localization must additionally yield compact spatial force support and the comparator's rapid-decay class.

### 10. Bounded energy and dissipation

Tracked by `G2_ENERGY`.

The C route requires finite/uniformly bounded kinetic energy for the comparator target, while the whole-space uniqueness step also consumes finite-energy comparison inputs. These are kept independent of pointwise speed blowup.

### 11. Uniqueness and continuation

Tracked separately for C and D.

For C, `R3FiniteEnergyComparison.lean` uses the whole-space uniqueness development to force agreement with any hypothetical global finite-energy solution before the singular time.

For D, `MaximalLifespan.lean` states that its continuation argument uses proved periodic uniqueness and does not assume a general Navier-Stokes existence theorem.

### 12. Periodicization

Tracked by `G2_PERIODIZATION` and `G2_D_BRIDGE`.

The D path must retain the periodic velocity/pressure conditions already verified at Gate 1 and derive the comparator's all-order time decay for the force. Periodization is therefore a proof dependency, not a formatting operation.

## Source-anchor precision

Not every Gate 2 node claims an exact paper lemma number.

The registry records one of several anchor precisions:

- `exact_label` — e.g. Theorem 1.1 or Corollary 10.6;
- `exact_labels_from_formalization_comments` — e.g. Proposition 10.3 / sections 8.1 and 10.2;
- `exact_label_from_formalization_comment` — e.g. Lemma 8.8;
- `section_label_from_formalization_comments`;
- `section_family`;
- `programme_obligation` — an obligation explicitly required by the QSOL verification programme but not promoted here to a more precise paper citation.

This is intentional. Gate 2 records dependencies without inventing source precision that has not yet been independently reconstructed.

## What Gate 2 closes

Gate 2 closes the **dependency-indexing problem**:

- both C and D have explicit roots;
- all required construction/comparison classes are registered;
- every node has at least one formal-module anchor;
- every node lies on a rooted dependency path;
- the reviewed graph is fail-closed under CI.

It does **not** close the **correctness problem**.

The next phase is Gate 3: independently re-derive and attack the proof-critical nodes. The highest-risk starting points remain axis regularity, stress signs/cone margins, pulse support separation, curl/amplitude derivative control, residual-limit interchange, smooth force extension, and the exact uniqueness hypotheses.

## Hard nonclaims

```text
DEPENDENCY_GRAPH_COMPLETENESS != PROOF_VALIDITY
FORMAL_MODULE_ANCHOR != ANALYTIC_RECONSTRUCTION
PAPER_LABEL_OR_SECTION != VERIFIED_LEMMA
GRAPH_EDGE != PROVED_IMPLICATION
GATE2_PASS != LEAN_REPLAY
GATE2_PASS != INDEPENDENT_VERIFICATION_COMPLETE
C_AND_D_DEPENDENCY_PATHS_DO_NOT_RESOLVE_A_OR_B
GATE3_MUST_RECONSTRUCT_PROOF_CRITICAL_NODES_INDEPENDENTLY
```

C and D therefore remain **external claims pending independent verification**, and A/B remain unresolved.
