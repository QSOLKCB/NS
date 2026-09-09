#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Phase 3A Gate 1: exact OpenAI 2026 C/D statement correspondence."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SCHEMAS = RESEARCH / "schemas"
FORMAT_CHECKER = FormatChecker()

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

# Audited semantic lock for the complete Gate 1 correspondence records. Any change
# to statement text, field text, relation classification, bridge wording, or
# disposition requires an explicit reviewed update to this validator in the same diff.
EXPECTED_CORRESPONDENCES = [
    {
        "formulation_id": "C",
        "external_claim_id": "OPENAI_2026_C",
        "analytical_source_statement": "Theorem 1.1",
        "lean_declaration": "NavierStokes.Comparator.navier_stokes_breakdown_R3",
        "lean_target_summary": "For every positive viscosity, there exist an initial velocity and force satisfying InitialVelocityConditionDecay and ForceConditionDecay such that no global NavierStokesExistenceAndSmoothnessRn velocity/pressure pair exists.",
        "fields": [
            {"field_id": "dimension", "clay_requirement": "three spatial dimensions", "source_or_lean_encoding": "local notation ℝ³ := EuclideanSpace ℝ (Fin 3)", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "viscosity", "clay_requirement": "nu > 0", "source_or_lean_encoding": "(nu : ℝ) (hnu : nu > 0)", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "domain", "clay_requirement": "R^3", "source_or_lean_encoding": "u₀ : ℝ³ → ℝ³ and f : ℝ³ → ℝ → ℝ³", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "initial_data", "clay_requirement": "there exists smooth divergence-free rapidly decaying u0 satisfying Fefferman condition (4)", "source_or_lean_encoding": "InitialVelocityConditionDecay u₀ requires smoothness, divergence-free initial data, and all-order rapid spatial decay; the analytical source uses the stronger special witness u₀ = 0.", "relation": "source_special_case_satisfies_target", "audit_status": "accounted_for"},
            {"field_id": "forcing", "clay_requirement": "there exists smooth rapidly decaying f satisfying Fefferman condition (5)", "source_or_lean_encoding": "ForceConditionDecay f requires smoothness on t ≥ 0 and all-order rapid decay in space and time; the analytical source states a smooth compactly supported force, a stronger admissible special case.", "relation": "source_special_case_satisfies_target", "audit_status": "accounted_for"},
            {"field_id": "equation", "clay_requirement": "Navier-Stokes momentum equation with forcing", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.navier_stokes encodes ∂t v + (v·∇)v = nu Δv - ∇p + f on t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "incompressibility", "clay_requirement": "div u = 0", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.div_free requires divergence zero for all x and t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "initial_condition", "clay_requirement": "u(x,0)=u0(x)", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.initial_condition requires v x 0 = u₀ x.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "global_smoothness", "clay_requirement": "global smooth velocity and pressure on R^3 x [0,infinity)", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness requires C∞ velocity and pressure on univ × [0,∞).", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "bounded_energy", "clay_requirement": "bounded kinetic energy for all t ≥ 0", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothnessRn requires per-time L2 membership and a uniform global kinetic-energy bound.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "breakdown_conclusion", "clay_requirement": "no global physically reasonable solution p,u satisfying the equations, global smoothness, and bounded energy", "source_or_lean_encoding": "¬ (∃ v p, NavierStokesExistenceAndSmoothnessRn nu u₀ f v p)", "relation": "exact_match", "audit_status": "accounted_for"},
        ],
        "construction_to_target_bridge": "The final Lean declaration has the exact existential/non-existence target shape. The separate proof obligation that OpenAI's constructed zero-data, compactly-supported-forcing witness satisfies these hypotheses remains a Gate 2/3 proof audit, not a Gate 1 statement fact.",
        "statement_disposition": "correspondence_accounted_for",
        "proof_disposition": "not_assessed",
    },
    {
        "formulation_id": "D",
        "external_claim_id": "OPENAI_2026_D",
        "analytical_source_statement": "Corollary 10.6",
        "lean_declaration": "NavierStokes.Comparator.navier_stokes_breakdown_periodic",
        "lean_target_summary": "For every positive viscosity, there exist periodic initial velocity and force data satisfying InitialVelocityConditionPeriodic and ForceConditionPeriodic such that no global NavierStokesExistenceAndSmoothnessPeriodic velocity/pressure pair exists.",
        "fields": [
            {"field_id": "dimension", "clay_requirement": "three spatial dimensions", "source_or_lean_encoding": "local notation ℝ³ := EuclideanSpace ℝ (Fin 3)", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "viscosity", "clay_requirement": "nu > 0", "source_or_lean_encoding": "(nu : ℝ) (hnu : nu > 0)", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "domain", "clay_requirement": "R^3/Z^3", "source_or_lean_encoding": "IsOnePeriodic encodes unit-periodicity in every coordinate, representing R^3/Z^3.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "initial_data", "clay_requirement": "there exists smooth divergence-free spatially periodic u0 satisfying Fefferman condition (8)", "source_or_lean_encoding": "InitialVelocityConditionPeriodic u₀ requires smoothness, divergence-free initial data, and unit spatial periodicity.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "forcing", "clay_requirement": "there exists smooth spatially periodic f with time decay satisfying Fefferman condition (9)", "source_or_lean_encoding": "ForceConditionPeriodic f requires smoothness, unit spatial periodicity for t ≥ 0, and all-order rapid time decay.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "equation", "clay_requirement": "Navier-Stokes momentum equation with forcing", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.navier_stokes encodes ∂t v + (v·∇)v = nu Δv - ∇p + f on t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "incompressibility", "clay_requirement": "div u = 0", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.div_free requires divergence zero for all x and t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "initial_condition", "clay_requirement": "u(x,0)=u0(x)", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness.initial_condition requires v x 0 = u₀ x.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "global_smoothness", "clay_requirement": "global smooth velocity and pressure on R^3 x [0,infinity) with spatial periodicity", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothness requires C∞ velocity and pressure on univ × [0,∞), while the periodic extension requires spatial periodicity for the solution.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "velocity_periodicity", "clay_requirement": "solution velocity is spatially periodic", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothnessPeriodic.isOnePeriodic_velocity requires unit spatial periodicity for all t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "pressure_periodicity_erratum", "clay_requirement": "pressure is spatially periodic, per the official Clay erratum", "source_or_lean_encoding": "NavierStokesExistenceAndSmoothnessPeriodic.isOnePeriodic_pressure requires unit spatial periodicity for all t ≥ 0.", "relation": "exact_match", "audit_status": "accounted_for"},
            {"field_id": "breakdown_conclusion", "clay_requirement": "no global smooth spatially periodic solution p,u satisfying the equations", "source_or_lean_encoding": "¬ (∃ v p, NavierStokesExistenceAndSmoothnessPeriodic nu u₀ f v p)", "relation": "exact_match", "audit_status": "accounted_for"},
        ],
        "construction_to_target_bridge": "The final Lean declaration has the exact periodic existential/non-existence target shape, including pressure periodicity. The separate proof obligation that the paper's periodicized construction satisfies ForceConditionPeriodic and the other target hypotheses remains a Gate 2/3 proof audit.",
        "statement_disposition": "correspondence_accounted_for",
        "proof_disposition": "not_assessed",
    },
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

    # The complete reviewed correspondence objects are the Gate 1 authority. This
    # catches contradictory prose, relation reclassification, bridge drift, and
    # disposition changes—not only field-ID or status changes.
    if corr["correspondences"] != EXPECTED_CORRESPONDENCES:
        raise SystemExit(
            "audited Gate 1 correspondence semantic drift; update the explicit "
            "validator lock only after statement re-review"
        )

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
    mutated["as_of"] = "not-a-date"
    reject_schema(validator, mutated, "malformed Gate 1 audit date accepted")

    mutated = copy.deepcopy(corr)
    mutated["formal_artifact_pin"]["files"][0]["blob_sha"] = "0" * 40
    reject_cross(mutated, clay, external, "ComparatorSolution blob pin rewritten")

    mutated = copy.deepcopy(corr)
    mutated["clay_snapshot"]["C"]["domain"] = "R^3/Z^3"
    reject_cross(mutated, clay, external, "Clay C domain substituted")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][0]["lean_target_summary"] = "QSOL has independently proved Clay C."
    reject_cross(mutated, clay, external, "C Lean target summary contradicted")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][0]["fields"][2]["clay_requirement"] = "R^3/Z^3"
    reject_cross(mutated, clay, external, "C audited field requirement corrupted")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][0]["fields"][5]["source_or_lean_encoding"] = "modified equation"
    reject_cross(mutated, clay, external, "C audited Lean/source encoding corrupted")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][0]["fields"][0]["relation"] = "source_special_case_satisfies_target"
    reject_cross(mutated, clay, external, "exact-match relation silently reclassified")

    mutated = copy.deepcopy(corr)
    mutated["correspondences"][1]["construction_to_target_bridge"] = "The paper is accepted without further proof audit."
    reject_cross(mutated, clay, external, "D construction-to-target bridge corrupted")

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
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
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
