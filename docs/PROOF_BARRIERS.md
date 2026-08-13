<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Proof Barriers and Invalid Inference Patterns

This document is the human-readable companion to `research/proof_barriers.json`.

A registered barrier is **not** a theorem that a research direction is impossible. It is a proof obligation: if an argument crosses the barrier, it must provide a rigorous bridge or weaken its conclusion.

## Registered barriers

1. **Weak existence is not smoothness.** A global Leray weak solution is not automatically a global smooth Clay A/B solution.
2. **A conditional criterion is not an a priori bound.** Serrin/endpoint criteria identify sufficient regularity control; they do not automatically provide that control for arbitrary data.
3. **Partial regularity is not an empty singular set.** CKN restricts the possible singular set but does not prove it is empty.
4. **Self-similar exclusion is not general no-blow-up.** Excluding one similarity class leaves other concentration mechanisms logically available.
5. **Small-data global theory is not arbitrary-data global theory.** A smallness hypothesis cannot disappear during the conclusion.
6. **`R^3` is not the periodic domain.** Results do not silently transfer between the two official geometries.
7. **Forcing quantifiers matter.** Clay A/B are unforced; C/D permit admissible forcing and use existential rather than universal breakdown quantifiers.
8. **A modified equation is not canonical Navier-Stokes.** Hyperviscosity, regularization, truncation, discretization and averaging require a rigorous transfer theorem.
9. **Numerics do not automatically cross the discrete-continuum gap.** Resolution convergence alone is not a proof of continuum singularity or smoothness.
10. **Circular regularity is forbidden.** An estimate cannot assume the regularity/norm finiteness it is intended to establish.
11. **Limit interchanges require hypotheses.** Compactness, domination, uniformity and convergence must be proved where used.
12. **Formal verification checks the encoding.** Correspondence between a proof-assistant object and the official PDE remains an explicit obligation.
13. **A special family cannot inherit a universal quantifier.** A result for an ansatz, symmetry class or finite-dimensional family is not an all-data theorem without a universal reduction theorem.

## Required response rule

For every barrier encountered, a promoted argument must do one of two things:

```text
PROVE_BRIDGE_THEOREM
OR
WEAKEN_CLAIM_TO_ACTUAL_SCOPE
```

Silence is not a third option.

## Adversarial use

Agents and reviewers should actively try to match a proposed proof step against the barrier registry. The registry is especially important when an argument looks surprisingly short: Millennium-scale problems often hide the unresolved difficulty in a change of solution concept, quantifier, domain, limit, norm or regularity assumption.
