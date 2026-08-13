# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from crucible_core import (
    AnalogyFirewall,
    AnalogyRecord,
    Candidate,
    ContentAddressedLedger,
    EvidenceRecord,
    FailureRecord,
    LedgerError,
    TransferTicket,
)
from crucible_core.engine import canonical_json_bytes

COMMIT = "a" * 40
STAMP = "2026-08-13T09:00:00Z"
DOMAIN = "navier_stokes_3d_incompressible"
ROOT = Path(__file__).resolve().parents[1]


def candidate(candidate_id: str = "c1", claim_level: str = "exploratory") -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        domain_id=DOMAIN,
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="candidate hypothesis",
        claim_level=claim_level,
        generation_method="unit_test",
    )


def analogy(
    analogy_id: str = "A1",
    mapping_class: str = "operator_correspondence",
) -> AnalogyRecord:
    return AnalogyRecord(
        analogy_id=analogy_id,
        source_domain="source",
        target_domain=DOMAIN,
        mapping_class=mapping_class,
        shared_structure="shared operator",
        assumptions=("operator only",),
        known_differences=("different states",),
        allowed_uses=("candidate_generation",),
        forbidden_inferences=("not domain equivalence",),
        provenance_ref="unit:test",
    )


def analogy_candidate(
    analogy_id: str = "A1",
    mapping_class: str = "operator_correspondence",
    candidate_id: str = "c-transfer",
) -> tuple[AnalogyRecord, Candidate]:
    record = analogy(analogy_id, mapping_class)
    firewall = AnalogyFirewall(target_domain=DOMAIN)
    firewall.register(record)
    issued = firewall.issue_candidate(
        analogy_id=analogy_id,
        candidate_id=candidate_id,
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="candidate generated through an analogy firewall",
        generation_method="unit-test",
    )
    return record, issued


def ticket_for(
    candidate_object_id: str,
    *,
    analogy_id: str = "A1",
    mapping_class: str = "operator_correspondence",
    ticket_id: str = "t1",
) -> TransferTicket:
    return TransferTicket(
        ticket_id=ticket_id,
        analogy_id=analogy_id,
        mapping_class=mapping_class,
        source_sha256="b" * 64,
        target_domain=DOMAIN,
        firewall_decision="candidate_generation_authorized",
        candidate_object_id=candidate_object_id,
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
    first = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    second = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
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
    object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ledger._object_path(object_id).write_text("{}\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.verify()


def test_replay_detects_event_chain_tampering(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    event = json.loads(ledger.log_path.read_text(encoding="utf-8"))
    event["actor"] = "tampered"
    ledger.log_path.write_bytes(canonical_json_bytes(event))
    with pytest.raises(LedgerError):
        ledger.verify()


@pytest.mark.parametrize("mutation", ["spacing", "missing-newline"])
def test_replay_requires_exact_canonical_event_bytes(tmp_path: Path, mutation: str):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    event = json.loads(ledger.log_path.read_text(encoding="utf-8"))
    if mutation == "spacing":
        data = (json.dumps(event, sort_keys=False, indent=2) + "\n").encode()
    else:
        data = canonical_json_bytes(event).rstrip(b"\n")
    ledger.log_path.write_bytes(data)
    with pytest.raises(LedgerError):
        ledger.verify()


def test_replay_detects_ref_tampering(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ref = ledger.refs_root / "candidate" / "c1.json"
    value = json.loads(ref.read_text(encoding="utf-8"))
    value["logical_id"] = "other"
    ref.write_text(json.dumps(value) + "\n", encoding="utf-8")
    with pytest.raises(LedgerError):
        ledger.verify()


def test_missing_ref_is_recovered_from_authoritative_log(tmp_path: Path):
    root = tmp_path / "ledger"
    ledger = ContentAddressedLedger(root)
    object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ref = ledger.refs_root / "candidate" / "c1.json"
    ref.unlink()

    reopened = ContentAddressedLedger(root)
    assert ref.is_file()
    assert reopened.verify().refs["candidate:c1"] == object_id


def test_retry_after_ref_publication_failure_does_not_duplicate_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    original = ledger._materialize_ref
    calls = 0

    def fail_once(event):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("synthetic ref publication failure")
        return original(event)

    monkeypatch.setattr(ledger, "_materialize_ref", fail_once)
    with pytest.raises(OSError):
        ledger.persist_candidate(
            candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        )

    assert len(ledger.log_path.read_text(encoding="utf-8").splitlines()) == 1
    object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    assert len(ledger.log_path.read_text(encoding="utf-8").splitlines()) == 1
    assert ledger.verify().refs["candidate:c1"] == object_id


def test_replay_fails_when_authoritative_log_disappears_but_refs_remain(
    tmp_path: Path,
):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ledger.log_path.unlink()
    with pytest.raises(LedgerError):
        ledger.verify()


def test_replay_rejects_event_type_that_disagrees_with_object_envelope(
    tmp_path: Path,
):
    root = tmp_path / "ledger"
    ledger = ContentAddressedLedger(root)
    object_id = ledger.persist_candidate(
        candidate(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    event = json.loads(ledger.log_path.read_text(encoding="utf-8"))
    (ledger.refs_root / "candidate" / "c1.json").unlink()

    event["object_type"] = "evidence"
    core = dict(event)
    core.pop("event_sha256")
    event["event_sha256"] = hashlib.sha256(canonical_json_bytes(core)).hexdigest()
    ledger.log_path.write_bytes(canonical_json_bytes(event))

    new_ref = ledger.refs_root / "evidence" / "c1.json"
    new_ref.parent.mkdir(parents=True, exist_ok=True)
    new_ref.write_bytes(
        canonical_json_bytes(
            {
                "ledger_version": "0.1.0",
                "object_type": "evidence",
                "logical_id": "c1",
                "object_id": object_id,
                "event_sha256": event["event_sha256"],
            }
        )
    )
    with pytest.raises(LedgerError):
        ContentAddressedLedger(root)


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
    ids = {
        ledger.persist_evidence(
            evidence, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        ),
        ledger.persist_failure(
            failure, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        ),
        ledger.persist_analogy(
            analogy(), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
        ),
    }
    assert len(ids) == 3
    assert ledger.verify().event_count == 3


def test_transfer_ticket_requires_existing_matching_analogy_and_candidate(
    tmp_path: Path,
):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    record, issued = analogy_candidate()
    ledger.persist_analogy(
        record, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    candidate_object_id = ledger.persist_candidate(
        issued, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ticket_id = ledger.persist_transfer_ticket(
        ticket_for(candidate_object_id),
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    assert ledger._read_object(ticket_id)["object_type"] == "transfer_ticket"
    assert ledger.verify().event_count == 3


@pytest.mark.parametrize(
    "mapping_class",
    ["visual_resemblance", "explicit_non_correspondence", "made_up_mapping"],
)
def test_transfer_ticket_rejects_forbidden_mapping_classes(
    mapping_class: str, tmp_path: Path
):
    ticket = ticket_for("sha256:" + "c" * 64, mapping_class=mapping_class)
    with pytest.raises(LedgerError):
        ticket.validate()


def test_transfer_ticket_rejects_non_candidate_target(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    record, _issued = analogy_candidate()
    ledger.persist_analogy(
        record, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    snapshot_object = ledger.put_object(
        object_type="snapshot",
        logical_id="s1",
        payload={"x": 1},
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    with pytest.raises(LedgerError):
        ledger.persist_transfer_ticket(
            ticket_for(snapshot_object),
            actor="agent",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )


def test_transfer_ticket_rejects_non_exploratory_intake(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    record = analogy()
    ledger.persist_analogy(
        record, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    bad = Candidate(
        candidate_id="c-transfer",
        domain_id=DOMAIN,
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="bad elevated transfer",
        claim_level="candidate_lemma",
        generation_method="unit_test",
        assumptions=(
            "analogy_source=A1",
            "mapping_class=operator_correspondence",
            "cross_domain_transfer_requires_target_domain_validation",
        ),
    )
    candidate_object_id = ledger.persist_candidate(
        bad, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    with pytest.raises(LedgerError):
        ledger.persist_transfer_ticket(
            ticket_for(candidate_object_id),
            actor="agent",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )


def test_analogy_candidate_cannot_pass_final_verification_without_ticket(
    tmp_path: Path,
):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    record, issued = analogy_candidate()
    ledger.persist_analogy(
        record, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    candidate_object_id = ledger.persist_candidate(
        issued, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    with pytest.raises(LedgerError):
        ledger.verify()
    with pytest.raises(LedgerError):
        ledger.snapshot(
            snapshot_id="must-not-exist",
            actor="agent",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )

    ledger.persist_transfer_ticket(
        ticket_for(candidate_object_id),
        actor="agent",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    assert ledger.verify().event_count == 3


def test_transfer_ticket_must_match_candidate_and_persisted_analogy(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    record, issued = analogy_candidate()
    ledger.persist_analogy(
        record, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    candidate_object_id = ledger.persist_candidate(
        issued, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    wrong = ticket_for(
        candidate_object_id,
        analogy_id="OTHER",
        mapping_class="operator_correspondence",
    )
    with pytest.raises(LedgerError):
        ledger.persist_transfer_ticket(
            wrong, actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
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
        ledger.persist_candidate(
            candidate(), actor="agent", source_commit="main", recorded_at_utc=STAMP
        )
    with pytest.raises(LedgerError):
        ledger.persist_candidate(
            candidate(),
            actor="agent",
            source_commit=COMMIT,
            recorded_at_utc="2026-08-13T09:00:00+09:30",
        )


@pytest.mark.parametrize(
    "bad_stamp",
    ["garbage", "2026-08-13T09:00:00+09:30"],
)
def test_event_schema_rejects_non_utc_timestamp(bad_stamp: str):
    schema = json.loads(
        (ROOT / "research/schemas/crucible_ledger_event.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)
    event = {
        "ledger_version": "0.1.0",
        "sequence": 1,
        "previous_event_sha256": None,
        "action": "bind_object",
        "object_type": "candidate",
        "object_id": "sha256:" + "a" * 64,
        "logical_id": "c1",
        "actor": "unit-test",
        "source_commit": "a" * 40,
        "recorded_at_utc": bad_stamp,
        "metadata": {},
        "event_sha256": "b" * 64,
    }
    with pytest.raises(ValidationError):
        validator.validate(event)


def test_appends_do_not_replay_full_history_after_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    ledger = ContentAddressedLedger(tmp_path / "ledger")

    def forbidden_scan():
        raise AssertionError("append unexpectedly replayed the full ledger")

    monkeypatch.setattr(ledger, "_scan_events", forbidden_scan)
    ledger.persist_candidate(
        candidate("c1"), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )
    ledger.persist_candidate(
        candidate("c2"), actor="agent", source_commit=COMMIT, recorded_at_utc=STAMP
    )


def test_no_deletion_api_is_exposed(tmp_path: Path):
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    assert not hasattr(ledger, "delete")
    assert not hasattr(ledger, "remove")
