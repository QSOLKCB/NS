#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate fail-closed intake of external Navier-Stokes solution claims."""

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

BASELINE_COMMIT = "504180162eb117bc3eb280b93c8ef4df845c0d27"
OPENAI_SOURCE_IDS = ["OPENAI_NS_BLOWUP_2026", "OPENAI_NS_LEAN_2026"]
EXPECTED = {
    "A": ("not_addressed_by_source", "not_resolved"),
    "B": ("not_addressed_by_source", "not_resolved"),
    "C": ("claims_satisfied", "external_claim_pending_independent_verification"),
    "D": ("claims_satisfied", "external_claim_pending_independent_verification"),
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject_cross(candidate: dict, sources: dict, label: str) -> None:
    try:
        validate_cross(candidate, sources)
    except SystemExit:
        return
    raise SystemExit(f"external-claim regression: forbidden mutation accepted: {label}")


def reject_schema(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"external-claim schema regression: forbidden mutation accepted: {label}")


def validate_cross(claims: dict, sources: dict) -> None:
    if claims["repository_baseline_commit"] != BASELINE_COMMIT:
        raise SystemExit("pre-OpenAI baseline commit drift")

    source_by_id = {record["source_id"]: record for record in sources["sources"]}
    for source_id in OPENAI_SOURCE_IDS:
        if source_id not in source_by_id:
            raise SystemExit(f"missing required OpenAI intake source: {source_id}")
        if source_by_id[source_id]["authority_class"] != "primary_research":
            raise SystemExit(f"OpenAI intake source lost primary-research authority: {source_id}")

    records = claims["claims"]
    formulation_ids = [record["formulation_id"] for record in records]
    if formulation_ids != ["A", "B", "C", "D"]:
        raise SystemExit(f"external claim formulation order/identity drift: {formulation_ids}")

    claim_ids = [record["claim_id"] for record in records]
    if len(claim_ids) != len(set(claim_ids)):
        raise SystemExit(f"duplicate external claim IDs: {claim_ids}")

    for record in records:
        formulation_id = record["formulation_id"]
        expected_source_position, expected_qsol_status = EXPECTED[formulation_id]
        if record["claim_id"] != f"OPENAI_2026_{formulation_id}":
            raise SystemExit(f"claim/formulation mismatch: {record['claim_id']}")
        if record["source_ids"] != OPENAI_SOURCE_IDS:
            raise SystemExit(f"source set drift for formulation {formulation_id}")
        if record["source_position"] != expected_source_position:
            raise SystemExit(f"source-position promotion/drift for formulation {formulation_id}")
        if record["qsol_status"] != expected_qsol_status:
            raise SystemExit(f"QSOL status promotion/drift for formulation {formulation_id}")
        if not record["verification_obligations"]:
            raise SystemExit(f"missing verification obligations for formulation {formulation_id}")

    if claims["policy"]["repository_claim"] != "no_solution_claim":
        raise SystemExit("external intake improperly promoted to a repository solution claim")


def run_negative_probes(
    claims: dict,
    sources: dict,
    validator: Draft202012Validator,
) -> None:
    mutated = copy.deepcopy(claims)
    mutated["policy"]["repository_claim"] = "solution_verified"
    reject_schema(validator, mutated, "repository solution claim smuggled into policy")

    mutated = copy.deepcopy(claims)
    mutated["claims"][0]["source_position"] = "claims_satisfied"
    reject_cross(mutated, sources, "OpenAI source promoted to Clay A")

    mutated = copy.deepcopy(claims)
    mutated["claims"][2]["qsol_status"] = "not_resolved"
    reject_cross(mutated, sources, "Clay C external-claim status erased")

    mutated = copy.deepcopy(claims)
    mutated["claims"][2]["source_ids"] = ["OPENAI_NS_BLOWUP_2026"]
    reject_cross(mutated, sources, "Lean artifact removed from pinned C intake")

    mutated = copy.deepcopy(claims)
    mutated["repository_baseline_commit"] = "0" * 40
    reject_cross(mutated, sources, "historical baseline commit rewritten")

    mutated_sources = copy.deepcopy(sources)
    lean = next(
        record
        for record in mutated_sources["sources"]
        if record["source_id"] == "OPENAI_NS_LEAN_2026"
    )
    lean["authority_class"] = "secondary_discovery"
    reject_cross(claims, mutated_sources, "formalization artifact authority downgraded silently")


def main() -> None:
    claims_path = RESEARCH / "external_claim_registry.json"
    schema_path = SCHEMAS / "external_claim_registry.schema.json"
    sources_path = RESEARCH / "source_registry.json"

    claims = load_json(claims_path)
    sources = load_json(sources_path)
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    validator.validate(claims)

    validate_cross(claims, sources)
    run_negative_probes(claims, sources, validator)

    print(
        "External-claim validation: PASS "
        f"({len(claims['claims'])} Clay formulations, baseline {BASELINE_COMMIT[:12]})"
    )


if __name__ == "__main__":
    main()
