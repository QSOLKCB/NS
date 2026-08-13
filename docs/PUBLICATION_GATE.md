<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Publication Gate

Private work may be messy. Public claims may not be.

## Gate A — Internal reproducibility

Required before promoted computational evidence:

- exact source commit;
- complete experiment manifest;
- clean rerun;
- artifact hashes;
- resolution/precision checks appropriate to the claim;
- documented failure modes.

## Gate B — Mathematical completeness

Required before theorem language:

- exact statement and hypotheses;
- complete proof;
- dependencies cited;
- known edge cases checked;
- numerical evidence removed from any step presented as deductive proof unless a rigorous bridge theorem is supplied.

## Gate C — Prior art and novelty

Required before novelty language:

- literature search recorded;
- nearest known results identified;
- distinction from known criteria/theorems stated;
- independent expert review sought for major claims.

Seeking review at Gate C is encouraged but does **not** satisfy Gate D.

## Gate D — Millennium-solution claim

Required before any public statement that the Clay problem has been solved or disproved:

- explicit mapping to an official CMI formulation;
- proof artifact frozen to an exact commit/tag;
- all assumptions and external theorem dependencies enumerated;
- adversarial internal review completed;
- independent mathematical review **completed**, with reviewer identity or attributable review record, review scope, and material findings preserved;
- all blocking issues raised by that external review resolved or explicitly incorporated into a downgrade decision;
- human operator explicitly authorizes the wording;
- repository status and citation metadata match the frozen artifact.

Merely requesting, soliciting, scheduling, or awaiting independent review is insufficient for Gate D.

No automated agent may waive Gate D.

## Retraction/downgrade

If a flaw is found after promotion, preserve the old artifact, mark its status as superseded or invalidated, document the reason, and publish the correction with equal or greater prominence than the original claim.
