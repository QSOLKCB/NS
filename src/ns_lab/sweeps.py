# SPDX-License-Identifier: Apache-2.0
"""Deterministic timestep/resolution sensitivity comparisons."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .solver import RunConfig, run_taylor_green


def _final_summary(result: dict[str, Any]) -> dict[str, float]:
    final = result["diagnostics"][-1]
    return {
        "kinetic_energy": float(final["kinetic_energy"]),
        "enstrophy": float(final["enstrophy"]),
        "max_vorticity": float(final["max_vorticity"]),
        "divergence_l2": float(final["divergence_l2"]),
    }


def _differences(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    return {key: float(abs(a[key] - b[key])) for key in a}


def timestep_comparison(config: RunConfig) -> dict[str, Any]:
    """Compare dt against dt/2 at the same final physical time."""
    config.validate()
    fine = replace(config, dt=config.dt / 2.0, steps=config.steps * 2)
    base_result = run_taylor_green(config)
    fine_result = run_taylor_green(fine)
    base_summary = _final_summary(base_result)
    fine_summary = _final_summary(fine_result)
    return {
        "kind": "timestep_comparison",
        "base": {"dt": config.dt, "steps": config.steps, **base_summary},
        "comparison": {"dt": fine.dt, "steps": fine.steps, **fine_summary},
        "absolute_metric_differences": _differences(base_summary, fine_summary),
        "claim_boundary": "sensitivity_diagnostic_not_continuum_proof",
    }


def resolution_comparison(config: RunConfig) -> dict[str, Any]:
    """Compare N against 2N with all other configured parameters fixed."""
    config.validate()
    fine = replace(config, resolution=config.resolution * 2)
    base_result = run_taylor_green(config)
    fine_result = run_taylor_green(fine)
    base_summary = _final_summary(base_result)
    fine_summary = _final_summary(fine_result)
    return {
        "kind": "resolution_comparison",
        "base": {"resolution": config.resolution, **base_summary},
        "comparison": {"resolution": fine.resolution, **fine_summary},
        "absolute_metric_differences": _differences(base_summary, fine_summary),
        "claim_boundary": "sensitivity_diagnostic_not_continuum_proof",
    }
