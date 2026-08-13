# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import mpmath as mp
import pytest
from jsonschema import Draft202012Validator, FormatChecker

import ns_lab.precision_referee as referee_module
from ns_lab.precision_referee import (
    PrecisionConfig,
    build_precision_report,
    retained_axis,
    retained_modes,
    run_precision_referee,
    taylor_green_modal_state,
    write_precision_artifacts,
)
from ns_lab.solver import RunConfig, run_taylor_green

SOURCE_COMMIT = "a" * 40
CREATED_AT = "2026-08-13T00:00:00Z"


def _report(config: RunConfig) -> dict:
    return build_precision_report(
        config,
        experiment_id="TEST_PRECISION_REFEREE",
        source_commit=SOURCE_COMMIT,
        operator_or_agent="pytest",
        created_at_utc=CREATED_AT,
        low_dps=50,
        high_dps=80,
    )


def test_strict_retained_axis_has_no_cutoff_boundary_modes():
    assert retained_axis(8) == (-2, -1, 0, 1, 2)
    assert len(retained_modes(8)) == 125


def test_analytic_taylor_green_modal_state_is_exactly_divergence_free():
    config = RunConfig(resolution=8, steps=1)
    with mp.workdps(80):
        state = taylor_green_modal_state(config)
        for mode, value in state.items():
            divergence_coefficient = sum(mode[i] * value[i] for i in range(3))
            assert divergence_coefficient == 0


def test_precision_referee_rejects_unsupported_resolution():
    with pytest.raises(ValueError):
        run_precision_referee(RunConfig(resolution=16, steps=1), PrecisionConfig(80))


def test_precision_report_agrees_with_reference_and_self_converges():
    config = RunConfig(resolution=8, viscosity=0.01, dt=0.001, steps=1, amplitude=1.0)
    report = _report(config)

    assert report["comparison_status"] == "comparable"
    assert report["comparison_metrics"]["max_retained_modal_abs_difference"] < 1e-12
    assert report["comparison_metrics"]["kinetic_energy_abs_difference"] < 1e-12
    assert report["comparison_metrics"]["enstrophy_abs_difference"] < 1e-12
    assert Decimal(report["precision_ladder"]["max_modal_abs_difference_decimal"]) < Decimal("1e-45")
    assert report["independence"]["independent_spatial_discretization"] is False
    assert report["claim_level"] == "exploratory"
    assert report["provenance"] == {
        "experiment_id": "TEST_PRECISION_REFEREE",
        "source_commit": SOURCE_COMMIT,
        "created_at_utc": CREATED_AT,
        "operator_or_agent": "pytest",
    }


def test_precision_report_validates_against_schema():
    root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (root / "research/schemas/precision_referee_report.schema.json").read_text(
            encoding="utf-8"
        )
    )
    report = _report(
        RunConfig(resolution=8, viscosity=0.01, dt=0.001, steps=1)
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)


def test_failed_float64_reference_is_preserved_while_referee_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    config = RunConfig(resolution=8, viscosity=0.01, dt=0.001, steps=1)
    failed = run_taylor_green(config)
    failed["termination_reason"] = "non_finite_numerical_state"
    failed["warnings_or_errors"] = ["synthetic float64 failure for regression"]
    failed["completed_steps"] = 0

    monkeypatch.setattr(referee_module, "run_taylor_green", lambda _: failed)
    manifest, report = write_precision_artifacts(
        output_dir=tmp_path / "failed-reference",
        experiment_id="TEST_FAILED_REFERENCE",
        source_commit=SOURCE_COMMIT,
        operator_or_agent="pytest",
        config=config,
        low_dps=50,
        high_dps=80,
    )

    assert report["comparison_status"] == "reference_failed_referee_completed"
    assert report["reference_run"]["termination_reason"] == "non_finite_numerical_state"
    assert report["reference_run"]["warnings_or_errors"] == [
        "synthetic float64 failure for regression"
    ]
    assert report["referee_run"]["termination_reason"] == "requested_step_count_completed"
    assert report["comparison_metrics"]["max_retained_modal_abs_difference"] is None
    assert report["comparison_metrics"]["referee_kinetic_energy_decimal"] is not None
    assert manifest["termination_reason"] == "reference_failed_referee_completed"

    preserved = json.loads(
        (tmp_path / "failed-reference" / "reference_run.json").read_text(
            encoding="utf-8"
        )
    )
    assert preserved["termination_reason"] == "non_finite_numerical_state"
    assert preserved["warnings_or_errors"] == ["synthetic float64 failure for regression"]


def test_precision_artifact_bundle_has_full_manifest_and_matching_hashes(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    config = RunConfig(resolution=8, viscosity=0.01, dt=0.001, steps=1)
    output_dir = tmp_path / "bundle"
    manifest, report = write_precision_artifacts(
        output_dir=output_dir,
        experiment_id="TEST_PRECISION_BUNDLE",
        source_commit=SOURCE_COMMIT,
        operator_or_agent="pytest",
        config=config,
        low_dps=50,
        high_dps=80,
    )

    manifest_schema = json.loads(
        (root / "research/schemas/experiment_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator(
        manifest_schema,
        format_checker=FormatChecker(),
    ).validate(manifest)

    assert report["provenance"]["experiment_id"] == manifest["experiment_id"]
    assert report["provenance"]["source_commit"] == manifest["source_commit"]
    assert report["provenance"]["operator_or_agent"] == manifest["operator_or_agent"]
    assert report["provenance"]["created_at_utc"] == manifest["created_at_utc"]

    for filename, expected in manifest["output_hashes"].items():
        actual = hashlib.sha256((output_dir / filename).read_bytes()).hexdigest()
        assert actual == expected
