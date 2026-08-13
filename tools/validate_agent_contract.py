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
        ("read_research_precision_referee_contract_json", "precision referee contract removed from agent boot"),
        ("read_research_crucible_contract_json", "Crucible contract removed from agent boot"),
        ("read_research_ns_crucible_adapter_json", "NS Crucible adapter removed from agent boot"),
        ("read_research_analogy_firewall_contract_json", "Analogy Firewall contract removed from agent boot"),
        ("read_research_cross_domain_transfer_registry_json", "transfer registry removed from agent boot"),
        ("read_research_ns_cross_domain_transfer_adapter_json", "NS transfer adapter removed from agent boot"),
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

    mutated = copy.deepcopy(contract)
    mutated["review_policy"]["check_cross_domain_analogy_classification"] = False
    require_rejected(validator, mutated, "cross-domain analogy classification review disabled")

    mutated = copy.deepcopy(contract)
    mutated["review_policy"]["check_analogy_target_revalidation"] = False
    require_rejected(validator, mutated, "analogy target revalidation review disabled")

    print("AGENTS contract validation: PASS")


if __name__ == "__main__":
    main()
