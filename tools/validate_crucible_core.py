#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Crucible Core contracts, NS adapter correspondence and hostile mutations."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from crucible_core import (
    CORE_VERSION,
    Candidate,
    ConstraintResult,
    Crucible,
    CrucibleStateError,
    EvidenceRecord,
    HypothesisSet,
)

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
    raise SystemExit(f"Crucible schema regression: forbidden mutation accepted: {label}")


def validate_schema_pair(document: dict, schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(document)
    return validator


def executable_state_machine_probe(adapter: dict, agents: dict) -> None:
    levels = tuple(agents["claim_levels"])
    domain = adapter["domain_id"]
    hypothesis = adapter["primary_hypothesis_set"]
    tracks = hypothesis["tracks"]

    crucible = Crucible(domain_id=domain, allowed_claim_levels=levels)
    for track in tracks:
        crucible.register_candidate(
            Candidate(
                candidate_id=track["track_id"],
                domain_id=domain,
                hypothesis_set_id=hypothesis["hypothesis_set_id"],
                hypothesis=track["statement"],
                claim_level="exploratory",
                generation_method="validate_crucible_core.py",
            )
        )
    crucible.register_hypothesis_set(
        HypothesisSet(
            hypothesis_set_id=hypothesis["hypothesis_set_id"],
            domain_id=domain,
            candidate_ids=tuple(track["track_id"] for track in tracks),
        )
    )

    holdout = EvidenceRecord(
        evidence_id="probe-holdout",
        domain_id=domain,
        candidate_id=tracks[0]["track_id"],
        evidence_kind="challenging",
        stage="holdout",
        source_ref="sealed:validator-probe",
        provenance_ref="validator-probe",
        summary="holdout gate must reject access before freeze",
        reproducible=True,
    )
    try:
        crucible.attach_evidence(holdout)
    except CrucibleStateError:
        pass
    else:
        raise SystemExit("Crucible holdout gate failed: unfrozen candidate accessed holdout")

    crucible.freeze_candidate(tracks[0]["track_id"])
    crucible.attach_evidence(holdout)

    challenge = EvidenceRecord(
        evidence_id="probe-barrier-evidence",
        domain_id=domain,
        candidate_id=tracks[1]["track_id"],
        evidence_kind="challenging",
        stage="development",
        source_ref="research/proof_barriers.json",
        provenance_ref="barrier:NUMERICAL_CONTINUUM_GAP",
        summary="numerical signature lacks a rigorous continuum bridge",
        reproducible=True,
    )
    crucible.attach_evidence(challenge)
    failure = crucible.record_constraint_result(
        ConstraintResult(
            result_id="probe-hard-failure",
            domain_id=domain,
            candidate_id=tracks[1]["track_id"],
            constraint_id="NUMERICAL_CONTINUUM_GAP",
            outcome="fail",
            severity="hard",
            evidence_ids=("probe-barrier-evidence",),
            explanation="validator deliberately exercises append-only failure memory",
        ),
        failure_id="probe-failure-record",
        failure_class="discrete_continuum_gap",
        reusable_lesson="numerical signature requires an explicit rigorous continuum bridge",
        claim_level_after="exploratory",
        recorded_by="validate_crucible_core.py",
    )
    if failure is None or len(crucible.failure_ledger()) != 1:
        raise SystemExit("Crucible hard failure was not preserved in failure ledger")
    state = crucible.export_state()
    if state["universal_confidence_score"] is not None:
        raise SystemExit("Crucible unexpectedly emitted a universal confidence score")
    if state["hypothesis_sets"][0]["preferred_candidate_id"] is not None:
        raise SystemExit("Crucible selected a winner without domain authority")


def main() -> None:
    core = load(RESEARCH / "crucible_contract.json")
    core_schema = load(RESEARCH / "schemas/crucible_contract.schema.json")
    adapter = load(RESEARCH / "ns_crucible_adapter.json")
    adapter_schema = load(RESEARCH / "schemas/ns_crucible_adapter.schema.json")
    candidate_schema = load(RESEARCH / "schemas/crucible_candidate.schema.json")
    failure_schema = load(RESEARCH / "schemas/crucible_failure_record.schema.json")
    agents = load(ROOT / "AGENTS.md")
    clay = load(RESEARCH / "clay_target.json")
    barriers = load(RESEARCH / "proof_barriers.json")

    core_validator = validate_schema_pair(core, core_schema)
    adapter_validator = validate_schema_pair(adapter, adapter_schema)
    Draft202012Validator.check_schema(candidate_schema)
    Draft202012Validator.check_schema(failure_schema)

    if core["core_version"] != CORE_VERSION:
        raise SystemExit("Crucible implementation/contract version drift")
    if adapter["core_contract"] != "research/crucible_contract.json":
        raise SystemExit("NS adapter no longer binds canonical Crucible contract")
    if adapter["claim_authority"]["core_may_promote_claim"]:
        raise SystemExit("Crucible Core must not promote NS claims")
    if adapter["claim_authority"]["automatic_winner_selection"]:
        raise SystemExit("NS Crucible adapter must begin with unresolved competition")

    clay_ids = {item["id"] for item in clay["official_formulations"]}
    tracks = adapter["primary_hypothesis_set"]["tracks"]
    mapped = {formulation for track in tracks for formulation in track["official_formulations"]}
    if mapped != clay_ids or clay_ids != {"A", "B", "C", "D"}:
        raise SystemExit("NS Crucible track mapping drifted from exact Clay A-D target")
    if adapter["primary_hypothesis_set"]["preferred_candidate_id"] is not None:
        raise SystemExit("NS primary competition may not have a default winner")

    registry_barriers = [item["barrier_id"] for item in barriers["barriers"]]
    adapter_barriers = adapter["constraint_bindings"]["proof_barrier_ids"]
    if adapter_barriers != registry_barriers:
        raise SystemExit("NS Crucible adapter proof barriers do not exactly match registry order")

    if adapter["evaluator_bindings"]["numerical_evidence_maximum_automatic_claim_level"] != agents["claim_promotion"]["numerics_can_promote_to"]:
        raise SystemExit("NS Crucible numerical evidence ceiling drift")
    if adapter["holdout_policy"]["holdout_success_changes_claim_level"]:
        raise SystemExit("holdout success may not silently promote an NS claim")

    mutated = copy.deepcopy(core)
    mutated["authority"]["core_defines_domain_truth"] = True
    reject(core_validator, mutated, "core promoted to truth authority")

    mutated = copy.deepcopy(core)
    mutated["principles"]["universal_confidence_score_enabled"] = True
    reject(core_validator, mutated, "universal confidence meter enabled")

    mutated = copy.deepcopy(core)
    mutated["holdout_policy"]["candidate_must_be_frozen_before_holdout_evidence"] = False
    reject(core_validator, mutated, "holdout freeze gate disabled")

    mutated = copy.deepcopy(adapter)
    mutated["claim_authority"]["core_may_promote_claim"] = True
    reject(adapter_validator, mutated, "core granted NS claim promotion authority")

    mutated = copy.deepcopy(adapter)
    mutated["primary_hypothesis_set"]["preferred_candidate_id"] = "NS_GLOBAL_REGULARITY"
    reject(adapter_validator, mutated, "default NS winner injected")

    mutated = copy.deepcopy(adapter)
    mutated["holdout_policy"]["holdout_success_changes_claim_level"] = True
    reject(adapter_validator, mutated, "holdout silently promotes claim")

    executable_state_machine_probe(adapter, agents)

    print(
        "Crucible Core validation: PASS "
        f"(core={CORE_VERSION}, domain={adapter['domain_id']}, "
        f"barriers={len(adapter_barriers)}, competing_tracks={len(tracks)})"
    )


if __name__ == "__main__":
    main()
