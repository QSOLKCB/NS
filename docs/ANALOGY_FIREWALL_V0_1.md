<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Analogy Firewall & Cross-Domain Transfer Registry v0.1

## Purpose

The Analogy Firewall lets Crucible use cross-domain resemblance as a **candidate-generation aid** without laundering resemblance into target-domain evidence.

The constitutional boundary is:

```text
VISUAL_RESEMBLANCE != PHYSICAL_MECHANISM
SHARED_OPERATOR != SHARED_DYNAMICS
STRUCTURAL_ANALOGY != DOMAIN_EQUIVALENCE
ANALOGY != DOMAIN_EVIDENCE
ANALOGY_CANNOT_PROMOTE_CLAIM
CROSS_DOMAIN_TRANSFER_REQUIRES_TARGET_DOMAIN_VALIDATION
```

The firewall is intentionally permissive about *ideas* and strict about *authority*.

## Mapping classes

Every registry record is assigned exactly one class:

1. `exact_correspondence` — a declared exact/formal correspondence under explicit assumptions;
2. `operator_correspondence` — a mathematical operator/form is shared;
3. `structural_analogy` — architecture or relationships resemble one another;
4. `heuristic_analogy` — useful prompt for exploration without stronger correspondence;
5. `visual_resemblance` — appearance only;
6. `explicit_non_correspondence` — a recorded negative control.

The first four may seed exploratory candidates. The final two are negative-control-only.

Even `exact_correspondence` does not automatically establish domain equivalence: the target adapter still owns evidentiary and theorem correspondence.

## Authority firewall

An analogy may:

- seed a schema-valid exploratory candidate;
- preserve a provenance-bearing record of why the idea was considered;
- act as a negative control when the registry says it is only resemblance/non-correspondence.

An analogy may **not**:

- become target-domain evidence merely by registration;
- raise a claim level;
- satisfy a proof barrier;
- select a winning hypothesis;
- inherit source-domain theorem/proof status;
- inherit source-domain evidence status;
- assert whole-domain equivalence.

## Source material

The initial registry was derived from a user-supplied technical reference named `pr6.md`, SHA-256:

`2bb9bc6f44af2dda571c70cc925196b29e02fc14cc50aef84fc69fc41c761042`

The registry labels this source as `design_input_not_domain_authority`.

Its initial examples distinguish optical/display effects from physical fluid flow and propose several stochastic/generative-model-to-fluid mathematical analogies. PR #6 does not promote those proposed analogies to established scientific facts. Instead, it records the relationship class, assumptions, known differences, allowed uses and forbidden inferences so later ML search cannot silently strengthen them.

## NS intake

`research/ns_cross_domain_transfer_adapter.json` binds the firewall to the existing NS Crucible domain.

For NS:

- every analogy-derived candidate starts at `exploratory`;
- analogy provenance must remain attached to candidate generation;
- all registered NS proof barriers reapply;
- Clay domain/forcing/formulation correspondence remains mandatory;
- theorem/prior-art checks remain mandatory before novelty language;
- analogy records are not attachable as NS evidence merely because they exist in the transfer registry.

The initial NS-eligible examples are operator/heuristic prompts around diffusion/Laplacian structure, score/vector fields and conservation-style structure. They are candidate generators only.

## Machine authority

Canonical machine files:

- `research/analogy_firewall_contract.json`;
- `research/cross_domain_transfer_registry.json`;
- `research/ns_cross_domain_transfer_adapter.json`;
- `research/schemas/analogy_*.schema.json`;
- `research/schemas/cross_domain_transfer_registry.schema.json`;
- `research/schemas/ns_cross_domain_transfer_adapter.schema.json`;
- `tools/validate_analogy_firewall.py`.

Implementation:

- `src/crucible_core/analogy.py`.

## ML use

The intended ML flow is:

```text
external structure
  -> classified analogy record
  -> firewall authority check
  -> exploratory candidate
  -> target-domain Crucible
  -> target theorem/proof barriers/evaluators
  -> failure ledger or surviving candidate
```

The firewall expands the search frontier without expanding evidentiary authority.

## Nonclaim

PR #6 is research infrastructure. It establishes no Navier-Stokes theorem, no singularity mechanism, no regularity mechanism, no physical equivalence between fluids and generative AI, and no solution claim.
