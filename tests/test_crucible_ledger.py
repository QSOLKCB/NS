# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crucible_core import (
    AnalogyRecord,
    Candidate,
    ContentAddressedLedger,
    EvidenceRecord,
    FailureRecord,
    LedgerError,
    TransferTicket,
)

COMMIT = "a" * 40
STAMP = "2026-08-13T09:00:00Z"
DOMAIN = "navier_stokes_3d_incompressible"


def candidate(candidate_id: str = "c1", claim_level: str = "exploratory") -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        domain_id=DOMAIN,
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="candidate hypothesis",
        claim_level=claim_level,
        generation_method="unit_test",
    )


def test_canonical_object_identity_is_order_independent(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    a = ledger.put_object(
        object_type="snapshot",
        logical_id="s1",
        payload={"b": 2, "a": 1},
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    b = ContentAddressedLedger(tmp_path / "other").put_object(
        object_type="snapshot",
        logical_id="s1",
        payload={"a": 1, "b": 2},
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    assert a == b


def test_payload_mutation_changes_object_identity(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    a = ledger.put_object(
        object_type="snapshot",
        logical_id="s1",
        payload={"value": 1},
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    b = ContentAddressedLedger(tmp_path / "other").put_object(
        object_type="snapshot",
        logical_id="s2",
        payload={"value": 2},
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    assert a != b


def test_same_logical_ref_is_idempotent_but_cannot_rebind(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    first = ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP)
    second = ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP)
    assert first == second
    assert ledger.verify().event_count == 1
    with pytest.raises(LedgerError):
        ledger.persist_candidate(
            Candidate(
                candidate_id="c1",
                domain_id=DOMAIN,
                hypothesis_set_id="NS_PRIMARY_COMPETITION",
                hypothesis="changed hypothesis",
                claim_level="exploratory",
                generation_method="unit_test",
            ),
            actor="agent",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )


def test_replay_detects_object_tampering(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    object_id = ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP)
    path = ledger._object_path(object_id)
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.verify()


def test_replay_detects_event_chain_tampering(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP)
    event = json.loads(ledger.log_path.read_text(encoding="utf-8"))
    event["actor"] = "tampered"
    ledger.log_path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.verify()


def test_replay_detects_ref_tampering(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP)
    ref = ledger.refs_root / "candidate" / "c1.json"
    value = json.loads(ref.read_text(encoding="utf-8"))
    value["logical_id"] = "other"
    ref.write_text(json.dumps(value) + "\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.verify()


def test_persistence_preserves_claim_level_without_promotion(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    object_id = ledger.persist_candidate(
        candidate(claim_level="candidate_lemma"),
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    payload = ledger._read_object(object_id)["payload"]
    assert payload["claim_level"] == "candidate_lemma"
    authority = ledger.verify().authority_snapshot()
    assert authority["persisted_state_is_truth"] is False
    assert authority["replay_promotes_claim"] is False
    assert authority["replay_selects_winner"] is False


def test_evidence_failure_and_analogy_are_content_addressed(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    evidence = EvidenceRecord(
        evidence_id="e1",
        domain_id=DOMAIN,
        candidate_id="c1",
        evidence_kind="challenging",
        stage="development",
        source_ref="unit:test",
        provenance_ref="sha256:test",
        summary="challenge",
        reproducible=True,
    )
    failure = FailureRecord(
        failure_id="f1",
        candidate_id="c1",
        domain_id=DOMAIN,
        failed_constraint="CIRCULAR_REGULARITY",
        failure_class="circularity",
        evidence_ids=("e1",),
        reusable_lesson="do not assume the desired regularity",
        claim_level_before="candidate_lemma",
        claim_level_after="exploratory",
        recorded_by="unit-test",
    )
    analogy = AnalogyRecord(
        analogy_id="A1",
        source_domain="source",
        target_domain=DOMAIN,
        mapping_class="operator_correspondence",
        shared_structure="shared operator",
        assumptions=("operator only",),
        known_differences=("different states",),
        allowed_uses=("candidate_generation",),
        forbidden_inferences=("not domain equivalence",),
        provenance_ref="unit:test",
    )
    ids = {
        ledger.persist_evidence(evidence, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP),
        ledger.persist_failure(failure, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP),
        ledger.persist_analogy(analogy, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP),
    }
    assert len(ids) == 3
    assert ledger.verify().event_count == 3


def test_transfer_ticket_requires_existing_exploratory_candidate(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    candidate_object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ticket = TransferTicket(
        ticket_id="t1",
        analogy_id="A1",
        mapping_class="operator_correspondence",
        source_sha256="b" * 64,
        target_domain=DOMAIN,
        firewall_decision="candidate_generation_authorized",
        candidate_object_id=candidate_object_id,
    )
    ticket_id = ledger.persist_transfer_ticket(
        ticket, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    assert ledger._read_object(ticket_id)["object_type"] == "transfer_ticket"


def test_transfer_ticket_rejects_non_candidate_target(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    snapshot_object = ledger.put_object(
        object_type="snapshot",
        logical_id="s1",
        payload={"x": 1},
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    ticket = TransferTicket(
        ticket_id="t1",
        analogy_id="A1",
        mapping_class="operator_correspondence",
        source_sha256="b" * 64,
        target_domain=DOMAIN,
        firewall_decision="candidate_generation_authorized",
        candidate_object_id=snapshot_object,
    )
    with pytest.raises(LedgerError):
        ledger.persist_transfer_ticket(
            ticket, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        )


def test_transfer_ticket_rejects_non_exploratory_intake(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    candidate_object_id = ledger.persist_candidate(
        candidate(claim_level="candidate_lemma"),
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    ticket = TransferTicket(
        ticket_id="t1",
        analogy_id="A1",
        mapping_class="operator_correspondence",
        source_sha256="b" * 64,
        target_domain=DOMAIN,
        firewall_decision="candidate_generation_authorized",
        candidate_object_id=candidate_object_id,
    )
    with pytest.raises(LedgerError):
        ledger.persist_transfer_ticket(
            ticket, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        )


def test_snapshot_records_verified_refs_without_gaining_authority(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    candidate_object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    snapshot_id = ledger.snapshot(
        snapshot_id="snap1",
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc="2026-08-13T09:01:00Z",
    )
    snapshot = ledger._read_object(snapshot_id)["payload"]
    assert snapshot["refs"]["candidate:c1"] == candidate_object_id
    assert snapshot["authority"]["persisted_state_is_truth"] is False


def test_event_provenance_requires_exact_commit_and_utc_timestamp(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    with pytest.raises(LedgerError):
        ledger.persist_candidate(candidate(), actor="agent", source_commit="main", recorded_at_utc=STAMP)
    with pytest.raises(LedgerError):
        ledger.persist_candidate(candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc="2026-08-13T09:00:00+09:30")


def test_no_deletion_api_is_exposed(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "remove")
