<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Independent Precision Referee v0.1

## Purpose

The precision referee checks whether the existing NumPy/FFT reference laboratory and an independently evaluated arbitrary-precision implementation agree on the **same finite-dimensional retained Fourier system**.

Its job is numerical skepticism, not prophecy.

## Independent path

For the supported `N=8` Taylor-Green reference case the referee:

1. constructs the Taylor-Green Fourier coefficients analytically;
2. retains modes satisfying the same strict 2/3 rule used by the reference solver;
3. evaluates `(u · grad)u` by direct modal convolution rather than an FFT/pseudo-spectral product;
4. applies the divergence-free projection directly in modal space;
5. advances the modal ODE with fixed-step classical RK4;
6. performs arithmetic with `mpmath` at configurable decimal precision;
7. compares normalized retained coefficients, kinetic energy and enstrophy with the NumPy/FFT reference path when that path completes comparably;
8. checks self-convergence between a lower and higher arbitrary-precision run.

The default precision ladder is 50 to 80 decimal digits.

## What is genuinely independent

The referee uses an independent arithmetic path, does not use NumPy FFTs for its high-precision evolution, and computes the nonlinear term by direct Fourier convolution.

These differences are useful for detecting finite-precision, FFT-path, normalization, indexing, de-aliasing and nonlinear-evaluation defects.

## What is not independent

The referee is **not** a different spatial discretization. Both implementations describe the same strict-2/3 retained Fourier system. They also use the same RK4 time-integration formula.

Therefore agreement is stronger than a same-code rerun but weaker than agreement between genuinely different numerical methods.

## Failure is evidence, not an exception

A float64 reference failure is exactly the kind of event the precision referee is intended to investigate. The referee therefore does not abort merely because the reference path terminates with a non-finite state or diagnostic.

Instead, the failed reference termination reason, completed-step count, warnings and partial diagnostics are preserved, and the arbitrary-precision path is still executed when possible. In that case the report is marked `reference_failed_referee_completed`; direct state-difference metrics are left null because the two paths are no longer comparable at the same completed final state.

A higher-precision survivor does **not** prove a mathematical singularity was absent. It establishes only that the tested float64 failure was not reproduced by the referee under the recorded finite-dimensional configuration.

## Provenance-complete evidence bundles

The installed `qsol-ns-precision-referee` command requires:

- `--experiment-id`;
- `--source-commit` as an exact lowercase 40-hex commit;
- `--operator-or-agent`;
- `--output-dir`.

Each retained referee execution writes:

- `manifest.json` — the full repository experiment contract;
- `precision_report.json` — the structured comparison/referee report with matching provenance;
- `reference_run.json` — the reference diagnostics, balances, termination reason and warnings, including failed runs;
- `reference_final_velocity.npy` — the preserved raw reference final/failed velocity state.

All evidentiary outputs are SHA-256 content-hashed in the manifest and are checked by `tools/validate_precision_artifacts.py`.

Because the referee command is exposed by a normal package install, `mpmath` is a normal runtime dependency rather than an optional extra.

## Evidence ceiling

The referee is restricted to the low-resolution Taylor-Green reference family in v0.1. It is not a scalable singularity-search backend and it does not enable singularity-oriented claim promotion.

The following remain hard boundaries:

```text
FINITE_DIMENSIONAL_AGREEMENT != CONTINUUM_PROOF
PRECISION_AGREEMENT != GLOBAL_REGULARITY
PRECISION_DISAGREEMENT != MATHEMATICAL_SINGULARITY
REFEREE != INDEPENDENT_SPATIAL_DISCRETIZATION
LOW_RESOLUTION_AGREEMENT != HIGH_RESOLUTION_VALIDATION
```

A disagreement means the numerical implementations need investigation. An agreement means the tested finite-dimensional computation survived an additional precision/implementation challenge. Neither outcome resolves Navier-Stokes.

## Machine authority

The exact scope and nonclaims are locked in:

- `research/precision_referee_contract.json`;
- `research/schemas/precision_referee_contract.schema.json`;
- `research/schemas/precision_referee_report.schema.json`;
- `tools/validate_precision_referee.py`;
- `tools/validate_precision_artifacts.py`.

The referee implementation is `src/ns_lab/precision_referee.py`.
