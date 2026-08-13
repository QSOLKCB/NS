<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# NS Cross-Domain Transfer Adapter v0.1

The NS transfer adapter is the target-domain half of the Analogy Firewall.

`research/cross_domain_transfer_registry.json` may describe an interesting relationship, but only `research/ns_cross_domain_transfer_adapter.json` determines whether that relationship may seed an NS candidate and what must happen next.

## Intake rule

Eligible classes:

```text
exact_correspondence
operator_correspondence
structural_analogy
heuristic_analogy
```

Blocked as positive transfers:

```text
visual_resemblance
explicit_non_correspondence
```

Every accepted transfer starts at:

```text
claim_level = exploratory
```

There is no inheritance of a source theorem, source proof status or source evidence level.

## Revalidation

An analogy-derived NS candidate enters the same Crucible as any other candidate.

It must still face:

- the exact Clay A-D target and domain/forcing quantifiers;
- the theorem registry and prior-art boundary;
- every registered proof barrier;
- numerical evidence ceilings;
- formal correspondence requirements;
- human/publication gates.

A source-domain theorem cannot discharge an NS proof barrier merely because a shared operator or structure was identified.

## Why this matters

Cross-domain ML search is valuable precisely because it can notice structures humans may not have tried. The danger is that a model can turn a suggestive analogy into a persuasive narrative and then quietly count that narrative as evidence.

The adapter prevents that authority escalation while retaining the creative search benefit.
