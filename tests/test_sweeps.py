# SPDX-License-Identifier: Apache-2.0
from ns_lab.solver import RunConfig
from ns_lab.sweeps import resolution_comparison, timestep_comparison


def test_timestep_comparison_preserves_final_time():
    config = RunConfig(resolution=8, dt=0.001, steps=2)
    result = timestep_comparison(config)
    assert result["base"]["dt"] * result["base"]["steps"] == result["comparison"]["dt"] * result["comparison"]["steps"]
    assert result["claim_boundary"] == "sensitivity_diagnostic_not_continuum_proof"


def test_resolution_comparison_is_exact_double_resolution():
    result = resolution_comparison(RunConfig(resolution=8, dt=0.001, steps=1))
    assert result["comparison"]["resolution"] == 16
    assert result["claim_boundary"] == "sensitivity_diagnostic_not_continuum_proof"
