#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate QSOL NS known-boundary registries and cross-file invariants."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SCHEMAS = RESEARCH / "schemas"

DOCUMENTS = {
    "clay": (RESEARCH / "clay_target.json", SCHEMAS / "clay_target.schema.json"),
    "sources": (RESEARCH / "source_registry.json", SCHEMAS / "source_registry.schema.json"),
    "theorems": (RESEARCH / "theorem_registry.json", SCHEMAS / "theorem_registry.schema.json"),
    "barriers": (RESEARCH / "proof_barriers.json", SCHEMAS / "proof_barriers.schema.json"),
    "identities": (RESEARCH / "baseline_identities.json", SCHEMAS / "baseline_identities.schema.json"),
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
    return Draft202012Validator(schema)


def reject(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"schema regression: forbidden mutation accepted: {label}")


def require_unique(records: list[dict], key: str, label: str) -> set[str]:
    values = [record[key] for record in records]
    if len(values) != len(set(values)):
        raise SystemExit(f"duplicate {label}: {values}")
    return set(values)


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

    mutated = copy.deepcopy(documents["theorems"])
    mutated["theorems"][0]["hypotheses_summary"] = ""
    reject(validators["theorems"], mutated, "theorem hypotheses removed")

    mutated = copy.deepcopy(documents["theorems"])
    mutated["theorems"][0]["solves_clay"] = True
    reject(validators["theorems"], mutated, "known theorem promoted to solves_clay")

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
    try:
        validate_cross_registry(mixed)
    except SystemExit:
        pass
    else:
        raise SystemExit("cross-registry regression: secondary source authorized theorem")


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
