# Security and Research-Integrity Reporting

QSOL NS is research software. Security defects and research-integrity defects are both treated as release blockers when they can corrupt evidence, provenance or reproducibility.

## Report privately

For the private phase, report issues through the repository's private GitHub issue/PR channels available to authorized collaborators. Do not publish secrets, credentials, private datasets, unpublished third-party material or exploit details in public channels.

## Security scope

Relevant software issues include:

- arbitrary code execution;
- unsafe deserialization;
- path traversal;
- dependency or CI compromise;
- secret leakage;
- artifact substitution;
- hash/provenance mismatch;
- nondeterministic execution presented as deterministic;
- tampering with experiment manifests or evidence bundles.

## Research-integrity scope

Also report:

- output attributed to the wrong source commit;
- silent changes to initial/boundary conditions;
- solver failures misclassified as singularities;
- missing negative/null runs that materially alter interpretation;
- plots or diagnostics that cannot be reconstructed from stored data;
- theorem statements that do not match the proof artifact;
- numerical-to-continuum inferences lacking a stated bridge argument.

## Secrets

No credentials, private API keys or personal access tokens belong in this repository. Use external secret storage and least-privilege CI credentials when automation is added.
