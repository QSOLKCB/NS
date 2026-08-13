#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the content-addressed Crucible ledger and its authority boundaries."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from crucible_core import (
    AnalogyFirewall,
    AnalogyRecord,
    ContentAddressedLedger,
    LEDGER_VERSION,
    LedgerError,
    TransferTicket,
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
    raise SystemExit(f"Crucible ledger schema regression: forbidden mutation accepted: {label}")


def make_record(raw: dict) -> AnalogyRecord:
    return AnalogyRecord(
        analogy_id=raw["analogy_id"],
        source_domain=raw["source_domain"],
        target_domain=raw["target_domain"],
        mapping_class=raw["mapping_class"],
        shared_structure=raw["shared_structure"],
        assumptions=tuple(raw["assumptions"]),
        known_differences=tuple(raw["known_differences"]),
        allowed_uses=tuple(raw["allowed_uses"]),
        forbidden_inferences=tuple(raw["forbidden_inferences"]),
        provenance_ref=raw["provenance_ref"],
    )


def main() -> None:
    contract = load(RESEARCH / "crucible_ledger_contract.json")
    contract_schema = load(RESEARCH / "schemas/crucible_ledger_contract.schema.json")
    event_schema = load(RESEARCH / "schemas/crucible_ledger_event.schema.json")
    ticket_schema = load(RESEARCH / "schemas/crucible_transfer_ticket.schema.json")
    transfer_registry = load(RESEARCH / "cross_domain_transfer_registry.json")
    ns_transfer = load(RESEARCH / "ns_cross_domain_transfer_adapter.json")
    agents = load(ROOT / "AGENTS.md")

    for schema in (contract_schema, event_schema, ticket_schema):
        Draft202012Validator.check_schema(schema)
    contract_validator = Draft202012Validator(contract_schema)
    event_validator = Draft202012Validator(event_schema)
    ticket_validator = Draft202012Validator(ticket_schema)
    contract_validator.validate(contract)

    if contract["ledger_version"] != LEDGER_VERSION:
        raise SystemExit("Crucible ledger implementation/contract version drift")
    if contract["authority"]["persisted_state_is_truth"]:
        raise SystemExit("persistent storage may not become truth authority")
    if contract["authority"]["ledger_may_promote_claim"]:
        raise SystemExit("ledger may not promote claims")
    if contract["transfer_ticket_policy"]["candidate_claim_level_at_intake"] != "exploratory":
        raise SystemExit("transfer tickets must preserve exploratory intake")
    if contract["transfer_ticket_policy"]["ticket_is_domain_evidence"]:
        raise SystemExit("transfer tickets may not become domain evidence")

    required_invariants = {
        "persisted_state_is_not_truth",
        "ledger_replay_is_not_claim_promotion",
        "content_addressing_is_not_mathematical_validation",
        "mutable_history_is_not_research_provenance",
        "transfer_ticket_is_not_domain_evidence",
    }
    if not required_invariants.issubset(set(agents["research_invariants"])):
        raise SystemExit("AGENTS contract is missing Crucible ledger invariants")

    for mutation, label in [
        (("object_store", "objects_immutable", False), "object immutability disabled"),
        (("object_store", "deletion_api_exposed", True), "ledger deletion API enabled"),
        (("ref_policy", "logical_ref_rebinding_forbidden", False), "ref rebinding enabled"),
        (("event_log", "append_only", False), "append-only event log disabled"),
        (("event_log", "sha256_hash_chained", False), "event hash chain disabled"),
        (("replay_policy", "replay_may_promote_claim", True), "replay granted claim promotion"),
        (("replay_policy", "replay_may_define_truth", True), "replay granted truth authority"),
        (("authority", "persisted_state_is_truth", True), "persistence granted truth authority"),
        (("authority", "persistence_creates_domain_evidence", True), "persistence creates evidence"),
        (("transfer_ticket_policy", "ticket_is_domain_evidence", True), "transfer ticket becomes evidence"),
    ]:
        mutated = copy.deepcopy(contract)
        section, key, value = mutation
        mutated[section][key] = value
        reject(contract_validator, mutated, label)

    eligible_id = ns_transfer["eligible_registry_ids"][0]
    raw_record = next(item for item in transfer_registry["records"] if item["analogy_id"] == eligible_id)
    record = make_record(raw_record)
    firewall = AnalogyFirewall(target_domain=ns_transfer["target_domain"])
    firewall.register(record)
    candidate = firewall.issue_candidate(
        analogy_id=eligible_id,
        candidate_id="ledger-validator-candidate",
        hypothesis_set_id="NS_PRIMARY_COMPETITION",
        hypothesis="cross-domain suggestion retained only as an exploratory target-domain candidate",
        generation_method="validate_crucible_ledger.py",
    )

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with tempfile.TemporaryDirectory(prefix="qsol-crucible-ledger-") as tmp:
        ledger = ContentAddressedLedger(Path(tmp) / "ledger")
        analogy_object_id = ledger.persist_analogy(
            record, actor="validate_crucible_ledger.py", source_commit=commit, recorded_at_utc=stamp
        )
        candidate_object_id = ledger.persist_candidate(
            candidate, actor="validate_crucible_ledger.py", source_commit=commit, recorded_at_utc=stamp
        )
        ticket = TransferTicket(
            ticket_id="validator-transfer-ticket",
            analogy_id=eligible_id,
            mapping_class=record.mapping_class,
            source_sha256=transfer_registry["source_material"]["sha256"],
            target_domain=record.target_domain,
            firewall_decision="candidate_generation_authorized",
            candidate_object_id=candidate_object_id,
        )
        ticket_object_id = ledger.persist_transfer_ticket(
            ticket, actor="validate_crucible_ledger.py", source_commit=commit, recorded_at_utc=stamp
        )
        snapshot_object_id = ledger.snapshot(
            snapshot_id="validator-snapshot",
            actor="validate_crucible_ledger.py",
            source_commit=commit,
            recorded_at_utc=stamp,
        )
        replay = ledger.verify()
        if replay.event_count != 4:
            raise SystemExit("ledger replay did not recover all persisted objects")
        if any(replay.authority_snapshot().values()):
            raise SystemExit("ledger replay authority exceeds persistence scope")
        if len({analogy_object_id, candidate_object_id, ticket_object_id, snapshot_object_id}) != 4:
            raise SystemExit("distinct ledger objects unexpectedly share identities")

        for line in ledger.log_path.read_text(encoding="utf-8").splitlines():
            event_validator.validate(json.loads(line))
        ticket_payload = ledger._read_object(ticket_object_id)["payload"]
        ticket_validator.validate(ticket_payload)

        try:
            ledger.put_object(
                object_type="candidate",
                logical_id=candidate.candidate_id,
                payload={**candidate.to_dict(), "hypothesis": "mutated"},
                actor="validate_crucible_ledger.py",
                source_commit=commit,
                recorded_at_utc=stamp,
            )
        except LedgerError:
            pass
        else:
            raise SystemExit("ledger allowed immutable candidate ref rebinding")

        tampered_root = Path(tmp) / "tampered"
        shutil.copytree(ledger.root, tampered_root)
        tampered = ContentAddressedLedger(tampered_root)
        object_path = tampered._object_path(candidate_object_id)
        object_path.write_text("{}\n", encoding="utf-8")
        try:
            tampered.verify()
        except LedgerError:
            pass
        else:
            raise SystemExit("ledger replay accepted a tampered content-addressed object")

    print(
        "Crucible ledger validation: PASS "
        f"(version={LEDGER_VERSION}, object_types={len(contract['object_store']['object_types'])}, "
        "hash_chain=sha256, authority=persistence_only)"
    )


if __name__ == "__main__":
    main()
