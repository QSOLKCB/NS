#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate one generated reference-run manifest."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_reference_artifacts.py <run-directory>")
    run_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "research/schemas/experiment_manifest.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)

    required_outputs = {"manifest.json", "diagnostics.json", "final_velocity.npy"}
    present = {path.name for path in run_dir.iterdir() if path.is_file()}
    missing = required_outputs - present
    if missing:
        raise SystemExit(f"missing run artifacts: {sorted(missing)}")

    print("Reference artifacts validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
