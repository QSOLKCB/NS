# SPDX-License-Identifier: Apache-2.0
from dataclasses import replace
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from crucible_core.holdout import (
    AssuranceState,
    HoldoutError,
    HoldoutLeakageError,
    SealedHoldoutStore,
)
from crucible_core.models import Candidate

COMMIT = "a" * 40
HEAD = "b" * 64
T0 = "2026-08-14T12:00:00+00:00"
T1 = "2026-08-14T12:01:00+00:00"
T2 = "2026-08-14T12:02:00+00:00"
T3 = "2026-08-14T12:03:00+00:00"


def candidate() -> Candidate:
    return Candidate(
        candidate_id="cand-1",
        domain_id="navier-stokes-3d",
        hypothesis_set_id="hs-1",
        hypothesis="test mechanism",
        claim_level="exploratory",
        generation_method="fixture",
    )


def seal(store: SealedHoldoutStore):
    return store.seal(
        holdout_id="h-1",
        domain_id="navier-stokes-3d",
        evaluator_id="fixture-evaluator",
        evaluator_version="0.1.0",
        payload={
            "cases": [{"case_id": "hidden-1", "expected": "challenge"}],
            "leakage_sentinels": ["HOLDOUT-SENTINEL-7f62c8"],
        },
        negative_control_ids=("negative-control-null", "negative-control-symmetry"),
        actor="fixture",
        source_commit=COMMIT,
        sealed_at_utc=T0,
    )


def test_holdout_materialization_requires_frozen_candidate(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        with pytest.raises(HoldoutError, match="requires status=frozen"):
            store.materialize(
                materialization_id="m-1",
                holdout_id="h-1",
                candidate=candidate(),
                crucible_ledger_head_sha256=HEAD,
                pre_release_context={"candidate": "public-only"},
                actor="fixture",
                source_commit=COMMIT,
                materialized_at_utc=T1,
            )


def test_pre_release_leakage_sentinel_and_payload_identity_fail_closed(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        with pytest.raises(HoldoutLeakageError):
            store.materialize(
                materialization_id="m-sentinel",
                holdout_id="h-1",
                candidate=frozen,
                crucible_ledger_head_sha256=HEAD,
                pre_release_context={"prompt": "HOLDOUT-SENTINEL-7f62c8"},
                actor="fixture",
                source_commit=COMMIT,
                materialized_at_utc=T1,
            )
        with pytest.raises(HoldoutLeakageError):
            store.materialize(
                materialization_id="m-hash",
                holdout_id="h-1",
                candidate=frozen,
                crucible_ledger_head_sha256=HEAD,
                pre_release_context={"payload_sha256": manifest.payload_sha256},
                actor="fixture",
                source_commit=COMMIT,
                materialized_at_utc=T1,
            )


def test_materialize_release_and_assurance_are_auditable_and_separate(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        materialized = store.materialize(
            materialization_id="m-1",
            holdout_id="h-1",
            candidate=frozen,
            crucible_ledger_head_sha256=HEAD,
            pre_release_context={"candidate_id": "cand-1", "theorems": ["T1"]},
            actor="fixture",
            source_commit=COMMIT,
            materialized_at_utc=T1,
        )
        payload, release = store.release(
            release_id="r-1",
            materialization_id=materialized.materialization_id,
            candidate=frozen,
            actor="fixture",
            source_commit=COMMIT,
            released_at_utc=T2,
        )
        assert payload["cases"][0]["case_id"] == "hidden-1"
        state = AssuranceState(
            assurance_id="a-1",
            candidate_id=frozen.candidate_id,
            schema_admission="passed",
            deterministic_replay="passed",
            cross_method_challenge="failed",
            holdout_evaluation="passed",
            continuum_bridge="unsatisfied",
            holdout_release_id=release.release_id,
            negative_controls=(
                ("negative-control-null", "passed"),
                ("negative-control-symmetry", "passed"),
            ),
            notes="Distinct assurance states; no aggregate proof status.",
        )
        store.record_assurance(
            state,
            manifest=manifest,
            actor="fixture",
            source_commit=COMMIT,
            recorded_at_utc=T3,
        )
        replay = store.verify()
        assert replay["event_count"] == 4
        assert replay["authority"]["holdout_success_promotes_claim"] is False
        exported = state.to_dict()
        assert exported["cross_method_challenge"] == "failed"
        assert exported["holdout_evaluation"] == "passed"
        assert exported["continuum_bridge"] == "unsatisfied"
        assert exported["authority"]["replay_is_continuum_proof"] is False


def test_candidate_snapshot_is_immutable_across_materialization_and_release(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        frozen = candidate().freeze()
        store.materialize(
            materialization_id="m-1",
            holdout_id="h-1",
            candidate=frozen,
            crucible_ledger_head_sha256=HEAD,
            pre_release_context={},
            actor="fixture",
            source_commit=COMMIT,
            materialized_at_utc=T1,
        )
        changed = replace(frozen, assumptions=("changed-after-freeze",))
        with pytest.raises(HoldoutError, match="changed after holdout materialization"):
            store.release(
                release_id="r-1",
                materialization_id="m-1",
                candidate=changed,
                actor="fixture",
                source_commit=COMMIT,
                released_at_utc=T2,
            )


def test_negative_controls_can_block_a_passing_holdout_claim(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        store.materialize(
            materialization_id="m-1",
            holdout_id="h-1",
            candidate=frozen,
            crucible_ledger_head_sha256=HEAD,
            pre_release_context={},
            actor="fixture",
            source_commit=COMMIT,
            materialized_at_utc=T1,
        )
        _, release = store.release(
            release_id="r-1",
            materialization_id="m-1",
            candidate=frozen,
            actor="fixture",
            source_commit=COMMIT,
            released_at_utc=T2,
        )
        bad = AssuranceState(
            assurance_id="a-bad",
            candidate_id=frozen.candidate_id,
            holdout_evaluation="passed",
            holdout_release_id=release.release_id,
            negative_controls=(
                ("negative-control-null", "passed"),
                ("negative-control-symmetry", "failed"),
            ),
        )
        with pytest.raises(HoldoutError, match="negative control fails"):
            store.record_assurance(
                bad,
                manifest=manifest,
                actor="fixture",
                source_commit=COMMIT,
                recorded_at_utc=T3,
            )


def test_holdout_journal_and_artifacts_fail_on_tamper(tmp_path):
    root = tmp_path / "holdout"
    with SealedHoldoutStore(root) as store:
        seal(store)
        frozen = candidate().freeze()
        store.materialize(
            materialization_id="m-1",
            holdout_id="h-1",
            candidate=frozen,
            crucible_ledger_head_sha256=HEAD,
            pre_release_context={},
            actor="fixture",
            source_commit=COMMIT,
            materialized_at_utc=T1,
        )
    path = root / "materializations" / "m-1.json"
    raw = json.loads(path.read_text())
    raw["actor"] = "tampered"
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(HoldoutError, match="artifact hash mismatch"):
        with SealedHoldoutStore(root) as reopened:
            reopened.verify()


def test_holdout_store_is_single_writer(tmp_path):
    root = tmp_path / "holdout"
    first = SealedHoldoutStore(root)
    try:
        with pytest.raises(HoldoutError, match="single-writer"):
            SealedHoldoutStore(root)
    finally:
        first.close()


def test_holdout_schema_artifacts_are_valid_draft_2020_12():
    root = Path(__file__).parents[1]
    schema_names = (
        "holdout-manifest.schema.json",
        "holdout-materialization.schema.json",
        "holdout-release.schema.json",
        "holdout-assurance-state.schema.json",
        "holdout-event.schema.json",
        "holdout-contract.schema.json",
    )
    for name in schema_names:
        schema = json.loads((root / "research" / "schemas" / name).read_text())
        Draft202012Validator.check_schema(schema)
