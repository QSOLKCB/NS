#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the sealed-holdout contract, schemas, and hostile invariants."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from jsonschema import Draft202012Validator

from crucible_core.holdout import AssuranceState, HoldoutError, HoldoutLeakageError, SealedHoldoutStore
from crucible_core.models import Candidate

ROOT = Path(__file__).parents[1]
SCHEMAS = ROOT / "research" / "schemas"
COMMIT = "a" * 40
HEAD = "b" * 64


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def main() -> int:
    contract = load_json(ROOT / "research" / "holdout_contract.json")
    validator("holdout-contract.schema.json").validate(contract)
    assert contract["authority"]["holdout_success_promotes_claim"] is False
    assert contract["authority"]["holdout_success_selects_winner"] is False
    assert contract["assurance_states_are_independent"] is True
    assert contract["freeze_and_release"]["candidate_snapshot_hash_bound_before_release"] is True
    assert contract["leakage_controls"]["negative_controls_required_when_holdout_evaluation_runs"] is True

    manifest_validator = validator("holdout-manifest.schema.json")
    materialization_validator = validator("holdout-materialization.schema.json")
    release_validator = validator("holdout-release.schema.json")
    assurance_validator = validator("holdout-assurance-state.schema.json")
    event_validator = validator("holdout-event.schema.json")

    candidate = Candidate(
        candidate_id="validator-candidate",
        domain_id="navier-stokes-3d",
        hypothesis_set_id="validator-set",
        hypothesis="hostile validation fixture",
        claim_level="exploratory",
        generation_method="validator",
    )

    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "holdout"
        with SealedHoldoutStore(root) as store:
            manifest = store.seal(
                holdout_id="validator-holdout",
                domain_id="navier-stokes-3d",
                evaluator_id="validator",
                evaluator_version="0.1.0",
                payload={"cases": [{"id": "hidden"}], "leakage_sentinels": ["VALIDATOR-SECRET-9e31"]},
                negative_control_ids=("null-control",),
                actor="validator",
                source_commit=COMMIT,
                sealed_at_utc="2026-08-14T12:00:00+00:00",
            )
            manifest_validator.validate(manifest.to_dict())

            try:
                store.materialize(
                    materialization_id="must-fail-active",
                    holdout_id=manifest.holdout_id,
                    candidate=candidate,
                    crucible_ledger_head_sha256=HEAD,
                    pre_release_context={},
                    actor="validator",
                    source_commit=COMMIT,
                    materialized_at_utc="2026-08-14T12:01:00+00:00",
                )
            except HoldoutError:
                pass
            else:
                raise AssertionError("active candidate reached holdout materialization")

            frozen = candidate.freeze()
            try:
                store.assert_context_clean({"prompt": "VALIDATOR-SECRET-9e31"}, holdout_id=manifest.holdout_id)
            except HoldoutLeakageError:
                pass
            else:
                raise AssertionError("leakage sentinel was not detected")

            materialization = store.materialize(
                materialization_id="validator-materialization",
                holdout_id=manifest.holdout_id,
                candidate=frozen,
                crucible_ledger_head_sha256=HEAD,
                pre_release_context={"candidate_id": frozen.candidate_id},
                actor="validator",
                source_commit=COMMIT,
                materialized_at_utc="2026-08-14T12:02:00+00:00",
            )
            materialization_validator.validate(materialization.to_dict())
            _, release = store.release(
                release_id="validator-release",
                materialization_id=materialization.materialization_id,
                candidate=frozen,
                actor="validator",
                source_commit=COMMIT,
                released_at_utc="2026-08-14T12:03:00+00:00",
            )
            release_validator.validate(release.to_dict())
            assurance = AssuranceState(
                assurance_id="validator-assurance",
                candidate_id=frozen.candidate_id,
                schema_admission="passed",
                deterministic_replay="passed",
                cross_method_challenge="failed",
                holdout_evaluation="passed",
                continuum_bridge="unsatisfied",
                holdout_release_id=release.release_id,
                negative_controls=(("null-control", "passed"),),
            )
            assurance_validator.validate(assurance.to_dict())
            store.record_assurance(
                assurance,
                manifest=manifest,
                actor="validator",
                source_commit=COMMIT,
                recorded_at_utc="2026-08-14T12:04:00+00:00",
            )
            replay = store.verify()
            assert replay["event_count"] == 4
            assert replay["authority"]["holdout_success_promotes_claim"] is False

        for line in (root / "holdout.jsonl").read_text(encoding="utf-8").splitlines():
            event_validator.validate(json.loads(line))

    print("sealed holdout validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
