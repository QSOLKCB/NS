# SPDX-License-Identifier: Apache-2.0
"""Content-addressed persistent memory for QSOL Crucible.

The ledger persists what the research process recorded. Persistence and replay do
not grant truth, evidence, claim-promotion, or winner-selection authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .analogy import AnalogyRecord
from .engine import canonical_json_bytes
from .models import Candidate, EvidenceRecord, FailureRecord

LEDGER_VERSION = "0.1.0"
_OBJECT_TYPES = {
    "candidate",
    "evidence",
    "failure",
    "analogy",
    "transfer_ticket",
    "snapshot",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class LedgerError(ValueError):
    """Raised when persistence or replay would violate ledger invariants."""


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LedgerError(f"{field} must be a non-empty string")


def _require_safe_id(value: str, field: str) -> None:
    _require_text(value, field)
    if not _SAFE_ID.fullmatch(value):
        raise LedgerError(f"{field} contains unsupported characters")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise LedgerError(f"{field} must be a lowercase 64-hex SHA-256 digest")


def _require_source_commit(value: str) -> None:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise LedgerError("source_commit must be an exact lowercase 40-hex commit SHA")


def _require_utc_timestamp(value: str) -> None:
    _require_text(value, "recorded_at_utc")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise LedgerError("recorded_at_utc must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise LedgerError("recorded_at_utc must carry UTC timezone information")


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object_id(digest: str) -> str:
    _require_sha256(digest, "digest")
    return f"sha256:{digest}"


def _digest_from_object_id(object_id: str) -> str:
    _require_text(object_id, "object_id")
    if not object_id.startswith("sha256:"):
        raise LedgerError("object_id must use sha256:<digest>")
    digest = object_id.split(":", 1)[1]
    _require_sha256(digest, "object_id digest")
    return digest


@dataclass(frozen=True)
class TransferTicket:
    """Immutable intake receipt for an analogy-derived candidate."""

    ticket_id: str
    analogy_id: str
    mapping_class: str
    source_sha256: str
    target_domain: str
    firewall_decision: str
    candidate_object_id: str
    target_domain_validation_required: bool = True
    initial_claim_level: str = "exploratory"

    def validate(self) -> None:
        for field in ("ticket_id", "analogy_id", "mapping_class", "target_domain"):
            _require_safe_id(getattr(self, field), field)
        _require_sha256(self.source_sha256, "source_sha256")
        _digest_from_object_id(self.candidate_object_id)
        if self.firewall_decision != "candidate_generation_authorized":
            raise LedgerError("transfer ticket may only record an authorized candidate-generation decision")
        if self.target_domain_validation_required is not True:
            raise LedgerError("transfer ticket must require target-domain validation")
        if self.initial_claim_level != "exploratory":
            raise LedgerError("analogy-derived transfer ticket must begin exploratory")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class LedgerReplay:
    event_count: int
    head_event_sha256: str | None
    refs: Mapping[str, str]

    def authority_snapshot(self) -> dict[str, bool]:
        return {
            "persisted_state_is_truth": False,
            "replay_promotes_claim": False,
            "replay_selects_winner": False,
            "ledger_object_is_domain_evidence_by_persistence": False,
        }


class ContentAddressedLedger:
    """Filesystem-backed append-only Crucible memory.

    v0.1 is intentionally single-writer. The event log is authoritative; ref
    files are immutable navigation bindings and must agree with replay.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.objects_root = self.root / "objects" / "sha256"
        self.refs_root = self.root / "refs"
        self.log_path = self.root / "ledger.jsonl"
        self.objects_root.mkdir(parents=True, exist_ok=True)
        self.refs_root.mkdir(parents=True, exist_ok=True)

    def _object_path(self, object_id: str) -> Path:
        digest = _digest_from_object_id(object_id)
        return self.objects_root / digest[:2] / f"{digest[2:]}.json"

    def _ref_path(self, object_type: str, logical_id: str) -> Path:
        if object_type not in _OBJECT_TYPES:
            raise LedgerError("unsupported object_type")
        _require_safe_id(logical_id, "logical_id")
        return self.refs_root / object_type / f"{logical_id}.json"

    def _write_immutable(self, path: Path, data: bytes, *, label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as handle:
                handle.write(data)
        except FileExistsError:
            if path.read_bytes() != data:
                raise LedgerError(f"immutable {label} already exists with different content")

    def _store_envelope(self, object_type: str, payload: Mapping[str, Any]) -> str:
        if object_type not in _OBJECT_TYPES:
            raise LedgerError("unsupported object_type")
        envelope = {
            "ledger_version": LEDGER_VERSION,
            "object_type": object_type,
            "payload": dict(payload),
        }
        data = canonical_json_bytes(envelope)
        object_id = _object_id(_digest_bytes(data))
        self._write_immutable(self._object_path(object_id), data, label="object")
        return object_id

    def _read_object(self, object_id: str) -> dict[str, Any]:
        path = self._object_path(object_id)
        if not path.is_file():
            raise LedgerError(f"missing ledger object: {object_id}")
        data = path.read_bytes()
        digest = _digest_from_object_id(object_id)
        if _digest_bytes(data) != digest:
            raise LedgerError(f"ledger object hash mismatch: {object_id}")
        try:
            value = json.loads(data)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"ledger object is not valid JSON: {object_id}") from exc
        if canonical_json_bytes(value) != data:
            raise LedgerError(f"ledger object is not canonical JSON: {object_id}")
        if value.get("ledger_version") != LEDGER_VERSION:
            raise LedgerError("ledger object version mismatch")
        if value.get("object_type") not in _OBJECT_TYPES:
            raise LedgerError("ledger object has unsupported type")
        if not isinstance(value.get("payload"), dict):
            raise LedgerError("ledger object payload must be an object")
        return value

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        events: list[dict[str, Any]] = []
        previous: str | None = None
        for index, raw_line in enumerate(self.log_path.read_bytes().splitlines(), start=1):
            if not raw_line:
                raise LedgerError("ledger contains an empty event line")
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"invalid ledger event JSON at line {index}") from exc
            if not isinstance(event, dict):
                raise LedgerError("ledger event must be an object")
            recorded_hash = event.get("event_sha256")
            _require_sha256(recorded_hash, "event_sha256")
            core = dict(event)
            del core["event_sha256"]
            expected = _digest_bytes(canonical_json_bytes(core))
            if recorded_hash != expected:
                raise LedgerError(f"ledger event hash mismatch at sequence {index}")
            if event.get("sequence") != index:
                raise LedgerError("ledger event sequence is not contiguous")
            if event.get("previous_event_sha256") != previous:
                raise LedgerError("ledger event hash chain is broken")
            if event.get("ledger_version") != LEDGER_VERSION:
                raise LedgerError("ledger event version mismatch")
            _require_source_commit(event.get("source_commit"))
            _require_utc_timestamp(event.get("recorded_at_utc"))
            self._read_object(event.get("object_id"))
            previous = recorded_hash
            events.append(event)
        return events

    def _append_event(
        self,
        *,
        object_type: str,
        object_id: str,
        logical_id: str,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if object_type not in _OBJECT_TYPES:
            raise LedgerError("unsupported object_type")
        _require_safe_id(logical_id, "logical_id")
        _require_text(actor, "actor")
        _require_source_commit(source_commit)
        _require_utc_timestamp(recorded_at_utc)
        self._read_object(object_id)
        events = self._read_events()
        previous = events[-1]["event_sha256"] if events else None
        core = {
            "ledger_version": LEDGER_VERSION,
            "sequence": len(events) + 1,
            "previous_event_sha256": previous,
            "action": "bind_object",
            "object_type": object_type,
            "object_id": object_id,
            "logical_id": logical_id,
            "actor": actor,
            "source_commit": source_commit,
            "recorded_at_utc": recorded_at_utc,
            "metadata": dict(metadata or {}),
        }
        event = dict(core)
        event["event_sha256"] = _digest_bytes(canonical_json_bytes(core))
        self.root.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("ab") as handle:
            handle.write(canonical_json_bytes(event))
        return event

    def put_object(
        self,
        *,
        object_type: str,
        logical_id: str,
        payload: Mapping[str, Any],
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Persist an immutable object and bind its immutable logical ref."""
        if object_type not in _OBJECT_TYPES:
            raise LedgerError("unsupported object_type")
        _require_safe_id(logical_id, "logical_id")
        object_id = self._store_envelope(object_type, payload)
        ref_path = self._ref_path(object_type, logical_id)
        if ref_path.exists():
            try:
                existing = json.loads(ref_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise LedgerError("existing ref is invalid JSON") from exc
            if existing.get("object_id") != object_id:
                raise LedgerError("logical ref is immutable and cannot be rebound")
            self.verify()
            return object_id

        event = self._append_event(
            object_type=object_type,
            object_id=object_id,
            logical_id=logical_id,
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
            metadata=metadata,
        )
        ref = {
            "ledger_version": LEDGER_VERSION,
            "object_type": object_type,
            "logical_id": logical_id,
            "object_id": object_id,
            "event_sha256": event["event_sha256"],
        }
        self._write_immutable(ref_path, canonical_json_bytes(ref), label="ref")
        return object_id

    def persist_candidate(
        self,
        candidate: Candidate,
        *,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        candidate.validate()
        return self.put_object(
            object_type="candidate",
            logical_id=candidate.candidate_id,
            payload=candidate.to_dict(),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def persist_evidence(
        self,
        evidence: EvidenceRecord,
        *,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        evidence.validate()
        return self.put_object(
            object_type="evidence",
            logical_id=evidence.evidence_id,
            payload=evidence.to_dict(),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def persist_failure(
        self,
        failure: FailureRecord,
        *,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        failure.validate()
        return self.put_object(
            object_type="failure",
            logical_id=failure.failure_id,
            payload=failure.to_dict(),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def persist_analogy(
        self,
        analogy: AnalogyRecord,
        *,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        analogy.validate()
        return self.put_object(
            object_type="analogy",
            logical_id=analogy.analogy_id,
            payload=analogy.to_dict(),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def persist_transfer_ticket(
        self,
        ticket: TransferTicket,
        *,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        ticket.validate()
        candidate = self._read_object(ticket.candidate_object_id)
        if candidate["object_type"] != "candidate":
            raise LedgerError("transfer ticket candidate_object_id must reference a candidate object")
        payload = candidate["payload"]
        if payload.get("domain_id") != ticket.target_domain:
            raise LedgerError("transfer ticket target domain does not match candidate")
        if payload.get("claim_level") != "exploratory":
            raise LedgerError("transfer ticket candidate must be exploratory at intake")
        return self.put_object(
            object_type="transfer_ticket",
            logical_id=ticket.ticket_id,
            payload=ticket.to_dict(),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def snapshot(
        self,
        *,
        snapshot_id: str,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        replay = self.verify()
        payload = {
            "refs": dict(sorted(replay.refs.items())),
            "event_count_before_snapshot": replay.event_count,
            "head_event_sha256_before_snapshot": replay.head_event_sha256,
            "authority": replay.authority_snapshot(),
        }
        return self.put_object(
            object_type="snapshot",
            logical_id=snapshot_id,
            payload=payload,
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )

    def verify(self) -> LedgerReplay:
        """Replay and verify the complete event chain, objects, and immutable refs."""
        events = self._read_events()
        refs: dict[str, str] = {}
        for event in events:
            key = f"{event['object_type']}:{event['logical_id']}"
            if key in refs and refs[key] != event["object_id"]:
                raise LedgerError("event log attempts to rebind an immutable logical ref")
            refs[key] = event["object_id"]
            ref_path = self._ref_path(event["object_type"], event["logical_id"])
            if not ref_path.is_file():
                raise LedgerError(f"missing immutable ref for event: {key}")
            ref_bytes = ref_path.read_bytes()
            try:
                ref = json.loads(ref_bytes)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"invalid ref JSON: {key}") from exc
            if canonical_json_bytes(ref) != ref_bytes:
                raise LedgerError(f"ref is not canonical JSON: {key}")
            expected = {
                "ledger_version": LEDGER_VERSION,
                "object_type": event["object_type"],
                "logical_id": event["logical_id"],
                "object_id": event["object_id"],
                "event_sha256": event["event_sha256"],
            }
            if ref != expected:
                raise LedgerError(f"ref does not match authoritative event: {key}")
        head = events[-1]["event_sha256"] if events else None
        return LedgerReplay(event_count=len(events), head_event_sha256=head, refs=refs)

    def authority_snapshot(self) -> dict[str, bool]:
        return LedgerReplay(0, None, {}).authority_snapshot()
