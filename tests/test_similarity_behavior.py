# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

import crucible_core as cc

DOMAIN = "navier_stokes_3d_incompressible"
HSET = "NS_PRIMARY_COMPETITION"
REG = "NS_GLOBAL_REGULARITY"
BRK = "NS_FINITE_TIME_BREAKDOWN"
COMMIT = "a" * 40
STAMP = "2026-08-13T12:00:00Z"


def candidate(
    candidate_id: str,
    hypothesis: str,
    *,
    track: str = REG,
    assumptions: tuple[str, ...] = ("smooth solution on its interval of existence",),
) -> cc.Candidate:
    return cc.Candidate(
        candidate_id=candidate_id,
        domain_id=DOMAIN,
        hypothesis_set_id=HSET,
        hypothesis=hypothesis,
        claim_level="exploratory",
        generation_method=f"fixture:{candidate_id}",
        assumptions=(
            *assumptions,
            f"target_track={track}",
            f"generator_context_sha256={'b' * 64}",
            f"generation_attempt_id=attempt-{candidate_id}",
        ),
    )


def persist(ledger: cc.ContentAddressedLedger, item: cc.Candidate) -> cc.CandidateReference:
    object_id = ledger.persist_candidate(
        item,
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    return cc.CandidateReference(item, object_id)


def origin(
    ref: cc.CandidateReference,
    origin_class: str = "exact_domain_construction",
) -> cc.CandidateOriginClassification:
    return cc.CandidateOriginClassification(
        origin_id=f"origin-{ref.candidate.candidate_id}",
        candidate_id=ref.candidate.candidate_id,
        candidate_object_id=ref.candidate_object_id,
        origin_class=origin_class,
        source_refs=("unit-test",),
        rationale="screening provenance only",
    )


def detector() -> cc.DuplicateDeadFamilyDetector:
    return cc.DuplicateDeadFamilyDetector(
        structural_threshold=0.60,
        dead_family_threshold=0.60,
        minimum_shared_tokens=3,
    )


def failure(candidate_id: str) -> cc.FailureRecord:
    return cc.FailureRecord(
        failure_id=f"failure-{candidate_id}",
        candidate_id=candidate_id,
        domain_id=DOMAIN,
        failed_constraint="CIRCULAR_REGULARITY",
        failure_class="circular_estimate",
        evidence_ids=(),
        reusable_lesson="Do not assume the estimate that the argument must prove.",
        claim_level_before="exploratory",
        claim_level_after="exploratory",
        recorded_by="unit-test",
    )


def test_exact_fingerprint_ignores_identity_and_machine_provenance():
    a = candidate("a", "Investigate a scale local vorticity estimate.")
    b = candidate("b", "  INVESTIGATE   a scale local vorticity estimate. ")
    assert cc.candidate_exact_fingerprint(a) == cc.candidate_exact_fingerprint(b)


def test_exact_duplicate_requires_review_but_never_auto_rejects(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    prior = persist(ledger, candidate("prior", "Investigate a scale local vorticity estimate."))
    current = persist(ledger, candidate("current", "INVESTIGATE a scale local vorticity estimate."))
    report = detector().screen(
        report_id="exact",
        candidate=current,
        origin=origin(current),
        prior_candidates=(prior,),
        dead_families=(),
    )
    assert report.primary_classification == "exact_duplicate"
    assert report.flags == ("exact_duplicate",)
    assert report.review_required is True
    assert report.automatic_rejection is False
    assert report.mathematical_equivalence_established is False
    assert report.proof_of_falsehood is False
    assert report.claim_level_effect == "none"
    assert report.evidence_effect == "none"


def test_structural_near_match_does_not_establish_equivalence(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    prior = persist(
        ledger,
        candidate(
            "prior",
            "Investigate scale local vorticity control through a critical continuation estimate.",
            assumptions=("bound the critical vorticity quantity without circular smoothness",),
        ),
    )
    current = persist(
        ledger,
        candidate(
            "current",
            "Investigate scale local vorticity control using a critical continuation estimate.",
            assumptions=("bound the critical vorticity quantity without assuming smoothness",),
        ),
    )
    report = detector().screen(
        report_id="near",
        candidate=current,
        origin=origin(current),
        prior_candidates=(prior,),
        dead_families=(),
    )
    assert report.primary_classification == "structural_near_duplicate"
    assert report.max_structural_score >= report.structural_threshold
    assert report.mathematical_equivalence_established is False


def test_cross_track_identical_text_is_not_collapsed(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    prior = persist(ledger, candidate("prior", "Investigate scale local vorticity.", track=BRK))
    current = persist(ledger, candidate("current", "Investigate scale local vorticity.", track=REG))
    report = detector().screen(
        report_id="cross-track",
        candidate=current,
        origin=origin(current),
        prior_candidates=(prior,),
        dead_families=(),
    )
    assert report.primary_classification == "novel_to_screening_memory"
    assert report.flags == ()


def test_failure_backed_family_match_is_review_only(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    prior = persist(
        ledger,
        candidate(
            "failed-source",
            "Investigate scale local vorticity control with a critical bootstrap estimate.",
            assumptions=("close the critical vorticity estimate by a bootstrap bound",),
        ),
    )
    failed = failure("failed-source")
    failure_object_id = ledger.persist_failure(
        failed,
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    family = cc.DeadFamilyRecord.from_failure_candidate(
        family_id="family-circular-vorticity",
        candidate=prior.candidate,
        candidate_object_id=prior.candidate_object_id,
        failures=(failed,),
        failure_object_ids=(failure_object_id,),
    )
    screening = cc.DuplicateScreeningJournal(tmp_path / "screening")
    family_object_id = screening.record_dead_family(family, ledger_replay=ledger.verify())

    current = persist(
        ledger,
        candidate(
            "current",
            "Investigate scale local vorticity control using a critical bootstrap estimate.",
            assumptions=("close the critical vorticity estimate using a bootstrap bound",),
        ),
    )
    report = detector().screen(
        report_id="family-match",
        candidate=current,
        origin=origin(current),
        prior_candidates=(),
        dead_families=((family, family_object_id),),
    )
    assert report.primary_classification == "dead_family_match"
    assert report.review_required is True
    assert report.proof_of_falsehood is False
    assert report.automatic_rejection is False


def test_authority_escalation_mutations_fail(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    current = persist(ledger, candidate("current", "Investigate a pressure decomposition."))
    report = detector().screen(
        report_id="report",
        candidate=current,
        origin=origin(current, "heuristic"),
        prior_candidates=(),
        dead_families=(),
    )
    with pytest.raises(cc.DuplicateDetectorError):
        replace(report, automatic_rejection=True).validate()
    with pytest.raises(cc.DuplicateDetectorError):
        replace(report, mathematical_equivalence_established=True).validate()
    with pytest.raises(cc.DuplicateDetectorError):
        replace(report, claim_level_effect="promote").validate()
    with pytest.raises(cc.DuplicateDetectorError):
        replace(origin(current), evidence_effect="supporting").validate()


def test_thresholds_are_explicit_local_parameters():
    with pytest.raises(cc.DuplicateDetectorError):
        cc.DuplicateDeadFamilyDetector(
            structural_threshold=0.0,
            dead_family_threshold=0.6,
            minimum_shared_tokens=3,
        )
    with pytest.raises(cc.DuplicateDetectorError):
        cc.DuplicateDeadFamilyDetector(
            structural_threshold=0.6,
            dead_family_threshold=1.1,
            minimum_shared_tokens=3,
        )


def test_screening_journal_binds_candidate_to_verified_ledger(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    ref = persist(ledger, candidate("candidate", "Investigate one mechanism."))
    journal = cc.DuplicateScreeningJournal(tmp_path / "screening")
    bad = replace(origin(ref), candidate_object_id="sha256:" + "0" * 64)
    with pytest.raises(cc.DuplicateMemoryError):
        journal.record_origin(bad, ledger_replay=ledger.verify())


def test_screening_journal_rejects_unpersisted_failure_object(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    ref = persist(ledger, candidate("failed-source", "Investigate one mechanism."))
    failed = failure("failed-source")
    family = cc.DeadFamilyRecord.from_failure_candidate(
        family_id="family",
        candidate=ref.candidate,
        candidate_object_id=ref.candidate_object_id,
        failures=(failed,),
        failure_object_ids=("sha256:" + "f" * 64,),
    )
    journal = cc.DuplicateScreeningJournal(tmp_path / "screening")
    with pytest.raises(cc.DuplicateMemoryError):
        journal.record_dead_family(family, ledger_replay=ledger.verify())


def test_screening_journal_detects_event_tampering(tmp_path: Path):
    ledger = cc.ContentAddressedLedger(tmp_path / "ledger")
    ref = persist(ledger, candidate("candidate", "Investigate one mechanism."))
    journal = cc.DuplicateScreeningJournal(tmp_path / "screening")
    journal.record_origin(origin(ref), ledger_replay=ledger.verify())
    event = json.loads(journal.log_path.read_text("utf-8"))
    event["logical_id"] = "tampered"
    journal.log_path.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(cc.DuplicateMemoryError):
        journal.verify()
