<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Literature and Prior-Art Map

This file is a controlled intake map, not a claim that the literature has been exhaustively reconstructed.

## Machine registries

Phase 1 uses machine-readable registries so AI agents do not repeatedly reconstruct theorem boundaries from prose:

- `research/clay_target.json` — exact official A-D target and errata;
- `research/source_registry.json` — source identity and authority class;
- `research/theorem_registry.json` — source-checked known-result summaries with hypotheses and limitations;
- `research/proof_barriers.json` — invalid inference patterns and required bridge obligations;
- `research/baseline_identities.json` — analytic identities to become Phase 2 solver diagnostics.

All are validated by `tools/validate_boundary_map.py`.

## Source-authority policy

A source may have one of three authority classes:

1. `official_problem_statement` — controls the prize target;
2. `primary_research` — may authorize a theorem-registry entry;
3. `secondary_discovery` — may help locate or contextualize a result but may **not** authorize a theorem entry.

Secondary summaries, encyclopedia pages, lecture notes, AI-generated summaries and memory are useful discovery tools. They are not substitutes for checking the official or primary source before encoding hypotheses/conclusions.

## Initial source spine

The first boundary reconstruction deliberately begins with a conservative classical/critical spine:

- Fefferman / Clay Mathematics Institute — official A-D problem target;
- Leray (1934) — global weak existence;
- Serrin (1962) — conditional regularity;
- Fujita & Kato (1964) — local strong theory;
- Caffarelli, Kohn & Nirenberg (1982) — partial regularity;
- Kato (1984) — critical-space local and small-data theory;
- Necas, Ruzicka & Sverak (1996) — backward self-similar exclusion under stated hypotheses;
- Tsai (1998) — self-similar exclusion under local-energy/integrability hypotheses;
- Koch & Tataru (2001) — small-data global theory in `BMO^{-1}`;
- Escauriaza, Seregin & Sverak (2003) — endpoint `L^3` regularity/blow-up criterion.

Exact DOI/URL metadata is in `research/source_registry.json`.

## Buckets still to expand

Phase 1 is iterative. Future boundary PRs should expand, with primary-source checking:

1. weak solution existence and uniqueness/nonuniqueness landscape;
2. local strong/smooth existence across critical and subcritical spaces;
3. weak-strong uniqueness regimes;
4. partial regularity refinements;
5. continuation and regularity criteria beyond the initial Serrin/endpoint entries;
6. scaling-critical spaces and endpoint refinements;
7. vorticity direction/geometric depletion criteria;
8. self-similar, discretely self-similar and asymptotically self-similar scenarios;
9. concentration/compactness and blow-up exclusion;
10. quantitative bounds and supercritical obstacles;
11. computational singularity diagnostics;
12. rigorous numerics/computer-assisted proof methods for PDEs;
13. related or modified Navier-Stokes systems, segregated from the canonical target.

## Intake record for each source

Before a source becomes theorem authority, record:

- stable `source_id`;
- full citation;
- DOI and/or publisher/author URL;
- authority class;
- theorem/result used;
- exact hypotheses relevant to the registry summary;
- exact conclusion relevant to the registry summary;
- relation to an official A-D formulation;
- limitations and known errata;
- whether it blocks, supports or merely resembles a current research direction.

## Theorem registry rule

A theorem entry is a **boundary summary**, not a replacement for the paper. It must state hypotheses and limitations strongly enough to prevent common upgrades such as:

```text
WEAK -> SMOOTH
LOCAL -> GLOBAL
SMALL_DATA -> ARBITRARY_DATA
CONDITIONAL -> UNCONDITIONAL
PARTIAL_REGULARITY -> NO_SINGULARITIES
SPECIAL_ANSATZ -> ALL_SOLUTIONS
R3 -> PERIODIC
NUMERICAL -> CONTINUUM_PROOF
```

## Novelty rule

Do not use `new`, `novel`, `first`, `previously unknown` or equivalent language until the nearest known results have been identified and compared at the level of hypotheses and conclusion, and the relevant machine registries have been updated.

A derivation that reconstructs a known theorem can still be scientifically useful. It must be labelled reconstruction rather than novelty.
