# SPDX-License-Identifier: Apache-2.0
import json
from decimal import Decimal
from pathlib import Path

import mpmath as mp
import pytest
from jsonschema import Draft202012Validator

from ns_lab.precision_referee import (
    PrecisionConfig,
    build_precision_report,
    retained_axis,
    retained_modes,
    run_precision_referee,
    taylor_green_modal_state,
)
from ns_lab.solver import RunConfig


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
    report = build_precision_report(config, low_dps=50, high_dps=80)

    assert report["comparison_metrics"]["max_retained_modal_abs_difference"] < 1e-12
    assert report["comparison_metrics"]["kinetic_energy_abs_difference"] < 1e-12
    assert report["comparison_metrics"]["enstrophy_abs_difference"] < 1e-12
    assert Decimal(report["precision_ladder"]["max_modal_abs_difference_decimal"]) < Decimal("1e-45")
    assert report["independence"]["independent_spatial_discretization"] is False
    assert report["claim_level"] == "exploratory"


def test_precision_report_validates_against_schema():
    root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (root / "research/schemas/precision_referee_report.schema.json").read_text(
            encoding="utf-8"
        )
    )
    report = build_precision_report(
        RunConfig(resolution=8, viscosity=0.01, dt=0.001, steps=1),
        low_dps=50,
        high_dps=80,
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(report)
