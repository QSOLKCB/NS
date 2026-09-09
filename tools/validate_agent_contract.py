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


def remove_boot_step(contract: dict, validator: Draft202012Validator, step: str, label: str) -> None:
    mutated = copy.deepcopy(contract)
    mutated["agent_boot_sequence"].remove(step)
    require_rejected(validator, mutated, label)


def flip_bool(contract: dict, validator: Draft202012Validator, section: str, field: str, value: bool, label: str) -> None:
    mutated = copy.deepcopy(contract)
    mutated[section][field] = value
    require_rejected(validator, mutated, label)


def main() -> None:
    contract = load_json(CONTRACT_PATH)
    schema = load_json(SCHEMA_PATH)
    if not isinstance(contract, dict) or not isinstance(schema, dict):
        raise SystemExit("AGENTS contract and schema must both be JSON objects")

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(contract)

    mutated = copy.deepcopy(contract)
    mutated["branch_policy"]["direct_main_write"] = True
    require_rejected(validator, mutated, "direct_main_write=true")

    mutated = copy.deepcopy(contract)
    del mutated["human_operator"]["role"]
    require_rejected(validator, mutated, "missing human_operator.role")

    flip_bool(
        contract,
        validator,
        "claim_promotion",
        "public_solution_claim_requires_completed_external_mathematical_review",
        False,
        "external review gate disabled",
    )

    mutated = copy.deepcopy(contract)
    mutated["experiment_requirements"]["required_fields"].remove("created_at_utc")
    require_rejected(validator, mutated, "experiment field removed")

    mutated = copy.deepcopy(contract)
    mutated["proof_requirements"]["formal_artifact_required_fields"].remove("encoded_statement")
    require_rejected(validator, mutated, "formal provenance field removed")

    required_boot_steps = [
        ("run_tools_validate_boundary_map_py", "boundary validator removed from agent boot"),
        ("run_tools_validate_external_claim_registry_py", "external-claim validator removed from agent boot"),
        ("run_tools_validate_lab_contract_py", "lab validator removed from agent boot"),
        ("run_tools_validate_precision_referee_py", "precision referee validator removed from agent boot"),
        ("run_tools_validate_crucible_core_py", "Crucible validator removed from agent boot"),
        ("run_tools_validate_analogy_firewall_py", "Analogy Firewall validator removed from agent boot"),
        ("run_tools_validate_crucible_ledger_py", "Crucible ledger validator removed from agent boot"),
        ("run_tools_validate_ml_generator_py", "ML generator validator removed from agent boot"),
        ("run_tools_validate_candidate_transform_py", "candidate-transform validator removed from agent boot"),
        ("read_research_external_claim_registry_json", "external-claim registry removed from agent boot"),
        ("read_research_precision_referee_contract_json", "precision referee contract removed from agent boot"),
        ("read_research_crucible_contract_json", "Crucible contract removed from agent boot"),
        ("read_research_ns_crucible_adapter_json", "NS Crucible adapter removed from agent boot"),
        ("read_research_analogy_firewall_contract_json", "Analogy Firewall contract removed from agent boot"),
        ("read_research_cross_domain_transfer_registry_json", "transfer registry removed from agent boot"),
        ("read_research_ns_cross_domain_transfer_adapter_json", "NS transfer adapter removed from agent boot"),
        ("read_research_crucible_ledger_contract_json", "Crucible ledger contract removed from agent boot"),
        ("read_research_ml_generator_contract_json", "ML generator contract removed from agent boot"),
        ("read_research_ns_ml_generator_adapter_json", "NS ML generator adapter removed from agent boot"),
        ("read_research_candidate_transform_contract_json", "candidate-transform contract removed from agent boot"),
        ("read_research_ns_candidate_transform_adapter_json", "NS candidate-transform adapter removed from agent boot"),
    ]
    for step, label in required_boot_steps:
        remove_boot_step(contract, validator, step, label)

    expected_external_policy = {
        "external_claim_registry": "research/external_claim_registry.json",
        "external_claim_validator": "tools/validate_external_claim_registry.py",
    }
    for field, expected in expected_external_policy.items():
        if contract["literature_boundary_policy"].get(field) != expected:
            raise SystemExit(f"agent contract missing external-claim policy binding: {field}")
        mutated = copy.deepcopy(contract)
        mutated["literature_boundary_policy"][field] = "wrong"
        require_rejected(validator, mutated, f"external-claim policy binding drift: {field}")

    flip_bool(
        contract,
        validator,
        "literature_boundary_policy",
        "secondary_sources_may_discover_but_not_authorize",
        False,
        "secondary-source authority boundary disabled",
    )
    flip_bool(
        contract,
        validator,
        "literature_boundary_policy",
        "hypothesis_weakening_without_proof_forbidden",
        False,
        "hypothesis weakening protection disabled",
    )
    flip_bool(
        contract,
        validator,
        "literature_boundary_policy",
        "domain_or_forcing_substitution_without_bridge_forbidden",
        False,
        "domain/forcing bridge protection disabled",
    )

    required_invariants = [
        "precision_agreement_is_not_continuum_proof",
        "crucible_core_does_not_define_domain_truth",
        "visual_resemblance_is_not_physical_mechanism",
        "shared_operator_is_not_shared_dynamics",
        "structural_analogy_is_not_domain_equivalence",
        "analogy_is_not_domain_evidence",
        "analogy_cannot_promote_claim",
        "cross_domain_transfer_requires_target_domain_validation",
        "persisted_state_is_not_truth",
        "ledger_replay_is_not_claim_promotion",
        "content_addressing_is_not_mathematical_validation",
        "mutable_history_is_not_research_provenance",
        "transfer_ticket_is_not_domain_evidence",
        "model_output_is_not_candidate",
        "valid_json_is_not_valid_research_candidate",
        "generator_output_is_not_domain_evidence",
        "generator_output_is_not_claim_promotion",
        "generator_self_assessment_is_not_evidence_status",
        "invalid_generation_attempt_is_not_mathematical_failure",
        "accepted_candidate_is_not_surviving_candidate",
        "transform_output_is_not_domain_evidence",
        "transform_child_does_not_inherit_parent_authority",
        "operator_label_is_not_mathematical_validation",
        "crossover_is_not_proof_synthesis",
        "transform_run_is_not_ledger_commit",
    ]
    for invariant in required_invariants:
        mutated = copy.deepcopy(contract)
        mutated["research_invariants"].remove(invariant)
        require_rejected(validator, mutated, f"research invariant removed: {invariant}")

    for field in ["core_may_define_domain_truth", "core_may_promote_claim", "core_may_select_winner"]:
        flip_bool(contract, validator, "crucible_policy", field, True, f"Crucible authority enabled: {field}")
    flip_bool(contract, validator, "crucible_policy", "holdout_access_requires_candidate_freeze", False, "Crucible holdout freeze gate disabled")
    flip_bool(contract, validator, "crucible_policy", "negative_results_preserved", False, "Crucible negative-result preservation disabled")

    for field in [
        "analogy_may_be_domain_evidence",
        "analogy_may_promote_claim",
        "analogy_may_satisfy_proof_barrier",
        "analogy_may_select_winner",
        "analogy_may_assert_domain_equivalence",
    ]:
        flip_bool(contract, validator, "analogy_policy", field, True, f"analogy authority enabled: {field}")
    flip_bool(contract, validator, "analogy_policy", "target_domain_validation_required", False, "analogy target-domain validation disabled")

    for field in [
        "ledger_may_define_truth",
        "ledger_may_promote_claim",
        "ledger_may_select_winner",
        "persistence_creates_domain_evidence",
    ]:
        flip_bool(contract, validator, "ledger_policy", field, True, f"ledger authority enabled: {field}")

    for field in [
        "model_output_is_candidate",
        "generator_may_be_domain_evidence",
        "generator_may_promote_claim",
        "generator_may_assign_proof_status",
        "generator_may_select_winner",
        "direct_analogy_bypass",
        "model_facing_airlock_may_mutate_crucible_ledger",
    ]:
        flip_bool(contract, validator, "generator_policy", field, True, f"generator authority enabled: {field}")

    for field in [
        "parent_claim_level_inherited",
        "parent_evidence_inherited",
        "parent_survival_status_inherited",
        "model_may_write_engine_provenance_fields",
        "model_facing_transform_may_mutate_crucible_ledger",
    ]:
        flip_bool(contract, validator, "transform_policy", field, True, f"transform authority enabled: {field}")

    print(
        "AGENTS contract validation: PASS "
        f"(schema {contract['schema_version']}, external claim boundary boot-wired)"
    )


if __name__ == "__main__":
    main()
