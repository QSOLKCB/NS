<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenAI 2026 formal declaration index — Gate 2 slice 1

## Purpose

PR #14 established a rooted **coarse** analytical dependency DAG for OpenAI's 2026 Navier–Stokes C/D claim, but deliberately left Gate 2 open. Twelve DAG parents still carry programme-level shorthand rather than an explicit lemma/proposition or formal-declaration dependency surface.

This document records the first refinement slice. It indexes the exact pinned Lean declarations for six endpoint, bridge, comparison, and candidate-extraction parents:

- `G2_C_BRIDGE`;
- `G2_D_BRIDGE`;
- `G2_WHOLE_SPACE_UNIQUENESS`;
- `G2_PERIODIC_MAX_LIFESPAN`;
- `G2_R3_COMPACT_CANDIDATE`;
- `G2_PERIODIC_CANDIDATE`.

The machine-readable manifest is `research/openai_2026_formal_index/manifest.json` and the six parent records live beside it.

## Frozen formal source

All declarations in this slice are indexed against the already frozen OpenAI formalization:

- repository: `openai/NavierStokesAndEuler`;
- commit: `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`;
- PR #14 merge baseline: `66206230bc8504dc57808468adac6f1b5ffd39b4`.

Twelve formal modules used by this slice are pinned by Git blob SHA in the manifest. A declaration name or module path is provenance, **not** independent proof acceptance.

## C endpoint and comparison spine

The C target is decomposed below the final comparator declaration rather than represented as one narrative bridge.

At the top, `NavierStokes.ComparatorBridge.navier_stokes_breakdown_R3` obtains the selected compact candidate and invokes `option_C_of_compact_candidate`. The bridge then depends on two distinct obligations:

1. force admissibility, through `CompactSpatialForceDecay.forceConditionDecay`;
2. exclusion of a hypothetical global finite-energy solution, through `compact_candidate_excludes_global_solution`.

The whole-space comparison surface is indexed separately. It includes `NavierStokesR3.WholeSpaceUniqueness.classical_uniqueness_on_Icc`, candidate-specialized comparison, conversion of the comparator's global energy bound to the finite-energy hypothesis, and the final contradiction with the compact candidate's unbounded speed.

The compact-candidate surface is also broken down: outer-cutoff smoothness/support, local transfer of divergence and the exact PDE, extraction through `of_periodic_local_model` / `of_localized_fields`, selected-witness binding, and the comparator force-decay theorem.

This is a declaration dependency index. It does not independently verify any uniqueness estimate, compact-support argument, limit, or PDE identity.

## D endpoint and continuation spine

The D target is indexed independently rather than inferred from the C route.

`NavierStokes.ComparatorBridge.navier_stokes_breakdown_periodic` obtains `ActualCandidateAssembly.selected_candidate` and invokes `option_D_of_candidate`. The bridge uses:

- `CandidateConsequences.futureJet_decay` to discharge the periodic force-decay requirement after viscosity rescaling;
- `MaximalLifespan.candidate_excludes_global_solution` for the continuation contradiction.

The lifespan surface is expanded through the candidate-as-classical-solution theorem, overlap agreement, exclusion of lifespans beyond one, maximality, equality of maximal lifespan to one, and the underlying periodic uniqueness theorem.

The periodic candidate surface separately indexes `ActualCandidateAssembly.witness`, `selected_witness`, `selected_candidate`, the candidate consequence bundle, and `MixedPeriodicAssembly.exists_candidate_force`.

Again, this records exact formal relationships in the pinned source. It does not establish that the source proofs are correct or that their statements match every manuscript intermediate claim.

## What is indexed in this slice

The manifest records:

- 6 of the 12 programme-obligation-bearing DAG parents;
- 42 parent-to-declaration bindings;
- 34 unique formal declarations;
- 30 selected direct body-reference edges between indexed declarations;
- 12 pinned formal modules.

The direct edges intentionally form only a selected local surface. They are **not** claimed to be the complete transitive import/theorem dependency graph.

## What remains inside Gate 2

Six construction-core parents still need the same formal-declaration refinement:

- `G2_LEADING_PROFILE`;
- `G2_ANNULAR_STRESS`;
- `G2_RESIDUAL_FLATNESS`;
- `G2_LOCALIZATION`;
- `G2_ENERGY`;
- `G2_PERIODIZATION`.

After that formal surface is indexed, Gate 2 still requires explicit paper lemma/proposition mapping and enough transitive dependency expansion to satisfy its governing pass condition: **no proof-critical dependency may remain only narrative shorthand or an untracked citation.**

Gate 3 therefore has **not** begun.

## Machine authority boundary

```text
FORMAL_DECLARATION_INDEX != PROOF_VALIDITY
FORMAL_DECLARATION_NAME != INDEPENDENT_RECONSTRUCTION
DIRECT_BODY_REFERENCE_EDGE != COMPLETE_TRANSITIVE_DEPENDENCY_GRAPH
FORMAL_SURFACE_COVERAGE != PAPER_LEMMA_MAPPING
FORMAL_INDEX_SLICE_1 != GATE2_PASS
GATE2_FORMAL_INDEX_SLICE != LEAN_REPLAY
GATE2_FORMAL_INDEX_SLICE != INDEPENDENT_VERIFICATION_COMPLETE
C_AND_D_REMAIN_EXTERNAL_CLAIMS_PENDING_INDEPENDENT_VERIFICATION
```

C and D remain external claims pending independent verification. A and B remain unresolved.
