<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Content-Addressed Crucible Ledger v0.1

## Purpose

PR #7 gives Crucible durable memory. Candidate search is only cumulative if a later worker can recover exactly what was proposed, what evidence was attached, why a candidate failed, which analogy seeded it, and which source revision produced the record.

The ledger therefore persists research-process state without changing its epistemic status.

```text
PERSISTED_STATE != TRUTH
LEDGER_REPLAY != CLAIM_PROMOTION
CONTENT_ADDRESSING != MATHEMATICAL_VALIDATION
MUTABLE_HISTORY != RESEARCH_PROVENANCE
TRANSFER_TICKET != DOMAIN_EVIDENCE
```

## Storage model

`ContentAddressedLedger` stores canonical JSON envelopes under SHA-256 object identities:

```text
<ledger-root>/
  objects/
    sha256/
      ab/
        cdef....json
  refs/
    candidate/
    evidence/
    failure/
    analogy/
    transfer_ticket/
    snapshot/
  ledger.jsonl
```

An object ID is:

```text
sha256:<64 lowercase hexadecimal characters>
```

and is computed over the complete canonical envelope, not merely a caller-supplied identifier.

The canonicalization contract uses UTF-8 JSON, sorted keys, compact separators, no NaN/Infinity, and a terminal newline. A byte-level change therefore changes the object identity.

## Immutable refs

Human/model-facing logical IDs remain useful, so the ledger binds names such as `candidate:c17` to content-addressed objects.

A logical ref is immutable. Repeating the exact same binding is idempotent; attempting to bind the same logical ID to different content is rejected.

Refs are a navigation index. They do not define the authoritative history.

## Append-only event history

`ledger.jsonl` is the authoritative history. Every successful new binding produces a canonical event containing:

- contiguous sequence number;
- previous-event SHA-256;
- object type and object ID;
- logical ID;
- actor;
- exact 40-hex source commit;
- UTC timestamp;
- optional metadata;
- event SHA-256.

The event digest covers the event body, and every event points to the previous event digest. Replay rejects broken sequence, broken hash chain, missing/tampered objects, noncanonical objects, missing/tampered refs, invalid commit identity or non-UTC timestamps.

v0.1 is explicitly **single-writer-process only**. This is a declared limitation, not an implied concurrency guarantee.

## Persisted object classes

v0.1 supports:

- `candidate`;
- `evidence`;
- `failure`;
- `analogy`;
- `transfer_ticket`;
- `snapshot`.

Candidate/evidence/failure/analogy helpers serialize the existing immutable Crucible models directly. Persistence does not alter their claim/evidence status.

## Transfer tickets

PR #6 allows an analogy to seed an exploratory candidate after the Analogy Firewall authorizes candidate generation. PR #7 makes that intake decision durable.

A transfer ticket records:

- ticket ID;
- analogy ID;
- mapping class;
- source SHA-256;
- target domain;
- exact firewall decision;
- content-addressed candidate object ID;
- mandatory target-domain revalidation;
- exploratory intake claim level.

The referenced candidate object must already exist, must actually be a candidate envelope, must target the same domain, and must still be `exploratory` at intake.

A transfer ticket is provenance. It is **not** NS evidence and cannot satisfy a proof barrier.

## Snapshots

A snapshot stores the verified ref map, event count and event-chain head at a point in history. The snapshot itself is another content-addressed object.

Snapshots carry an explicit authority record stating that persistence/replay cannot define truth, promote claims, select a winner, or upgrade stored material into domain evidence.

## Failure behavior

The ledger fails closed. It does not silently repair or reinterpret tampered history.

A detected hash mismatch, event-chain break, ref mismatch, illegal rebind, invalid provenance field, transfer-ticket mismatch, or noncanonical object raises `LedgerError`.

Unreferenced content-addressed objects can exist after an interrupted or rejected operation; because authoritative history is the event chain, such objects do not silently become ledger state. Garbage collection is intentionally out of scope for v0.1 because deleting evidentiary material has separate governance consequences.

## Authority boundary

The ledger answers:

> What did the research process record, under which identity and provenance?

It does not answer:

> Is this mathematically true?

Those remain different questions. Domain adapters, theorem boundaries, proof barriers, formal checks, numerical evidence limits, human authorization and external review retain their existing authority.

## Validation

`tools/validate_crucible_ledger.py` cross-checks the machine contract and runs a live temporary-ledger exercise integrating the Analogy Firewall, candidate persistence, transfer ticket, snapshot and replay. Hostile mutations attempt to weaken immutability, hash chaining, claim authority and evidence boundaries.

`tests/test_crucible_ledger.py` attacks object/event/ref tampering, logical-ref rebinding, provenance weakening, transfer-ticket misuse and authority escalation.

The dedicated GitHub workflow runs on Python 3.11 and 3.13 and also executes the older agent, Crucible and Analogy Firewall validators first.
