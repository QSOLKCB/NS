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

    print("AGENTS contract validation: PASS")


if __name__ == "__main__":
    main()
