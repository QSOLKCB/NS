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
from dataclasses import asdict, dataclass
from itertools import product
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any

import mpmath as mp

from .artifacts import (
    _numpy_runtime_configuration,
    canonical_json_bytes,
    sha256_bytes,
    utc_now_iso,
    write_canonical_json,
    write_deterministic_npy,
)
from .solver import LAB_VERSION, RunConfig, run_taylor_green

REFEREE_VERSION = "0.1.0"
REFEREE_BACKEND_ID = "mpmath_direct_modal_galerkin_referee"
SUPPORTED_RESOLUTION = 8
MIN_DPS = 50
DEFAULT_HIGH_DPS = 80
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

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


def _reference_state_is_finite(result: dict[str, Any]) -> bool:
    import numpy as np

    u_hat = result["final_velocity_hat"]
    return bool(np.isfinite(u_hat.real).all() and np.isfinite(u_hat.imag).all())


def _reference_modal_state(
    config: RunConfig,
    reference_result: dict[str, Any] | None = None,
) -> tuple[ModalState | None, dict[str, Any]]:
    """Extract comparable reference modes, preserving failed runs instead of raising."""
    import numpy as np

    result = reference_result if reference_result is not None else run_taylor_green(config)
    comparable = (
        result["termination_reason"] == "requested_step_count_completed"
        and int(result["completed_steps"]) == config.steps
        and _reference_state_is_finite(result)
    )
    if not comparable:
        return None, result

    u_hat = result["final_velocity_hat"]
    fft_modes = [
        int(value)
        for value in np.fft.fftfreq(config.resolution, d=1.0 / config.resolution)
    ]
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


def _validate_provenance(experiment_id: str, source_commit: str, operator_or_agent: str) -> None:
    if not experiment_id.strip():
        raise ValueError("experiment_id must be non-empty")
    if not _SHA_RE.fullmatch(source_commit):
        raise ValueError("source_commit must be an exact lowercase 40-hex Git commit")
    if not operator_or_agent.strip():
        raise ValueError("operator_or_agent must be non-empty")


def build_precision_report(
    config: RunConfig,
    *,
    experiment_id: str,
    source_commit: str,
    operator_or_agent: str,
    created_at_utc: str | None = None,
    low_dps: int = 50,
    high_dps: int = 80,
    reference_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config.validate()
    _validate_provenance(experiment_id, source_commit, operator_or_agent)
    if config.resolution != SUPPORTED_RESOLUTION:
        raise ValueError(f"v0.1 referee supports only N={SUPPORTED_RESOLUTION}")

    created = created_at_utc or utc_now_iso()
    reference, reference_result = _reference_modal_state(config, reference_result)
    referee = run_precision_referee(config, PrecisionConfig(high_dps))
    ladder = precision_ladder(config, low_dps=low_dps, high_dps=high_dps)

    with mp.workdps(high_dps):
        hp_energy = modal_kinetic_energy(referee)
        hp_enstrophy = modal_enstrophy(referee)

        if reference is not None:
            maximum, rms = _state_differences(reference, referee)
            ref_energy = modal_kinetic_energy(reference)
            ref_enstrophy = modal_enstrophy(reference)
            comparison_status = "comparable"
            comparison_metrics = {
                "max_retained_modal_abs_difference": float(maximum),
                "rms_retained_modal_abs_difference": float(rms),
                "reference_kinetic_energy": float(ref_energy),
                "referee_kinetic_energy_decimal": mp.nstr(hp_energy, 50),
                "kinetic_energy_abs_difference": float(abs(ref_energy - hp_energy)),
                "reference_enstrophy": float(ref_enstrophy),
                "referee_enstrophy_decimal": mp.nstr(hp_enstrophy, 50),
                "enstrophy_abs_difference": float(abs(ref_enstrophy - hp_enstrophy)),
            }
        else:
            comparison_status = "reference_failed_referee_completed"
            comparison_metrics = {
                "max_retained_modal_abs_difference": None,
                "rms_retained_modal_abs_difference": None,
                "reference_kinetic_energy": None,
                "referee_kinetic_energy_decimal": mp.nstr(hp_energy, 50),
                "kinetic_energy_abs_difference": None,
                "reference_enstrophy": None,
                "referee_enstrophy_decimal": mp.nstr(hp_enstrophy, 50),
                "enstrophy_abs_difference": None,
            }

    return {
        "schema_version": "0.1.0",
        "document_type": "qsol_ns_precision_referee_report",
        "provenance": {
            "experiment_id": experiment_id,
            "source_commit": source_commit,
            "created_at_utc": created,
            "operator_or_agent": operator_or_agent,
        },
        "comparison_kind": "fft_reference_vs_direct_modal_arbitrary_precision",
        "comparison_status": comparison_status,
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
        "reference_run": {
            "termination_reason": reference_result["termination_reason"],
            "completed_steps": int(reference_result["completed_steps"]),
            "requested_steps": config.steps,
            "warnings_or_errors": list(reference_result["warnings_or_errors"]),
            "final_state_finite": _reference_state_is_finite(reference_result),
        },
        "referee_run": {
            "termination_reason": "requested_step_count_completed",
            "completed_steps": config.steps,
            "requested_steps": config.steps,
            "warnings_or_errors": [],
        },
        "precision_ladder": ladder,
        "comparison_metrics": comparison_metrics,
        "independence": {
            "independent_arithmetic": True,
            "independent_fft_path": True,
            "independent_nonlinear_evaluation": True,
            "independent_spatial_discretization": False,
        },
        "nonclaims": list(NONCLAIMS),
        "claim_level": "exploratory",
    }


def _reference_run_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "lab_version": result["lab_version"],
        "config": result["config"],
        "diagnostics": result["diagnostics"],
        "balance_history": result["balance_history"],
        "termination_reason": result["termination_reason"],
        "warnings_or_errors": result["warnings_or_errors"],
        "completed_steps": result["completed_steps"],
    }


def _build_precision_manifest(
    *,
    output_dir: Path,
    config: RunConfig,
    report: dict[str, Any],
    low_dps: int,
    high_dps: int,
    output_hashes: dict[str, str],
) -> dict[str, Any]:
    import numpy as np

    provenance = report["provenance"]
    numpy_config, hardware = _numpy_runtime_configuration()
    input_identity = {
        "config": asdict(config),
        "low_dps": low_dps,
        "high_dps": high_dps,
    }
    warnings = list(report["reference_run"]["warnings_or_errors"])

    return {
        "experiment_id": provenance["experiment_id"],
        "source_commit": provenance["source_commit"],
        "created_at_utc": provenance["created_at_utc"],
        "operator_or_agent": provenance["operator_or_agent"],
        "purpose": "independent_precision_referee_comparison",
        "hypothesis": "arithmetic_or_implementation_disagreement_is_detected_and_failed_reference_runs_are_preserved",
        "claim_level": "exploratory",
        "singularity_oriented": False,
        "spatial_domain": "[0,2pi)^3_periodic",
        "boundary_conditions": "periodic_velocity_and_pressure",
        "initial_velocity_field_definition": f"Taylor-Green vortex amplitude={config.amplitude}",
        "divergence_free_admissibility": "analytic_modal_construction_and_reference_spectral_projection_checked",
        "viscosity": config.viscosity,
        "forcing": "identically_zero",
        "scaling_convention": "dimensionless_2pi_periodic_cube",
        "measured_solution_quantity": [
            "retained_modal_difference",
            "kinetic_energy",
            "enstrophy",
            "precision_ladder",
            "reference_failure_status",
        ],
        "solver": "qsol_ns_precision_referee_comparison",
        "solver_version": REFEREE_VERSION,
        "spatial_discretization": "same_strict_2over3_retained_Fourier_system_two_implementation_paths",
        "time_integrator": "classical_RK4_fixed_step",
        "time_step_policy": "fixed",
        "resolution": [config.resolution, config.resolution, config.resolution],
        "precision": f"float64_complex128_reference_vs_mpmath_{low_dps}_to_{high_dps}_decimal_digits",
        "tolerances": {"comparison_metrics_are_diagnostics_not_continuum_proof_thresholds": True},
        "filtering_regularization": "strict_2over3_spectral_retained_modes_only",
        "interpolation_remeshing": None,
        "random_seed_or_null": None,
        "operating_system_or_container_identity": platform.platform(),
        "compiler_or_interpreter": sys.version.splitlines()[0],
        "dependency_lock_or_exact_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "numpy_build_configuration": numpy_config,
            "mpmath": mp.__version__,
        },
        "numerics_relevant_hardware_features": hardware,
        "thread_or_process_count": 1,
        "input_hashes": {"comparison_config": sha256_bytes(canonical_json_bytes(input_identity))},
        "output_hashes": output_hashes,
        "diagnostics": {
            "comparison_status": report["comparison_status"],
            "reference_run": report["reference_run"],
            "referee_run": report["referee_run"],
            "comparison_metrics": report["comparison_metrics"],
            "precision_ladder": report["precision_ladder"],
            "evidence_boundary": "finite_dimensional_precision_check_not_continuum_proof",
        },
        "termination_reason": report["comparison_status"],
        "warnings_or_errors": warnings,
        "wall_clock_independent_step_counts": int(report["referee_run"]["completed_steps"]),
        "raw_outputs_or_content_addressed_pointer": "local_directory:" + str(output_dir),
    }


def write_precision_artifacts(
    *,
    output_dir: Path,
    experiment_id: str,
    source_commit: str,
    operator_or_agent: str,
    config: RunConfig,
    low_dps: int = 50,
    high_dps: int = 80,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write a provenance-complete referee evidence bundle, including failed references."""
    _validate_provenance(experiment_id, source_commit, operator_or_agent)
    created = utc_now_iso()
    reference_result = run_taylor_green(config)
    report = build_precision_report(
        config,
        experiment_id=experiment_id,
        source_commit=source_commit,
        operator_or_agent=operator_or_agent,
        created_at_utc=created,
        low_dps=low_dps,
        high_dps=high_dps,
        reference_result=reference_result,
    )

    output_dir.mkdir(parents=True, exist_ok=False)
    report_hash = write_canonical_json(output_dir / "precision_report.json", report)
    reference_run_hash = write_canonical_json(
        output_dir / "reference_run.json",
        _reference_run_payload(reference_result),
    )
    reference_velocity_hash = write_deterministic_npy(
        output_dir / "reference_final_velocity.npy",
        reference_result["final_velocity"],
    )
    output_hashes = {
        "precision_report.json": report_hash,
        "reference_run.json": reference_run_hash,
        "reference_final_velocity.npy": reference_velocity_hash,
    }
    manifest = _build_precision_manifest(
        output_dir=output_dir,
        config=config,
        report=report,
        low_dps=low_dps,
        high_dps=high_dps,
        output_hashes=output_hashes,
    )
    write_canonical_json(output_dir / "manifest.json", manifest)
    return manifest, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qsol-ns-precision-referee")
    parser.add_argument("--viscosity", type=float, default=0.01)
    parser.add_argument("--dt", type=float, default=0.001)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--amplitude", type=float, default=1.0)
    parser.add_argument("--low-dps", type=int, default=50)
    parser.add_argument("--high-dps", type=int, default=80)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--operator-or-agent", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    if not _SHA_RE.fullmatch(args.source_commit):
        raise SystemExit("--source-commit must be an exact lowercase 40-hex Git commit")

    config = RunConfig(
        resolution=SUPPORTED_RESOLUTION,
        viscosity=args.viscosity,
        dt=args.dt,
        steps=args.steps,
        amplitude=args.amplitude,
        diagnostic_stride=1,
    )
    manifest, report = write_precision_artifacts(
        output_dir=args.output_dir,
        experiment_id=args.experiment_id,
        source_commit=args.source_commit,
        operator_or_agent=args.operator_or_agent,
        config=config,
        low_dps=args.low_dps,
        high_dps=args.high_dps,
    )
    print(
        json.dumps(
            {
                "experiment_id": manifest["experiment_id"],
                "comparison_status": report["comparison_status"],
                "output_dir": str(args.output_dir),
                "claim_level": report["claim_level"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
