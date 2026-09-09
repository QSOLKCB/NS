<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Pre-OpenAI 2026 Navier–Stokes baseline

This record preserves the QSOL NS repository state immediately before intake of OpenAI's September 2026 finite-time blowup claim.

## Frozen repository point

- Repository: `QSOLKCB/NS`
- Baseline commit: `504180162eb117bc3eb280b93c8ef4df845c0d27`
- Baseline commit message: `Merge pull request #11 from QSOLKCB/agent/pr11-sealed-holdout-v0.1`
- Named preservation branch: `archive/pre-openai-ns-2026-09-08`
- External-claim intake begins only after this commit.

The baseline matters because the repository already treated global regularity and finite-time breakdown as unresolved competing tracks, already mapped regularity to Clay A/B and breakdown to Clay C/D, and already prohibited numerical, formal, ML, analogy or persistence artifacts from silently becoming mathematical truth.

## What this preservation means

The historical state is not rewritten to make the project appear to have anticipated or independently derived the September 2026 construction. New source records, claim-status records and verification work are layered on top of the frozen baseline with ordinary Git provenance.

The pre-intake theorem registry remains the source-checked historical boundary. The OpenAI result enters through a separate external-claim registry until an explicit audited promotion decision is justified.

## External artifacts admitted after the baseline

The intake phase registers:

1. OpenAI, *Finite time blowup for Navier-Stokes* (2026), exact reviewed PDF SHA-256 `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`.
2. OpenAI `NavierStokesAndEuler` Lean repository pinned at commit `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`.

Registration is provenance, not acceptance.
