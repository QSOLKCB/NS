# SPDX-License-Identifier: Apache-2.0
"""Content-addressed audit memory for duplicate/dead-family screening."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from .duplicate import DUPLICATE_DETECTOR_VERSION, CandidateOriginClassification, DeadFamilyRecord, SimilarityReport
from .engine import canonical_json_bytes
from .ledger import LedgerReplay

SCREENING_MEMORY_VERSION = "0.1.0"
_OBJECT_TYPES = {"origin_classification", "dead_family", "similarity_report"}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

class DuplicateMemoryError(ValueError):
    pass

def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _require_safe_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise DuplicateMemoryError(f"{field} must be a component-safe ID")

def _require_object_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:") or not _SHA256.fullmatch(value[7:]):
        raise DuplicateMemoryError(f"{field} must be sha256:<digest>")

def _object_id(data: bytes) -> str:
    return f"sha256:{_digest(data)}"

def _validate_ledger_ref(replay: LedgerReplay, object_type: str, logical_id: str, object_id: str) -> None:
    if replay.refs.get(f"{object_type}:{logical_id}") != object_id:
        raise DuplicateMemoryError(f"screening record does not match ledger ref {object_type}:{logical_id}")

class DuplicateScreeningJournal:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.objects_root = self.root / "objects" / "sha256"
        self.refs_root = self.root / "refs"
        self.log_path = self.root / "screening.jsonl"
        self.objects_root.mkdir(parents=True, exist_ok=True)
        self.refs_root.mkdir(parents=True, exist_ok=True)
        self._refs: dict[str, str] = {}
        self._count = 0
        self._head: str | None = None
        self._initialize()

    def _object_path(self, object_id: str) -> Path:
        _require_object_id(object_id, "object_id")
        digest = object_id[7:]
        return self.objects_root / digest[:2] / f"{digest[2:]}.json"

    def _ref_path(self, object_type: str, logical_id: str) -> Path:
        if object_type not in _OBJECT_TYPES:
            raise DuplicateMemoryError("unsupported screening object type")
        _require_safe_id(logical_id, "logical_id")
        return self.refs_root / object_type / f"{logical_id}.json"

    def _write_immutable(self, path: Path, data: bytes, label: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != data:
                raise DuplicateMemoryError(f"immutable {label} differs")
            return
        temp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{_digest(data)[:12]}")
        temp.unlink(missing_ok=True)
        try:
            with temp.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def _store(self, object_type: str, payload: Mapping[str, Any]) -> str:
        envelope = {"screening_memory_version": SCREENING_MEMORY_VERSION, "detector_version": DUPLICATE_DETECTOR_VERSION, "object_type": object_type, "payload": dict(payload)}
        data = canonical_json_bytes(envelope)
        object_id = _object_id(data)
        self._write_immutable(self._object_path(object_id), data, "screening object")
        return object_id

    def _append(self, *, object_type: str, logical_id: str, object_id: str) -> None:
        key = f"{object_type}:{logical_id}"
        existing = self._refs.get(key)
        if existing is not None:
            if existing != object_id:
                raise DuplicateMemoryError("screening logical ref cannot be rebound")
            return
        core = {"screening_memory_version": SCREENING_MEMORY_VERSION, "detector_version": DUPLICATE_DETECTOR_VERSION, "sequence": self._count + 1, "previous_event_sha256": self._head, "action": "bind_screening_object", "object_type": object_type, "logical_id": logical_id, "object_id": object_id}
        event = dict(core)
        event["event_sha256"] = _digest(canonical_json_bytes(core))
        with self.log_path.open("ab") as handle:
            handle.write(canonical_json_bytes(event))
            handle.flush()
            os.fsync(handle.fileno())
        ref = {"screening_memory_version": SCREENING_MEMORY_VERSION, "object_type": object_type, "logical_id": logical_id, "object_id": object_id, "event_sha256": event["event_sha256"]}
        self._write_immutable(self._ref_path(object_type, logical_id), canonical_json_bytes(ref), "screening ref")
        self._count += 1
        self._head = event["event_sha256"]
        self._refs[key] = object_id

    def _initialize(self) -> None:
        if not self.log_path.exists():
            if any(self.refs_root.rglob("*.json")):
                raise DuplicateMemoryError("screening refs exist without log")
            return
        raw = self.log_path.read_bytes()
        previous: str | None = None
        refs: dict[str, str] = {}
        for sequence, line in enumerate(raw.splitlines(keepends=True), start=1):
            if not line.endswith(b"\n"):
                raise DuplicateMemoryError("screening event lacks canonical newline")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DuplicateMemoryError("invalid screening event JSON") from exc
            if canonical_json_bytes(event) != line:
                raise DuplicateMemoryError("screening event is not canonical JSON")
            if event.get("sequence") != sequence or event.get("previous_event_sha256") != previous:
                raise DuplicateMemoryError("screening event chain is broken")
            if event.get("screening_memory_version") != SCREENING_MEMORY_VERSION or event.get("detector_version") != DUPLICATE_DETECTOR_VERSION:
                raise DuplicateMemoryError("screening version mismatch")
            if event.get("action") != "bind_screening_object" or event.get("object_type") not in _OBJECT_TYPES:
                raise DuplicateMemoryError("unsupported screening event")
            _require_safe_id(event.get("logical_id"), "logical_id")
            _require_object_id(event.get("object_id"), "object_id")
            event_hash = event.get("event_sha256")
            if not isinstance(event_hash, str) or not _SHA256.fullmatch(event_hash):
                raise DuplicateMemoryError("invalid screening event digest")
            core = dict(event); del core["event_sha256"]
            if _digest(canonical_json_bytes(core)) != event_hash:
                raise DuplicateMemoryError("screening event hash mismatch")
            path = self._object_path(event["object_id"])
            if not path.is_file() or _object_id(path.read_bytes()) != event["object_id"]:
                raise DuplicateMemoryError("screening object missing or mismatched")
            envelope = json.loads(path.read_bytes())
            if canonical_json_bytes(envelope) != path.read_bytes() or envelope.get("object_type") != event["object_type"]:
                raise DuplicateMemoryError("screening object is invalid")
            key = f"{event['object_type']}:{event['logical_id']}"
            if key in refs and refs[key] != event["object_id"]:
                raise DuplicateMemoryError("screening ref rebinding in log")
            ref_path = self._ref_path(event["object_type"], event["logical_id"])
            if not ref_path.is_file():
                raise DuplicateMemoryError("screening ref missing")
            ref = json.loads(ref_path.read_bytes())
            expected_ref = {"screening_memory_version": SCREENING_MEMORY_VERSION, "object_type": event["object_type"], "logical_id": event["logical_id"], "object_id": event["object_id"], "event_sha256": event_hash}
            if canonical_json_bytes(ref) != ref_path.read_bytes() or ref != expected_ref:
                raise DuplicateMemoryError("screening ref mismatch")
            refs[key] = event["object_id"]
            previous = event_hash
        expected = {self._ref_path(*key.split(":", 1)) for key in refs}
        actual = {path for path in self.refs_root.rglob("*.json") if path.is_file()}
        if actual != expected:
            raise DuplicateMemoryError("screening ref set does not match log")
        self._refs = refs
        self._count = len(raw.splitlines()) if raw else 0
        self._head = previous

    def record_origin(self, origin: CandidateOriginClassification, *, ledger_replay: LedgerReplay) -> str:
        origin.validate()
        _validate_ledger_ref(ledger_replay, "candidate", origin.candidate_id, origin.candidate_object_id)
        object_id = self._store("origin_classification", origin.to_dict())
        self._append(object_type="origin_classification", logical_id=origin.origin_id, object_id=object_id)
        return object_id

    def record_dead_family(self, family: DeadFamilyRecord, *, ledger_replay: LedgerReplay) -> str:
        family.validate()
        _validate_ledger_ref(ledger_replay, "candidate", family.failed_candidate_id, family.failed_candidate_object_id)
        failure_objects = {oid for key, oid in ledger_replay.refs.items() if key.startswith("failure:")}
        if not set(family.failure_object_ids).issubset(failure_objects):
            raise DuplicateMemoryError("dead-family failure object is not in verified ledger")
        object_id = self._store("dead_family", family.to_dict())
        self._append(object_type="dead_family", logical_id=family.family_id, object_id=object_id)
        return object_id

    def record_report(self, report: SimilarityReport, *, ledger_replay: LedgerReplay) -> str:
        report.validate()
        _validate_ledger_ref(ledger_replay, "candidate", report.candidate_id, report.candidate_object_id)
        for candidate_id, object_id in zip(report.matched_candidate_ids, report.matched_candidate_object_ids, strict=True):
            _validate_ledger_ref(ledger_replay, "candidate", candidate_id, object_id)
        if report.origin_classification_object_id is not None:
            origin_objects = {oid for key, oid in self._refs.items() if key.startswith("origin_classification:")}
            if report.origin_classification_object_id not in origin_objects:
                raise DuplicateMemoryError("report origin object is not in screening history")
        dead_objects = {oid for key, oid in self._refs.items() if key.startswith("dead_family:")}
        if not set(report.matched_dead_family_object_ids).issubset(dead_objects):
            raise DuplicateMemoryError("report references unknown dead-family object")
        object_id = self._store("similarity_report", report.to_dict())
        self._append(object_type="similarity_report", logical_id=report.report_id, object_id=object_id)
        return object_id

    def verify(self) -> tuple[int, str | None, Mapping[str, str]]:
        fresh = DuplicateScreeningJournal(self.root)
        return fresh._count, fresh._head, dict(fresh._refs)

    def authority_snapshot(self) -> dict[str, bool]:
        return {"screening_memory_is_domain_evidence": False, "screening_memory_establishes_equivalence": False, "screening_memory_proves_falsehood": False, "screening_memory_may_reject_candidate": False, "screening_memory_may_promote_claim": False}
