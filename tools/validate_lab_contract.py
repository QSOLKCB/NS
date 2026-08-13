#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the deterministic PDE laboratory contract and cross-file invariants."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
LAB_PATH = RESEARCH / "lab_contract.json"
LAB_SCHEMA_PATH = RESEARCH / "schemas" / "lab_contract.schema.json"
MANIFEST_SCHEMA_PATH = RESEARCH / "schemas" / "experiment_manifest.schema.json"
AGENTS_PATH = ROOT / "AGENTS.md"
BASELINE_PATH = RESEARCH / "baseline_identities.json"


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
    raise SystemExit(f"lab schema regression: forbidden mutation accepted: {label}")


def validate_manifest_field_alignment(agents: dict, manifest_schema: dict) -> None:
    contract_fields = agents["experiment_requirements"]["required_fields"]
    schema_fields = manifest_schema["required"]
    if contract_fields != schema_fields:
        raise SystemExit(
            "experiment manifest field drift against AGENTS.md canonical order: "
            f"contract={contract_fields}, schema={schema_fields}"
        )


def validate_identity_bindings(lab: dict, baseline: dict) -> None:
    baseline_ids = {record["identity_id"] for record in baseline["identities"]}
    bindings = lab["baseline_identity_bindings"]
    binding_ids = [record["identity_id"] for record in bindings]
    if len(binding_ids) != len(set(binding_ids)):
        raise SystemExit("duplicate baseline identity binding")
    if set(binding_ids) != baseline_ids:
        raise SystemExit(
            f"baseline identity binding drift: bound={sorted(binding_ids)}, expected={sorted(baseline_ids)}"
        )

    for binding in bindings:
        callable_path = binding["implementation"].split(":", 1)[0]
        module_name, attr_name = callable_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        if not callable(getattr(module, attr_name, None)):
            raise SystemExit(f"baseline identity binding is not callable: {binding['implementation']}")


def validate_runtime_correspondence(lab: dict) -> None:
    from ns_lab.solver import LAB_VERSION
    if lab["solver_version"] != LAB_VERSION:
        raise SystemExit(f"lab contract version drift: {lab['solver_version']} != {LAB_VERSION}")


def negative_probes(lab: dict, validator: Draft202012Validator, agents: dict, manifest_schema: dict) -> None:
    mutated = copy.deepcopy(lab)
    mutated["evidence_policy"]["singularity_oriented_promotion_enabled"] = True
    reject(validator, mutated, "singularity promotion enabled in v0.1")

    mutated = copy.deepcopy(lab)
    mutated["evidence_policy"]["maximum_automatic_claim_level"] = "proved_lemma"
    reject(validator, mutated, "numerical lab allowed to promote to proved_lemma")

    mutated = copy.deepcopy(lab)
    mutated["scope"]["forcing"] = "arbitrary"
    reject(validator, mutated, "reference solver forcing scope broadened")

    mutated = copy.deepcopy(lab)
    mutated["determinism"]["cross_platform_bitwise_identity_promised"] = True
    reject(validator, mutated, "unsupported cross-platform bitwise promise enabled")

    mutated = copy.deepcopy(lab)
    mutated["baseline_identity_bindings"].pop()
    reject(validator, mutated, "baseline identity binding removed")

    drifted_schema = copy.deepcopy(manifest_schema)
    drifted_schema["required"].remove("created_at_utc")
    try:
        validate_manifest_field_alignment(agents, drifted_schema)
    except SystemExit:
        pass
    else:
        raise SystemExit("manifest/AGENTS field drift probe was accepted")


def main() -> None:
    lab = load(LAB_PATH)
    lab_schema = load(LAB_SCHEMA_PATH)
    manifest_schema = load(MANIFEST_SCHEMA_PATH)
    agents = load(AGENTS_PATH)
    baseline = load(BASELINE_PATH)

    Draft202012Validator.check_schema(lab_schema)
    validator = Draft202012Validator(lab_schema)
    validator.validate(lab)
    Draft202012Validator.check_schema(manifest_schema)

    validate_manifest_field_alignment(agents, manifest_schema)
    validate_identity_bindings(lab, baseline)
    validate_runtime_correspondence(lab)
    negative_probes(lab, validator, agents, manifest_schema)

    print(f"PDE lab contract validation: PASS ({len(lab['baseline_identity_bindings'])} baseline identity bindings)")


if __name__ == "__main__":
    main()
