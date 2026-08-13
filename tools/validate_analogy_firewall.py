#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Analogy Firewall contracts, registry and NS transfer authority."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from crucible_core import AnalogyFirewall, AnalogyFirewallError, AnalogyRecord, FIREWALL_VERSION

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"Analogy Firewall schema regression: forbidden mutation accepted: {label}")


def make_record(raw: dict) -> AnalogyRecord:
    return AnalogyRecord(
        analogy_id=raw["analogy_id"],
        source_domain=raw["source_domain"],
        target_domain=raw["target_domain"],
        mapping_class=raw["mapping_class"],
        shared_structure=raw["shared_structure"],
        assumptions=tuple(raw["assumptions"]),
        known_differences=tuple(raw["known_differences"]),
        allowed_uses=tuple(raw["allowed_uses"]),
        forbidden_inferences=tuple(raw["forbidden_inferences"]),
        provenance_ref=raw["provenance_ref"],
    )


def main() -> None:
    contract = load(RESEARCH / "analogy_firewall_contract.json")
    contract_schema = load(RESEARCH / "schemas/analogy_firewall_contract.schema.json")
    registry = load(RESEARCH / "cross_domain_transfer_registry.json")
    registry_schema = load(RESEARCH / "schemas/cross_domain_transfer_registry.schema.json")
    record_schema = load(RESEARCH / "schemas/analogy_record.schema.json")
    adapter = load(RESEARCH / "ns_cross_domain_transfer_adapter.json")
    adapter_schema = load(RESEARCH / "schemas/ns_cross_domain_transfer_adapter.schema.json")
    ns_crucible = load(RESEARCH / "ns_crucible_adapter.json")
    barriers = load(RESEARCH / "proof_barriers.json")
    agents = load(ROOT / "AGENTS.md")

    for schema in (contract_schema, registry_schema, record_schema, adapter_schema):
        Draft202012Validator.check_schema(schema)

    contract_validator = Draft202012Validator(contract_schema)
    registry_validator = Draft202012Validator(registry_schema)
    adapter_validator = Draft202012Validator(adapter_schema)
    record_validator = Draft202012Validator(record_schema)

    contract_validator.validate(contract)
    registry_validator.validate(registry)
    adapter_validator.validate(adapter)

    if contract["firewall_version"] != FIREWALL_VERSION:
        raise SystemExit("Analogy Firewall implementation/contract version drift")
    if adapter["target_domain"] != ns_crucible["domain_id"]:
        raise SystemExit("NS transfer adapter target does not match NS Crucible domain")
    if adapter["crucible_adapter"] != "research/ns_crucible_adapter.json":
        raise SystemExit("NS transfer adapter no longer binds canonical Crucible adapter")
    if adapter["candidate_intake"]["initial_claim_level"] != "exploratory":
        raise SystemExit("analogy-derived NS candidates must start exploratory")
    if adapter["epistemic_authority"]["analogy_registry_is_ns_evidence"]:
        raise SystemExit("analogy registry may not become NS evidence")
    if adapter["epistemic_authority"]["analogy_can_discharge_proof_barrier"]:
        raise SystemExit("analogy may not discharge an NS proof barrier")
    if adapter["epistemic_authority"]["analogy_can_change_claim_level"]:
        raise SystemExit("analogy may not change NS claim level")

    registry_by_id = {}
    for raw in registry["records"]:
        record_validator.validate(raw)
        record = make_record(raw)
        record.validate()
        if record.analogy_id in registry_by_id:
            raise SystemExit(f"duplicate analogy_id: {record.analogy_id}")
        registry_by_id[record.analogy_id] = record

    eligible = adapter["eligible_registry_ids"]
    negatives = adapter["negative_control_registry_ids"]
    if len(eligible) != len(set(eligible)) or len(negatives) != len(set(negatives)):
        raise SystemExit("NS transfer adapter registry IDs must be unique")
    missing = [key for key in eligible + negatives if key not in registry_by_id]
    if missing:
        raise SystemExit(f"NS transfer adapter references missing registry IDs: {missing}")

    for key in eligible:
        record = registry_by_id[key]
        if record.target_domain != adapter["target_domain"]:
            raise SystemExit(f"eligible analogy {key} targets the wrong domain")
        if record.mapping_class not in adapter["candidate_intake"]["allowed_mapping_classes"]:
            raise SystemExit(f"eligible analogy {key} uses blocked mapping class")
        if "candidate_generation" not in record.allowed_uses:
            raise SystemExit(f"eligible analogy {key} does not authorize candidate generation")

    for key in negatives:
        record = registry_by_id[key]
        if record.mapping_class not in adapter["candidate_intake"]["blocked_positive_mapping_classes"]:
            raise SystemExit(f"negative control {key} is not a blocked positive class")
        if record.allowed_uses != ("negative_control",):
            raise SystemExit(f"negative control {key} has unexpected allowed uses")

    barrier_ids = [item["barrier_id"] for item in barriers["barriers"]]
    ns_barrier_ids = ns_crucible["constraint_bindings"]["proof_barrier_ids"]
    if barrier_ids != ns_barrier_ids:
        raise SystemExit("NS Crucible proof-barrier registry drift")
    if not adapter["target_revalidation"]["all_registered_proof_barriers_reapply"]:
        raise SystemExit("cross-domain intake must reapply all NS proof barriers")

    required_invariants = {
        "visual_resemblance_is_not_physical_mechanism",
        "shared_operator_is_not_shared_dynamics",
        "structural_analogy_is_not_domain_equivalence",
        "analogy_is_not_domain_evidence",
        "analogy_cannot_promote_claim",
        "cross_domain_transfer_requires_target_domain_validation",
    }
    if not required_invariants.issubset(set(agents["research_invariants"])):
        raise SystemExit("AGENTS contract is missing Analogy Firewall invariants")

    mutated = copy.deepcopy(contract)
    mutated["authority"]["analogy_may_be_domain_evidence"] = True
    reject(contract_validator, mutated, "analogy promoted to domain evidence")

    mutated = copy.deepcopy(contract)
    mutated["authority"]["analogy_may_promote_claim"] = True
    reject(contract_validator, mutated, "analogy granted claim-promotion authority")

    mutated = copy.deepcopy(contract)
    mutated["authority"]["analogy_may_satisfy_proof_barrier"] = True
    reject(contract_validator, mutated, "analogy granted proof-barrier authority")

    mutated = copy.deepcopy(contract)
    mutated["authority"]["analogy_may_assert_domain_equivalence"] = True
    reject(contract_validator, mutated, "analogy granted domain-equivalence authority")

    mutated = copy.deepcopy(contract)
    mutated["transfer_policy"]["source_proof_status_inherited"] = True
    reject(contract_validator, mutated, "source proof status inherited")

    mutated = copy.deepcopy(adapter)
    mutated["candidate_intake"]["initial_claim_level"] = "candidate_lemma"
    reject(adapter_validator, mutated, "analogy-derived candidate starts above exploratory")

    mutated = copy.deepcopy(adapter)
    mutated["epistemic_authority"]["analogy_can_discharge_proof_barrier"] = True
    reject(adapter_validator, mutated, "NS proof barrier discharged by analogy")

    mutated = copy.deepcopy(registry)
    target = next(
        item for item in mutated["records"]
        if item["analogy_id"] == "LASER_SPECKLE_NOT_FLUID_FLOW"
    )
    target["allowed_uses"] = ["candidate_generation"]
    try:
        registry_validator.validate(mutated)
        make_record(target).validate()
    except (ValidationError, ValueError):
        pass
    else:
        raise SystemExit("visual/non-correspondence mapping gained positive transfer authority")

    firewall = AnalogyFirewall(
        target_domain=adapter["target_domain"],
        initial_claim_level=adapter["candidate_intake"]["initial_claim_level"],
    )
    for record in registry_by_id.values():
        firewall.register(record)

    candidate = firewall.issue_candidate(
        analogy_id="GENERATIVE_DIFFUSION_LAPLACIAN_TO_NS_VISCOSITY",
        candidate_id="validator-transfer-candidate",
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="test whether an operator-level analogy suggests a target-domain estimate worth checking",
        generation_method="validate_analogy_firewall.py",
    )
    if candidate.claim_level != "exploratory":
        raise SystemExit("firewall promoted analogy-derived candidate")
    if candidate.domain_id != adapter["target_domain"]:
        raise SystemExit("firewall emitted candidate into wrong domain")
    if "mapping_class=operator_correspondence" not in candidate.assumptions:
        raise SystemExit("firewall did not preserve mapping class in candidate provenance")

    for forbidden_use in (
        "domain_evidence",
        "claim_promotion",
        "proof_barrier_satisfaction",
        "domain_equivalence_claim",
        "winner_selection",
    ):
        try:
            firewall.authorize_use(
                "GENERATIVE_DIFFUSION_LAPLACIAN_TO_NS_VISCOSITY",
                forbidden_use,
            )
        except AnalogyFirewallError:
            pass
        else:
            raise SystemExit(f"firewall authorized forbidden use: {forbidden_use}")

    try:
        firewall.issue_candidate(
            analogy_id="LASER_SPECKLE_NOT_FLUID_FLOW",
            candidate_id="forbidden-negative-control-candidate",
            hypothesis_set_id="NS_PRIMARY_COMPETITION",
            hypothesis="should never be created",
            generation_method="validator",
        )
    except AnalogyFirewallError:
        pass
    else:
        raise SystemExit("negative control generated a positive NS candidate")

    authority = firewall.authority_snapshot()
    if any(authority[key] for key in (
        "domain_evidence",
        "claim_promotion",
        "proof_barrier_satisfaction",
        "domain_equivalence_claim",
        "winner_selection",
        "source_proof_status_inherited",
        "source_evidence_status_inherited",
    )):
        raise SystemExit("firewall authority snapshot exceeds candidate-generation scope")

    print(
        "Analogy Firewall validation: PASS "
        f"(version={FIREWALL_VERSION}, records={len(registry_by_id)}, "
        f"eligible_ns={len(eligible)}, barriers={len(barrier_ids)})"
    )


if __name__ == "__main__":
    main()
