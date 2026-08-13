# SPDX-License-Identifier: Apache-2.0

import pytest

from crucible_core import (
    Candidate,
    ConstraintResult,
    Crucible,
    CrucibleStateError,
    EvidenceRecord,
    HypothesisSet,
)


LEVELS = (
    "exploratory",
    "reproduced_numerical",
    "candidate_lemma",
    "proved_lemma",
    "externally_checked_theorem",
    "publication_candidate",
    "public_solution_claim",
)

BARRIER_SEVERITIES = {
    "NUMERICAL_CONTINUUM_GAP": "hard",
}


def make_candidate(
    candidate_id: str,
    hypothesis: str,
    *,
    hypothesis_set_id: str = "NS_PRIMARY_COMPETITION",
    claim_level: str = "exploratory",
    parent_candidate_ids: tuple[str, ...] = (),
    status: str = "active",
    frozen: bool = False,
) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        domain_id="navier_stokes_3d_incompressible",
        hypothesis_set_id=hypothesis_set_id,
        hypothesis=hypothesis,
        claim_level=claim_level,
        generation_method="unit_test",
        parent_candidate_ids=parent_candidate_ids,
        status=status,
        frozen=frozen,
    )


def make_crucible() -> Crucible:
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
        constraint_severities=BARRIER_SEVERITIES,
    )
    crucible.register_candidate(make_candidate("regularity", "global smoothness"))
    crucible.register_candidate(make_candidate("breakdown", "finite-time breakdown"))
    crucible.register_hypothesis_set(
        HypothesisSet(
            hypothesis_set_id="NS_PRIMARY_COMPETITION",
            domain_id="navier_stokes_3d_incompressible",
            candidate_ids=("regularity", "breakdown"),
        )
    )
    return crucible


def make_barrier_evidence(
    evidence_id: str,
    candidate_id: str,
    *,
    stage: str = "development",
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        domain_id="navier_stokes_3d_incompressible",
        candidate_id=candidate_id,
        evidence_kind="challenging",
        stage=stage,
        source_ref="research/proof_barriers.json",
        provenance_ref="barrier:NUMERICAL_CONTINUUM_GAP",
        summary="candidate lacks a rigorous discrete-to-continuum bridge",
        reproducible=True,
    )


def make_hard_result(
    result_id: str,
    candidate_id: str,
    evidence_id: str,
    *,
    severity: str = "hard",
) -> ConstraintResult:
    return ConstraintResult(
        result_id=result_id,
        domain_id="navier_stokes_3d_incompressible",
        candidate_id=candidate_id,
        constraint_id="NUMERICAL_CONTINUUM_GAP",
        outcome="fail",
        severity=severity,
        evidence_ids=(evidence_id,),
        explanation="no rigorous discrete-to-continuum bridge supplied",
    )


def record_hard_failure(
    crucible: Crucible,
    result: ConstraintResult,
    *,
    failure_id: str,
    claim_level_after: str = "exploratory",
):
    return crucible.record_constraint_result(
        result,
        failure_id=failure_id,
        failure_class="discrete_continuum_gap",
        reusable_lesson="do not regenerate this family without a rigorous continuum bridge",
        claim_level_after=claim_level_after,
        recorded_by="unit_test",
    )


def test_competing_hypothesis_set_has_no_default_winner():
    crucible = make_crucible()
    state = crucible.export_state()
    assert state["hypothesis_sets"][0]["selection_state"] == "unresolved"
    assert state["hypothesis_sets"][0]["preferred_candidate_id"] is None
    assert state["universal_confidence_score"] is None
    assert set(crucible.frontier()) == {"regularity", "breakdown"}


def test_holdout_evidence_is_sealed_until_candidate_freeze():
    crucible = make_crucible()
    holdout = make_barrier_evidence("heldout-1", "regularity", stage="holdout")
    with pytest.raises(CrucibleStateError):
        crucible.attach_evidence(holdout)

    crucible.freeze_candidate("regularity")
    crucible.attach_evidence(holdout)
    assert any(item["evidence_id"] == "heldout-1" for item in crucible.export_state()["evidence"])


def test_hard_failure_requires_append_only_failure_record_and_removes_frontier_candidate():
    crucible = make_crucible()
    evidence = make_barrier_evidence("e1", "breakdown")
    crucible.attach_evidence(evidence)
    result = make_hard_result("r1", "breakdown", "e1")

    with pytest.raises(CrucibleStateError):
        crucible.record_constraint_result(result)

    failure = record_hard_failure(crucible, result, failure_id="f1")
    assert failure is not None
    assert crucible.frontier() == ("regularity",)
    assert crucible.failure_ledger()[0].reusable_lesson.startswith("do not regenerate")


def test_failure_record_cannot_promote_claim_level_and_rejected_transaction_is_atomic():
    crucible = make_crucible()
    crucible.attach_evidence(make_barrier_evidence("e-promote", "breakdown"))
    result = make_hard_result("r-promote", "breakdown", "e-promote")

    with pytest.raises(CrucibleStateError, match="may not promote"):
        record_hard_failure(
            crucible,
            result,
            failure_id="f-promote",
            claim_level_after="public_solution_claim",
        )

    state = crucible.export_state()
    assert all(item["result_id"] != "r-promote" for item in state["constraint_results"])
    assert state["failure_ledger"] == []
    assert set(crucible.frontier()) == {"regularity", "breakdown"}


def test_failed_failure_validation_does_not_poison_corrected_retry():
    crucible = make_crucible()
    crucible.attach_evidence(make_barrier_evidence("e-breakdown", "breakdown"))
    first = make_hard_result("r-first", "breakdown", "e-breakdown")
    record_hard_failure(crucible, first, failure_id="duplicate-id")

    crucible.attach_evidence(make_barrier_evidence("e-regularity", "regularity"))
    second = make_hard_result("r-second", "regularity", "e-regularity")
    with pytest.raises(CrucibleStateError, match="failure_id already"):
        record_hard_failure(crucible, second, failure_id="duplicate-id")

    state_after_reject = crucible.export_state()
    assert all(item["result_id"] != "r-second" for item in state_after_reject["constraint_results"])

    failure = record_hard_failure(crucible, second, failure_id="corrected-id")
    assert failure is not None
    assert len(crucible.failure_ledger()) == 2


def test_constraint_evidence_must_belong_to_same_candidate():
    crucible = make_crucible()
    crucible.freeze_candidate("regularity")
    holdout = make_barrier_evidence("heldout-foreign", "regularity", stage="holdout")
    crucible.attach_evidence(holdout)

    cross_candidate = make_hard_result("r-cross", "breakdown", "heldout-foreign")
    with pytest.raises(CrucibleStateError, match="same candidate"):
        record_hard_failure(crucible, cross_candidate, failure_id="f-cross")

    assert all(
        item["result_id"] != "r-cross"
        for item in crucible.export_state()["constraint_results"]
    )


def test_domain_adapter_severity_cannot_be_softened_by_caller():
    crucible = make_crucible()
    crucible.attach_evidence(make_barrier_evidence("e-soften", "breakdown"))
    softened = make_hard_result(
        "r-soften",
        "breakdown",
        "e-soften",
        severity="soft",
    )
    with pytest.raises(CrucibleStateError, match="requires hard"):
        crucible.record_constraint_result(softened)

    assert set(crucible.frontier()) == {"regularity", "breakdown"}


def test_soft_failure_for_unregistered_constraint_does_not_select_competitor():
    crucible = make_crucible()
    result = ConstraintResult(
        result_id="soft-1",
        domain_id="navier_stokes_3d_incompressible",
        candidate_id="regularity",
        constraint_id="heuristic_weakness",
        outcome="fail",
        severity="soft",
        evidence_ids=(),
        explanation="interesting but not a hard domain falsifier",
    )
    assert crucible.record_constraint_result(result) is None
    assert set(crucible.frontier()) == {"regularity", "breakdown"}


def test_pre_rejected_candidate_cannot_be_registered_without_failure_ledger():
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
    )
    candidate = make_candidate(
        "pre-rejected",
        "already rejected without provenance",
        hypothesis_set_id="H",
        status="rejected_by_domain_constraint",
        frozen=True,
    )
    with pytest.raises(CrucibleStateError, match="active status"):
        crucible.register_candidate(candidate)


def test_hypothesis_set_membership_must_be_reciprocal():
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
    )
    for cid in ("a", "b", "c"):
        crucible.register_candidate(
            make_candidate(cid, f"hypothesis {cid}", hypothesis_set_id="H")
        )

    with pytest.raises(CrucibleStateError, match="membership must be reciprocal"):
        crucible.register_hypothesis_set(
            HypothesisSet(
                hypothesis_set_id="H",
                domain_id="navier_stokes_3d_incompressible",
                candidate_ids=("a", "b"),
            )
        )


def test_late_candidate_requires_atomic_hypothesis_set_addition():
    crucible = make_crucible()
    child = make_candidate(
        "regularity-child",
        "refined regularity candidate",
        parent_candidate_ids=("regularity",),
    )

    with pytest.raises(CrucibleStateError, match="add_candidate_to_hypothesis_set"):
        crucible.register_candidate(child)

    crucible.add_candidate_to_hypothesis_set(child)
    state = crucible.export_state()
    assert "regularity-child" in state["hypothesis_sets"][0]["candidate_ids"]
    assert "regularity-child" in crucible.frontier()


def test_state_fingerprint_is_deterministic_for_same_state():
    a = make_crucible().export_state()
    b = make_crucible().export_state()
    assert a["state_sha256"] == b["state_sha256"]


def test_parentage_must_reference_existing_candidate():
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
    )
    child = make_candidate(
        "child",
        "refined idea",
        hypothesis_set_id="set",
        parent_candidate_ids=("missing",),
    )
    with pytest.raises(CrucibleStateError):
        crucible.register_candidate(child)
