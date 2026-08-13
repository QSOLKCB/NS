#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the machine-readable QSOL NS agent contract and key invariants."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "AGENTS.md"
SCHEMA_PATH = ROOT / "AGENTS.schema.json"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_rejected(validator: Draft202012Validator, candidate: object, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"schema regression: forbidden mutation accepted: {label}")


def main() -> None:
    contract = load_json(CONTRACT_PATH)
    schema = load_json(SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(contract)

    mutated = copy.deepcopy(contract)
    mutated["branch_policy"]["direct_main_write"] = True
    require_rejected(validator, mutated, "direct_main_write=true")

    mutated = copy.deepcopy(contract)
    del mutated["human_operator"]["role"]
    require_rejected(validator, mutated, "missing human_operator.role")

    mutated = copy.deepcopy(contract)
    mutated["claim_promotion"]["public_solution_claim_requires_completed_external_mathematical_review"] = False
    require_rejected(validator, mutated, "external review gate disabled")

    mutated = copy.deepcopy(contract)
    mutated["experiment_requirements"]["required_fields"].remove("created_at_utc")
    require_rejected(validator, mutated, "experiment field removed")

    mutated = copy.deepcopy(contract)
    mutated["proof_requirements"]["formal_artifact_required_fields"].remove("encoded_statement")
    require_rejected(validator, mutated, "formal provenance field removed")

    for boot_step, label in [
        ("run_tools_validate_boundary_map_py", "boundary validator removed from agent boot"),
        ("run_tools_validate_lab_contract_py", "lab validator removed from agent boot"),
        ("run_tools_validate_precision_referee_py", "precision referee validator removed from agent boot"),
        ("run_tools_validate_crucible_core_py", "Crucible validator removed from agent boot"),
        ("run_tools_validate_analogy_firewall_py", "Analogy Firewall validator removed from agent boot"),
        ("run_tools_validate_crucible_ledger_py", "Crucible ledger validator removed from agent boot"),
        ("run_tools_validate_ml_generator_py", "ML generator validator removed from agent boot"),
        ("read_research_precision_referee_contract_json", "precision referee contract removed from agent boot"),
        ("read_research_crucible_contract_json", "Crucible contract removed from agent boot"),
        ("read_research_ns_crucible_adapter_json", "NS Crucible adapter removed from agent boot"),
        ("read_research_analogy_firewall_contract_json", "Analogy Firewall contract removed from agent boot"),
        ("read_research_cross_domain_transfer_registry_json", "transfer registry removed from agent boot"),
        ("read_research_ns_cross_domain_transfer_adapter_json", "NS transfer adapter removed from agent boot"),
        ("read_research_crucible_ledger_contract_json", "Crucible ledger contract removed from agent boot"),
        ("read_research_ml_generator_contract_json", "ML generator contract removed from agent boot"),
        ("read_research_ns_ml_generator_adapter_json", "NS ML generator adapter removed from agent boot"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["agent_boot_sequence"].remove(boot_step)
        require_rejected(validator, mutated, label)

    mutated = copy.deepcopy(contract)
    mutated["literature_boundary_policy"]["secondary_sources_may_discover_but_not_authorize"] = False
    require_rejected(validator, mutated, "secondary-source authority boundary disabled")

    mutated = copy.deepcopy(contract)
    mutated["literature_boundary_policy"]["hypothesis_weakening_without_proof_forbidden"] = False
    require_rejected(validator, mutated, "hypothesis weakening protection disabled")

    mutated = copy.deepcopy(contract)
    mutated["literature_boundary_policy"]["domain_or_forcing_substitution_without_bridge_forbidden"] = False
    require_rejected(validator, mutated, "domain/forcing bridge protection disabled")

    for invariant, label in [
        ("precision_agreement_is_not_continuum_proof", "precision evidence boundary removed"),
        ("crucible_core_does_not_define_domain_truth", "Crucible truth-authority boundary removed"),
        ("visual_resemblance_is_not_physical_mechanism", "visual resemblance boundary removed"),
        ("shared_operator_is_not_shared_dynamics", "shared-operator boundary removed"),
        ("structural_analogy_is_not_domain_equivalence", "domain-equivalence analogy boundary removed"),
        ("analogy_is_not_domain_evidence", "analogy evidence firewall removed"),
        ("analogy_cannot_promote_claim", "analogy claim-promotion firewall removed"),
        ("cross_domain_transfer_requires_target_domain_validation", "target-domain validation requirement removed"),
        ("persisted_state_is_not_truth", "persistence truth boundary removed"),
        ("ledger_replay_is_not_claim_promotion", "ledger replay promotion boundary removed"),
        ("content_addressing_is_not_mathematical_validation", "content-addressing validation boundary removed"),
        ("mutable_history_is_not_research_provenance", "immutable history boundary removed"),
        ("transfer_ticket_is_not_domain_evidence", "transfer-ticket evidence boundary removed"),
        ("model_output_is_not_candidate", "model output/candidate boundary removed"),
        ("valid_json_is_not_valid_research_candidate", "JSON/research-candidate boundary removed"),
        ("generator_output_is_not_domain_evidence", "generator evidence boundary removed"),
        ("generator_output_is_not_claim_promotion", "generator claim boundary removed"),
        ("generator_self_assessment_is_not_evidence_status", "generator self-assessment boundary removed"),
        ("invalid_generation_attempt_is_not_mathematical_failure", "generation failure/math failure boundary removed"),
        ("accepted_candidate_is_not_surviving_candidate", "accepted/surviving candidate boundary removed"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["research_invariants"].remove(invariant)
        require_rejected(validator, mutated, label)

    for field, label in [
        ("core_may_define_domain_truth", "Crucible granted domain-truth authority"),
        ("core_may_promote_claim", "Crucible granted claim-promotion authority"),
        ("core_may_select_winner", "Crucible granted winner-selection authority"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["crucible_policy"][field] = True
        require_rejected(validator, mutated, label)

    mutated = copy.deepcopy(contract)
    mutated["crucible_policy"]["holdout_access_requires_candidate_freeze"] = False
    require_rejected(validator, mutated, "Crucible holdout freeze gate disabled")

    mutated = copy.deepcopy(contract)
    mutated["crucible_policy"]["negative_results_preserved"] = False
    require_rejected(validator, mutated, "Crucible negative-result preservation disabled")

    for field, label in [
        ("analogy_may_be_domain_evidence", "analogy granted domain-evidence authority"),
        ("analogy_may_promote_claim", "analogy granted claim-promotion authority"),
        ("analogy_may_satisfy_proof_barrier", "analogy granted proof-barrier authority"),
        ("analogy_may_select_winner", "analogy granted winner-selection authority"),
        ("analogy_may_assert_domain_equivalence", "analogy granted domain-equivalence authority"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["analogy_policy"][field] = True
        require_rejected(validator, mutated, label)

    mutated = copy.deepcopy(contract)
    mutated["analogy_policy"]["target_domain_validation_required"] = False
    require_rejected(validator, mutated, "analogy target-domain validation disabled")

    mutated = copy.deepcopy(contract)
    mutated["analogy_policy"]["analogy_derived_candidate_initial_claim_level"] = "candidate_lemma"
    require_rejected(validator, mutated, "analogy-derived candidate starts above exploratory")

    for field, label in [
        ("objects_immutable", "ledger object immutability disabled"),
        ("logical_ref_rebinding_forbidden", "ledger ref rebinding enabled"),
        ("event_log_append_only", "ledger event log made mutable"),
        ("event_log_sha256_hash_chained", "ledger event hash chain disabled"),
        ("event_provenance_requires_actor_source_commit_and_utc", "ledger event provenance weakened"),
        ("analogy_derived_candidate_requires_transfer_ticket", "transfer ticket requirement disabled"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["ledger_policy"][field] = False
        require_rejected(validator, mutated, label)

    for field, label in [
        ("ledger_may_define_truth", "ledger granted truth authority"),
        ("ledger_may_promote_claim", "ledger granted claim-promotion authority"),
        ("ledger_may_select_winner", "ledger granted winner-selection authority"),
        ("persistence_creates_domain_evidence", "persistence granted evidence authority"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["ledger_policy"][field] = True
        require_rejected(validator, mutated, label)

    for field, label in [
        ("model_output_is_candidate", "model output made candidate automatically"),
        ("generator_may_be_domain_evidence", "generator granted domain-evidence authority"),
        ("generator_may_promote_claim", "generator granted claim-promotion authority"),
        ("generator_may_assign_proof_status", "generator granted proof authority"),
        ("generator_may_select_winner", "generator granted winner authority"),
        ("direct_analogy_bypass", "generator granted Analogy Firewall bypass"),
        ("model_facing_airlock_may_mutate_crucible_ledger", "model-facing airlock granted ledger mutation"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["generator_policy"][field] = True
        require_rejected(validator, mutated, label)

    mutated = copy.deepcopy(contract)
    mutated["generator_policy"]["accepted_candidate_initial_claim_level"] = "candidate_lemma"
    require_rejected(validator, mutated, "ML candidate starts above exploratory")

    for field, label in [
        ("every_attempt_recorded", "generation attempts may disappear"),
        ("rejected_attempts_recorded", "rejected generation attempts may disappear"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["generator_policy"][field] = False
        require_rejected(validator, mutated, label)

    for field, label in [
        ("check_cross_domain_analogy_classification", "cross-domain analogy classification review disabled"),
        ("check_analogy_target_revalidation", "analogy target revalidation review disabled"),
        ("check_content_addressed_ledger_integrity", "ledger integrity review disabled"),
        ("check_transfer_ticket_provenance", "transfer-ticket provenance review disabled"),
        ("check_ml_generator_authority", "ML generator authority review disabled"),
        ("check_generation_attempt_provenance", "generation-attempt provenance review disabled"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated["review_policy"][field] = False
        require_rejected(validator, mutated, label)

    print("AGENTS contract validation: PASS")


if __name__ == "__main__":
    main()
