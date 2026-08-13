<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Numerical Evidence Policy

Numerical computation is a discovery, falsification and stress-testing instrument. It is not a substitute for a continuum proof.

## Permitted uses

- search for candidate singularity mechanisms;
- test scaling hypotheses;
- falsify proposed universal estimates numerically;
- identify regimes worthy of analysis;
- compare diagnostics across solvers/resolutions;
- generate conjectures and counterexample candidates;
- reproduce published computational claims.

## Forbidden inference shortcuts

The following implications are invalid unless an independent mathematical argument supplies the missing bridge:

```text
finite_grid_divergence -> continuum_singularity
stable_long_run -> global_regular_solution
large_vorticity -> finite_time_blowup
spectral_tail_growth -> singularity
solver_nonconvergence -> PDE_nonexistence
formal_fit_to_power_law -> exact_self_similarity
```

## Required adversarial checks for blow-up signatures

- spatial refinement;
- timestep refinement;
- precision increase;
- independent diagnostic quantities;
- conservation/balance residuals where applicable;
- alternate solver or method when feasible;
- filtering/dealiasing sensitivity;
- domain/boundary sensitivity where relevant;
- explicit numerical-failure null hypothesis.

## Reporting

Plots must identify the underlying artifact/experiment ID. Cropped or transformed visualizations must not be the sole retained evidence. Raw or losslessly reconstructable numerical data must be preserved for promoted results.
