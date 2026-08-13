<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Formal Verification Policy

Formal methods may be used to check algebraic lemmas, inequalities, finite-dimensional reductions, logical dependencies, definitions and proof obligations.

## Authority boundary

A proof assistant establishes that an encoded statement follows in the chosen formal system from the encoded assumptions and imported libraries. It does not automatically establish:

- that the encoding matches the official Clay formulation;
- that a numerical approximation equals the continuum PDE;
- that imported physical assumptions are true;
- that a theorem is novel;
- that a result applies outside its stated hypotheses.

## Required metadata for machine-checked results

- prover and exact version;
- dependency/lock identity;
- theorem fully qualified name;
- encoded statement;
- assumptions/axioms used;
- source commit;
- build command;
- successful CI/run identity when available;
- correspondence note linking the formal statement to repository prose.

## Proof-hole policy

No result may carry `proved_lemma` status if the relevant proof path contains admitted goals, placeholders, unchecked axioms introduced by the project, or an unrecorded external assumption.

## Correspondence rule

For any formal result promoted into a paper, maintain a human-readable correspondence statement explaining which mathematical proposition the formal object is intended to represent and what remains outside the formalization boundary.
