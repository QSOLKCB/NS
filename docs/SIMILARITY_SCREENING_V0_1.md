<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Similarity Screening v0.1

PR #9 adds deterministic search-memory screening to reduce repeated compute on candidate mechanisms already represented in the Crucible history.

The screen is advisory. It does not establish mathematical equivalence, create domain evidence, change claim level, select a winner, or automatically remove a candidate.

## Classifications

The detector can report:

- `novel_to_screening_memory` — no configured screening threshold was crossed;
- `exact_duplicate` — the normalized declared-mechanism fingerprint is identical within the same domain, hypothesis set and target track;
- `structural_near_duplicate` — deterministic token Jaccard overlap crosses the local structural threshold;
- `dead_family_match` — overlap crosses the local threshold for a mechanism family backed by persisted Crucible failure records.

The last label is historical search-memory terminology. It means resemblance to a previously failed mechanism family, not mathematical falsehood.

## Exact fingerprint

`normalized_declared_mechanism_sha256_v1` hashes canonical JSON containing domain, hypothesis set, target track, normalized hypothesis text, and normalized semantic assumptions. Candidate identity and machine provenance fields are excluded.

## Local similarity calibration

v0.1 uses `token_jaccard_v1`. The NS adapter records a structural threshold of `0.82`, a prior-failure-family threshold of `0.76`, and a minimum of four shared tokens.

These are local screening parameters, not universal constants. Historical reports retain the algorithm version and thresholds that produced them.

## Candidate origin

Origin is recorded separately from claim level using:

- `exact_domain_construction`;
- `established_bridge`;
- `source_described`;
- `structural_transfer`;
- `heuristic`;
- `schematic`.

This adapts the useful editorial separation pattern from `QSOLKCB/synergetics2`. Origin classification has no claim-level or evidence effect.

## Failure-backed family memory

A prior-failure family is constructed from a candidate, its content-addressed Crucible Ledger object ID, one or more `FailureRecord` objects belonging to that candidate, and the corresponding persisted failure object IDs.

A match is a prompt to inspect earlier failure lessons before spending more compute. It is not a proof that the new candidate fails for the same reason.

## Audit memory

`DuplicateScreeningJournal` stores content-addressed origin classifications, failure-backed family records, and similarity reports behind a SHA-chained append-only log with immutable refs. Candidate and failure references must agree with a verified Crucible Ledger replay.

## Machine boundary

```text
SIMILAR_CANDIDATE != MATHEMATICALLY_EQUIVALENT_CANDIDATE
DEAD_FAMILY_MATCH != PROOF_OF_FALSEHOOD
SCREENING_FLAG != CANDIDATE_REJECTION
ORIGIN_CLASS != CLAIM_LEVEL
LOCAL_SIMILARITY_THRESHOLD != UNIVERSAL_CONSTANT
SCREENING_MEMORY != DOMAIN_EVIDENCE
```

The intended path is Generator Airlock -> candidate persistence -> similarity screen -> review if flagged -> ordinary Crucible evaluation.
