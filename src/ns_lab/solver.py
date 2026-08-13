# SPDX-License-Identifier: Apache-2.0
"""Deterministic pseudo-spectral reference solver for the periodic cube."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .diagnostics import balance_residuals, snapshot, velocity_rhs_hat
from .initial_data import taylor_green_hat
from .spectral import (
    SpectralOperators,
    dealias,
    ifft_velocity,
    project_divergence_free,
)

LAB_VERSION = "0.1.0"


@dataclass(frozen=True)
class RunConfig:
    resolution: int = 8
    viscosity: float = 0.01
    dt: float = 0.001
    steps: int = 4
    amplitude: float = 1.0
    diagnostic_stride: int = 1

    def validate(self) -> None:
        if self.resolution < 6 or self.resolution % 2:
            raise ValueError("resolution must be an even integer >= 6")
        if self.viscosity <= 0.0:
            raise ValueError("viscosity must be > 0")
        if self.dt <= 0.0:
            raise ValueError("dt must be > 0")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")
        if self.amplitude <= 0.0:
            raise ValueError("amplitude must be > 0")
        if self.diagnostic_stride < 1:
            raise ValueError("diagnostic_stride must be >= 1")


def _canonicalize(u_hat: np.ndarray, ops: SpectralOperators) -> np.ndarray:
    return project_divergence_free(dealias(u_hat, ops), ops)


def rk4_step(
    u_hat: np.ndarray,
    *,
    dt: float,
    viscosity: float,
    ops: SpectralOperators,
) -> np.ndarray:
    def rhs(state: np.ndarray) -> np.ndarray:
        return velocity_rhs_hat(_canonicalize(state, ops), viscosity, ops)

    k1 = rhs(u_hat)
    k2 = rhs(u_hat + 0.5 * dt * k1)
    k3 = rhs(u_hat + 0.5 * dt * k2)
    k4 = rhs(u_hat + dt * k3)
    updated = u_hat + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return _canonicalize(updated, ops)


def run_taylor_green(config: RunConfig) -> dict[str, Any]:
    config.validate()
    ops = SpectralOperators.periodic_cube(config.resolution)
    u_hat = taylor_green_hat(config.resolution, config.amplitude, ops)

    diagnostics: list[dict[str, Any]] = []
    initial = snapshot(
        u_hat,
        time=0.0,
        dt=config.dt,
        viscosity=config.viscosity,
        ops=ops,
    )
    diagnostics.append(initial.to_dict())
    previous = initial

    balance_history: list[dict[str, float]] = []
    for step in range(1, config.steps + 1):
        u_hat = rk4_step(
            u_hat,
            dt=config.dt,
            viscosity=config.viscosity,
            ops=ops,
        )
        current = snapshot(
            u_hat,
            time=step * config.dt,
            dt=config.dt,
            viscosity=config.viscosity,
            ops=ops,
        )
        balance = balance_residuals(
            previous,
            current,
            dt=config.dt,
            viscosity=config.viscosity,
        )
        balance_history.append({"step": step, **balance})
        if step % config.diagnostic_stride == 0 or step == config.steps:
            diagnostics.append({"step": step, **current.to_dict(), **balance})
        previous = current

    return {
        "lab_version": LAB_VERSION,
        "config": {
            "resolution": config.resolution,
            "viscosity": config.viscosity,
            "dt": config.dt,
            "steps": config.steps,
            "amplitude": config.amplitude,
            "diagnostic_stride": config.diagnostic_stride,
        },
        "diagnostics": diagnostics,
        "balance_history": balance_history,
        "final_velocity": ifft_velocity(u_hat),
        "final_velocity_hat": u_hat,
    }
