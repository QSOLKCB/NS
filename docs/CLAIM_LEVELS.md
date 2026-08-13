<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Claim Levels

Every research result must carry exactly one current claim level. Promotion is deliberate; no tool may silently promote a result.

## L0 — Exploratory

Unreproduced calculation, sketch, conjecture, visual anomaly, single numerical run, heuristic or incomplete derivation.

Permitted language: `suggests`, `candidate`, `exploratory`, `hypothesis`.

## L1 — Reproduced Numerical

A computational result reproduced under the experiment contract with source/environment identity, hashes, repeated runs where applicable, and sensitivity checks appropriate to the claim.

This level is still **not proof** of continuum behavior.

## L2 — Candidate Lemma

A precise mathematical proposition with explicit hypotheses and a plausible derivation, but with at least one unverified step, imported assumption, unresolved edge case or unchecked dependency.

## L3 — Proved Lemma

A complete proof is present and internally checked to the project's current standard. If machine-checked, the exact encoded statement, assumptions and axiom dependencies are recorded.

This status says nothing by itself about novelty.

## L4 — Externally Checked Theorem

A theorem-level result that has survived independent expert checking of both proof and statement, including known-prior-art comparison.

## L5 — Publication Candidate

A coherent manuscript-grade result with reproducible artifacts, explicit limitations, citations, authorship/provenance, and an adversarial review pass.

## L6 — Public Solution Claim

Reserved for a proposed solution of an official Clay formulation. Requires explicit human-operator authorization, an exact mapping to the official statement, complete proof, prior-art review, release provenance and independent mathematical scrutiny.

No AI agent, numerical pipeline or proof checker may automatically assign L6.

## Promotion invariants

```text
L1 != L3
L3 != L4
L4 != L6
FORMAL_CHECK != NOVELTY_CHECK
REPRODUCIBILITY != MATHEMATICAL_PROOF
```

Downgrades are always permitted when flaws are discovered and must preserve the reason in version history.
