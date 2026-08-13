#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate one generated precision-referee evidence bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_precision_artifacts.py <run-directory>")

    run_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    manifest_schema = _load(root / "research/schemas/experiment_manifest.schema.json")
    report_schema = _load(root / "research/schemas/precision_referee_report.schema.json")
    manifest = _load(run_dir / "manifest.json")
    report = _load(run_dir / "precision_report.json")

    for schema in (manifest_schema, report_schema):
        Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        manifest_schema,
        format_checker=FormatChecker(),
    ).validate(manifest)
    Draft202012Validator(
        report_schema,
        format_checker=FormatChecker(),
    ).validate(report)

    required_outputs = {
        "manifest.json",
        "precision_report.json",
        "reference_run.json",
        "reference_final_velocity.npy",
    }
    present = {path.name for path in run_dir.iterdir() if path.is_file()}
    missing = required_outputs - present
    if missing:
        raise SystemExit(f"missing precision-referee artifacts: {sorted(missing)}")

    expected_hash_keys = required_outputs - {"manifest.json"}
    if set(manifest["output_hashes"]) != expected_hash_keys:
        raise SystemExit(
            "precision-referee output hash set drift: "
            f"recorded={sorted(manifest['output_hashes'])}, expected={sorted(expected_hash_keys)}"
        )
    for filename, expected in manifest["output_hashes"].items():
        actual = hashlib.sha256((run_dir / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(
                f"precision-referee artifact hash mismatch for {filename}: {actual} != {expected}"
            )

    provenance = report["provenance"]
    for key in ("experiment_id", "source_commit", "created_at_utc", "operator_or_agent"):
        if manifest[key] != provenance[key]:
            raise SystemExit(f"manifest/report provenance mismatch for {key}")

    reference_run = _load(run_dir / "reference_run.json")
    for key in ("termination_reason", "completed_steps", "warnings_or_errors"):
        if reference_run[key] != report["reference_run"][key]:
            raise SystemExit(f"preserved reference-run/report mismatch for {key}")

    if manifest["termination_reason"] != report["comparison_status"]:
        raise SystemExit("manifest/report comparison status mismatch")

    print(
        "Precision artifact validation: PASS "
        f"({report['comparison_status']}, experiment={manifest['experiment_id']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
