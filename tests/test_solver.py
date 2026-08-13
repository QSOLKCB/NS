# SPDX-License-Identifier: Apache-2.0
import hashlib
import math

import numpy as np
import pytest

from ns_lab.diagnostics import velocity_lp_scaling_exponent
from ns_lab.solver import RunConfig, run_taylor_green
from ns_lab.spectral import SpectralOperators


def _digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(array).tobytes(order="C")).hexdigest()


def test_taylor_green_reference_is_numerically_divergence_free():
    result = run_taylor_green(RunConfig(resolution=8, steps=2, dt=0.001))
    max_div = max(d["divergence_l2"] for d in result["diagnostics"])
    assert max_div < 1e-12


def test_unforced_viscous_reference_energy_does_not_increase():
    result = run_taylor_green(
        RunConfig(resolution=8, steps=4, dt=0.001, viscosity=0.01)
    )
    energies = [d["kinetic_energy"] for d in result["diagnostics"]]
    assert all(b <= a + 1e-13 for a, b in zip(energies, energies[1:]))


def test_identical_inputs_replay_to_identical_final_state():
    config = RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.01)
    first = run_taylor_green(config)
    second = run_taylor_green(config)
    assert _digest(first["final_velocity"]) == _digest(second["final_velocity"])


def test_changed_parameter_changes_result_identity():
    first = run_taylor_green(
        RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.01)
    )
    second = run_taylor_green(
        RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.02)
    )
    assert _digest(first["final_velocity"]) != _digest(second["final_velocity"])


def test_baseline_operator_residuals_are_small_for_reference_case():
    result = run_taylor_green(RunConfig(resolution=8, steps=1, dt=0.001))
    for d in result["diagnostics"]:
        assert d["pressure_poisson_residual_l2"] < 1e-12
        assert d["vorticity_equation_residual_l2"] < 1e-11


def test_l3_is_critical_under_ns_velocity_scaling():
    assert abs(velocity_lp_scaling_exponent(3.0)) < 1e-15
    assert velocity_lp_scaling_exponent(2.0) == -0.5


def test_strict_two_thirds_mask_excludes_both_cutoff_modes():
    ops = SpectralOperators.periodic_cube(12)
    axis_modes = np.fft.fftfreq(12, d=1.0 / 12)
    plus = int(np.where(axis_modes == 4.0)[0][0])
    minus = int(np.where(axis_modes == -4.0)[0][0])
    zero = int(np.where(axis_modes == 0.0)[0][0])

    assert not bool(ops.dealias_mask[plus, zero, zero])
    assert not bool(ops.dealias_mask[minus, zero, zero])
    assert bool(ops.dealias_mask[plus - 1, zero, zero])


@pytest.mark.parametrize(
    "field,value",
    [
        ("dt", math.nan),
        ("dt", math.inf),
        ("viscosity", math.nan),
        ("amplitude", math.inf),
    ],
)
def test_non_finite_run_parameters_are_rejected(field, value):
    kwargs = {field: value}
    with pytest.raises(ValueError, match="finite"):
        RunConfig(**kwargs).validate()


def test_finite_but_unstable_integration_is_marked_as_numerical_failure():
    result = run_taylor_green(
        RunConfig(resolution=8, steps=1, dt=1.0e308, viscosity=0.01)
    )
    assert result["termination_reason"] != "requested_step_count_completed"
    assert result["warnings_or_errors"]
    assert result["completed_steps"] == 0
