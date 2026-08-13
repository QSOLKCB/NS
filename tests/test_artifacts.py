# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
import pytest

from ns_lab.artifacts import write_run_artifacts
from ns_lab.solver import RunConfig, run_taylor_green


def _load_schema() -> dict:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "research/schemas/experiment_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_manifest_contains_complete_promoted_experiment_contract(tmp_path: Path):
    schema = _load_schema()
    config = RunConfig(resolution=8, steps=1, dt=0.001)
    result = run_taylor_green(config)
    manifest = write_run_artifacts(
        output_dir=tmp_path / "run",
        experiment_id="TEST_TG_0001",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result,
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)

    hardware = manifest["numerics_relevant_hardware_features"]
    assert hardware["machine"]
    assert hardware["processor"]
    assert "numpy_cpu_features_enabled" in hardware
    assert len(hardware["numpy_build_configuration_sha256"]) == 64


def test_deterministic_outputs_hash_identically_across_replays(tmp_path: Path):
    config = RunConfig(resolution=8, steps=1, dt=0.001)
    result_a = run_taylor_green(config)
    result_b = run_taylor_green(config)

    manifest_a = write_run_artifacts(
        output_dir=tmp_path / "a",
        experiment_id="TEST_A",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result_a,
    )
    manifest_b = write_run_artifacts(
        output_dir=tmp_path / "b",
        experiment_id="TEST_B",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result_b,
    )
    assert manifest_a["output_hashes"] == manifest_b["output_hashes"]


def test_artifact_writer_rejects_config_result_mismatch(tmp_path: Path):
    result_config = RunConfig(resolution=8, steps=1, dt=0.001, viscosity=0.01)
    supplied_config = RunConfig(resolution=8, steps=1, dt=0.001, viscosity=0.02)
    result = run_taylor_green(result_config)

    with pytest.raises(ValueError, match="provenance mismatch"):
        write_run_artifacts(
            output_dir=tmp_path / "mismatch",
            experiment_id="TEST_MISMATCH",
            source_commit="a" * 40,
            operator_or_agent="pytest",
            config=supplied_config,
            result=result,
        )
    assert not (tmp_path / "mismatch").exists()


def test_manifest_schema_can_represent_required_singularity_metadata(tmp_path: Path):
    schema = _load_schema()
    config = RunConfig(resolution=8, steps=1, dt=0.001)
    result = run_taylor_green(config)
    manifest = write_run_artifacts(
        output_dir=tmp_path / "singularity",
        experiment_id="TEST_SINGULARITY_METADATA",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result,
    )
    manifest.update(
        {
            "singularity_oriented": True,
            "convergence_resolution_behavior": {"status": "not_yet_established"},
            "precision_sensitivity": {"status": "not_yet_established"},
            "conservation_balance_residuals": {"status": "reported"},
            "timestep_sensitivity": {"status": "not_yet_established"},
            "competing_numerical_failure_explanation": [
                "under_resolution",
                "finite_precision",
            ],
        }
    )
    Draft202012Validator(schema).validate(manifest)


def test_singularity_marker_requires_all_five_metadata_fields(tmp_path: Path):
    schema = _load_schema()
    config = RunConfig(resolution=8, steps=1, dt=0.001)
    result = run_taylor_green(config)
    manifest = write_run_artifacts(
        output_dir=tmp_path / "conditional",
        experiment_id="TEST_SINGULARITY_CONDITIONAL",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result,
    )
    manifest["singularity_oriented"] = True
    errors = list(Draft202012Validator(schema).iter_errors(manifest))
    assert errors


def test_reference_artifact_validator_detects_content_tampering(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    run_dir = tmp_path / "tamper"
    config = RunConfig(resolution=8, steps=1, dt=0.001)
    result = run_taylor_green(config)
    write_run_artifacts(
        output_dir=run_dir,
        experiment_id="TEST_TAMPER",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result,
    )

    diagnostics_path = run_dir / "diagnostics.json"
    diagnostics_path.write_bytes(diagnostics_path.read_bytes() + b" ")

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "tools/validate_reference_artifacts.py"),
            str(run_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "artifact hash mismatch" in (completed.stdout + completed.stderr)


def test_failed_numerical_run_is_recorded_as_failure_manifest(tmp_path: Path):
    config = RunConfig(resolution=8, steps=1, dt=1.0e308, viscosity=0.01)
    result = run_taylor_green(config)
    manifest = write_run_artifacts(
        output_dir=tmp_path / "failed",
        experiment_id="TEST_FAILED_NUMERICS",
        source_commit="a" * 40,
        operator_or_agent="pytest",
        config=config,
        result=result,
    )
    assert manifest["termination_reason"] != "requested_step_count_completed"
    assert manifest["warnings_or_errors"]
    assert manifest["wall_clock_independent_step_counts"] == 0
