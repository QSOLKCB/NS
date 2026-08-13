#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the independent precision referee contract and executable correspondence."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ns_lab.precision_referee import (
    NONCLAIMS,
    REFEREE_BACKEND_ID,
    REFEREE_VERSION,
    build_precision_report,
)
from ns_lab.solver import RunConfig

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
CONTRACT_PATH = RESEARCH / "precision_referee_contract.json"
CONTRACT_SCHEMA_PATH = RESEARCH / "schemas" / "precision_referee_contract.schema.json"
REPORT_SCHEMA_PATH = RESEARCH / "schemas" / "precision_referee_report.schema.json"
LAB_CONTRACT_PATH = RESEARCH / "lab_contract.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {path}")
    return value


def reject(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"precision referee schema regression: forbidden mutation accepted: {label}")


def negative_probes(contract: dict, validator: Draft202012Validator) -> None:
    mutated = copy.deepcopy(contract)
    mutated["independence_claims"]["independent_spatial_discretization"] = True
    reject(validator, mutated, "referee falsely promoted to independent spatial discretization")

    mutated = copy.deepcopy(contract)
    mutated["evidence_policy"]["singularity_oriented_promotion_enabled"] = True
    reject(validator, mutated, "singularity-oriented promotion enabled by low-resolution referee")

    mutated = copy.deepcopy(contract)
    mutated["scope"]["resolution"] = 16
    reject(validator, mutated, "unsupported referee resolution broadened")

    mutated = copy.deepcopy(contract)
    mutated["required_nonclaims"].pop()
    reject(validator, mutated, "precision-referee nonclaim removed")


def main() -> None:
    contract = load(CONTRACT_PATH)
    contract_schema = load(CONTRACT_SCHEMA_PATH)
    report_schema = load(REPORT_SCHEMA_PATH)
    lab = load(LAB_CONTRACT_PATH)

    Draft202012Validator.check_schema(contract_schema)
    contract_validator = Draft202012Validator(contract_schema)
    contract_validator.validate(contract)
    Draft202012Validator.check_schema(report_schema)
    report_validator = Draft202012Validator(report_schema)

    if contract["backend_id"] != REFEREE_BACKEND_ID:
        raise SystemExit("precision referee backend ID drift")
    if contract["backend_version"] != REFEREE_VERSION:
        raise SystemExit("precision referee implementation/version drift")
    if contract["required_nonclaims"] != NONCLAIMS:
        raise SystemExit("precision referee code/contract nonclaim drift")

    expected_link = {
        "contract": "research/precision_referee_contract.json",
        "available_for_reference_family": True,
        "independent_arithmetic": True,
        "independent_nonlinear_evaluation": True,
        "independent_spatial_discretization": False,
        "scalable_mechanism_search_backend": False,
    }
    if lab.get("precision_referee") != expected_link:
        raise SystemExit("lab contract precision-referee correspondence drift")
    if lab["evidence_policy"]["singularity_oriented_promotion_enabled"]:
        raise SystemExit("lab improperly enabled singularity-oriented promotion")

    config = RunConfig(
        resolution=contract["scope"]["resolution"],
        viscosity=0.01,
        dt=0.001,
        steps=1,
        amplitude=1.0,
        diagnostic_stride=1,
    )
    report = build_precision_report(
        config,
        low_dps=contract["precision_policy"]["default_low_dps"],
        high_dps=contract["precision_policy"]["default_high_dps"],
    )
    report_validator.validate(report)

    if (
        report["comparison_metrics"]["max_retained_modal_abs_difference"]
        >= contract["acceptance"]["max_reference_modal_abs_difference"]
    ):
        raise SystemExit("reference/referee modal agreement exceeded contract tolerance")
    if Decimal(report["precision_ladder"]["max_modal_abs_difference_decimal"]) >= Decimal(
        contract["acceptance"]["max_precision_ladder_modal_abs_difference_decimal"]
    ):
        raise SystemExit("precision ladder failed arbitrary-precision self-convergence threshold")

    negative_probes(contract, contract_validator)
    print(
        "Precision referee validation: PASS "
        f"(N={contract['scope']['resolution']}, "
        f"dps={contract['precision_policy']['default_low_dps']}->"
        f"{contract['precision_policy']['default_high_dps']})"
    )


if __name__ == "__main__":
    main()
