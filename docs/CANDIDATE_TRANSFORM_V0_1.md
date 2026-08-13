<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Controlled Mutation & Crossover Engine v0.1

PR #10 adds a role-separated candidate-transformation layer between the existing ML generator/search memory and ordinary Crucible evaluation.

The runtime chooses the operator, target track, exact parent objects, bounded theorem/proof-barrier context and survivor frontier. A backend receives that frozen context and may propose only the child mathematical content. It does not choose its own ancestry, claim level, evidence status, survival status or ledger write.

## Operators

- `weaken_assumption` — one parent, same track, with at least one exact parent assumption explicitly removed from the child declaration;
- `repair_scaling_defect` — one parent, same track;
- `replace_failed_estimate` — one parent, same track, backed by verified persisted failure provenance and explicit addressed failure IDs;
- `reverse_track_perspective` — one parent and a different adapter-approved target track;
- `adversarial_attack` — one parent, same track, producing a new exploratory candidate rather than modifying the parent;
- `crossover_survivors` — exactly two same-track parents from the frozen survivor frontier.

The operator label records search intent. It does **not** establish that an assumption is logically weaker, that a scaling defect has actually been repaired, or that a proposed estimate is mathematically valid. Ordinary theorem-boundary, proof-barrier and Crucible checks remain authoritative.

## Child authority

Every accepted child is constructed by the engine as `claim_level=exploratory`, `status=active`, and `frozen=false`. Parent claim level, attached evidence, frozen state and survival history are not inherited. Parent IDs are taken from the frozen context, not from model output.

Engine-owned provenance is written into the child candidate: operator, context SHA-256, attempt ID, receipt SHA-256, prompt/output SHA-256 values and exact parent content-addressed object IDs. The ordinary `parent_candidate_ids` field preserves immutable lineage.

## Attempt receipt and commit separation

`TransformAttemptJournal` stores canonical content-addressed attempt objects behind a SHA-chained event stream with actor, exact source commit and UTC provenance. v0.1 enforces one writer per journal root.

The model-facing `run()` path does not mutate the Crucible Ledger. An accepted decision predicts the exact candidate object identity. `commit_candidate()` is a separate explicit operation and succeeds only when the ledger head/context still match, parent/failure refs remain verified, the decision still matches its recorded attempt, and the persisted child object ID equals the predicted ID.

## Cross-domain boundary

v0.1 rejects parents carrying Analogy Firewall transfer markers. This is intentionally conservative: transforming an analogy-derived mechanism will require a future explicit firewall-aware route rather than silently laundering cross-domain provenance through child lineage.

## Machine boundary

```text
TRANSFORM_OUTPUT != DOMAIN_EVIDENCE
TRANSFORM_CHILD != PARENT_AUTHORITY
PARENT_CLAIM_LEVEL != CHILD_CLAIM_LEVEL
PARENT_EVIDENCE != CHILD_EVIDENCE
PARENT_SURVIVAL != CHILD_SURVIVAL
OPERATOR_LABEL != MATHEMATICAL_VALIDATION
CROSSOVER != PROOF_SYNTHESIS
TRANSFORM_RUN != LEDGER_COMMIT
```

The intended path is: persisted survivor(s) -> frozen transform context -> explicit operator -> untrusted backend proposal -> transform airlock -> content-addressed attempt receipt -> explicit child ledger commit -> similarity screening -> ordinary Crucible evaluation.
