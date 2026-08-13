<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Numerical Failure Modes

A suspicious numerical signature must first survive an attempt to explain it as a numerical or implementation failure.

Before treating rapid norm growth as scientifically interesting, check spatial under-resolution and spectral pile-up; timestep instability or excessive CFL; aliasing/de-aliasing sensitivity; divergence/projection drift; finite-precision overflow, cancellation or roundoff amplification; hidden filtering/regularization; altered initial-data normalization; incorrect viscosity/forcing convention; pressure reconstruction inconsistency; failure of energy/enstrophy balance diagnostics; dependency-version drift; and output/provenance corruption.

If a signature disappears under finer resolution, smaller timestep, corrected projection, alternate precision, or an independently implemented solver, the result must be downgraded or explained before further promotion.

If a signature persists, that persistence justifies additional investigation. It does not by itself increase theorem status.

```text
ROBUST_NUMERICAL_SIGNATURE != CONTINUUM_PROOF
```

Failed and null runs that constrain a hypothesis are evidence and must not be deleted merely because a later configuration behaves better.
