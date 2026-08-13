<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Baseline Identities for the Deterministic PDE Laboratory

These identities define the first analytic consistency checks that Phase 2 solvers will be expected to reproduce under their stated assumptions. The machine-readable source is `research/baseline_identities.json`.

They are **diagnostics, not solution criteria**.

## 1. Incompressibility

```text
div u = 0
```

A numerical solver should report divergence/projection residuals. Loss of the constraint is first evidence of numerical invalidity, not evidence of a continuum singularity.

## 2. Navier-Stokes scaling

For the unforced equations on a scaling-compatible domain,

```text
u_lambda(x,t) = lambda u(lambda x, lambda^2 t)
p_lambda(x,t) = lambda^2 p(lambda x, lambda^2 t)
```

This scaling is a basic dimensional check for proposed norms, estimates and diagnostics.

## 3. Smooth unforced energy equality

For a sufficiently smooth, divergence-free solution with decay or periodic cancellation and `f = 0`,

```text
(1/2) d/dt ||u||_L2^2 + nu ||grad u||_L2^2 = 0.
```

Phase 2 should record a discrete energy-balance residual rather than only plotting kinetic energy.

## 4. Vorticity equation

With `omega = curl u`,

```text
partial_t omega + (u dot grad) omega
  = (omega dot grad) u + nu Delta omega + curl f.
```

The vortex-stretching term is central in three dimensions, but a large stretching term by itself is not a proof of blow-up.

## 5. Smooth unforced enstrophy balance

Under the stated smoothness and boundary assumptions,

```text
(1/2) d/dt ||omega||_L2^2 + nu ||grad omega||_L2^2
  = integral omega_i partial_i u_j omega_j dx.
```

The future laboratory should separately record stretching production, viscous dissipation and the balance residual.

## 6. Pressure Poisson relation

For sufficiently smooth incompressible solutions,

```text
-Delta p = partial_i partial_j (u_i u_j) - div f.
```

For divergence-free forcing this reduces to the familiar velocity-only pressure relation.

## Phase 2 rule

Every solver-facing identity must carry its assumptions into the experiment manifest. A diagnostic may not silently outlive the smoothness, forcing, boundary or domain assumptions under which it was derived.

```text
DIAGNOSTIC_PASS != GLOBAL_REGULARITY_PROOF
DIAGNOSTIC_FAIL != CONTINUUM_SINGULARITY
```
