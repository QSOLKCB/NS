<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Deterministic PDE Laboratory v0.1

## Purpose

Phase 2 begins with a deliberately narrow reference solver for the three-dimensional incompressible Navier–Stokes equations on the periodic cube `[0,2π)^3` with positive viscosity and zero forcing.

The laboratory exists to make numerical behavior reproducible, inspectable and adversarially testable. It is not a numerical proof engine.

## Reference method

v0.1 uses Fourier pseudo-spectral spatial discretization, 2/3 de-aliasing, spectral divergence-free projection, classical fixed-step RK4, `float64/complex128`, deterministic Taylor–Green initial data, and no randomness.

The solver is intentionally small enough to audit line-by-line.

## Executable baseline identities

All six Phase-1 identities in `research/baseline_identities.json` are bound to executable diagnostics by `research/lab_contract.json`: incompressibility, Navier–Stokes scaling, smooth unforced energy equality, vorticity evolution, smooth unforced enstrophy balance, and the pressure Poisson relation.

Passing these checks shows internal numerical consistency at the tested discretization. It does not establish continuum regularity.

## Deterministic artifacts

A reference run writes `manifest.json`, `diagnostics.json`, and `final_velocity.npy`. The deterministic outputs are content-hashed in the manifest. `manifest.json` contains time/runtime provenance and is therefore not expected to be byte-identical across different execution times.

```text
SAME_ENVIRONMENT + SAME_INPUTS -> SAME_DETERMINISTIC_OUTPUT_HASHES
```

The project does not promise bitwise identity across different FFT implementations, CPU architectures, NumPy versions or platforms.

## Current evidence ceiling

The numerical laboratory may support at most `reproduced_numerical` evidence after the required replay, timestep and resolution checks.

v0.1 does not implement an independent precision backend. Therefore singularity-oriented promotion is disabled in the machine contract.

```text
LARGE_VORTICITY != SINGULARITY
ENERGY_BALANCE_RESIDUAL != CONTINUUM_DEFECT
SOLVER_FAILURE != PDE_BLOWUP
UNDER_RESOLUTION != MATHEMATICAL_SINGULARITY
```

## Reference initial condition

The first reference family is the Taylor–Green vortex:

```text
u1 = A sin(x) cos(y) cos(z)
u2 = -A cos(x) sin(y) cos(z)
u3 = 0
```

It is deterministic and analytically divergence-free. It is not asserted to be a privileged candidate for resolving the Clay problem.

## Expansion rule

New solvers, initial-data families, forcing conventions, precision backends or boundary conditions must arrive through reviewed changes that update the machine lab contract and corresponding validation.
