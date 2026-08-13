#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate QSOL NS known-boundary registries and cross-file invariants."""

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

DOCUMENTS = {
    "clay": (RESEARCH / "clay_target.json", SCHEMAS / "clay_target.schema.json"),
    "sources": (RESEARCH / "source_registry.json", SCHEMAS / "source_registry.schema.json"),
    "theorems": (RESEARCH / "theorem_registry.json", SCHEMAS / "theorem_registry.schema.json"),
    "barriers": (RESEARCH / "proof_barriers.json", SCHEMAS / "proof_barriers.schema.json"),
    "identities": (RESEARCH / "baseline_identities.json", SCHEMAS / "baseline_identities.schema.json"),
}

# Audited semantic lock for the source-checked historical theorem boundary.
# Changing one of these semantics requires an explicit change to this validator
# in the same reviewed diff; editing theorem_registry.json alone must fail CI.
LOCKED_THEOREM_FIELDS = (
    "source_ids",
    "year",
    "domain",
    "hypotheses_summary",
    "conclusion_summary",
    "limitations",
)

SOURCE_CHECKED_THEOREM_SEMANTICS = {
    "KNOWN_LERAY_GLOBAL_WEAK_EXISTENCE": {
        "source_ids": ["LERAY_1934", "CMI_FEFFERMAN_2000"],
        "year": 1934,
        "domain": "R^3",
        "hypotheses_summary": "Finite-energy divergence-free initial data in the classical Leray framework; consult the primary source for the exact approximation and function-space formulation.",
        "conclusion_summary": "Global-in-time weak solutions exist in the Leray sense.",
        "limitations": [
            "does_not_establish_global_smoothness",
            "does_not_establish_general_uniqueness_of_weak_solutions",
            "weak_existence_is_not_a_solution_of_A_or_B",
        ],
    },
    "KNOWN_FUJITA_KATO_LOCAL_3D": {
        "source_ids": ["FUJITA_KATO_1964"],
        "year": 1964,
        "domain": "R^3",
        "hypotheses_summary": "Initial data satisfying the source's strong-solution function-space hypotheses.",
        "conclusion_summary": "A unique strong solution exists for a nonzero time interval in the source framework.",
        "limitations": [
            "local_not_global",
            "exact_function_space_hypotheses_must_be_preserved",
            "does_not_control_arbitrary_large_time_behavior",
        ],
    },
    "KNOWN_SERRIN_CONDITIONAL_REGULARITY": {
        "source_ids": ["SERRIN_1962"],
        "year": 1962,
        "domain": "source_dependent",
        "hypotheses_summary": "A weak solution additionally satisfies a Serrin integrability condition; the standard three-dimensional summary is a mixed space-time condition with 2/q + 3/p <= 1 in the admissible source range, with exact endpoint and locality assumptions taken from the primary source.",
        "conclusion_summary": "Under the additional integrability hypothesis the weak solution is regular in the corresponding region/time interval.",
        "limitations": [
            "criterion_is_conditional",
            "criterion_does_not_supply_the_required_norm_bound_for_arbitrary_data",
            "endpoint_and_domain_hypotheses_must_not_be_inferred_from_memory",
        ],
    },
    "KNOWN_CKN_PARTIAL_REGULARITY": {
        "source_ids": ["CKN_1982"],
        "year": 1982,
        "domain": "R^3_space_time_local",
        "hypotheses_summary": "Suitable weak solutions satisfying the local energy inequality in the Caffarelli-Kohn-Nirenberg framework.",
        "conclusion_summary": "The possible singular set is small; in particular its one-dimensional parabolic Hausdorff measure is zero.",
        "limitations": [
            "does_not_prove_the_singular_set_is_empty",
            "applies_to_suitable_weak_solutions",
            "partial_regularity_is_not_global_smoothness",
        ],
    },
    "KNOWN_KATO_CRITICAL_L3_THEORY": {
        "source_ids": ["KATO_1984"],
        "year": 1984,
        "domain": "R^3",
        "hypotheses_summary": "Initial data in the critical L3-based framework used by Kato, with a sufficiently small critical norm for the global small-data conclusion.",
        "conclusion_summary": "Local strong well-posedness holds in the critical framework, and sufficiently small critical data give global solutions.",
        "limitations": [
            "small_data_global_result_does_not_cover_arbitrary_large_data",
            "critical_space_membership_alone_is_not_the_smallness_condition",
            "exact_source_solution_class_must_be_preserved",
        ],
    },
    "KNOWN_KOCH_TATARU_SMALL_BMO_MINUS_1": {
        "source_ids": ["KOCH_TATARU_2001"],
        "year": 2001,
        "domain": "R^3",
        "hypotheses_summary": "Divergence-free initial data sufficiently small in the BMO^{-1}-type critical norm of the source framework.",
        "conclusion_summary": "A global well-posed solution exists in the Koch-Tataru solution space.",
        "limitations": [
            "requires_small_critical_norm",
            "does_not_cover_arbitrary_large_data",
            "must_not_be_promoted_to_general_global_regularness",
        ],
    },
    "KNOWN_ESS_ENDPOINT_L3": {
        "source_ids": ["ESS_2003"],
        "year": 2003,
        "domain": "R^3_local_or_global_source_framework",
        "hypotheses_summary": "A suitable/weak solution remains uniformly bounded in the spatial L3 norm up to a candidate singular time, under the source's precise hypotheses.",
        "conclusion_summary": "The endpoint L3 control prevents the candidate finite-time singularity; contrapositively, finite-time blow-up requires loss of the corresponding uniform L3 control.",
        "limitations": [
            "does_not_prove_uniform_L3_control_for_arbitrary_smooth_data",
            "title_notation_L_3_infinity_must_not_be_misread_as_spatial_Lorentz_L3_infinity",
            "exact_locality_and_solution_hypotheses_come_from_primary_source",
        ],
    },
    "KNOWN_NRS_NO_L3_BACKWARD_SELF_SIMILAR_PROFILE": {
        "source_ids": ["NRS_1996"],
        "year": 1996,
        "domain": "R^3",
        "hypotheses_summary": "Backward self-similar Leray-form solutions whose similarity profile obeys the source's L3/integrability hypotheses.",
        "conclusion_summary": "No nontrivial profile in the stated class yields the proposed backward self-similar blow-up.",
        "limitations": [
            "excludes_a_specific_self_similar_class_not_all_blowup",
            "does_not_exclude_asymptotically_or_discretely_self_similar_scenarios_without_additional_results",
            "profile_integrability_hypotheses_are_essential",
        ],
    },
    "KNOWN_TSAI_LOCAL_ENERGY_SELF_SIMILAR_EXCLUSION": {
        "source_ids": ["TSAI_1998"],
        "year": 1998,
        "domain": "R^3",
        "hypotheses_summary": "Self-similar Navier-Stokes solutions satisfying the source's local-energy and stated integrability hypotheses; the published erratum must be consulted for proof-level reuse.",
        "conclusion_summary": "Self-similar solutions in the covered class are trivial, excluding that class as a finite-time blow-up mechanism.",
        "limitations": [
            "does_not_exclude_all_singularities",
            "published_erratum_must_be_consulted",
            "local_energy_and_integrability_hypotheses_are_not_optional",
        ],
    },
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def validator_for(schema_path: Path) -> Draft202012Validator:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FORMAT_CHECKER)


def reject(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"schema regression: forbidden mutation accepted: {label}")


def require_cross_rejected(candidate: dict[str, dict], label: str) -> None:
    try:
        validate_cross_registry(candidate)
    except SystemExit:
        return
    raise SystemExit(f"cross-registry regression: forbidden mutation accepted: {label}")


def require_unique(records: list[dict], key: str, label: str) -> set[str]:
    values = [record[key] for record in records]
    if len(values) != len(set(values)):
        raise SystemExit(f"duplicate {label}: {values}")
    return set(values)


def validate_official_source_identity(clay: dict, sources: dict) -> None:
    official_records = [
        record
        for record in sources["sources"]
        if record["authority_class"] == "official_problem_statement"
    ]
    if len(official_records) != 1:
        raise SystemExit(
            f"expected exactly one official problem source, found {len(official_records)}"
        )

    authority = clay["authority"]
    official = official_records[0]
    expected = {
        "source_id": "CMI_FEFFERMAN_2000",
        "authors": [authority["author"]],
        "year": 2000,
        "title": authority["problem_title"],
        "publisher_or_venue": authority["name"],
        "doi": None,
        "url": authority["official_pdf"],
        "role": "canonical_problem_authority",
    }
    for field, expected_value in expected.items():
        if official[field] != expected_value:
            raise SystemExit(
                "canonical official-source identity drift: "
                f"{field}={official[field]!r}, expected {expected_value!r}"
            )


def validate_theorem_semantic_locks(theorems: dict) -> None:
    current_ids = {record["theorem_id"] for record in theorems["theorems"]}
    expected_ids = set(SOURCE_CHECKED_THEOREM_SEMANTICS)
    if current_ids != expected_ids:
        raise SystemExit(
            "source-checked theorem lock set changed without audited validator update: "
            f"current={sorted(current_ids)}, expected={sorted(expected_ids)}"
        )

    for theorem in theorems["theorems"]:
        theorem_id = theorem["theorem_id"]
        actual = {field: theorem[field] for field in LOCKED_THEOREM_FIELDS}
        expected = SOURCE_CHECKED_THEOREM_SEMANTICS[theorem_id]
        if actual != expected:
            raise SystemExit(
                f"source-checked theorem semantic drift: {theorem_id}; "
                "update the audited semantic lock only after source review"
            )


def validate_cross_registry(documents: dict[str, dict]) -> None:
    clay = documents["clay"]
    sources = documents["sources"]
    theorems = documents["theorems"]
    barriers = documents["barriers"]
    identities = documents["identities"]

    formulation_ids = [record["id"] for record in clay["official_formulations"]]
    if formulation_ids != ["A", "B", "C", "D"]:
        raise SystemExit(f"official formulation order/identity drift: {formulation_ids}")

    source_ids = require_unique(sources["sources"], "source_id", "source_id")
    theorem_ids = require_unique(theorems["theorems"], "theorem_id", "theorem_id")
    require_unique(barriers["barriers"], "barrier_id", "barrier_id")
    require_unique(identities["identities"], "identity_id", "identity_id")

    validate_official_source_identity(clay, sources)
    validate_theorem_semantic_locks(theorems)

    authority_by_source = {
        record["source_id"]: record["authority_class"] for record in sources["sources"]
    }
    permitted_authorities = {"official_problem_statement", "primary_research"}

    for theorem in theorems["theorems"]:
        missing_sources = set(theorem["source_ids"]) - source_ids
        if missing_sources:
            raise SystemExit(
                f"{theorem['theorem_id']} references unknown sources: {sorted(missing_sources)}"
            )
        unauthorized = [
            source_id
            for source_id in theorem["source_ids"]
            if authority_by_source[source_id] not in permitted_authorities
        ]
        if unauthorized:
            raise SystemExit(
                f"{theorem['theorem_id']} uses non-authoritative theorem sources: {unauthorized}"
            )
        if theorem["novelty_claim"] or theorem["solves_clay"]:
            raise SystemExit(
                f"known-boundary entry improperly promoted: {theorem['theorem_id']}"
            )
        if theorem["formalized"]:
            raise SystemExit(
                f"historical theorem entry claims formalization without registered artifact: {theorem['theorem_id']}"
            )
        if not theorem["hypotheses_summary"].strip() or not theorem["limitations"]:
            raise SystemExit(f"incomplete theorem boundary: {theorem['theorem_id']}")

    for barrier in barriers["barriers"]:
        missing_theorems = set(barrier["related_theorem_ids"]) - theorem_ids
        if missing_theorems:
            raise SystemExit(
                f"{barrier['barrier_id']} references unknown theorem IDs: {sorted(missing_theorems)}"
            )
        if not barrier["required_response"].strip():
            raise SystemExit(f"barrier has no proof obligation: {barrier['barrier_id']}")

    for identity in identities["identities"]:
        if not identity["assumptions"]:
            raise SystemExit(f"baseline identity has no assumptions: {identity['identity_id']}")


def run_negative_probes(documents: dict[str, dict], validators: dict[str, Draft202012Validator]) -> None:
    mutated = copy.deepcopy(documents["clay"])
    mutated["official_formulations"].pop()
    reject(validators["clay"], mutated, "Clay formulation D removed")

    mutated = copy.deepcopy(documents["clay"])
    mutated["official_formulations"][0]["initial_data"] = "any smooth divergence-free u0"
    reject(validators["clay"], mutated, "Clay A initial-data semantics weakened")

    mutated = copy.deepcopy(documents["clay"])
    mutated["official_formulations"][2]["forcing"] = "f identically zero"
    reject(validators["clay"], mutated, "Clay C forcing quantifier changed")

    mutated = copy.deepcopy(documents["clay"])
    mutated["official_formulations"][3]["required_conclusion"] = "some solution becomes large"
    reject(validators["clay"], mutated, "Clay D required conclusion weakened")

    mutated = copy.deepcopy(documents["clay"])
    mutated["authority"]["retrieved_date"] = "13-08-2026"
    reject(validators["clay"], mutated, "malformed authority date accepted")

    mutated = copy.deepcopy(documents["sources"])
    mutated["sources"][1]["url"] = "not a uri"
    reject(validators["sources"], mutated, "malformed source URI accepted")

    mutated = copy.deepcopy(documents["theorems"])
    mutated["theorems"][0]["hypotheses_summary"] = ""
    reject(validators["theorems"], mutated, "theorem hypotheses removed")

    mutated = copy.deepcopy(documents["theorems"])
    mutated["theorems"][0]["solves_clay"] = True
    reject(validators["theorems"], mutated, "known theorem promoted to solves_clay")

    mutated = copy.deepcopy(documents["theorems"])
    mutated["theorems"][0]["formalized"] = True
    reject(validators["theorems"], mutated, "bare formalized=true accepted")

    weakened_theorems = copy.deepcopy(documents["theorems"])
    serrin = next(
        record
        for record in weakened_theorems["theorems"]
        if record["theorem_id"] == "KNOWN_SERRIN_CONDITIONAL_REGULARITY"
    )
    serrin["hypotheses_summary"] = "Any weak solution, with no additional integrability condition."
    mixed = copy.deepcopy(documents)
    mixed["theorems"] = weakened_theorems
    require_cross_rejected(mixed, "Serrin hypotheses semantically weakened")

    strengthened_theorems = copy.deepcopy(documents["theorems"])
    serrin = next(
        record
        for record in strengthened_theorems["theorems"]
        if record["theorem_id"] == "KNOWN_SERRIN_CONDITIONAL_REGULARITY"
    )
    serrin["conclusion_summary"] = "Every three-dimensional weak solution is globally smooth."
    mixed = copy.deepcopy(documents)
    mixed["theorems"] = strengthened_theorems
    require_cross_rejected(mixed, "Serrin conclusion semantically strengthened")

    mutated = copy.deepcopy(documents["barriers"])
    del mutated["barriers"][0]["required_response"]
    reject(validators["barriers"], mutated, "barrier proof obligation removed")

    mutated = copy.deepcopy(documents["identities"])
    mutated["identities"][0]["assumptions"] = []
    reject(validators["identities"], mutated, "baseline identity assumptions removed")

    secondary_sources = copy.deepcopy(documents["sources"])
    secondary_sources["sources"][1]["authority_class"] = "secondary_discovery"
    mixed = copy.deepcopy(documents)
    mixed["sources"] = secondary_sources
    require_cross_rejected(mixed, "secondary source authorized theorem")

    disguised_official = copy.deepcopy(documents["sources"])
    official = disguised_official["sources"][0]
    official["authority_class"] = "primary_research"
    official["authors"] = ["Different Author"]
    official["title"] = "Different valid-looking title"
    official["url"] = "https://example.org/different-primary-source"
    mixed = copy.deepcopy(documents)
    mixed["sources"] = disguised_official
    require_cross_rejected(mixed, "canonical CMI source identity removed")


def main() -> None:
    documents: dict[str, dict] = {}
    validators: dict[str, Draft202012Validator] = {}

    for name, (document_path, schema_path) in DOCUMENTS.items():
        documents[name] = load_json(document_path)
        validators[name] = validator_for(schema_path)
        validators[name].validate(documents[name])

    validate_cross_registry(documents)
    run_negative_probes(documents, validators)

    print(
        "Known-boundary validation: PASS "
        f"({len(documents['sources']['sources'])} sources, "
        f"{len(documents['theorems']['theorems'])} theorem summaries, "
        f"{len(documents['barriers']['barriers'])} barriers, "
        f"{len(documents['identities']['identities'])} baseline identities)"
    )


if __name__ == "__main__":
    main()
