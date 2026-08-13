#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate schema-constrained ML generator contracts and authority boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from crucible_core import (
    ContentAddressedLedger,
    DeterministicFixtureBackend,
    GENERATOR_VERSION,
    GeneratorAirlock,
    GeneratorAttemptJournal,
    GeneratorContextPacket,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"ML generator schema regression: forbidden mutation accepted: {label}")


def main() -> None:
    contract = load(RESEARCH / "ml_generator_contract.json")
    contract_schema = load(RESEARCH / "schemas/ml_generator_contract.schema.json")
    proposal_schema = load(RESEARCH / "schemas/ml_candidate_proposal.schema.json")
    context_schema = load(RESEARCH / "schemas/ml_generator_context.schema.json")
    attempt_schema = load(RESEARCH / "schemas/ml_generation_attempt.schema.json")
    adapter = load(RESEARCH / "ns_ml_generator_adapter.json")
    adapter_schema = load(RESEARCH / "schemas/ns_ml_generator_adapter.schema.json")
    ns_crucible = load(RESEARCH / "ns_crucible_adapter.json")
    theorem_registry = load(RESEARCH / "theorem_registry.json")
    barriers = load(RESEARCH / "proof_barriers.json")
    analogies = load(RESEARCH / "cross_domain_transfer_registry.json")
    agents = load(ROOT / "AGENTS.md")

    for schema in (
        contract_schema,
        proposal_schema,
        context_schema,
        attempt_schema,
        adapter_schema,
    ):
        Draft202012Validator.check_schema(schema)
    contract_validator = Draft202012Validator(contract_schema)
    proposal_validator = Draft202012Validator(proposal_schema)
    context_validator = Draft202012Validator(context_schema)
    adapter_validator = Draft202012Validator(adapter_schema)
    contract_validator.validate(contract)
    adapter_validator.validate(adapter)

    if contract["generator_version"] != GENERATOR_VERSION:
        raise SystemExit("ML generator implementation/contract version drift")
    if adapter["domain_id"] != ns_crucible["domain_id"]:
        raise SystemExit("NS generator adapter domain drift")
    if (
        adapter["hypothesis_set_id"]
        != ns_crucible["primary_hypothesis_set"]["hypothesis_set_id"]
    ):
        raise SystemExit("NS generator hypothesis-set drift")
    track_ids = [
        item["track_id"] for item in ns_crucible["primary_hypothesis_set"]["tracks"]
    ]
    if adapter["allowed_target_hypotheses"] != track_ids:
        raise SystemExit("NS generator tracks do not exactly match Crucible tracks")
    barrier_ids = [item["barrier_id"] for item in barriers["barriers"]]
    if barrier_ids != ns_crucible["constraint_bindings"]["proof_barrier_ids"]:
        raise SystemExit("NS proof-barrier registry drift")
    if not adapter["context_policy"]["must_include_all_registered_proof_barrier_ids"]:
        raise SystemExit("NS generator adapter must require every proof barrier")
    if not adapter["context_policy"]["target_tracks_must_match_ns_crucible_adapter"]:
        raise SystemExit("NS generator adapter must require the complete track set")

    for field in (
        "generator_is_ns_evidence",
        "generator_can_discharge_proof_barrier",
        "generator_can_change_claim_level",
        "generator_can_select_track_winner",
        "accepted_candidate_is_ns_result",
    ):
        if adapter["epistemic_authority"][field]:
            raise SystemExit(f"NS generator exceeds authority: {field}")
    if adapter["candidate_intake"]["initial_claim_level"] != "exploratory":
        raise SystemExit("ML candidates must enter as exploratory")

    required_invariants = {
        "model_output_is_not_candidate",
        "valid_json_is_not_valid_research_candidate",
        "generator_output_is_not_domain_evidence",
        "generator_output_is_not_claim_promotion",
        "generator_self_assessment_is_not_evidence_status",
        "invalid_generation_attempt_is_not_mathematical_failure",
        "accepted_candidate_is_not_surviving_candidate",
    }
    if not required_invariants.issubset(set(agents["research_invariants"])):
        raise SystemExit("AGENTS contract is missing ML generator invariants")

    for path, key, value, label in [
        (("authority",), "model_output_is_candidate", True, "model output becomes candidate automatically"),
        (("authority",), "generator_output_is_domain_evidence", True, "generator becomes domain evidence"),
        (("authority",), "generator_may_promote_claim", True, "generator gains claim promotion"),
        (("authority",), "generator_may_assign_proof_status", True, "generator gains proof authority"),
        (("authority",), "generator_may_select_winner", True, "generator gains winner selection"),
        (("proposal_policy",), "model_supplied_claim_level_forbidden", False, "model may set claim level"),
        (("proposal_policy",), "direct_analogy_intake_forbidden", False, "generator bypasses analogy firewall"),
        (("attempt_journal",), "rejected_attempts_recorded", False, "rejected attempts disappear"),
        (("commit_policy",), "model_cannot_directly_commit_candidate", False, "model directly commits candidates"),
    ]:
        mutated = copy.deepcopy(contract)
        mutated[path[0]][key] = value
        reject(contract_validator, mutated, label)

    hostile = {
        "proposal_id": "hostile",
        "target_hypothesis": track_ids[0],
        "precise_statement": "test statement",
        "motivation": "test motivation",
        "assumptions": ["one assumption"],
        "claimed_dependencies": [],
        "suggested_tests": ["one test"],
        "possible_failure_modes": ["one failure mode"],
        "analogy_sources": [],
        "parent_candidate_ids": [],
        "generator_notes": "exploratory only",
        "claim_level": "public_solution_claim",
    }
    reject(proposal_validator, hostile, "proposal schema accepts claim_level")

    overlong = dict(hostile)
    del overlong["claim_level"]
    overlong["proposal_id"] = "x" * 129
    reject(proposal_validator, overlong, "proposal schema accepts filesystem-sized ID")

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    theorem_ids = {item["theorem_id"] for item in theorem_registry["theorems"]}
    analogy_ids = {item["analogy_id"] for item in analogies["records"]}

    with tempfile.TemporaryDirectory(prefix="qsol-ml-generator-") as tmp:
        ledger = ContentAddressedLedger(Path(tmp) / "ledger")
        replay = ledger.verify()
        journal = GeneratorAttemptJournal(Path(tmp) / "generation-journal")
        context = GeneratorContextPacket(
            domain_id=adapter["domain_id"],
            hypothesis_set_id=adapter["hypothesis_set_id"],
            target_hypotheses=tuple(adapter["allowed_target_hypotheses"]),
            theorem_ids=tuple(sorted(theorem_ids)),
            proof_barrier_ids=tuple(barrier_ids),
            frontier_candidate_ids=(),
            failure_lessons=(),
            permitted_analogy_ids=tuple(sorted(analogy_ids)),
            ledger_event_count=replay.event_count,
            ledger_head_event_sha256=replay.head_event_sha256,
            source_commit=commit,
            task="generate one precise exploratory NS mechanism candidate",
        )
        context_validator.validate(context.to_dict())
        proposal = {
            "proposal_id": "validator-ml-candidate",
            "target_hypothesis": track_ids[0],
            "precise_statement": "Investigate a scale-local estimate whose failure modes are explicit.",
            "motivation": "Exercise the generator airlock without asserting a theorem.",
            "assumptions": ["smooth solution on its interval of existence"],
            "claimed_dependencies": [],
            "suggested_tests": ["check scaling", "check proof barriers"],
            "possible_failure_modes": ["estimate may be circular"],
            "analogy_sources": [],
            "parent_candidate_ids": [],
            "generator_notes": "exploratory validator fixture",
        }
        proposal_validator.validate(proposal)
        output = json.dumps(proposal, sort_keys=True, separators=(",", ":"))
        gate = GeneratorAirlock(
            domain_id=adapter["domain_id"],
            hypothesis_set_id=adapter["hypothesis_set_id"],
            allowed_target_hypotheses=set(track_ids),
            required_proof_barrier_ids=set(barrier_ids),
            known_candidate_ids=set(),
            known_theorem_ids=theorem_ids,
            known_analogy_ids=analogy_ids,
            journal=journal,
        )
        decision = gate.run(
            backend=DeterministicFixtureBackend(output),
            context=context,
            attempt_id="validator-attempt",
            prompt_template_sha256=hashlib.sha256(b"validator-template-v1").hexdigest(),
            recorded_at_utc=stamp,
        )
        if not decision.accepted or decision.candidate is None:
            raise SystemExit(f"valid fixture was rejected: {decision.rejection_reasons}")
        if decision.candidate.claim_level != "exploratory":
            raise SystemExit("generator promoted an accepted candidate")
        if ledger.verify().event_count != 0:
            raise SystemExit(
                "model-facing airlock mutated Crucible ledger before explicit commit"
            )
        gate.commit_candidate(
            decision,
            ledger=ledger,
            actor="validate_ml_generator.py",
            source_commit=commit,
            recorded_at_utc=stamp,
        )
        if ledger.verify().event_count != 1:
            raise SystemExit(
                "explicit accepted-candidate commit did not enter Crucible ledger"
            )
        count, _head = journal.verify()
        if count != 1:
            raise SystemExit("generation attempt was not durably journaled")
        if any(
            gate.authority_snapshot()[key]
            for key in (
                "domain_evidence",
                "claim_promotion",
                "proof_status_assignment",
                "winner_selection",
                "confidence_as_authority",
                "direct_analogy_bypass",
                "rejection_is_mathematical_failure",
            )
        ):
            raise SystemExit("generator authority snapshot exceeds proposal/intake scope")

    print(
        "ML generator validation: PASS "
        f"(version={GENERATOR_VERSION}, tracks={len(track_ids)}, theorems={len(theorem_ids)}, "
        f"barriers={len(barrier_ids)}, provider_neutral=true)"
    )


if __name__ == "__main__":
    main()
