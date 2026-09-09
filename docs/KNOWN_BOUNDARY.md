<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Known Boundary Reconstruction

This document is a human-readable view of the machine registries under `research/`. The machine-readable files are authoritative for automated checks; this prose is explanatory.

## Official target: four admissible routes

Charles L. Fefferman's official Clay Mathematics Institute problem description asks for a proof of at least one of four formulations:

- **A — global smoothness on `R^3`:** every admissible smooth, divergence-free, rapidly decaying initial datum has a global smooth solution for `f = 0`, with bounded energy.
- **B — global smoothness on `R^3/Z^3`:** every admissible smooth, divergence-free periodic initial datum has a global smooth periodic solution for `f = 0`.
- **C — breakdown on `R^3`:** there exist admissible smooth data and admissible smooth forcing for which no global physically reasonable smooth bounded-energy solution exists.
- **D — breakdown on `R^3/Z^3`:** there exist admissible smooth periodic data and forcing for which no global smooth periodic solution exists.

The official PDF also carries errata. In particular, the periodic formulation must include periodicity of the pressure. The repository records these details in `research/clay_target.json` rather than relying on a folk-summary of the problem.

## September 2026 external C/D claim — independent verification pending

On 2026-09-08 OpenAI published *Finite time blowup for Navier-Stokes* and an accompanying Lean 4 repository. The paper's Theorem 1.1 constructs, for every positive viscosity, a smooth compactly supported force and a solution starting from zero velocity whose kinetic energy remains uniformly bounded while its velocity becomes unbounded in finite time. The paper explicitly states that this establishes Fefferman alternative **C**. It further states that compact support yields the corresponding periodic construction and identifies Corollary 10.6 with alternative **D**.

The accompanying pinned Lean artifact likewise describes its two Navier-Stokes main results as alternatives C and D. Its upstream metadata reports zero `sorry` declarations for those results and labels its review status `self-assessed`.

QSOL NS therefore records the event with the following exact boundary:

- **A:** not addressed by the OpenAI 2026 construction; still unresolved in this repository.
- **B:** not addressed by the OpenAI 2026 construction; still unresolved in this repository.
- **C:** explicitly claimed by OpenAI; **external claim pending QSOL independent verification**.
- **D:** explicitly claimed by OpenAI; **external claim pending QSOL independent verification**.

This distinction is forced by the official forcing quantifiers. A and B require `f = 0`. C and D permit suitable smooth forcing. A valid C or D proof would satisfy an official route to the Millennium problem while leaving the mathematically separate unforced A/B questions untouched.

The new primary sources live in `research/source_registry.json`; the exact A-D intake state lives in `research/external_claim_registry.json`. The source-checked historical `research/theorem_registry.json` is intentionally unchanged until a separate audited promotion decision is justified. See `docs/OPENAI_2026_INDEPENDENT_VERIFICATION.md` for the verification programme.

## What is already known

### Global weak solutions exist

Leray's classical theory supplies global weak solutions in three dimensions. That is foundational, but it does **not** establish the global smooth solution required by formulations A or B, nor general uniqueness of weak solutions.

### Strong solutions exist locally

Fujita-Kato-type theory gives local strong solutions in appropriate function spaces. Thus the central difficulty is not whether sufficiently regular solutions can begin evolving; it is whether the required regularity can be controlled for all future time or must fail for some admissible data.

### Conditional regularity criteria identify dangerous norms

Serrin-type criteria show that additional mixed space-time integrability prevents singular behavior. Escauriaza-Seregin-Sverak provide a critical endpoint `L^3` result: remaining uniformly controlled in the relevant spatial `L^3` norm up to a candidate singular time rules out that singularity.

These are conditional results. The missing step is an unconditional a priori estimate that forces the qualifying norm to remain controlled for every datum in a global-regularity formulation, or a rigorous construction showing the necessary control must fail in a breakdown formulation.

### Singularities of suitable weak solutions are strongly restricted

Caffarelli-Kohn-Nirenberg partial regularity makes the possible singular set very small in parabolic Hausdorff dimension/measure. A very small possible singular set is not the same thing as an empty singular set.

### Small critical data are globally controlled

Kato and Koch-Tataru establish strong critical-space results, including global well-posedness for sufficiently small critical data in their respective frameworks. These results isolate the hard regime: arbitrary large admissible data.

### Important self-similar blow-up scenarios are excluded

Necas-Ruzicka-Sverak and Tsai exclude important classes of backward self-similar singular profiles under their stated integrability/local-energy hypotheses. This removes specific candidate mechanisms; it does not prove that every possible singularity must be self-similar.

## Five questions for every future idea

Before a candidate argument advances beyond exploration, ask:

1. **Which exact Clay formulation does it address: A, B, C or D?**
2. **Does it preserve the exact domain, forcing quantifier, data class and solution concept?**
3. **Does it assume a regularity/norm bound that is actually the thing needing proof?**
4. **Is the conclusion already a known conditional/small-data/special-ansatz theorem?**
5. **What explicit bridge closes any gap between computation, a modified model, formal encoding or special family and the canonical continuum PDE?**

If those questions do not have explicit answers, the claim remains exploratory.

## Initial theorem spine

The initial machine registry includes source-checked summaries of:

- Leray (1934): global weak existence;
- Serrin (1962): conditional regularity;
- Fujita & Kato (1964): local strong theory;
- Caffarelli, Kohn & Nirenberg (1982): partial regularity;
- Kato (1984): critical `L^3`-based local/small-data theory;
- Necas, Ruzicka & Sverak (1996): exclusion of classical backward self-similar profiles under stated hypotheses;
- Tsai (1998): self-similar exclusion under local-energy/integrability hypotheses;
- Koch & Tataru (2001): small-data global well-posedness in `BMO^{-1}`;
- Escauriaza, Seregin & Sverak (2003): endpoint `L^3` regularity/blow-up criterion.

See `research/source_registry.json` and `research/theorem_registry.json` for exact source IDs, DOI records, limitations and machine status. Externally published solution claims are intentionally tracked separately in `research/external_claim_registry.json` until an audited promotion is warranted.

## Status and incompleteness

This is an intentionally conservative **initial boundary map**, not a claim that the Navier-Stokes literature has been exhaustively reconstructed. Future Phase 1 PRs may add additional continuation criteria, geometric depletion results, concentration/compactness arguments, discretely/asymptotically self-similar exclusions, computer-assisted PDE methods and newer results.

A missing paper from this registry does not imply that its theorem is unknown. Conversely, an entry may not be strengthened beyond its recorded hypotheses without a new proof and source audit.
