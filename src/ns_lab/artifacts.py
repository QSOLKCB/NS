# SPDX-License-Identifier: Apache-2.0
"""Canonical artifact and manifest writing for deterministic replay."""

from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np

from .solver import LAB_VERSION, RunConfig


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_canonical_json(path: Path, value: Any) -> str:
    data = canonical_json_bytes(value)
    path.write_bytes(data)
    return sha256_bytes(data)


def write_deterministic_npy(path: Path, array: np.ndarray) -> str:
    with path.open("wb") as handle:
        np.lib.format.write_array(handle, np.asarray(array), allow_pickle=False)
    return sha256_bytes(path.read_bytes())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _numpy_runtime_configuration() -> tuple[str, dict[str, Any]]:
    stream = io.StringIO()
    with redirect_stdout(stream):
        np.show_config()
    config_text = stream.getvalue()

    cpu_features: dict[str, bool] = {}
    try:
        cpu_features = dict(np._core._multiarray_umath.__cpu_features__)
    except (AttributeError, TypeError):
        pass

    hardware = {
        "machine": platform.machine() or "unknown",
        "processor": platform.processor() or "unknown",
        "numpy_cpu_features_enabled": sorted(
            name for name, enabled in cpu_features.items() if enabled
        ),
        "numpy_cpu_features_disabled": sorted(
            name for name, enabled in cpu_features.items() if not enabled
        ),
        "numpy_build_configuration_sha256": sha256_bytes(
            config_text.encode("utf-8")
        ),
    }
    return config_text, hardware


def _validate_result_config(config: RunConfig, result: dict[str, Any]) -> None:
    expected = asdict(config)
    actual = result.get("config")
    if actual != expected:
        raise ValueError(
            "result/config provenance mismatch: "
            f"result={actual!r}, supplied_config={expected!r}"
        )


def build_manifest(
    *,
    experiment_id: str,
    source_commit: str,
    operator_or_agent: str,
    config: RunConfig,
    diagnostics_hash: str,
    velocity_hash: str,
    diagnostics_summary: dict[str, Any],
    raw_pointer: str,
    termination_reason: str,
    warnings_or_errors: list[str],
    completed_steps: int,
) -> dict[str, Any]:
    numpy_config, hardware = _numpy_runtime_configuration()
    return {
        "experiment_id": experiment_id,
        "source_commit": source_commit,
        "created_at_utc": utc_now_iso(),
        "operator_or_agent": operator_or_agent,
        "purpose": "deterministic_periodic_reference_solver_baseline",
        "hypothesis": "reference_solver_preserves_baseline_numerical_contract_within_reported_discretization_error",
        "claim_level": "exploratory",
        "singularity_oriented": False,
        "spatial_domain": "[0,2pi)^3_periodic",
        "boundary_conditions": "periodic_velocity_and_pressure",
        "initial_velocity_field_definition": f"Taylor-Green vortex amplitude={config.amplitude}",
        "divergence_free_admissibility": "analytic_and_spectral_projection_checked",
        "viscosity": config.viscosity,
        "forcing": "identically_zero",
        "scaling_convention": "dimensionless_2pi_periodic_cube",
        "measured_solution_quantity": [
            "velocity",
            "energy",
            "enstrophy",
            "vorticity",
            "divergence",
            "pressure_poisson_residual",
            "vorticity_equation_residual",
        ],
        "solver": "qsol_ns_periodic_pseudospectral_reference",
        "solver_version": LAB_VERSION,
        "spatial_discretization": "Fourier_pseudospectral_strict_2over3_dealiasing",
        "time_integrator": "classical_RK4_fixed_step",
        "time_step_policy": "fixed",
        "resolution": [config.resolution, config.resolution, config.resolution],
        "precision": "float64_complex128",
        "tolerances": {
            "diagnostics_are_reported_not_used_as_proof_thresholds": True
        },
        "filtering_regularization": "strict_2over3_spectral_dealiasing_only",
        "interpolation_remeshing": None,
        "random_seed_or_null": None,
        "operating_system_or_container_identity": platform.platform(),
        "compiler_or_interpreter": sys.version.splitlines()[0],
        "dependency_lock_or_exact_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "numpy_build_configuration": numpy_config,
        },
        "numerics_relevant_hardware_features": hardware,
        "thread_or_process_count": 1,
        "input_hashes": {},
        "output_hashes": {
            "diagnostics.json": diagnostics_hash,
            "final_velocity.npy": velocity_hash,
        },
        "diagnostics": diagnostics_summary,
        "termination_reason": termination_reason,
        "warnings_or_errors": warnings_or_errors,
        "wall_clock_independent_step_counts": completed_steps,
        "raw_outputs_or_content_addressed_pointer": raw_pointer,
    }


def write_run_artifacts(
    *,
    output_dir: Path,
    experiment_id: str,
    source_commit: str,
    operator_or_agent: str,
    config: RunConfig,
    result: dict[str, Any],
) -> dict[str, Any]:
    _validate_result_config(config, result)
    output_dir.mkdir(parents=True, exist_ok=False)

    deterministic_result = {
        "lab_version": result["lab_version"],
        "config": result["config"],
        "diagnostics": result["diagnostics"],
        "balance_history": result["balance_history"],
        "termination_reason": result["termination_reason"],
        "warnings_or_errors": result["warnings_or_errors"],
        "completed_steps": result["completed_steps"],
    }
    diagnostics_hash = write_canonical_json(
        output_dir / "diagnostics.json",
        deterministic_result,
    )
    velocity_hash = write_deterministic_npy(
        output_dir / "final_velocity.npy",
        result["final_velocity"],
    )

    last = result["diagnostics"][-1]
    summary = {
        "final_time": last["time"],
        "final_kinetic_energy": last["kinetic_energy"],
        "final_enstrophy": last["enstrophy"],
        "final_max_vorticity": last["max_vorticity"],
        "max_recorded_divergence_l2": max(
            d["divergence_l2"] for d in result["diagnostics"]
        ),
        "max_recorded_cfl": max(d["cfl"] for d in result["diagnostics"]),
        "baseline_identity_status": "numerical_diagnostics_only_not_proof",
    }
    manifest = build_manifest(
        experiment_id=experiment_id,
        source_commit=source_commit,
        operator_or_agent=operator_or_agent,
        config=config,
        diagnostics_hash=diagnostics_hash,
        velocity_hash=velocity_hash,
        diagnostics_summary=summary,
        raw_pointer="local_directory:" + str(output_dir),
        termination_reason=result["termination_reason"],
        warnings_or_errors=list(result["warnings_or_errors"]),
        completed_steps=int(result["completed_steps"]),
    )
    write_canonical_json(output_dir / "manifest.json", manifest)
    return manifest
