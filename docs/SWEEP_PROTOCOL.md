<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Sensitivity Sweep Protocol

## Reproduced-numerical minimum

Before a v0.1 laboratory result may be promoted from `exploratory` to `reproduced_numerical`, record an identical-input replay, a timestep comparison using `dt` and `dt/2` at the same final physical time, and a resolution comparison using `N` and `2N` with the remaining declared configuration fixed.

The reference implementation exposes deterministic timestep and resolution comparison helpers in `ns_lab.sweeps`.

## Singularity-oriented work

Any run used in support of a blow-up-oriented hypothesis additionally requires precision sensitivity, conservation/balance residuals, explicit competing numerical-failure explanations, and convergence behavior across more than one resolution and timestep.

The v0.1 solver has only a `float64/complex128` backend, so it cannot yet satisfy the required independent precision comparison. The machine contract therefore sets:

```text
singularity_oriented_promotion_enabled = false
```

This does not forbid exploratory searches. It forbids promoting their numerical signatures beyond what the available validation can support.

## Comparisons are not extrapolations

A decreasing difference between two tested resolutions or timesteps is useful evidence about those runs. It must not be silently converted into an asymptotic convergence theorem.
