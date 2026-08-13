# SPDX-License-Identifier: Apache-2.0
"""Diagnostics tied to the Phase-1 baseline identity registry."""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

from .spectral import (
    SpectralOperators,
    curl_hat,
    derivative_from_hat,
    divergence_from_hat,
    gradient_tensor,
    ifft_velocity,
    nonlinear_hat,
    pressure_hat_from_velocity,
    project_divergence_free,
)

Array = np.ndarray


@dataclass(frozen=True)
class SnapshotDiagnostics:
    time: float
    kinetic_energy: float
    enstrophy: float
    max_vorticity: float
    divergence_l2: float
    projection_residual_l2: float
    palinstrophy: float
    vortex_stretching: float
    pressure_poisson_residual_l2: float
    vorticity_equation_residual_l2: float
    cfl: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def l2_rms(field: Array) -> float:
    return float(np.sqrt(np.mean(np.square(np.abs(field)))))


def kinetic_energy(u_hat: Array, ops: SpectralOperators) -> float:
    u = ifft_velocity(u_hat)
    return float(0.5 * np.mean(np.sum(u * u, axis=0)))


def vorticity_hat(u_hat: Array, ops: SpectralOperators) -> Array:
    return curl_hat(u_hat, ops)


def enstrophy(u_hat: Array, ops: SpectralOperators) -> float:
    omega = ifft_velocity(vorticity_hat(u_hat, ops))
    return float(0.5 * np.mean(np.sum(omega * omega, axis=0)))


def palinstrophy(u_hat: Array, ops: SpectralOperators) -> float:
    omega_hat = vorticity_hat(u_hat, ops)
    total = np.zeros((ops.resolution, ops.resolution, ops.resolution), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            grad_component = derivative_from_hat(omega_hat[i], j, ops)
            total += grad_component * grad_component
    return float(0.5 * np.mean(total))


def vortex_stretching(u_hat: Array, ops: SpectralOperators) -> float:
    omega = ifft_velocity(vorticity_hat(u_hat, ops))
    grad_u = gradient_tensor(u_hat, ops)
    stretching_vector = np.einsum("jxyz,ijxyz->ixyz", omega, grad_u, optimize=True)
    return float(np.mean(np.einsum("ixyz,ixyz->xyz", omega, stretching_vector, optimize=True)))


def pressure_poisson_residual_l2(u_hat: Array, ops: SpectralOperators) -> float:
    n_hat = nonlinear_hat(u_hat, ops)
    p_hat = pressure_hat_from_velocity(u_hat, ops)
    residual_hat = (
        -ops.k2 * p_hat
        + 1j * (ops.kx * n_hat[0] + ops.ky * n_hat[1] + ops.kz * n_hat[2])
    )
    residual = np.fft.ifftn(residual_hat).real
    return l2_rms(residual)


def velocity_rhs_hat(u_hat: Array, viscosity: float, ops: SpectralOperators) -> Array:
    n_hat = nonlinear_hat(u_hat, ops)
    nonlinear_projected = project_divergence_free(n_hat, ops)
    return -nonlinear_projected - viscosity * ops.k2[None, ...] * u_hat


def vorticity_equation_residual_l2(
    u_hat: Array,
    viscosity: float,
    ops: SpectralOperators,
) -> float:
    """Check curl(du/dt) against -u·∇ω + ω·∇u + νΔω."""
    rhs_u_hat = velocity_rhs_hat(u_hat, viscosity, ops)
    lhs = ifft_velocity(curl_hat(rhs_u_hat, ops))

    u = ifft_velocity(u_hat)
    omega_hat = curl_hat(u_hat, ops)
    omega = ifft_velocity(omega_hat)

    grad_omega = np.empty(
        (3, 3, ops.resolution, ops.resolution, ops.resolution),
        dtype=np.float64,
    )
    for i in range(3):
        for j in range(3):
            grad_omega[i, j] = derivative_from_hat(omega_hat[i], j, ops)
    grad_u = gradient_tensor(u_hat, ops)

    advection = np.einsum("jxyz,ijxyz->ixyz", u, grad_omega, optimize=True)
    stretching = np.einsum("jxyz,ijxyz->ixyz", omega, grad_u, optimize=True)
    lap_omega = ifft_velocity(-ops.k2[None, ...] * omega_hat)
    rhs = -advection + stretching + viscosity * lap_omega

    # Both sides are compared after the same 2/3 spectral truncation implicit in
    # the velocity RHS. Residual is a solver-consistency diagnostic only.
    residual_hat = np.stack(
        [np.fft.fftn(rhs[i]) for i in range(3)],
        axis=0,
    )
    residual_hat *= ops.dealias_mask[None, ...]
    residual = lhs - ifft_velocity(residual_hat)
    return l2_rms(residual)


def projection_residual_l2(u_hat: Array, ops: SpectralOperators) -> float:
    projected = project_divergence_free(u_hat, ops)
    return l2_rms(ifft_velocity(projected - u_hat))


def snapshot(
    u_hat: Array,
    *,
    time: float,
    dt: float,
    viscosity: float,
    ops: SpectralOperators,
) -> SnapshotDiagnostics:
    u = ifft_velocity(u_hat)
    omega = ifft_velocity(curl_hat(u_hat, ops))
    speed = np.sqrt(np.sum(u * u, axis=0))
    vort_mag = np.sqrt(np.sum(omega * omega, axis=0))
    return SnapshotDiagnostics(
        time=float(time),
        kinetic_energy=kinetic_energy(u_hat, ops),
        enstrophy=enstrophy(u_hat, ops),
        max_vorticity=float(np.max(vort_mag)),
        divergence_l2=l2_rms(divergence_from_hat(u_hat, ops)),
        projection_residual_l2=projection_residual_l2(u_hat, ops),
        palinstrophy=palinstrophy(u_hat, ops),
        vortex_stretching=vortex_stretching(u_hat, ops),
        pressure_poisson_residual_l2=pressure_poisson_residual_l2(u_hat, ops),
        vorticity_equation_residual_l2=vorticity_equation_residual_l2(
            u_hat, viscosity, ops
        ),
        cfl=float(dt * np.max(speed) / ops.dx),
    )


def balance_residuals(
    before: SnapshotDiagnostics,
    after: SnapshotDiagnostics,
    *,
    dt: float,
    viscosity: float,
) -> dict[str, float]:
    energy_derivative = (after.kinetic_energy - before.kinetic_energy) / dt
    mean_enstrophy = 0.5 * (before.enstrophy + after.enstrophy)
    energy_residual = energy_derivative + 2.0 * viscosity * mean_enstrophy

    enstrophy_derivative = (after.enstrophy - before.enstrophy) / dt
    mean_stretching = 0.5 * (before.vortex_stretching + after.vortex_stretching)
    mean_palinstrophy = 0.5 * (before.palinstrophy + after.palinstrophy)
    enstrophy_residual = (
        enstrophy_derivative
        - mean_stretching
        + 2.0 * viscosity * mean_palinstrophy
    )
    return {
        "energy_balance_residual": float(energy_residual),
        "enstrophy_balance_residual": float(enstrophy_residual),
    }


def velocity_lp_scaling_exponent(p: float) -> float:
    """Exponent α in ||u_λ||_Lp = λ^α ||u||_Lp for 3D NS scaling."""
    if p <= 0.0:
        raise ValueError("p must be positive")
    return float(1.0 - 3.0 / p)
