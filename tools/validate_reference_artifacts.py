#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate one generated reference-run manifest and its recorded content hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_reference_artifacts.py <run-directory>")
    run_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (root / "research/schemas/experiment_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (run_dir / "manifest.json").read_text(encoding="utf-8"),
        parse_constant=_reject_nonstandard_constant,
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)

    required_outputs = {"manifest.json", "diagnostics.json", "final_velocity.npy"}
    present = {path.name for path in run_dir.iterdir() if path.is_file()}
    missing = required_outputs - present
    if missing:
        raise SystemExit(f"missing run artifacts: {sorted(missing)}")

    recorded_hashes = manifest["output_hashes"]
    expected_hashed_outputs = required_outputs - {"manifest.json"}
    if set(recorded_hashes) != expected_hashed_outputs:
        raise SystemExit(
            "manifest output_hashes must name exactly the evidentiary outputs: "
            f"recorded={sorted(recorded_hashes)}, expected={sorted(expected_hashed_outputs)}"
        )

    for name, recorded in recorded_hashes.items():
        if Path(name).name != name:
            raise SystemExit(f"unsafe/non-canonical output hash path: {name!r}")
        actual = sha256_file(run_dir / name)
        if actual != recorded:
            raise SystemExit(
                f"artifact hash mismatch for {name}: recorded={recorded}, actual={actual}"
            )

    json.loads(
        (run_dir / "diagnostics.json").read_text(encoding="utf-8"),
        parse_constant=_reject_nonstandard_constant,
    )

    print("Reference artifacts validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
