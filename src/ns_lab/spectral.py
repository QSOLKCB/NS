# SPDX-License-Identifier: Apache-2.0
"""Periodic pseudo-spectral operators for the reference laboratory."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

Array = np.ndarray


@dataclass(frozen=True)
class SpectralOperators:
    resolution: int
    length: float
    kx: Array
    ky: Array
    kz: Array
    k2: Array
    inv_k2: Array
    dealias_mask: Array

    @classmethod
    def periodic_cube(cls, resolution: int, length: float = 2.0 * np.pi) -> "SpectralOperators":
        if resolution < 6 or resolution % 2:
            raise ValueError("resolution must be an even integer >= 6")
        if not np.isclose(length, 2.0 * np.pi):
            raise ValueError("v0.1 reference solver supports only the [0,2π)^3 periodic cube")

        modes = np.fft.fftfreq(resolution, d=1.0 / resolution)
        kx, ky, kz = np.meshgrid(modes, modes, modes, indexing="ij")
        k2 = kx * kx + ky * ky + kz * kz
        inv_k2 = np.zeros_like(k2, dtype=np.float64)
        nonzero = k2 > 0.0
        inv_k2[nonzero] = 1.0 / k2[nonzero]

        # Strict 2/3 truncation is required when N is divisible by three.
        # Retaining both ±N/3 lets the quadratic interaction N/3 + N/3
        # alias back onto the retained -N/3 mode.
        cutoff = resolution / 3.0
        dealias_mask = (
            (np.abs(kx) < cutoff)
            & (np.abs(ky) < cutoff)
            & (np.abs(kz) < cutoff)
        )
        return cls(
            resolution=resolution,
            length=length,
            kx=kx,
            ky=ky,
            kz=kz,
            k2=k2,
            inv_k2=inv_k2,
            dealias_mask=dealias_mask,
        )

    @property
    def dx(self) -> float:
        return self.length / self.resolution


def fft_velocity(u: Array) -> Array:
    if u.ndim != 4 or u.shape[0] != 3:
        raise ValueError("velocity must have shape (3,N,N,N)")
    return np.stack([np.fft.fftn(component) for component in u], axis=0)


def ifft_velocity(u_hat: Array) -> Array:
    return np.stack(
        [np.fft.ifftn(component).real for component in u_hat],
        axis=0,
    )


def project_divergence_free(u_hat: Array, ops: SpectralOperators) -> Array:
    k_dot_u = ops.kx * u_hat[0] + ops.ky * u_hat[1] + ops.kz * u_hat[2]
    projected = np.empty_like(u_hat, dtype=np.complex128)
    projected[0] = u_hat[0] - ops.kx * k_dot_u * ops.inv_k2
    projected[1] = u_hat[1] - ops.ky * k_dot_u * ops.inv_k2
    projected[2] = u_hat[2] - ops.kz * k_dot_u * ops.inv_k2
    projected[:, 0, 0, 0] = u_hat[:, 0, 0, 0]
    return projected


def dealias(u_hat: Array, ops: SpectralOperators) -> Array:
    return u_hat * ops.dealias_mask[None, ...]


def derivative_from_hat(field_hat: Array, axis: int, ops: SpectralOperators) -> Array:
    multipliers = (ops.kx, ops.ky, ops.kz)
    return np.fft.ifftn(1j * multipliers[axis] * field_hat).real


def divergence_from_hat(u_hat: Array, ops: SpectralOperators) -> Array:
    div_hat = 1j * (
        ops.kx * u_hat[0]
        + ops.ky * u_hat[1]
        + ops.kz * u_hat[2]
    )
    return np.fft.ifftn(div_hat).real


def curl_hat(u_hat: Array, ops: SpectralOperators) -> Array:
    curl = np.empty_like(u_hat, dtype=np.complex128)
    curl[0] = 1j * (ops.ky * u_hat[2] - ops.kz * u_hat[1])
    curl[1] = 1j * (ops.kz * u_hat[0] - ops.kx * u_hat[2])
    curl[2] = 1j * (ops.kx * u_hat[1] - ops.ky * u_hat[0])
    return curl


def gradient_tensor(u_hat: Array, ops: SpectralOperators) -> Array:
    """Return grad[i,j] = ∂_j u_i in physical space."""
    out = np.empty((3, 3, ops.resolution, ops.resolution, ops.resolution), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            out[i, j] = derivative_from_hat(u_hat[i], j, ops)
    return out


def nonlinear_hat(u_hat: Array, ops: SpectralOperators) -> Array:
    u = ifft_velocity(u_hat)
    grad = gradient_tensor(u_hat, ops)
    nonlinear = np.einsum("jxyz,ijxyz->ixyz", u, grad, optimize=True)
    n_hat = fft_velocity(nonlinear)
    return dealias(n_hat, ops)


def pressure_hat_from_velocity(u_hat: Array, ops: SpectralOperators) -> Array:
    """Reconstruct zero-mean pressure from Δp = -div((u·∇)u)."""
    n_hat = nonlinear_hat(u_hat, ops)
    div_n_hat = 1j * (
        ops.kx * n_hat[0]
        + ops.ky * n_hat[1]
        + ops.kz * n_hat[2]
    )
    p_hat = div_n_hat * ops.inv_k2
    p_hat[0, 0, 0] = 0.0
    return p_hat
