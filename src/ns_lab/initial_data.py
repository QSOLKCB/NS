# SPDX-License-Identifier: Apache-2.0
"""Deterministic admissible initial data used by the reference laboratory."""

from __future__ import annotations

import numpy as np

from .spectral import SpectralOperators, dealias, fft_velocity, project_divergence_free


def taylor_green_velocity(resolution: int, amplitude: float = 1.0) -> np.ndarray:
    """Classical 2π-periodic Taylor-Green vortex embedded in three dimensions."""
    if amplitude <= 0.0:
        raise ValueError("amplitude must be positive")
    x = 2.0 * np.pi * np.arange(resolution, dtype=np.float64) / resolution
    xx, yy, zz = np.meshgrid(x, x, x, indexing="ij")
    u = np.empty((3, resolution, resolution, resolution), dtype=np.float64)
    u[0] = amplitude * np.sin(xx) * np.cos(yy) * np.cos(zz)
    u[1] = -amplitude * np.cos(xx) * np.sin(yy) * np.cos(zz)
    u[2] = 0.0
    return u


def taylor_green_hat(
    resolution: int,
    amplitude: float,
    ops: SpectralOperators,
) -> np.ndarray:
    u_hat = fft_velocity(taylor_green_velocity(resolution, amplitude))
    return project_divergence_free(dealias(u_hat, ops), ops)
