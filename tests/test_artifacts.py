# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ns_lab.artifacts import write_run_artifacts
from ns_lab.solver import RunConfig, run_taylor_green


def test_manifest_contains_complete_promoted_experiment_contract(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "research/schemas/experiment_manifest.schema.json").read_text())
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
