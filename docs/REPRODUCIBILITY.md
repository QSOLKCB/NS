<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Reproducibility Policy

## Goal

Another authorized researcher or agent should be able to identify exactly what was run, reconstruct the computational environment, rerun the experiment and determine whether the recorded output matches.

## Minimum controls

- exact source commit;
- immutable experiment manifest;
- dependency lock or exact versions;
- deterministic seed where randomness exists;
- explicit floating-point precision;
- input/output cryptographic hashes;
- preserved stdout/stderr or structured logs for evidentiary runs;
- explicit termination status;
- canonical units and scaling conventions.

## Determinism classes

`D0`: exploratory, determinism unknown.

`D1`: same executable/configuration repeats within declared numerical tolerance.

`D2`: reproducible across clean environments of the same declared platform class.

`D3`: cross-platform or independently implemented replication within a stated tolerance/observable contract.

No experiment is called deterministic without naming its class and tolerance model.

## Numerical equality

Bitwise identity and mathematical/numerical agreement are different contracts. When bitwise equality is impossible or inappropriate, define the observable, norm, tolerance and reduction order used for comparison before running the experiment.

## Archive rule

Results promoted into a manuscript or public release must be tied to an immutable commit/tag and an artifact manifest. If a DOI is later minted, the DOI record must identify the exact release artifact rather than a moving branch.
