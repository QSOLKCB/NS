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


def make_candidate(candidate_id: str, hypothesis: str) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        domain_id="navier_stokes_3d_incompressible",
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis=hypothesis,
        claim_level="exploratory",
        generation_method="unit_test",
    )


def make_crucible() -> Crucible:
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
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


def test_competing_hypothesis_set_has_no_default_winner():
    crucible = make_crucible()
    state = crucible.export_state()
    assert state["hypothesis_sets"][0]["selection_state"] == "unresolved"
    assert state["hypothesis_sets"][0]["preferred_candidate_id"] is None
    assert state["universal_confidence_score"] is None
    assert set(crucible.frontier()) == {"regularity", "breakdown"}


def test_holdout_evidence_is_sealed_until_candidate_freeze():
    crucible = make_crucible()
    holdout = EvidenceRecord(
        evidence_id="heldout-1",
        domain_id="navier_stokes_3d_incompressible",
        candidate_id="regularity",
        evidence_kind="challenging",
        stage="holdout",
        source_ref="sealed:test",
        provenance_ref="sha256:test",
        summary="held-out adversarial case",
        reproducible=True,
    )
    with pytest.raises(CrucibleStateError):
        crucible.attach_evidence(holdout)

    crucible.freeze_candidate("regularity")
    crucible.attach_evidence(holdout)
    assert any(item["evidence_id"] == "heldout-1" for item in crucible.export_state()["evidence"])


def test_hard_failure_requires_append_only_failure_record_and_removes_frontier_candidate():
    crucible = make_crucible()
    evidence = EvidenceRecord(
        evidence_id="e1",
        domain_id="navier_stokes_3d_incompressible",
        candidate_id="breakdown",
        evidence_kind="challenging",
        stage="development",
        source_ref="research/proof_barriers.json",
        provenance_ref="barrier:NUMERICAL_CONTINUUM_GAP",
        summary="candidate attempts to promote finite-resolution behavior directly to continuum blow-up",
        reproducible=True,
    )
    crucible.attach_evidence(evidence)
    result = ConstraintResult(
        result_id="r1",
        domain_id="navier_stokes_3d_incompressible",
        candidate_id="breakdown",
        constraint_id="NUMERICAL_CONTINUUM_GAP",
        outcome="fail",
        severity="hard",
        evidence_ids=("e1",),
        explanation="no rigorous discrete-to-continuum bridge supplied",
    )

    with pytest.raises(CrucibleStateError):
        crucible.record_constraint_result(result)

    failure = crucible.record_constraint_result(
        result,
        failure_id="f1",
        failure_class="discrete_continuum_gap",
        reusable_lesson="do not regenerate this family without a rigorous continuum bridge",
        claim_level_after="exploratory",
        recorded_by="unit_test",
    )
    assert failure is not None
    assert crucible.frontier() == ("regularity",)
    assert crucible.failure_ledger()[0].reusable_lesson.startswith("do not regenerate")


def test_soft_failure_does_not_select_competitor_or_remove_candidate():
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


def test_state_fingerprint_is_deterministic_for_same_state():
    a = make_crucible().export_state()
    b = make_crucible().export_state()
    assert a["state_sha256"] == b["state_sha256"]


def test_parentage_must_reference_existing_candidate():
    crucible = Crucible(
        domain_id="navier_stokes_3d_incompressible",
        allowed_claim_levels=LEVELS,
    )
    child = Candidate(
        candidate_id="child",
        domain_id="navier_stokes_3d_incompressible",
        hypothesis_set_id="set",
        hypothesis="refined idea",
        claim_level="exploratory",
        generation_method="mutation",
        parent_candidate_ids=("missing",),
    )
    with pytest.raises(CrucibleStateError):
        crucible.register_candidate(child)
