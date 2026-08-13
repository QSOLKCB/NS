# SPDX-License-Identifier: Apache-2.0

import pytest

from crucible_core import (
    AnalogyFirewall,
    AnalogyFirewallError,
    AnalogyRecord,
)


def record(
    analogy_id="laplacian",
    mapping_class="operator_correspondence",
    target_domain="navier_stokes_3d_incompressible",
    allowed_uses=("candidate_generation",),
):
    return AnalogyRecord(
        analogy_id=analogy_id,
        source_domain="source",
        target_domain=target_domain,
        mapping_class=mapping_class,
        shared_structure="shared mathematical structure",
        assumptions=("operator-level comparison only",),
        known_differences=("source and target state spaces differ",),
        allowed_uses=allowed_uses,
        forbidden_inferences=("shared structure does not imply shared dynamics",),
        provenance_ref="unit:test",
    )


def firewall():
    fw = AnalogyFirewall(target_domain="navier_stokes_3d_incompressible")
    fw.register(record())
    return fw


def test_operator_analogy_can_only_seed_exploratory_candidate():
    fw = firewall()
    candidate = fw.issue_candidate(
        analogy_id="laplacian",
        candidate_id="candidate-1",
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="try a target-domain estimate suggested by the shared operator",
        generation_method="unit-test",
    )
    assert candidate.claim_level == "exploratory"
    assert candidate.domain_id == "navier_stokes_3d_incompressible"
    assert "analogy_source=laplacian" in candidate.assumptions
    assert "mapping_class=operator_correspondence" in candidate.assumptions
    assert candidate.generation_method.startswith("cross_domain_transfer:laplacian:")


@pytest.mark.parametrize(
    "forbidden_use",
    [
        "domain_evidence",
        "claim_promotion",
        "proof_barrier_satisfaction",
        "domain_equivalence_claim",
        "winner_selection",
    ],
)
def test_firewall_forbids_authority_escalation(forbidden_use):
    fw = firewall()
    with pytest.raises(AnalogyFirewallError):
        fw.authorize_use("laplacian", forbidden_use)


@pytest.mark.parametrize("mapping_class", ["visual_resemblance", "explicit_non_correspondence"])
def test_negative_control_classes_cannot_generate_positive_candidate(mapping_class):
    fw = AnalogyFirewall(target_domain="navier_stokes_3d_incompressible")
    fw.register(
        record(
            analogy_id="negative",
            mapping_class=mapping_class,
            allowed_uses=("negative_control",),
        )
    )
    with pytest.raises(AnalogyFirewallError):
        fw.issue_candidate(
            analogy_id="negative",
            candidate_id="bad",
            hypothesis_set_id="NS_PRIMARY_COMPETITION",
            hypothesis="must not exist",
            generation_method="unit-test",
        )


def test_record_rejects_positive_use_for_visual_resemblance():
    item = record(
        mapping_class="visual_resemblance",
        allowed_uses=("candidate_generation",),
    )
    with pytest.raises(ValueError):
        item.validate()


def test_target_domain_mismatch_blocks_candidate_generation():
    fw = AnalogyFirewall(target_domain="navier_stokes_3d_incompressible")
    fw.register(record(target_domain="another_domain"))
    with pytest.raises(AnalogyFirewallError):
        fw.issue_candidate(
            analogy_id="laplacian",
            candidate_id="wrong-domain",
            hypothesis_set_id="NS_PRIMARY_COMPETITION",
            hypothesis="wrong domain",
            generation_method="unit-test",
        )


def test_registry_export_and_authority_snapshot_are_deterministic_and_non_evidentiary():
    fw = firewall()
    assert fw.export_registry()[0]["analogy_id"] == "laplacian"
    authority = fw.authority_snapshot()
    assert authority["candidate_generation"] is True
    assert authority["domain_evidence"] is False
    assert authority["claim_promotion"] is False
    assert authority["proof_barrier_satisfaction"] is False
    assert authority["domain_equivalence_claim"] is False
    assert authority["winner_selection"] is False
    assert authority["target_domain_validation_required"] is True
    assert authority["source_proof_status_inherited"] is False
    assert authority["source_evidence_status_inherited"] is False


def test_duplicate_analogy_id_is_rejected():
    fw = firewall()
    with pytest.raises(AnalogyFirewallError):
        fw.register(record())


def test_known_differences_and_forbidden_inferences_are_required():
    item = AnalogyRecord(
        analogy_id="bad",
        source_domain="source",
        target_domain="target",
        mapping_class="heuristic_analogy",
        shared_structure="something",
        assumptions=(),
        known_differences=(),
        allowed_uses=("candidate_generation",),
        forbidden_inferences=(),
        provenance_ref="unit:test",
    )
    with pytest.raises(ValueError):
        item.validate()
