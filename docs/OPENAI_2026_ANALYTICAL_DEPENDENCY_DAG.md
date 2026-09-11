<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenAI 2026 analytical dependency DAG — Phase 3A Gate 2

## Purpose

This document records the current Gate 2 / WP2 dependency index for QSOL's independent review of OpenAI's 2026 *Finite time blowup for Navier-Stokes* claim.

Gate 1 established only that the pinned final C/D statements line up with Fefferman alternatives C and D. Gate 2 asks a different question:

> What proof-critical construction and comparison obligations must all survive before those final statements can be accepted?

The machine-readable answer is `research/openai_2026_dependency_dag.json`.

**Gate 2 remains open.** The current graph is a coarse rooted dependency index, not yet the lemma/proposition-level graph required by the governing pass condition. Twelve of the twenty current nodes still carry programme-obligation content: ten use `programme_obligation` directly, while `G2_D_BRIDGE` and `G2_PERIODIZATION` use `exact_label_plus_programme_obligation`. Several also aggregate multiple formal modules into a single obligation. Those aggregates must be expanded before `gate_status` may become complete.

The graph is also **not a proof**. Every node remains `indexed_not_reconstructed`; local correctness belongs to Gate 3 only after Gate 2's indexing pass condition is actually met.

## Frozen source surface

The graph inherits the paper and Lean pins established by PRs #12–#13:

- analytical PDF SHA-256: `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`;
- Lean repository: `openai/NavierStokesAndEuler`;
- pinned Lean commit: `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`;
- PR #13 merge baseline: `52fcdb1b4ec0eb561fd80e3dbdfab3f0e87465cf`.

Gate 2 additionally pins sixteen high-value formal modules whose comments and import structure expose the candidate/bridge spine. A formal module path is an **anchor**, not an assertion that its proof has been independently checked and not a substitute for indexing the theorem/lemma dependencies inside that module.

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
- the reviewed node and edge semantics remain fail-closed;
- lemma-level indexing remains explicitly false while programme-obligation-bearing anchors remain;
- Gate 2's pass condition remains false until those dependencies are expanded.

## C path

The current coarse C branch is:

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

The pinned OpenAI bridge `ComparatorR3Theorem.lean` separates candidate construction from comparison/non-existence. Gate 2 still has to descend the aggregate construction and uniqueness nodes into their proof-critical lemmas/propositions before this branch is considered fully indexed.

## D path

The current coarse D branch is:

```text
Corollary 10.6 / D target
  -> periodic candidate-to-D bridge
     -> periodic candidate
        -> periodicization and force decay
        -> literal candidate assembly
     -> periodic uniqueness / maximal lifespan
        -> periodic candidate
```

`ComparatorTheorem.lean` uses the selected periodic candidate, viscosity rescaling and maximal-lifespan exclusion. `CandidateConsequences.lean` separately derives future-jet decay from smoothness, periodicity and compact future-time support. These remain distinct dependencies, but their lemma-level internal dependencies are not yet fully indexed here.

## Shared construction spine

The current graph registers all twelve dependency classes required by the verification programme. This is **coverage**, not completion.

### 1. Concentrating axisymmetric leading profile

Tracked by `G2_LEADING_PROFILE` with formal anchors including `FinalSlowBase.lean`, `PreparedOutgoing.lean`, and `ReferenceBounds.lean`.

### 2. Self-similar scaling and velocity growth

Tracked by `G2_SCALING`. `ExponentLedger.lean` explicitly checks exponent arithmetic conditional on the analytic estimates being valid; arithmetic consistency is not the estimate itself.

### 3. Annular residual stress

Tracked by `G2_ANNULAR_STRESS`. It defines the stress target that later covariance construction is intended to realize.

### 4. Admissible stress cone

Tracked by `G2_STRESS_CONE`. `ConeAlgebra.lean` identifies the square-root criterion with manuscript Lemma 3.5 and equation (11), while explicitly not constructing the stress profile.

### 5. Oscillatory pulse covariance

Tracked by `G2_PULSE_COVARIANCE`. Because covariance realizes the previously defined residual-stress target, the dependency direction is:

```text
G2_PULSE_COVARIANCE depends on G2_ANNULAR_STRESS
```

not the reverse. The pulse node also depends on the stress-cone constraints used to make the realization admissible.

### 6. Exact divergence-free curl realization

Tracked by `G2_DIVERGENCE_FREE_CURL`. `CurlGeometry.lean` covers principal-symbol identities and algebraic divergence cancellation, not the full regularity/descent estimates.

### 7. Correction cycle

Tracked by `G2_CORRECTION_CYCLE`. The current node aggregates the actual recurrence, parameter choice and iteration ledger; Gate 2 still has to expose the proof-critical internal steps explicitly.

### 8. Residual flatness and summation

Tracked by `G2_RESIDUAL_FLATNESS`. `JointResidualLimits.lean` and `PeriodicResidualLimits.lean` distinguish genuine one-sided extensions and joint jet vanishing from assuming an already-smooth terminal residual.

### 9. Spatial localization and smooth force

Tracked by `G2_LOCALIZATION` and the compact-candidate extraction node. The current aggregate must still be decomposed into the cutoff/locality/support/force-extension lemmas that actually discharge this obligation.

### 10. Bounded energy and dissipation

Tracked by `G2_ENERGY`. The C route requires finite/uniform kinetic energy independently of pointwise speed blowup.

### 11. Uniqueness and continuation

Tracked separately for C and D through whole-space finite-energy comparison and periodic maximal lifespan. These comparison nodes remain coarse until their internal uniqueness/continuation hypotheses and dependencies are indexed explicitly.

### 12. Periodicization

Tracked by `G2_PERIODIZATION` and `G2_D_BRIDGE`. Periodic velocity, periodic pressure, force decay and the final comparator bridge remain separate obligations.

## Source-anchor precision

The registry distinguishes:

- `exact_label`;
- `exact_labels_from_formalization_comments`;
- `exact_label_from_formalization_comment`;
- `section_label_from_formalization_comments`;
- `section_family`;
- `exact_label_plus_programme_obligation`;
- `programme_obligation`.

Both `programme_obligation` and `exact_label_plus_programme_obligation` mean unresolved programme-level proof work remains. The hybrid form preserves an exact source label while still recording an unexpanded programme obligation. There are currently twelve programme-obligation-bearing nodes in total. Their presence is a machine-readable reason Gate 2 cannot pass.

## Current Gate 2 status

The current machine status is:

```text
analytical_dependency_graph_partial
```

What this PR establishes:

- C and D roots exist;
- all twelve required dependency classes are represented;
- the current graph is rooted and acyclic;
- high-value formal modules are pinned;
- aggregate obligations and their provenance are explicit;
- the reviewed coarse graph is fail-closed under CI.

What remains before Gate 2 can pass:

1. expand every programme-obligation-bearing node into explicit paper/formal lemma or proposition dependencies where the source supports that precision;
2. split aggregate multi-module obligations into proof-critical child nodes and edges;
3. ensure no proof-critical dependency remains only narrative shorthand or an untracked citation;
4. update the audited graph lock and only then set `lemma_level_dependency_indexing_complete = true` and the Gate 2 pass condition to true.

Only after those conditions are met may the programme advance to Gate 3 local proof reconstruction.

## Hard nonclaims

```text
DEPENDENCY_CLASS_COVERAGE != GATE2_COMPLETION
PROGRAMME_OBLIGATION_ANCHOR != EXPLICIT_LEMMA_PROPOSITION_INDEX
FORMAL_MODULE_ANCHOR != ANALYTIC_RECONSTRUCTION
PAPER_LABEL_OR_SECTION != VERIFIED_LEMMA
GRAPH_EDGE != PROVED_IMPLICATION
GATE2_PARTIAL != GATE2_PASS
GATE2_PARTIAL != LEAN_REPLAY
GATE2_PARTIAL != INDEPENDENT_VERIFICATION_COMPLETE
C_AND_D_DEPENDENCY_PATHS_DO_NOT_RESOLVE_A_OR_B
```

C and D therefore remain **external claims pending independent verification**, and A/B remain unresolved.
