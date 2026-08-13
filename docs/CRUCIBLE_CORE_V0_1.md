<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Crucible Core v0.1

## Purpose

Crucible Core is a domain-neutral orchestration layer for difficult research problems in which many plausible hypotheses can be generated but only a small fraction should survive adversarial testing.

The core manages competing hypotheses, candidate lineage, evidence provenance, domain-supplied constraint results, sealed holdout access, append-only failure memory, and the current survivor frontier. It deliberately does **not** decide what is true.

## Central boundary

```text
CRUCIBLE_CORE != DOMAIN_TRUTH_AUTHORITY
SURVIVAL != PROOF
FAILURE_OF_ONE_CANDIDATE != PROOF_OF_A_COMPETITOR
HOLDOUT_SUCCESS != UNIQUE_EXPLANATION
NARRATIVE_PLAUSIBILITY != EVIDENTIARY_STATUS
```

The domain adapter owns the epistemic standard. In this repository the NS adapter retains the exact Clay target, theorem boundary, proof barriers, numerical evidence ceiling and claim ladder.

## Candidate lifecycle

```text
generate -> formalize -> constrain -> falsify -> record failure -> refine -> domain-owned promotion
```

The core can freeze, reject and remember candidates according to domain-declared hard constraints. It cannot promote a mathematical claim or choose a winning theory.

## Competing hypotheses

Hypothesis sets are first-class records. They begin unresolved and contain no preferred candidate. For NS the first set contains the global-regularity and finite-time-breakdown tracks. The architecture does not treat either as the default truth.

A failed candidate is removed from the current frontier only when a domain-declared **hard** constraint fails and an append-only failure record is supplied. Eliminating one candidate does not automatically establish any competitor.

## Failure ledger

Hard failures must preserve candidate identity, failed constraint, failure class, evidence references, claim level before and after, a reusable lesson, and who recorded the failure.

This turns negative results into search-space information. ML systems can later avoid regenerating families that repeatedly die for the same reason while retaining the historical evidence for why they died.

## Holdout gate

The core distinguishes `training`, `development`, and `holdout` evidence. Holdout evidence may not be attached until a candidate is frozen. This prevents a generator from repeatedly rewriting a hypothesis around supposedly unseen evidence.

Holdout success never promotes a claim automatically. Some domains may not use holdouts as an epistemic requirement at all.

## No universal score

Crucible Core deliberately exposes no universal probability-of-truth or confidence score. Different domains require different standards: mathematical proof, predictive validation, archaeological correspondence, experimental replication, or something else. Flattening those into one number would destroy the boundary the Crucible is intended to preserve.

## Machine authority

The exact v0.1 contract is locked by `research/crucible_contract.json`, the Crucible schemas under `research/schemas/`, and `tools/validate_crucible_core.py`. The implementation is under `src/crucible_core/`.

## Future domains

NS is the first domain adapter, not the definition of the core. A future historical-script adapter could bind artifact provenance, sign inventories, positional constraints, competing language hypotheses and sealed inscriptions while defining its own rules for what counts as a validated decipherment. The Crucible would provide workflow and failure memory; it would not import the NS notion of mathematical proof into that domain.
