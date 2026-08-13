# SPDX-License-Identifier: Apache-2.0
"""Independent arbitrary-precision referee for the retained Fourier system.

The referee intentionally avoids NumPy FFTs in its high-precision evolution path.
It evolves the same finite-dimensional strict-2/3 retained Fourier system by
analytic Taylor-Green coefficients, direct modal convolution, spectral
projection and fixed-step RK4 using mpmath arithmetic.

Agreement with the reference solver is an implementation/precision check only.
It is not an independent spatial discretization and is not continuum evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Any, Iterable

import mpmath as mp

from .solver import RunConfig, run_taylor_green

REFEREE_VERSION = "0.1.0"
REFEREE_BACKEND_ID = "mpmath_direct_modal_galerkin_referee"
SUPPORTED_RESOLUTION = 8
MIN_DPS = 50
DEFAULT_HIGH_DPS = 80

Mode = tuple[int, int, int]
ModalVector = tuple[mp.mpc, mp.mpc, mp.mpc]
ModalState = dict[Mode, ModalVector]

NONCLAIMS = [
    "finite_dimensional_agreement_is_not_continuum_proof",
    "precision_agreement_is_not_global_regularity",
    "precision_disagreement_is_not_mathematical_singularity",
    "referee_is_not_an_independent_spatial_discretization",
    "low_resolution_agreement_does_not_establish_high_resolution_agreement",
]


@dataclass(frozen=True)
class PrecisionConfig:
    dps: int = DEFAULT_HIGH_DPS

    def validate(self) -> None:
        if not isinstance(self.dps, int) or isinstance(self.dps, bool):
            raise ValueError("dps must be an integer")
        if self.dps < MIN_DPS or self.dps > 200:
            raise ValueError("v0.1 referee requires 50 <= dps <= 200")


def retained_axis(resolution: int) -> tuple[int, ...]:
    """Return strict 2/3 retained integer Fourier modes without FFT helpers."""
    if resolution != SUPPORTED_RESOLUTION:
        raise ValueError(f"v0.1 referee supports only N={SUPPORTED_RESOLUTION}")
    return tuple(k for k in range(-resolution // 2, resolution // 2) if 3 * abs(k) < resolution)


def retained_modes(resolution: int) -> tuple[Mode, ...]:
    axis = retained_axis(resolution)
    return tuple(product(axis, repeat=3))


def _zero_vector() -> ModalVector:
    z = mp.mpc(0)
    return (z, z, z)


def taylor_green_modal_state(config: RunConfig) -> ModalState:
    """Construct Taylor-Green Fourier coefficients analytically, not via FFT."""
    config.validate()
    if config.resolution != SUPPORTED_RESOLUTION:
        raise ValueError(f"v0.1 referee supports only N={SUPPORTED_RESOLUTION}")

    modes = retained_modes(config.resolution)
    state = {mode: _zero_vector() for mode in modes}
    amplitude = mp.mpf(str(config.amplitude))

    for sx, sy, sz in product((-1, 1), repeat=3):
        mode = (sx, sy, sz)
        state[mode] = (
            -mp.j * amplitude * sx / 8,
            mp.j * amplitude * sy / 8,
            mp.mpc(0),
        )
    return state


def _project(mode: Mode, value: ModalVector) -> ModalVector:
    k2 = sum(component * component for component in mode)
    if k2 == 0:
        return value
    dot = sum(mp.mpf(mode[i]) * value[i] for i in range(3))
    return tuple(
        value[i] - mp.mpf(mode[i]) * dot / k2
        for i in range(3)
    )  # type: ignore[return-value]


def _active_modes(state: ModalState) -> list[Mode]:
    return [mode for mode, value in state.items() if any(component != 0 for component in value)]


def modal_rhs(state: ModalState, viscosity: mp.mpf) -> ModalState:
    """Evaluate the retained Fourier ODE by direct convolution."""
    modes = tuple(state)
    mode_set = set(modes)
    nonlinear: dict[Mode, list[mp.mpc]] = {
        mode: [mp.mpc(0), mp.mpc(0), mp.mpc(0)] for mode in modes
    }
    active = _active_modes(state)

    # (u · grad) u_i at k = sum_{p+q=k} i (q · u_p) u_i(q).
    for p in active:
        up = state[p]
        for q in active:
            target = (p[0] + q[0], p[1] + q[1], p[2] + q[2])
            if target not in mode_set:
                continue
            directional = mp.j * sum(mp.mpf(q[j]) * up[j] for j in range(3))
            if directional == 0:
                continue
            uq = state[q]
            for i in range(3):
                nonlinear[target][i] += directional * uq[i]

    out: ModalState = {}
    for mode in modes:
        projected = _project(mode, tuple(nonlinear[mode]))  # type: ignore[arg-type]
        k2 = sum(component * component for component in mode)
        out[mode] = tuple(
            -projected[i] - viscosity * k2 * state[mode][i]
            for i in range(3)
        )  # type: ignore[assignment]
    return out


def _add_scaled(base: ModalState, increment: ModalState, scale: mp.mpf) -> ModalState:
    return {
        mode: tuple(base[mode][i] + scale * increment[mode][i] for i in range(3))
        for mode in base
    }  # type: ignore[return-value]


def rk4_modal_step(state: ModalState, *, dt: mp.mpf, viscosity: mp.mpf) -> ModalState:
    k1 = modal_rhs(state, viscosity)
    k2 = modal_rhs(_add_scaled(state, k1, dt / 2), viscosity)
    k3 = modal_rhs(_add_scaled(state, k2, dt / 2), viscosity)
    k4 = modal_rhs(_add_scaled(state, k3, dt), viscosity)
    return {
        mode: tuple(
            state[mode][i]
            + dt * (k1[mode][i] + 2 * k2[mode][i] + 2 * k3[mode][i] + k4[mode][i]) / 6
            for i in range(3)
        )
        for mode in state
    }  # type: ignore[return-value]


def run_precision_referee(config: RunConfig, precision: PrecisionConfig | None = None) -> ModalState:
    config.validate()
    precision = precision or PrecisionConfig()
    precision.validate()
    if config.resolution != SUPPORTED_RESOLUTION:
        raise ValueError(f"v0.1 referee supports only N={SUPPORTED_RESOLUTION}")

    with mp.workdps(precision.dps):
        state = taylor_green_modal_state(config)
        dt = mp.mpf(str(config.dt))
        viscosity = mp.mpf(str(config.viscosity))
        for _ in range(config.steps):
            state = rk4_modal_step(state, dt=dt, viscosity=viscosity)
        return state


def modal_kinetic_energy(state: ModalState) -> mp.mpf:
    return mp.mpf("0.5") * sum(
        abs(component) ** 2 for value in state.values() for component in value
    )


def modal_enstrophy(state: ModalState) -> mp.mpf:
    total = mp.mpf(0)
    for mode, value in state.items():
        kx, ky, kz = mode
        ux, uy, uz = value
        omega = (
            mp.j * (ky * uz - kz * uy),
            mp.j * (kz * ux - kx * uz),
            mp.j * (kx * uy - ky * ux),
        )
        total += sum(abs(component) ** 2 for component in omega)
    return mp.mpf("0.5") * total


def _reference_modal_state(config: RunConfig) -> tuple[ModalState, dict[str, Any]]:
    """Extract normalized retained coefficients from the NumPy/FFT reference path."""
    import numpy as np

    result = run_taylor_green(config)
    if result["termination_reason"] != "requested_step_count_completed":
        raise FloatingPointError(
            f"reference solver did not complete: {result['termination_reason']}"
        )

    u_hat = result["final_velocity_hat"]
    fft_modes = [int(value) for value in np.fft.fftfreq(config.resolution, d=1.0 / config.resolution)]
    index = {mode: i for i, mode in enumerate(fft_modes)}
    normalization = config.resolution ** 3
    state: ModalState = {}
    for mode in retained_modes(config.resolution):
        ix, iy, iz = (index[mode[0]], index[mode[1]], index[mode[2]])
        state[mode] = tuple(
            mp.mpc(complex(u_hat[component, ix, iy, iz] / normalization))
            for component in range(3)
        )  # type: ignore[assignment]
    return state, result


def _state_differences(a: ModalState, b: ModalState) -> tuple[mp.mpf, mp.mpf]:
    differences = [
        abs(a[mode][component] - b[mode][component])
        for mode in a
        for component in range(3)
    ]
    maximum = max(differences)
    rms = mp.sqrt(sum(value * value for value in differences) / len(differences))
    return maximum, rms


def precision_ladder(config: RunConfig, low_dps: int = 50, high_dps: int = 80) -> dict[str, str | int]:
    if low_dps >= high_dps:
        raise ValueError("low_dps must be less than high_dps")
    low = run_precision_referee(config, PrecisionConfig(low_dps))
    high = run_precision_referee(config, PrecisionConfig(high_dps))
    with mp.workdps(high_dps):
        maximum, rms = _state_differences(low, high)
        return {
            "low_dps": low_dps,
            "high_dps": high_dps,
            "max_modal_abs_difference_decimal": mp.nstr(maximum, 50),
            "rms_modal_abs_difference_decimal": mp.nstr(rms, 50),
        }


def build_precision_report(
    config: RunConfig,
    *,
    low_dps: int = 50,
    high_dps: int = 80,
) -> dict[str, Any]:
    config.validate()
    if config.resolution != SUPPORTED_RESOLUTION:
        raise ValueError(f"v0.1 referee supports only N={SUPPORTED_RESOLUTION}")

    reference, reference_result = _reference_modal_state(config)
    referee = run_precision_referee(config, PrecisionConfig(high_dps))
    with mp.workdps(high_dps):
        maximum, rms = _state_differences(reference, referee)
        ref_energy = modal_kinetic_energy(reference)
        hp_energy = modal_kinetic_energy(referee)
        ref_enstrophy = modal_enstrophy(reference)
        hp_enstrophy = modal_enstrophy(referee)
        ladder = precision_ladder(config, low_dps=low_dps, high_dps=high_dps)

        return {
            "schema_version": "0.1.0",
            "document_type": "qsol_ns_precision_referee_report",
            "comparison_kind": "fft_reference_vs_direct_modal_arbitrary_precision",
            "reference_backend": "qsol_ns_periodic_pseudospectral_reference",
            "referee_backend": REFEREE_BACKEND_ID,
            "referee_version": REFEREE_VERSION,
            "mpmath_version": mp.__version__,
            "scope": {
                "resolution": config.resolution,
                "viscosity": config.viscosity,
                "dt": config.dt,
                "steps": config.steps,
                "amplitude": config.amplitude,
                "forcing": "identically_zero",
                "initial_data_family": "Taylor-Green_vortex",
                "retained_mode_count": len(retained_modes(config.resolution)),
            },
            "reference_termination_reason": reference_result["termination_reason"],
            "precision_ladder": ladder,
            "comparison_metrics": {
                "max_retained_modal_abs_difference": float(maximum),
                "rms_retained_modal_abs_difference": float(rms),
                "reference_kinetic_energy": float(ref_energy),
                "referee_kinetic_energy_decimal": mp.nstr(hp_energy, 50),
                "kinetic_energy_abs_difference": float(abs(ref_energy - hp_energy)),
                "reference_enstrophy": float(ref_enstrophy),
                "referee_enstrophy_decimal": mp.nstr(hp_enstrophy, 50),
                "enstrophy_abs_difference": float(abs(ref_enstrophy - hp_enstrophy)),
            },
            "independence": {
                "independent_arithmetic": True,
                "independent_fft_path": True,
                "independent_nonlinear_evaluation": True,
                "independent_spatial_discretization": False,
            },
            "nonclaims": list(NONCLAIMS),
            "claim_level": "exploratory",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qsol-ns-precision-referee")
    parser.add_argument("--viscosity", type=float, default=0.01)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--amplitude", type=float, default=1.0)
    parser.add_argument("--low-dps", type=int, default=50)
    parser.add_argument("--high-dps", type=int, default=80)
    args = parser.parse_args(argv)

    config = RunConfig(
        resolution=SUPPORTED_RESOLUTION,
        viscosity=args.viscosity,
        dt=args.dt,
        steps=args.steps,
        amplitude=args.amplitude,
        diagnostic_stride=1,
    )
    report = build_precision_report(config, low_dps=args.low_dps, high_dps=args.high_dps)
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
