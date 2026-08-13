<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Sensitivity Sweep Protocol

## Reproduced-numerical minimum

Before a laboratory result may be promoted from `exploratory` to `reproduced_numerical`, record an identical-input replay, a timestep comparison using `dt` and `dt/2` at the same final physical time, and a resolution comparison using `N` and `2N` with the remaining declared configuration fixed.

The reference implementation exposes deterministic timestep and resolution comparison helpers in `ns_lab.sweeps`.

## Independent precision referee

PR #4 adds an arbitrary-precision **referee** for the narrow `N=8` Taylor-Green reference family. It constructs the initial Fourier coefficients analytically and evolves the strict-2/3 retained modal system using direct convolution and `mpmath` arithmetic, without using NumPy FFTs in the referee evolution path.

The default comparison ladder is 50 to 80 decimal digits. Agreement checks arithmetic/FFT/nonlinear-evaluation sensitivity for the tested finite-dimensional system.

It is deliberately **not** described as an oracle and it is not an independent spatial discretization. The direct modal referee and the pseudo-spectral reference solver represent the same retained Fourier system by different computational paths.

## Singularity-oriented work

Any run used in support of a blow-up-oriented hypothesis additionally requires precision sensitivity, conservation/balance residuals, explicit competing numerical-failure explanations, and convergence behavior across more than one resolution and timestep.

The precision referee now supplies a real independent arithmetic check for the narrow reference family, but v0.1 is restricted to `N=8` Taylor-Green data and is not a scalable mechanism-search backend. The machine contract therefore **continues** to set:

```text
singularity_oriented_promotion_enabled = false
```

This does not forbid exploratory searches. It prevents a low-resolution precision agreement from being promoted into evidence about continuum singularity formation.

## Comparisons are not extrapolations

A decreasing difference between tested resolutions, timesteps, or arithmetic precisions is useful evidence about those runs. It must not be silently converted into an asymptotic convergence theorem.

In particular:

```text
PRECISION_AGREEMENT != CONTINUUM_PROOF
FINITE_DIMENSIONAL_AGREEMENT != GLOBAL_REGULARITY
LOW_RESOLUTION_AGREEMENT != HIGH_RESOLUTION_VALIDATION
```
