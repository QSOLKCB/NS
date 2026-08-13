# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import pytest

from crucible_core import (
    ContentAddressedLedger,
    DeterministicFixtureBackend,
    GeneratorAirlock,
    GeneratorAirlockError,
    GeneratorAttemptJournal,
    GeneratorContextPacket,
)

DOMAIN = "navier_stokes_3d_incompressible"
HSET = "NS_PRIMARY_COMPETITION"
TRACKS = {"NS_GLOBAL_REGULARITY", "NS_FINITE_TIME_BREAKDOWN"}
THEOREMS = {"KNOWN_LERAY_GLOBAL_WEAK_EXISTENCE", "KNOWN_ESS_ENDPOINT_L3"}
BARRIERS = {"CIRCULAR_REGULARITY", "NUMERICAL_CONTINUUM_GAP"}
ANALOGIES = {"GENERATIVE_DIFFUSION_LAPLACIAN_TO_NS_VISCOSITY"}
COMMIT = "a" * 40
STAMP = "2026-08-13T10:00:00Z"
PROMPT_SHA = "b" * 64


def context(**overrides) -> GeneratorContextPacket:
    values = {
        "domain_id": DOMAIN,
        "hypothesis_set_id": HSET,
        "target_hypotheses": tuple(sorted(TRACKS)),
        "theorem_ids": tuple(sorted(THEOREMS)),
        "proof_barrier_ids": tuple(sorted(BARRIERS)),
        "frontier_candidate_ids": ("parent1",),
        "failure_lessons": ("do not assume the desired regularity",),
        "permitted_analogy_ids": tuple(sorted(ANALOGIES)),
        "ledger_event_count": 0,
        "ledger_head_event_sha256": None,
        "source_commit": COMMIT,
        "task": "propose one precise exploratory mechanism",
    }
    values.update(overrides)
    return GeneratorContextPacket(**values)


def valid_payload(**overrides):
    value = {
        "proposal_id": "ml-candidate-1",
        "target_hypothesis": "NS_GLOBAL_REGULARITY",
        "precise_statement": "Investigate a scale-local estimate for a critical vorticity quantity.",
        "motivation": "The estimate would target an unresolved continuation bottleneck without assuming it.",
        "assumptions": ["smooth solution on its interval of existence"],
        "claimed_dependencies": ["KNOWN_ESS_ENDPOINT_L3"],
        "suggested_tests": ["check scaling", "check against proof barriers"],
        "possible_failure_modes": ["estimate may be circular", "constant may not close"],
        "analogy_sources": [],
        "parent_candidate_ids": ["parent1"],
        "generator_notes": "exploratory proposal only",
    }
    value.update(overrides)
    return value


def airlock(tmp_path: Path, *, known_candidates=None):
    journal = GeneratorAttemptJournal(tmp_path / "journal")
    return GeneratorAirlock(
        domain_id=DOMAIN,
        hypothesis_set_id=HSET,
        allowed_target_hypotheses=TRACKS,
        required_proof_barrier_ids=BARRIERS,
        known_candidate_ids=set(known_candidates or {"parent1"}),
        known_theorem_ids=THEOREMS,
        known_analogy_ids=ANALOGIES,
        journal=journal,
    ), journal


def run_payload(
    tmp_path: Path,
    payload,
    *,
    attempt="attempt-1",
    known_candidates=None,
    context_packet=None,
):
    gate, journal = airlock(tmp_path, known_candidates=known_candidates)
    backend = DeterministicFixtureBackend(
        json.dumps(payload, separators=(",", ":"), sort_keys=True)
    )
    decision = gate.run(
        backend=backend,
        context=context_packet or context(),
        attempt_id=attempt,
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    return gate, journal, decision


def journal_payload(journal: GeneratorAttemptJournal) -> dict:
    line = journal.log_path.read_text("utf-8").splitlines()[-1]
    event = json.loads(line)
    digest = event["attempt_object_sha256"]
    object_path = journal.objects_root / digest[:2] / f"{digest[2:]}.json"
    envelope = json.loads(object_path.read_text("utf-8"))
    return envelope["payload"]


def test_valid_proposal_becomes_exploratory_candidate(tmp_path: Path):
    _, journal, decision = run_payload(tmp_path, valid_payload())
    assert decision.accepted is True
    assert decision.candidate is not None
    assert decision.candidate.claim_level == "exploratory"
    assert decision.candidate.status == "active"
    assert decision.candidate.frozen is False
    assert "generation_attempt_id=attempt-1" in decision.candidate.assumptions
    assert journal.verify()[0] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("claim_level", "public_solution_claim"),
        ("proved", True),
        ("solves_clay", True),
        ("confidence_score", 0.999),
        ("evidence_status", "proved"),
    ],
)
def test_authority_fields_are_rejected_and_recorded(tmp_path: Path, field, value):
    payload = valid_payload()
    payload[field] = value
    _, journal, decision = run_payload(tmp_path, payload)
    assert decision.accepted is False
    assert "forbidden_authority_field" in decision.rejection_reasons
    assert journal.verify()[0] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("generator_notes", "Therefore proof complete"),
        ("assumptions", ["proof complete"]),
        ("suggested_tests", ["millennium problem resolved"]),
        ("possible_failure_modes", ["solves Clay"]),
    ],
)
def test_authority_language_is_rejected_in_every_text_surface(tmp_path: Path, field, value):
    payload = valid_payload(**{field: value})
    _, _, decision = run_payload(tmp_path, payload)
    assert decision.rejection_reasons == ("forbidden_authority_language",)


def test_invalid_json_is_recorded_not_raised(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    decision = gate.run(
        backend=DeterministicFixtureBackend("```json\n{}\n```"),
        context=context(),
        attempt_id="bad-json",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.accepted is False
    assert decision.rejection_reasons == ("invalid_json",)
    assert journal_payload(journal)["parse_status"] == "not_parsed"
    assert journal.verify()[0] == 1


def test_nonfinite_json_is_rejected(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    raw = json.dumps(valid_payload()).replace(
        '"generator_notes": "exploratory proposal only"',
        '"generator_notes": NaN',
    )
    decision = gate.run(
        backend=DeterministicFixtureBackend(raw),
        context=context(),
        attempt_id="nan-attempt",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.rejection_reasons == ("invalid_json",)
    assert journal.verify()[0] == 1


def test_nested_list_item_is_schema_failure_and_recorded(tmp_path: Path):
    _, journal, decision = run_payload(
        tmp_path,
        valid_payload(assumptions=[{}]),
        attempt="nested-list",
    )
    assert decision.rejection_reasons == ("schema_failure",)
    assert journal_payload(journal)["parse_status"] == "parsed"
    assert journal.verify()[0] == 1


def test_schema_invalid_but_parsed_json_is_recorded_as_parsed(tmp_path: Path):
    payload = valid_payload()
    del payload["generator_notes"]
    _, journal, decision = run_payload(tmp_path, payload, attempt="parsed-schema-fail")
    assert decision.rejection_reasons == ("schema_failure",)
    receipt = journal_payload(journal)
    assert receipt["parse_status"] == "parsed"
    assert receipt["proposal"] is None


def test_unknown_hypothesis_rejected(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path, valid_payload(target_hypothesis="NS_MAGIC")
    )
    assert "unknown_hypothesis" in decision.rejection_reasons


def test_unknown_parent_rejected(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path, valid_payload(parent_candidate_ids=["missing-parent"])
    )
    assert "unknown_parent" in decision.rejection_reasons


def test_known_parent_must_be_in_supplied_context(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path,
        valid_payload(parent_candidate_ids=["parent2"]),
        known_candidates={"parent1", "parent2"},
        context_packet=context(frontier_candidate_ids=("parent1",)),
    )
    assert "parent_not_in_context" in decision.rejection_reasons
    assert "unknown_parent" not in decision.rejection_reasons


def test_unknown_theorem_dependency_rejected(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path,
        valid_payload(claimed_dependencies=["FAKE_THEOREM"]),
    )
    assert "unknown_theorem_dependency" in decision.rejection_reasons


def test_known_theorem_dependency_must_be_in_supplied_context(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path,
        valid_payload(claimed_dependencies=["KNOWN_LERAY_GLOBAL_WEAK_EXISTENCE"]),
        context_packet=context(theorem_ids=("KNOWN_ESS_ENDPOINT_L3",)),
    )
    assert "theorem_dependency_not_in_context" in decision.rejection_reasons
    assert "unknown_theorem_dependency" not in decision.rejection_reasons


def test_unregistered_analogy_rejected(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path, valid_payload(analogy_sources=["FAKE_ANALOGY"])
    )
    assert "unregistered_analogy" in decision.rejection_reasons


def test_registered_analogy_must_route_through_firewall(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path,
        valid_payload(
            analogy_sources=["GENERATIVE_DIFFUSION_LAPLACIAN_TO_NS_VISCOSITY"]
        ),
    )
    assert decision.rejection_reasons == ("analogy_requires_firewall_route",)


def test_duplicate_candidate_id_rejected(tmp_path: Path):
    _, _, decision = run_payload(
        tmp_path,
        valid_payload(proposal_id="existing"),
        known_candidates={"parent1", "existing"},
    )
    assert "duplicate_candidate_id" in decision.rejection_reasons


def test_overlong_proposal_id_is_rejected_before_ledger_commit(tmp_path: Path):
    gate, journal, decision = run_payload(
        tmp_path,
        valid_payload(proposal_id="x" * 129),
        attempt="long-proposal-id",
    )
    assert decision.rejection_reasons == ("schema_failure",)
    assert journal.verify()[0] == 1
    ledger = ContentAddressedLedger(tmp_path / "ledger-long-id")
    with pytest.raises(GeneratorAirlockError):
        gate.commit_candidate(
            decision,
            ledger=ledger,
            actor="unit-test",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )
    assert ledger.verify().event_count == 0


def test_context_hash_is_deterministic():
    assert context().sha256() == context().sha256()


def test_wrong_domain_context_is_rejected_and_recorded(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    decision = gate.run(
        backend=DeterministicFixtureBackend(json.dumps(valid_payload())),
        context=context(domain_id="other_domain"),
        attempt_id="bad-context",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.rejection_reasons == ("invalid_context",)
    assert journal_payload(journal)["parse_status"] == "not_attempted"
    assert journal.verify()[0] == 1


def test_context_requires_complete_target_track_set(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    decision = gate.run(
        backend=DeterministicFixtureBackend(json.dumps(valid_payload())),
        context=context(target_hypotheses=("NS_GLOBAL_REGULARITY",)),
        attempt_id="one-sided-context",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.rejection_reasons == ("invalid_context",)
    assert journal.verify()[0] == 1


def test_context_requires_complete_proof_barrier_set(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    decision = gate.run(
        backend=DeterministicFixtureBackend(json.dumps(valid_payload())),
        context=context(proof_barrier_ids=("CIRCULAR_REGULARITY",)),
        attempt_id="missing-barrier-context",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.rejection_reasons == ("invalid_context",)
    assert journal.verify()[0] == 1


class RaisingBackend:
    backend_id = "raising-fixture"
    model_id = "raising-model"

    def generate(self, context_packet):
        del context_packet
        raise RuntimeError("provider detail must not escape into journal")


class NonTextBackend:
    backend_id = "nontext-fixture"
    model_id = "nontext-model"

    def generate(self, context_packet):
        del context_packet
        return {"not": "text"}


@pytest.mark.parametrize("backend", [RaisingBackend(), NonTextBackend()])
def test_provider_failures_are_rejected_and_journaled(tmp_path: Path, backend):
    gate, journal = airlock(tmp_path)
    decision = gate.run(
        backend=backend,
        context=context(),
        attempt_id=f"provider-failure-{backend.backend_id}",
        prompt_template_sha256=PROMPT_SHA,
        recorded_at_utc=STAMP,
    )
    assert decision.rejection_reasons == ("provider_failure",)
    receipt = journal_payload(journal)
    assert receipt["parse_status"] == "not_attempted"
    assert receipt["raw_output"] == ""
    assert "provider detail" not in json.dumps(receipt)
    assert journal.verify()[0] == 1


def test_invalid_journal_timestamp_is_rejected_before_record(tmp_path: Path):
    gate, journal = airlock(tmp_path)
    with pytest.raises(GeneratorAirlockError):
        gate.run(
            backend=DeterministicFixtureBackend(json.dumps(valid_payload())),
            context=context(),
            attempt_id="bad-time",
            prompt_template_sha256=PROMPT_SHA,
            recorded_at_utc="not-utc",
        )
    assert journal.verify()[0] == 0


def test_commit_candidate_is_explicit_separate_step(tmp_path: Path):
    gate, _, decision = run_payload(tmp_path, valid_payload())
    ledger = ContentAddressedLedger(tmp_path / "ledger")
    assert ledger.verify().event_count == 0
    object_id = gate.commit_candidate(
        decision,
        ledger=ledger,
        actor="unit-test",
        source_commit=COMMIT,
        recorded_at_utc=STAMP,
    )
    assert object_id.startswith("sha256:")
    assert ledger.verify().event_count == 1


def test_rejected_decision_cannot_be_committed(tmp_path: Path):
    gate, _, decision = run_payload(
        tmp_path, valid_payload(target_hypothesis="NS_MAGIC")
    )
    with pytest.raises(GeneratorAirlockError):
        gate.commit_candidate(
            decision,
            ledger=ContentAddressedLedger(tmp_path / "ledger"),
            actor="unit-test",
            source_commit=COMMIT,
            recorded_at_utc=STAMP,
        )


def test_generation_journal_detects_tampering(tmp_path: Path):
    _, journal, _ = run_payload(tmp_path, valid_payload())
    event = json.loads(journal.log_path.read_text("utf-8"))
    event["attempt_id"] = "tampered"
    journal.log_path.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GeneratorAirlockError):
        journal.verify()


def test_authority_snapshot_has_no_epistemic_power(tmp_path: Path):
    gate, _ = airlock(tmp_path)
    authority = gate.authority_snapshot()
    assert authority["candidate_initial_claim_level"] == "exploratory"
    for key in (
        "domain_evidence",
        "claim_promotion",
        "proof_status_assignment",
        "winner_selection",
        "confidence_as_authority",
        "direct_analogy_bypass",
        "rejection_is_mathematical_failure",
    ):
        assert authority[key] is False
