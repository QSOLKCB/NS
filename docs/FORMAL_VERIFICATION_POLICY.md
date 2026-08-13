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

## Canonical formal-artifact metadata

`AGENTS.md` → `proof_requirements.formal_artifact_required_fields` is the canonical machine-readable definition.

Every machine-checked result promoted to `proved_lemma` or above must record:

- `prover`
- `prover_version`
- `dependency_lock_identity`
- `theorem_fully_qualified_name`
- `encoded_statement`
- `assumptions_and_axioms_used`
- `source_commit`
- `build_command`
- `successful_ci_or_run_identity_or_null`
- `correspondence_note`

If CI or a comparable run identity is unavailable, `successful_ci_or_run_identity_or_null` must be recorded explicitly as `null`; the field itself may not be omitted.

## Proof-hole policy

No result may carry `proved_lemma` status if the relevant proof path contains admitted goals, placeholders, unchecked axioms introduced by the project, or an unrecorded external assumption.

## Correspondence rule

For any formal result promoted into a paper, maintain a human-readable correspondence statement explaining which mathematical proposition the formal object is intended to represent and what remains outside the formalization boundary.
