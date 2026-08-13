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

EXPECTED_IDENTITY_BINDINGS = {
    "BASE_INCOMPRESSIBILITY": "ns_lab.diagnostics.snapshot:divergence_l2",
    "BASE_NS_SCALING": "ns_lab.diagnostics.velocity_lp_scaling_exponent",
    "BASE_SMOOTH_ENERGY_EQUALITY": "ns_lab.diagnostics.balance_residuals:energy_balance_residual",
    "BASE_VORTICITY_EQUATION": "ns_lab.diagnostics.vorticity_equation_residual_l2",
    "BASE_SMOOTH_ENSTROPHY_BALANCE": "ns_lab.diagnostics.balance_residuals:enstrophy_balance_residual",
    "BASE_PRESSURE_POISSON": "ns_lab.diagnostics.pressure_poisson_residual_l2",
}


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


def require_rejected(callable_obj, label: str) -> None:
    try:
        callable_obj()
    except SystemExit:
        return
    raise SystemExit(f"lab cross-file regression: forbidden mutation accepted: {label}")


def validate_manifest_field_alignment(agents: dict, manifest_schema: dict) -> None:
    contract_fields = agents["experiment_requirements"]["required_fields"]
    schema_fields = manifest_schema["required"]
    if contract_fields != schema_fields:
        raise SystemExit(
            "experiment manifest field drift against AGENTS.md canonical order: "
            f"contract={contract_fields}, schema={schema_fields}"
        )

    singularity_fields = agents["experiment_requirements"][
        "singularity_run_required_fields"
    ]
    missing = [
        field
        for field in singularity_fields
        if field not in manifest_schema.get("properties", {})
    ]
    if missing:
        raise SystemExit(
            "experiment manifest schema cannot represent required singularity metadata: "
            f"{missing}"
        )


def _validate_target(
    *,
    callable_path: str,
    target: str | None,
    implementation: str,
) -> None:
    module_name, attr_name = callable_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    callable_obj = getattr(module, attr_name, None)
    if not callable(callable_obj):
        raise SystemExit(f"baseline identity binding is not callable: {implementation}")

    if target is None:
        return

    if callable_path == "ns_lab.diagnostics.snapshot":
        fields = set(module.SnapshotDiagnostics.__dataclass_fields__)
    elif callable_path == "ns_lab.diagnostics.balance_residuals":
        fields = {"energy_balance_residual", "enstrophy_balance_residual"}
    else:
        raise SystemExit(
            f"baseline identity binding names a target on unsupported callable: {implementation}"
        )

    if target not in fields:
        raise SystemExit(
            f"baseline identity binding target does not exist: {implementation}; "
            f"allowed={sorted(fields)}"
        )


def validate_identity_bindings(lab: dict, baseline: dict) -> None:
    baseline_ids = {record["identity_id"] for record in baseline["identities"]}
    bindings = lab["baseline_identity_bindings"]
    binding_ids = [record["identity_id"] for record in bindings]
    if len(binding_ids) != len(set(binding_ids)):
        raise SystemExit("duplicate baseline identity binding")
    if set(binding_ids) != baseline_ids:
        raise SystemExit(
            f"baseline identity binding drift: bound={sorted(binding_ids)}, "
            f"expected={sorted(baseline_ids)}"
        )
    if baseline_ids != set(EXPECTED_IDENTITY_BINDINGS):
        raise SystemExit(
            "baseline identity registry changed without an audited executable-binding update"
        )

    for binding in bindings:
        identity_id = binding["identity_id"]
        implementation = binding["implementation"]
        expected = EXPECTED_IDENTITY_BINDINGS[identity_id]
        if implementation != expected:
            raise SystemExit(
                f"baseline identity implementation mismatch for {identity_id}: "
                f"{implementation!r} != {expected!r}"
            )

        callable_path, separator, target = implementation.partition(":")
        _validate_target(
            callable_path=callable_path,
            target=target if separator else None,
            implementation=implementation,
        )


def validate_runtime_correspondence(lab: dict) -> None:
    from ns_lab.solver import LAB_VERSION

    if lab["solver_version"] != LAB_VERSION:
        raise SystemExit(
            f"lab contract version drift: {lab['solver_version']} != {LAB_VERSION}"
        )


def negative_probes(
    lab: dict,
    validator: Draft202012Validator,
    agents: dict,
    manifest_schema: dict,
    baseline: dict,
) -> None:
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
    require_rejected(
        lambda: validate_manifest_field_alignment(agents, drifted_schema),
        "manifest/AGENTS general field drift",
    )

    drifted_schema = copy.deepcopy(manifest_schema)
    del drifted_schema["properties"]["precision_sensitivity"]
    require_rejected(
        lambda: validate_manifest_field_alignment(agents, drifted_schema),
        "singularity metadata field removed from manifest schema",
    )

    mutated = copy.deepcopy(lab)
    mutated["baseline_identity_bindings"][0]["implementation"] = (
        "ns_lab.diagnostics.snapshot:not_a_diagnostic"
    )
    require_rejected(
        lambda: validate_identity_bindings(mutated, baseline),
        "nonexistent diagnostic target",
    )

    mutated = copy.deepcopy(lab)
    mutated["baseline_identity_bindings"][0]["implementation"] = (
        EXPECTED_IDENTITY_BINDINGS["BASE_PRESSURE_POISSON"]
    )
    require_rejected(
        lambda: validate_identity_bindings(mutated, baseline),
        "identity implementation swapped",
    )


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
    negative_probes(lab, validator, agents, manifest_schema, baseline)

    print(
        "PDE lab contract validation: PASS "
        f"({len(lab['baseline_identity_bindings'])} baseline identity bindings)"
    )


if __name__ == "__main__":
    main()
