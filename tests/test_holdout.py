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


def candidate(candidate_id: str = "cand-1") -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        domain_id="navier-stokes-3d",
        hypothesis_set_id="hs-1",
        hypothesis=f"test mechanism {candidate_id}",
        claim_level="exploratory",
        generation_method="fixture",
    )


def seal(store: SealedHoldoutStore, *, negative_control_ids=("negative-control-null", "negative-control-symmetry")):
    return store.seal(
        holdout_id="h-1",
        domain_id="navier-stokes-3d",
        evaluator_id="fixture-evaluator",
        evaluator_version="0.1.0",
        payload={
            "cases": [{"case_id": "hidden-1", "expected": "challenge"}],
            "leakage_sentinels": ["HOLDOUT-SENTINEL-7f62c8"],
        },
        negative_control_ids=tuple(negative_control_ids),
        actor="fixture",
        source_commit=COMMIT,
        sealed_at_utc=T0,
    )


def materialize(store: SealedHoldoutStore, frozen: Candidate, *, materialization_id="m-1"):
    return store.materialize(
        materialization_id=materialization_id,
        holdout_id="h-1",
        candidate=frozen,
        crucible_ledger_head_sha256=HEAD,
        pre_release_context={"candidate_id": frozen.candidate_id, "theorems": ["T1"]},
        actor="fixture",
        source_commit=COMMIT,
        materialized_at_utc=T1,
    )


def release(store: SealedHoldoutStore, frozen: Candidate, *, materialization_id="m-1", release_id="r-1"):
    return store.release(
        release_id=release_id,
        materialization_id=materialization_id,
        candidate=frozen,
        actor="fixture",
        source_commit=COMMIT,
        released_at_utc=T2,
    )


def test_holdout_materialization_requires_frozen_candidate(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        with pytest.raises(HoldoutError, match="requires status=frozen"):
            materialize(store, candidate())


def test_pre_release_leakage_sentinel_and_payload_identity_fail_closed(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        for materialization_id, context in (
            ("m-sentinel", {"prompt": "HOLDOUT-SENTINEL-7f62c8"}),
            ("m-sentinel-embedded", {"prompt": "evaluate HOLDOUT-SENTINEL-7f62c8 now"}),
            ("m-hash", {"payload_sha256": manifest.payload_sha256}),
            ("m-hash-embedded", {"prompt": f"payload={manifest.payload_sha256}; evaluate"}),
            ("m-key-embedded", {f"prefix-HOLDOUT-SENTINEL-7f62c8-suffix": "value"}),
        ):
            with pytest.raises(HoldoutLeakageError):
                store.materialize(
                    materialization_id=materialization_id,
                    holdout_id="h-1",
                    candidate=frozen,
                    crucible_ledger_head_sha256=HEAD,
                    pre_release_context=context,
                    actor="fixture",
                    source_commit=COMMIT,
                    materialized_at_utc=T1,
                )


def test_materialize_release_and_assurance_are_auditable_and_separate(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        frozen = candidate().freeze()
        materialized = materialize(store, frozen)
        payload, release_receipt = release(store, frozen, materialization_id=materialized.materialization_id)
        assert payload["cases"][0]["case_id"] == "hidden-1"
        state = AssuranceState(
            assurance_id="a-1",
            candidate_id=frozen.candidate_id,
            schema_admission="passed",
            deterministic_replay="passed",
            cross_method_challenge="failed",
            holdout_evaluation="passed",
            continuum_bridge="unsatisfied",
            holdout_release_id=release_receipt.release_id,
            negative_controls=(
                ("negative-control-null", "passed"),
                ("negative-control-symmetry", "passed"),
            ),
            notes="Distinct assurance states; no aggregate proof status.",
        )
        # Persisted manifest is authoritative; callers need not supply a trusted copy.
        store.record_assurance(
            state,
            manifest=None,
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
        materialize(store, frozen)
        changed = replace(frozen, assumptions=("changed-after-freeze",))
        with pytest.raises(HoldoutError, match="changed after holdout materialization"):
            release(store, changed)


def test_negative_controls_can_block_a_passing_holdout_claim(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        materialize(store, frozen)
        _, receipt = release(store, frozen)
        bad = AssuranceState(
            assurance_id="a-bad",
            candidate_id=frozen.candidate_id,
            holdout_evaluation="passed",
            holdout_release_id=receipt.release_id,
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


def test_assurance_reloads_persisted_manifest_instead_of_trusting_caller(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        manifest = seal(store)
        frozen = candidate().freeze()
        materialize(store, frozen)
        _, receipt = release(store, frozen)
        forged = replace(manifest, negative_control_ids=("forged-control",))
        state = AssuranceState(
            assurance_id="a-forged",
            candidate_id=frozen.candidate_id,
            holdout_evaluation="passed",
            holdout_release_id=receipt.release_id,
            negative_controls=(("forged-control", "passed"),),
        )
        with pytest.raises(HoldoutError, match="does not match persisted holdout manifest"):
            store.record_assurance(
                state,
                manifest=forged,
                actor="fixture",
                source_commit=COMMIT,
                recorded_at_utc=T3,
            )


def test_non_not_run_holdout_evaluation_requires_declared_negative_controls(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store, negative_control_ids=())
        frozen = candidate().freeze()
        materialize(store, frozen)
        _, receipt = release(store, frozen)
        state = AssuranceState(
            assurance_id="a-empty-declared",
            candidate_id=frozen.candidate_id,
            holdout_evaluation="failed",
            holdout_release_id=receipt.release_id,
            negative_controls=(("invented-control", "failed"),),
        )
        with pytest.raises(HoldoutError, match="at least one declared negative control"):
            store.record_assurance(
                state,
                manifest=None,
                actor="fixture",
                source_commit=COMMIT,
                recorded_at_utc=T3,
            )


def test_assurance_state_rejects_evaluation_without_control_results():
    state = AssuranceState(
        assurance_id="a-empty-results",
        candidate_id="cand-1",
        holdout_evaluation="passed",
        holdout_release_id="r-1",
        negative_controls=(),
    )
    with pytest.raises(HoldoutError, match="at least one negative control result"):
        state.validate()


def test_holdout_journal_and_artifacts_fail_on_tamper(tmp_path):
    root = tmp_path / "holdout"
    with SealedHoldoutStore(root) as store:
        seal(store)
        frozen = candidate().freeze()
        materialize(store, frozen)
    path = root / "materializations" / "m-1.json"
    raw = json.loads(path.read_text())
    raw["actor"] = "tampered"
    path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(HoldoutError, match="artifact hash mismatch"):
        SealedHoldoutStore(root)


def test_orphan_materialization_is_rejected_on_reopen(tmp_path):
    root = tmp_path / "holdout"
    with SealedHoldoutStore(root) as store:
        seal(store)
    orphan = root / "materializations" / "orphan.json"
    orphan.write_text("{}\n")
    with pytest.raises(HoldoutError, match="reconciliation failed for materialization"):
        SealedHoldoutStore(root)


def test_orphan_sealed_payload_is_rejected_on_reopen(tmp_path):
    root = tmp_path / "holdout"
    with SealedHoldoutStore(root):
        pass
    payload = b'{"unbound":true}\n'
    digest = __import__("hashlib").sha256(payload).hexdigest()
    path = root / "sealed" / "sha256" / digest[:2] / f"{digest[2:]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    with pytest.raises(HoldoutError, match="reconciliation failed for sealed payload"):
        SealedHoldoutStore(root)


def test_holdout_store_is_single_writer_and_closed_reference_is_dead(tmp_path):
    root = tmp_path / "holdout"
    first = SealedHoldoutStore(root)
    with pytest.raises(HoldoutError, match="single-writer"):
        SealedHoldoutStore(root)
    first.close()
    second = SealedHoldoutStore(root)
    try:
        with pytest.raises(HoldoutError, match="store is closed"):
            first.verify()
        with pytest.raises(HoldoutError, match="store is closed"):
            first.seal(
                holdout_id="stale",
                domain_id="navier-stokes-3d",
                evaluator_id="fixture",
                evaluator_version="0.1.0",
                payload={"leakage_sentinels": []},
                negative_control_ids=(),
                actor="fixture",
                source_commit=COMMIT,
                sealed_at_utc=T0,
            )
        # The live writer remains usable; the stale reference cannot race it.
        seal(second)
    finally:
        second.close()


def test_no_new_materializations_after_first_release_but_pre_release_batch_survives(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        first = candidate("cand-1").freeze()
        second = candidate("cand-2").freeze()
        late = candidate("cand-late").freeze()
        materialize(store, first, materialization_id="m-1")
        materialize(store, second, materialization_id="m-2")
        release(store, first, materialization_id="m-1", release_id="r-1")
        with pytest.raises(HoldoutError, match="already been released"):
            materialize(store, late, materialization_id="m-late")
        # A candidate frozen/materialized before first reveal can still be evaluated.
        _, second_receipt = release(store, second, materialization_id="m-2", release_id="r-2")
        assert second_receipt.candidate_id == "cand-2"


def test_materialization_can_only_be_released_once(tmp_path):
    with SealedHoldoutStore(tmp_path / "holdout") as store:
        seal(store)
        frozen = candidate().freeze()
        materialize(store, frozen)
        release(store, frozen)
        with pytest.raises(HoldoutError, match="already been released"):
            release(store, frozen, release_id="r-duplicate")


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
