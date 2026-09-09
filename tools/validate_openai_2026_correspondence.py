#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Phase 3A Gate 1: exact OpenAI 2026 C/D statement correspondence."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SCHEMAS = RESEARCH / "schemas"

PR12_MERGE = "ef48a7d7f195f475e9a0a792edbb750e74d210f0"
LEAN_REPOSITORY = "openai/NavierStokesAndEuler"
LEAN_COMMIT = "8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538"
EXPECTED_FORMAL_FILES = [
    {"path": "NavierStokes/ComparatorSolution.lean", "blob_sha": "cc232068cd384dbbddce2753b1fc4a4017c0f2d7"},
    {"path": "NavierStokes/ComparatorDefinitions.lean", "blob_sha": "d92c81ac99c1139e54c181c97d9021e975e23b7a"},
    {"path": "ComparatorChallenges/NavierStokes.lean", "blob_sha": "673fb19e26e60818d446363afd953f618719f99b"},
    {"path": "formalization.yaml", "blob_sha": "01270e9f666b0400b60d032204e02e6d684cee98"},
]
EXPECTED_INVARIANTS = [
    "STATEMENT_CORRESPONDENCE != PROOF_VALIDITY",
    "LEAN_STATEMENT_MATCH != CLEAN_ROOM_REPLAY",
    "SPECIAL_CASE_ADMISSIBILITY != PROOF_OF_CONSTRUCTION",
    "C_CORRESPONDENCE != A_RESOLUTION",
    "D_CORRESPONDENCE != B_RESOLUTION",
    "PERIODIC_PRESSURE_ERRATUM_REQUIRED",
    "GATE1_PASS != INDEPENDENT_VERIFICATION_COMPLETE",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject_schema(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"correspondence schema regression: forbidden mutation accepted: {label}")


def reject_cross(candidate: dict, clay: dict, external: dict, label: str) -> None:
    try:
        validate_cross(candidate, clay, external)
    except SystemExit:
        return
    raise SystemExit(f"correspondence cross-registry regression: forbidden mutation accepted: {label}")


def formulation(clay: dict, formulation_id: str) -> dict:
    matches = [item for item in clay["official_formulations"] if item["id"] == formulation_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one Clay formulation {formulation_id}")
    return matches[0]


def claim(external: dict, formulation_id: str) -> dict:
    matches = [item for item in external["claims"] if item["formulation_id"] == formulation_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one external claim for {formulation_id}")
    return matches[0]


def without_id(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "id"}


def validate_cross(corr: dict, clay: dict, external: dict) -> None:
    if corr["pr12_merge_baseline"] != PR12_MERGE:
        raise SystemExit("PR #12 merge baseline drift")

    if corr["authority"] != {
        "clay_target": "research/clay_target.json",
        "external_claim_registry": "research/external_claim_registry.json",
        "openai_paper_source_id": "OPENAI_NS_BLOWUP_2026",
        "openai_formalization_source_id": "OPENAI_NS_LEAN_2026",
    }:
        raise SystemExit("correspondence authority map drift")

    expected_pin = {
        "repository": LEAN_REPOSITORY,
        "commit": LEAN_COMMIT,
        "files": EXPECTED_FORMAL_FILES,
    }
    if corr["formal_artifact_pin"] != expected_pin:
        raise SystemExit("formal statement artifact pin drift")

    lean_external_pin = external["artifact_pins"]["OPENAI_NS_LEAN_2026"]
    if lean_external_pin["repository"] != LEAN_REPOSITORY or lean_external_pin["commit"] != LEAN_COMMIT:
        raise SystemExit("external-claim Lean pin no longer matches correspondence pin")

    if corr["scope"] != {
        "formulations": ["C", "D"],
        "statement_correspondence_only": True,
        "proof_validity_assessed": False,
        "lean_build_replayed_by_qsol": False,
        "comparator_replayed_by_qsol": False,
        "theorem_registry_promotion": False,
    }:
        raise SystemExit("Gate 1 scope/authority drift")

    if corr["gate_status"] != "statement_correspondence_confirmed":
        raise SystemExit("Gate 1 status drift")

    if corr["clay_snapshot"]["shared_equation_scope"] != clay["shared_equation_scope"]:
        raise SystemExit("shared Clay equation scope drift")

    for formulation_id in ("C", "D"):
        if corr["clay_snapshot"][formulation_id] != without_id(formulation(clay, formulation_id)):
            raise SystemExit(f"Clay {formulation_id} snapshot drift")
        ext = claim(external, formulation_id)
        if ext["qsol_status"] != "external_claim_pending_independent_verification":
            raise SystemExit(f"external {formulation_id} status no longer pending independent verification")
        if ext["source_position"] != "claims_satisfied":
            raise SystemExit(f"external {formulation_id} source position drift")

    for formulation_id in ("A", "B"):
        ext = claim(external, formulation_id)
        if ext["qsol_status"] != "not_resolved":
            raise SystemExit(f"unforced formulation {formulation_id} was silently resolved")

    errata = [
        item["statement"]
        for item in clay["errata"]
        if item["scope"] == "periodic_formulation"
    ]
    if errata != [corr["clay_snapshot"]["periodic_pressure_erratum"]]:
        raise SystemExit("periodic pressure erratum correspondence drift")

    records = corr["correspondences"]
    if [record["formulation_id"] for record in records] != ["C", "D"]:
        raise SystemExit("correspondence formulation order/identity drift")

    expected_claim_ids = {"C": "OPENAI_2026_C", "D": "OPENAI_2026_D"}
    expected_declarations = {
        "C": "NavierStokes.Comparator.navier_stokes_breakdown_R3",
        "D": "NavierStokes.Comparator.navier_stokes_breakdown_periodic",
    }
    expected_field_ids = {
        "C": [
            "dimension", "viscosity", "domain", "initial_data", "forcing", "equation",
            "incompressibility", "initial_condition", "global_smoothness", "bounded_energy",
            "breakdown_conclusion",
        ],
        "D": [
            "dimension", "viscosity", "domain", "initial_data", "forcing", "equation",
            "incompressibility", "initial_condition", "global_smoothness", "velocity_periodicity",
            "pressure_periodicity_erratum", "breakdown_conclusion",
        ],
    }
    for record in records:
        formulation_id = record["formulation_id"]
        if record["external_claim_id"] != expected_claim_ids[formulation_id]:
            raise SystemExit(f"external claim binding drift for {formulation_id}")
        if record["lean_declaration"] != expected_declarations[formulation_id]:
            raise SystemExit(f"Lean declaration binding drift for {formulation_id}")
        if record["statement_disposition"] != "correspondence_accounted_for":
            raise SystemExit(f"statement disposition drift for {formulation_id}")
        if record["proof_disposition"] != "not_assessed":
            raise SystemExit(f"proof authority smuggled into Gate 1 for {formulation_id}")
        field_ids = [field["field_id"] for field in record["fields"]]
        if field_ids != expected_field_ids[formulation_id]:
            raise SystemExit(f"correspondence field set/order drift for {formulation_id}")
        if any(field["audit_status"] != "accounted_for" for field in record["fields"]):
            raise SystemExit(f"incomplete Gate 1 field audit for {formulation_id}")

    if corr["machine_invariants"] != EXPECTED_INVARIANTS:
        raise SystemExit("Gate 1 machine invariant set drift")


def run_negative_probes(corr: dict, clay: dict, external: dict, validator: Draft202012Validator) -> None:
    mutated = copy.deepcopy(corr)
    mutated["scope"]["proof_validity_assessed"] = True
    reject_schema(validator, mutated, "Gate 1 promoted to proof-validity assessment")

    mutated = copy.deepcopy(corr)
    mutated["scope"]["lean_build_replayed_by_qsol"] = True
    reject_schema(validator, mutated, "clean-room Lean replay claimed without replay artifact")

    mutated = copy.deepcopy(corr)
    mutated["formal_artifact_pin"]["files"][0]["blob_sha"] = "0" * 40
    reject_cross(mutated, clay, external, "ComparatorSolution blob pin rewritten")

    mutated = copy.deepcopy(corr)
    mutated["clay_snapshot"]["C"]["domain"] = "R^3/Z^3"
    reject_cross(mutated, clay, external, "Clay C domain substituted")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][0]["proof_disposition"] = "verified"
    reject_schema(validator, mutated, "statement correspondence promoted to proof validity")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][1]["fields"] = [
        field for field in mutated["correspondences"][1]["fields"]
        if field["field_id"] != "pressure_periodicity_erratum"
    ]
    reject_cross(mutated, clay, external, "periodic pressure erratum removed")

    mutated = copy.deepcopy(corr)
    mutated["machine_invariants"].pop()
    reject_cross(mutated, clay, external, "Gate 1 nonclaim invariant removed")

    mutated_clay = copy.deepcopy(clay)
    formulation(mutated_clay, "C")["forcing"] = "f identically zero"
    reject_cross(corr, mutated_clay, external, "live Clay C forcing quantifier changed")

    mutated_external = copy.deepcopy(external)
    claim(mutated_external, "C")["qsol_status"] = "not_resolved"
    reject_cross(corr, clay, mutated_external, "external C pending-verification state erased")

    mutated_external = copy.deepcopy(external)
    mutated_external["artifact_pins"]["OPENAI_NS_LEAN_2026"]["commit"] = "0" * 40
    reject_cross(corr, clay, mutated_external, "external Lean pin diverged from correspondence pin")


def main() -> None:
    corr = load_json(RESEARCH / "openai_2026_correspondence.json")
    schema = load_json(SCHEMAS / "openai_2026_correspondence.schema.json")
    clay = load_json(RESEARCH / "clay_target.json")
    external = load_json(RESEARCH / "external_claim_registry.json")

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    validator.validate(corr)

    validate_cross(corr, clay, external)
    run_negative_probes(corr, clay, external, validator)

    print(
        "OpenAI 2026 C/D correspondence validation: PASS "
        f"(Gate 1={corr['gate_status']}, fields="
        f"{sum(len(record['fields']) for record in corr['correspondences'])}, "
        f"Lean={LEAN_COMMIT[:12]})"
    )


if __name__ == "__main__":
    main()
