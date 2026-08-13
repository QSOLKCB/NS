# SPDX-License-Identifier: Apache-2.0
import hashlib
import numpy as np

from ns_lab.diagnostics import velocity_lp_scaling_exponent
from ns_lab.solver import RunConfig, run_taylor_green


def _digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(array).tobytes(order="C")).hexdigest()


def test_taylor_green_reference_is_numerically_divergence_free():
    result = run_taylor_green(RunConfig(resolution=8, steps=2, dt=0.001))
    max_div = max(d["divergence_l2"] for d in result["diagnostics"])
    assert max_div < 1e-12


def test_unforced_viscous_reference_energy_does_not_increase():
    result = run_taylor_green(RunConfig(resolution=8, steps=4, dt=0.001, viscosity=0.01))
    energies = [d["kinetic_energy"] for d in result["diagnostics"]]
    assert all(b <= a + 1e-13 for a, b in zip(energies, energies[1:]))


def test_identical_inputs_replay_to_identical_final_state():
    config = RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.01)
    first = run_taylor_green(config)
    second = run_taylor_green(config)
    assert _digest(first["final_velocity"]) == _digest(second["final_velocity"])


def test_changed_parameter_changes_result_identity():
    first = run_taylor_green(RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.01))
    second = run_taylor_green(RunConfig(resolution=8, steps=3, dt=0.001, viscosity=0.02))
    assert _digest(first["final_velocity"]) != _digest(second["final_velocity"])


def test_baseline_operator_residuals_are_small_for_reference_case():
    result = run_taylor_green(RunConfig(resolution=8, steps=1, dt=0.001))
    for d in result["diagnostics"]:
        assert d["pressure_poisson_residual_l2"] < 1e-12
        assert d["vorticity_equation_residual_l2"] < 1e-11


def test_l3_is_critical_under_ns_velocity_scaling():
    assert abs(velocity_lp_scaling_exponent(3.0)) < 1e-15
    assert velocity_lp_scaling_exponent(2.0) == -0.5
