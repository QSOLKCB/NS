<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenAI 2026 Navier–Stokes independent verification programme

## Purpose

On 2026-09-08 OpenAI published *Finite time blowup for Navier-Stokes* together with a Lean 4 formalization. The paper states that its whole-space theorem establishes Fefferman alternative **C** and that its compactly supported construction yields the periodic alternative **D**. QSOL NS treats this as a major external primary-source claim that deserves priority independent verification.

This programme does **not** convert publication, a successful Lean build, a source-authored statement of success, numerical resemblance, or model consensus into a QSOL solution claim.

The pre-intake QSOL state is frozen at commit `504180162eb117bc3eb280b93c8ef4df845c0d27` and preserved on `archive/pre-openai-ns-2026-09-08`.

## Exact intake artifacts

### Analytical paper

- Source ID: `OPENAI_NS_BLOWUP_2026`
- Title: *Finite time blowup for Navier-Stokes*
- Author: OpenAI
- Published: 2026-09-08
- Intake PDF SHA-256: `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`

Theorem 1.1 states, for every positive viscosity, the existence of a smooth compactly supported force and smooth velocity/pressure fields on `R^3 x [0,1)` starting from zero velocity, with uniformly bounded kinetic energy and unbounded `L-infinity` velocity as the singular time is approached. The paper then states that this establishes Fefferman alternative C and that compact support gives the corresponding periodic D construction through Corollary 10.6.

### Lean formalization

- Source ID: `OPENAI_NS_LEAN_2026`
- Repository: `openai/NavierStokesAndEuler`
- Pinned intake commit: `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`
- Upstream toolchain: Lean `4.34.0-rc2`
- Upstream metadata reports `sorry_count: 0` for the formalization as a whole and for the C/D declarations.
- Upstream review status in `formalization.yaml`: `self-assessed`.

The upstream metadata aligns Theorem 1.1 with `NavierStokes.Comparator.navier_stokes_breakdown_R3` and Corollary 10.6 with `NavierStokes.Comparator.navier_stokes_breakdown_periodic`.

These metadata are facts about the upstream artifact. QSOL must independently replay and audit them.

## A/B versus C/D status

The four Clay alternatives remain distinct.

| Clay formulation | Forcing requirement | OpenAI 2026 source position | QSOL intake status |
|---|---|---|---|
| A — global smoothness on `R^3` | `f = 0` required | not claimed | unresolved |
| B — global smoothness on `R^3/Z^3` | `f = 0` required | not claimed | unresolved |
| C — breakdown on `R^3` | smooth forcing permitted | explicitly claimed | external claim pending independent verification |
| D — breakdown on `R^3/Z^3` | smooth periodic forcing permitted | explicitly claimed | external claim pending independent verification |

A forced C/D construction must not be described as resolving the unforced A/B question. Conversely, if a valid proof of C or D survives scrutiny, it would satisfy one of the official admissible routes in Fefferman's Millennium problem statement even though A/B remain mathematically separate questions.

The machine-readable version of this table is `research/external_claim_registry.json`.

## Verification gates

### Gate 0 — preserve provenance and freeze intake

- [x] preserve the pre-intake QSOL commit and named archive branch;
- [x] register the exact paper and pinned Lean source;
- [x] record the exact reviewed PDF digest;
- [x] keep the historical theorem registry unchanged;
- [x] create a machine-validated external-claim boundary.

**Pass condition:** future work cannot rewrite the pre-event state or silently promote the external claim.

### Gate 1 — exact Clay statement correspondence

**Implementation status:** complete in PR #13. See `research/openai_2026_correspondence.json` and `docs/OPENAI_2026_CD_CORRESPONDENCE.md`.

For C and D, reconstruct a field-by-field correspondence between the source theorem/corollary and Fefferman's assumptions and conclusion:

- domain;
- viscosity quantifier;
- initial-data regularity, divergence-free condition and decay/periodicity;
- forcing regularity and decay/periodicity;
- pressure conditions, including the periodic-pressure erratum;
- solution regularity interval;
- bounded-energy requirement for C;
- exact non-existence/breakdown conclusion.

**Pass condition:** every hypothesis and conclusion required by C/D is accounted for without strengthening, weakening or changing quantifiers.

### Gate 2 — analytical dependency graph

**Implementation status:** complete in PR #14 at the dependency-indexing level. See `research/openai_2026_dependency_dag.json` and `docs/OPENAI_2026_ANALYTICAL_DEPENDENCY_DAG.md`.

Build a dependency graph from Theorem 1.1 and Corollary 10.6 down to the construction lemmas and propositions. At minimum the audit must isolate:

1. the concentrating axisymmetric leading profile;
2. the self-similar radial/axial scales and velocity growth;
3. construction and support of the annular residual stress;
4. the admissible stress-cone argument;
5. the two oscillatory pulse families and their covariance realization;
6. exact divergence-free curl construction;
7. the correction cycle and improving residual exponent;
8. summation with shrinking cutoffs and infinite-order residual flatness;
9. spatial localization and smooth compact forcing;
10. bounded energy/integrated dissipation;
11. the uniqueness/continuation argument converting the constructed blowup into the stated non-existence result;
12. the periodicization step used for D.

**Pass condition:** there is no proof-critical dependency represented only by narrative shorthand or an untracked citation.

Gate 2 completion means the proof-critical spine is explicitly rooted, typed, pinned and fail-closed under CI. It does **not** mean that any local estimate, construction lemma, limit interchange or uniqueness hypothesis has been independently proved by QSOL. Those are Gate 3 obligations.

### Gate 3 — local proof reconstruction

For every proof-critical node, independently reproduce the algebraic identities, scaling exponents, support arguments, regularity statements, integral constraints and limiting estimates. Reconstruction should prefer small independently checkable lemmas rather than paraphrasing the paper.

High-risk checkpoints include:

- smooth Cartesian regularity at the cylindrical axis;
- preservation of incompressibility after every cutoff/curl operation;
- sign and orientation conventions in the stress divergence;
- positivity and edge behavior of the stress-cone representation;
- support separation of oscillatory families;
- control of chain-rule terms from the auxiliary torus phase map;
- uniform derivative losses in the correction/summation arguments;
- interchange of limits, differentiation and integration near the singular time;
- smooth extension of the residual force through the singular time;
- the exact hypotheses of the final weak/strong uniqueness step.

**Pass condition:** each critical estimate can be re-derived without importing the desired conclusion.

### Gate 4 — independent Lean replay

From the pinned commit:

```sh
lake exe cache get
lake build
```

Record:

- Lean version and platform;
- dependency revisions from `lake-manifest.json`;
- build command and exit status;
- build log hash;
- resulting source-tree hash/commit;
- declarations checked;
- any warnings or environment deviations.

Then run the upstream Comparator challenge workflow according to its pinned instructions rather than merely trusting the source repository's own declaration names.

**Pass condition:** the pinned artifact builds from a clean environment and the independent comparator path succeeds with reproducible receipts.

### Gate 5 — prose ↔ formal statement alignment

A compiling formal proof proves the encoded theorem, not automatically the prose theorem or the Clay statement. Audit three correspondences separately:

```text
Fefferman C/D
    ↕
OpenAI Theorem 1.1 / Corollary 10.6
    ↕
Lean comparator declarations
```

Check definitions of smoothness, forcing, periodicity, energy, global solution, pressure, domain representation and every imported helper used by the final declarations.

**Pass condition:** the Lean theorem is extensionally strong enough to imply the exact source theorem and the exact Clay alternative being claimed.

### Gate 6 — formal proof dependency audit

Inspect the Lean dependency graph and trusted base:

- confirm reported `sorry_count` independently;
- enumerate axioms used by the final C/D declarations;
- identify opaque/native/external computation paths if any;
- verify that comparator reference statements are independent of the submitted proof root in the intended sense;
- inspect definitions or helper lemmas capable of trivializing the target through inconsistent assumptions;
- pin every dependency revision.

**Pass condition:** no hidden assumption, admitted theorem, circular import or statement mismatch supplies the result.

### Gate 7 — computational diagnostics, explicitly non-proof

Use `NS-SIM` only after the analytical geometry has been reconstructed enough to define a faithful finite-resolution experiment. Candidate diagnostics may include the reported concentration scalings, velocity growth, bounded-energy behavior, annular stress/covariance structure and pulse growth/decay.

Numerical work has two purposes only:

1. detect implementation or transcription inconsistencies;
2. provide reproducible intuition for the constructed mechanism.

It cannot certify the continuum singularity or replace Gates 1–6.

**Pass condition:** numerical artifacts are provenance-complete and remain below the repository's mathematical claim threshold.

### Gate 8 — adversarial review

Run independent reviewer roles against both prose and formal proof:

- theorem-boundary reviewer;
- PDE regularity reviewer;
- scaling and asymptotics reviewer;
- functional-analysis reviewer;
- oscillatory/convex-integration-style construction reviewer;
- Lean statement-correspondence reviewer;
- Lean trusted-base/dependency reviewer;
- circularity and hidden-assumption reviewer.

Minority reports and unresolved objections remain visible. Consensus is not itself evidence.

**Pass condition:** every blocking objection is either reproduced and accepted as a failure or closed by a checkable argument/artifact.

### Gate 9 — QSOL disposition

Allowed dispositions are deliberately conservative:

- `intake_only`;
- `replay_confirmed`;
- `statement_correspondence_confirmed`;
- `analytic_reconstruction_partial`;
- `independent_verification_complete`;
- `blocking_issue_found`.

No disposition is equivalent to Clay Institute acceptance. Any future promotion into `research/theorem_registry.json` requires a separate audited change to its semantic lock and claim policy.

## Initial work packages

### WP1 — theorem/corollary correspondence

**Status:** implemented in PR #13.

Produce machine-readable maps for Theorem 1.1 → C and Corollary 10.6 → D, including every Fefferman field and erratum.

### WP2 — proof dependency graph

**Status:** implemented in PR #14 at the dependency-indexing level.

Index Sections 4–10, appendices and the main propositions/lemmas into a dependency DAG rooted at Theorem 1.1 and Corollary 10.6. The registry deliberately distinguishes exact paper labels from section-family and programme-obligation anchors rather than inventing citation precision.

### WP3 — scaling ledger

Re-derive and cross-check all concentration exponents and their compatibility with bounded energy and smooth forcing.

### WP4 — residual cancellation ledger

Track the background residual, annular stress, wave covariance, mean corrections and each residual-improvement cycle with explicit sign and support checks.

### WP5 — Lean clean-room replay

Build the pinned formalization, archive receipts, enumerate final declaration dependencies and run Comparator.

### WP6 — prose/Lean semantic diff

Create a field-by-field semantic diff between the analytical theorem, comparator statements and official C/D formulations.

### WP7 — independent reviewer packets

Give each reviewer a frozen subset of the proof and exact obligations before exposing other reviewers' conclusions, reducing anchoring and consensus leakage.

## Publication boundary

Until all required gates pass, repository wording must use forms such as:

> OpenAI published a construction claiming Fefferman alternatives C and D; QSOL NS is independently verifying the analytical and formal artifacts.

It must not use forms such as:

> QSOL verified that Navier–Stokes is solved.

That distinction is the point of this phase.
