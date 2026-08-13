<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Schema-Constrained ML Generator Interface v0.1

## Purpose

PR #8 introduces the first model-facing candidate-generation boundary for the Crucible architecture.

The generator is deliberately an **airlock**, not a research authority. A model may propose a structured exploratory idea. It may not decide that the idea is evidence, a theorem, a solution, a winner, or even a valid Crucible candidate.

The central boundary is:

```text
MODEL_OUTPUT != CANDIDATE
VALID_JSON != VALID_RESEARCH_CANDIDATE
GENERATOR_OUTPUT != DOMAIN_EVIDENCE
GENERATOR_OUTPUT != CLAIM_PROMOTION
GENERATOR_SELF_ASSESSMENT != EVIDENCE_STATUS
INVALID_GENERATION_ATTEMPT != MATHEMATICAL_FAILURE
ACCEPTED_CANDIDATE != SURVIVING_CANDIDATE
```

## Provider-neutral backend protocol

`GeneratorBackend` exposes only:

```text
backend_id
model_id
generate(context_packet) -> untrusted text
```

The core does not depend on OpenAI, Anthropic, Gemini, Ollama, or any other provider SDK. `DeterministicFixtureBackend` supplies the CI/replay implementation.

Provider adapters may be added later without changing the proposal schema or epistemic rules.

## Generator context packet

A `GeneratorContextPacket` is canonical JSON with a SHA-256 identity. It binds a generation attempt to:

- target domain;
- unresolved hypothesis set;
- allowed hypothesis tracks;
- known theorem IDs;
- proof-barrier IDs;
- current frontier candidate IDs;
- selected reusable failure lessons;
- permitted analogy IDs;
- Crucible-ledger event count/head digest;
- exact source commit;
- bounded generation task.

The context digest makes the question “what did the model know when it generated this?” answerable without treating the context as evidence.

## Candidate proposal schema

The untrusted model may emit only these fields:

```text
proposal_id
target_hypothesis
precise_statement
motivation
assumptions
claimed_dependencies
suggested_tests
possible_failure_modes
analogy_sources
parent_candidate_ids
generator_notes
```

Additional properties are forbidden. In particular, the model does **not** control fields such as:

```text
claim_level
evidence_status
proof_status
proved
solves_clay
winner
confidence
confidence_score
truth_probability
```

Non-finite JSON values such as `NaN` and `Infinity` are rejected.

## Intake checks

A structurally valid proposal is still rejected if it references:

- an unknown hypothesis track;
- an unknown parent candidate;
- an unknown theorem dependency;
- an unregistered analogy;
- an already-used candidate ID.

Direct analogy intake is also rejected even for registered analogies. A cross-domain proposal must go through the existing `AnalogyFirewall`, preserving the PR #6 transfer rules and PR #7 transfer-ticket provenance.

If all checks pass, the airlock constructs a registration-valid `Candidate` with:

```text
claim_level = exploratory
status = active
frozen = false
```

The candidate records the target track, context digest, and generation attempt ID in its assumptions/provenance.

## Attempt journal

Every backend attempt is retained in a separate content-addressed `GeneratorAttemptJournal`, including rejected attempts.

Each attempt preserves:

- backend and model identity;
- prompt-template SHA-256;
- context packet and context SHA-256;
- raw output and raw-output SHA-256;
- parse status;
- validation status;
- rejection reasons;
- parsed proposal if available;
- accepted candidate representation if available;
- UTC record time;
- explicit non-authority flags.

The journal stores canonical attempt objects under SHA-256 and uses a canonical SHA-chained JSONL event stream. This makes generator behavior auditable without confusing generator failures with mathematical failures.

## Separation from the Crucible ledger

The model-facing `GeneratorAirlock.run()` does **not** mutate `ContentAddressedLedger`.

An accepted `CandidateIntakeDecision` may later be committed through the explicit `commit_candidate()` step. This separation prevents an external model from writing trusted Crucible state simply by returning syntactically valid output.

The Crucible ledger remains the authority for persisted candidates. The generation journal is provenance for how a proposal was produced and screened.

## NS adapter

`research/ns_ml_generator_adapter.json` binds the generic airlock to:

- `navier_stokes_3d_incompressible`;
- `NS_PRIMARY_COMPETITION`;
- `NS_GLOBAL_REGULARITY`;
- `NS_FINITE_TIME_BREAKDOWN`;
- the theorem registry;
- the proof-barrier registry;
- the analogy registry;
- the NS Crucible adapter;
- the Crucible ledger contract.

All registered proof barriers remain part of the context boundary. Generator acceptance does not discharge any of them.

## Rejection taxonomy

v0.1 records machine-readable rejection reasons:

```text
invalid_json
proposal_not_object
schema_failure
forbidden_authority_field
forbidden_authority_language
unknown_hypothesis
unknown_parent
unknown_theorem_dependency
unregistered_analogy
analogy_requires_firewall_route
duplicate_candidate_id
invalid_context
candidate_validation_failure
```

These reasons describe **intake failures**, not mathematical falsification.

## Nonclaims

PR #8 does not claim that ML can solve Navier–Stokes, that a valid proposal is novel, that an accepted candidate survives the Crucible, or that model self-assessment has evidentiary value.

The purpose of this layer is narrower: make model generation reproducible, bounded, rejectable, attributable, and unable to promote itself.
