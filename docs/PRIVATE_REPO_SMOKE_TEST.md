# Private Repository Access Smoke Test

This document exists to verify that the connected GitHub integration can operate normally while `QSOLKCB/NS` is private.

## Operations exercised

The smoke test intentionally covers multiple private-repository operations rather than a single metadata lookup:

1. repository metadata read;
2. private branch/ref read;
3. private commit inspection;
4. private file read;
5. update of an existing file on `main`;
6. creation of a new file in a nested `docs/` path;
7. read-back verification of the resulting content.

## Expected interpretation

A successful test demonstrates that repository visibility is **not** preventing the connected GitHub integration from reading or writing this repository under its current installation permissions.

It does not guarantee that permissions can never change. If the GitHub App installation is later removed, restricted to a different repository set, or stripped of write permissions, access may fail even though the repository itself remains unchanged.

## Research use

The private phase is intended for exploratory work, adversarial testing, failed derivations, numerical experiments, theorem-boundary mapping, and formalization without prematurely presenting exploratory evidence as a claimed Navier–Stokes solution.

The publication gate should remain separate from the research gate:

```text
PRIVATE EXPERIMENT != PUBLIC CLAIM
NUMERICAL EVIDENCE != MATHEMATICAL PROOF
CANDIDATE LEMMA != VERIFIED THEOREM
```

When material is eventually promoted out of the private workspace, its exact hypotheses, derivation, verification status, commit identity, and provenance should travel with it.
