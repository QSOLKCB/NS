<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Sealed Holdout & Adversarial Evaluation v0.1

PR #11 adds a fail-closed freeze-before-observation holdout layer to Crucible. Its purpose is to make adversarial evaluation auditable without allowing holdout success, replay success, schema validity, formal assurance, or cross-method agreement to masquerade as mathematical proof.

## Boundary

`SealedHoldoutStore` is a research-process seal, not a cryptographic secrecy system. A process or operator with unrestricted filesystem access can inspect stored bytes. The guarantee is narrower and machine-checkable: the normal Crucible evaluation path cannot materialize or release a registered holdout until the candidate is frozen, and every relevant identity and transition is recorded immutably.

The machine contract lives at `research/holdout_contract.json` and is validated against `research/schemas/holdout-contract.schema.json`.

## Freeze before observation

A holdout may be sealed before a candidate exists. Its public manifest records only evaluator metadata, payload identity/size, hashes of optional leakage sentinels, negative-control IDs, source commit, and seal time.

Candidate-specific materialization requires all of the following:

- `Candidate.status == "frozen"` and `Candidate.frozen == true`;
- the candidate domain matches the holdout domain;
- an exact SHA-256 identity of the frozen candidate snapshot;
- the exact verified Crucible Ledger head SHA-256 supplied by the caller;
- the exact sealed holdout payload SHA-256;
- a pre-release context that does not contain the payload identity or any leakage sentinel, including when embedded inside a larger string;
- actor, exact source commit, and UTC timestamp provenance.

Multiple candidates may be frozen and materialized as one intended batch before the first reveal. Once any release for a holdout occurs, that batch is closed: no new candidate may be materialized against the already-observed holdout. A materialization may be released only once.

Release recomputes the candidate snapshot identity and fails closed if the candidate changed after materialization. It also verifies that the sealed payload still matches the hash bound at materialization.

## Leakage probes

A JSON holdout payload may contain a top-level `leakage_sentinels` array of unique strings. Only SHA-256 hashes of those sentinels are exposed in the public manifest.

Before materialization, `assert_context_clean` privately reloads the sealed payload, verifies that its sentinel identities still match the public manifest, and scans every string scalar and string mapping key in the supplied generation/evaluation context. A sentinel or payload SHA-256 appearing as a substring is rejected, not merely exact whole-string equality.

This is a deterministic verbatim-leakage probe, not a claim that every semantic, encoded, paraphrased, transformed, or side-channel leak can be detected.

The CI suite includes hostile standalone and embedded sentinel/payload-identity leakage tests.

## Negative controls

A holdout may be sealed without controls if no holdout evaluation will be asserted. Once a recorded assurance state says that holdout evaluation ran, the persisted holdout manifest must declare at least one negative control and every declared control must be reported exactly once. The persisted manifest is reloaded from the store; a caller-supplied modified manifest cannot change the expected control set. A holdout evaluation cannot be recorded as `passed` while any negative control is `failed`.

Negative controls test the evaluation machinery. Passing them does not validate the Navier–Stokes candidate itself.

## Separate assurance states

PR #11 deliberately refuses to collapse evaluation into one aggregate status. `AssuranceState` records five independent dimensions:

1. `schema_admission` — whether the evaluated artifact was admitted under its declared schema;
2. `deterministic_replay` — whether the relevant deterministic computation replayed under its stated contract;
3. `cross_method_challenge` — whether a genuinely separate declared method challenged or reproduced the result;
4. `holdout_evaluation` — outcome on the released sealed material;
5. `continuum_bridge` — whether the candidate has actually discharged the discrete/finite-computation to continuum mathematical obligation.

A valid state may therefore say, for example:

```text
schema_admission      = passed
deterministic_replay  = passed
cross_method_challenge= failed
holdout_evaluation    = passed
continuum_bridge      = unsatisfied
```

That combination is preserved as-is. No synthetic confidence score, winner, proof status, or claim promotion is derived from it.

## Audit journal

The holdout store writes canonical JSON artifacts for manifests, materializations, release receipts and assurance states. `holdout.jsonl` is an append-only SHA-256 hash chain whose events bind:

- action;
- logical artifact ID;
- artifact SHA-256;
- actor;
- exact source commit;
- UTC timestamp;
- previous event hash.

`verify()` replays the event chain, reloads the referenced artifacts, checks canonical serialization and artifact hashes, and reconciles the complete manifest/materialization/release/assurance directories plus sealed payload files against authoritative journal history. An artifact written before a crash but lacking its required event is therefore an orphan and fails closed on replay or reopen instead of being silently usable.

v0.1 is single-writer per store root via a nonblocking filesystem lock. Releasing that lock with `close()` permanently invalidates that store object; all later reads and mutations through the stale reference fail rather than racing a newly opened writer.

## Authority limits

The following are permanently false in v0.1:

```text
HOLDOUT_SUCCESS == PROOF
REPLAY_SUCCESS == CONTINUUM_PROOF
CROSS_METHOD_AGREEMENT == CONTINUUM_PROOF
SCHEMA_OR_FORMAL_ASSURANCE == PHYSICAL_TRUTH
SEALED_STORAGE == CRYPTOGRAPHIC_CONFIDENTIALITY_AGAINST_FILESYSTEM_ACCESS
HOLDOUT_SUCCESS == CLAIM_PROMOTION
HOLDOUT_SUCCESS == WINNER_SELECTION
```

These limits are represented in the machine contract, artifact authority snapshots, schemas, validator and regression tests.

## Validation

`tools/validate_holdout.py` performs contract/schema validation and an end-to-end hostile fixture. `tests/test_holdout.py` additionally covers review-derived adversarial cases: embedded leakage, forged caller manifests, empty declared controls, orphan artifacts/payloads, stale closed writers, post-release materialization, and duplicate releases.

`.github/workflows/holdout-evaluation.yml` runs the validator and `tests/test_holdout.py` on Python 3.11 and 3.13.

## Relationship to NS-SIM

This layer does not replace the deterministic PDE laboratory or NS-SIM. It is the evaluation gate around research candidates and future simulation evidence. Numerical outputs can be introduced as development or holdout evidence only under their own solver/provenance contracts, and even successful CPU/GPU or cross-method reproduction remains below a continuum proof obligation.
