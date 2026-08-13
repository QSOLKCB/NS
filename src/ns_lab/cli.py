# SPDX-License-Identifier: Apache-2.0
"""Command-line entry point for the deterministic reference laboratory."""

from __future__ import annotations

import argparse
from pathlib import Path
import re

from .artifacts import write_run_artifacts
from .solver import RunConfig, run_taylor_green

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qsol-ns-lab")
    sub = p.add_subparsers(dest="command", required=True)
    tg = sub.add_parser("taylor-green", help="run the periodic Taylor-Green reference case")
    tg.add_argument("--resolution", type=int, default=8)
    tg.add_argument("--viscosity", type=float, default=0.01)
    tg.add_argument("--dt", type=float, default=0.001)
    tg.add_argument("--steps", type=int, default=4)
    tg.add_argument("--amplitude", type=float, default=1.0)
    tg.add_argument("--diagnostic-stride", type=int, default=1)
    tg.add_argument("--experiment-id", required=True)
    tg.add_argument("--source-commit", required=True)
    tg.add_argument("--operator-or-agent", required=True)
    tg.add_argument("--output-dir", type=Path, required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not _SHA_RE.fullmatch(args.source_commit):
        raise SystemExit("--source-commit must be an exact lowercase 40-hex Git commit")

    config = RunConfig(
        resolution=args.resolution,
        viscosity=args.viscosity,
        dt=args.dt,
        steps=args.steps,
        amplitude=args.amplitude,
        diagnostic_stride=args.diagnostic_stride,
    )
    result = run_taylor_green(config)
    manifest = write_run_artifacts(
        output_dir=args.output_dir,
        experiment_id=args.experiment_id,
        source_commit=args.source_commit,
        operator_or_agent=args.operator_or_agent,
        config=config,
        result=result,
    )

    if manifest["termination_reason"] != "requested_step_count_completed":
        print(
            f"numerical failure {args.experiment_id}: "
            f"reason={manifest['termination_reason']}, "
            f"completed_steps={manifest['wall_clock_independent_step_counts']}"
        )
        return 2

    print(
        f"completed {args.experiment_id}: "
        f"E={manifest['diagnostics']['final_kinetic_energy']:.12g}, "
        f"max_div={manifest['diagnostics']['max_recorded_divergence_l2']:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
