# SPDX-License-Identifier: Apache-2.0
"""Sealed holdout materialization and adversarial-evaluation state for Crucible."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .engine import canonical_json_bytes, canonical_sha256
from .models import Candidate

HOLDOUT_VERSION = "0.1.0"

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_ASSURANCE = {"not_run", "passed", "failed", "blocked"}
_BRIDGE = {"not_run", "satisfied", "unsatisfied", "not_applicable"}
_ACTIONS = {
    "seal_holdout",
    "materialize_holdout",
    "release_holdout",
    "record_assurance",
}


class HoldoutError(ValueError):
    """Raised when sealed-holdout invariants would be violated."""


class HoldoutLeakageError(HoldoutError):
    """Raised when sealed material is detected in a pre-release context."""


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HoldoutError(f"{field} must be a non-empty string")
    return value


def _require_safe_id(value: Any, field: str) -> str:
    text = _require_text(value, field)
    if not _SAFE_ID.fullmatch(text):
        raise HoldoutError(f"{field} contains unsupported characters")
    return text


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise HoldoutError(f"{field} must be a lowercase 64-hex SHA-256 digest")
    return value


def _require_commit(value: Any) -> str:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise HoldoutError("source_commit must be an exact lowercase 40-hex commit SHA")
    return value


def _require_utc(value: Any, field: str) -> str:
    text = _require_text(value, field)
    parse = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        dt = datetime.fromisoformat(parse)
    except ValueError as exc:
        raise HoldoutError(f"{field} must be ISO-8601") from exc
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise HoldoutError(f"{field} must carry UTC timezone information")
    return text


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _string_scalars(value: Any) -> tuple[str, ...]:
    scalars: list[str] = []
    if isinstance(value, str):
        scalars.append(value)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                scalars.append(key)
            scalars.extend(_string_scalars(item))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            scalars.extend(_string_scalars(item))
    return tuple(scalars)


@dataclass(frozen=True)
class HoldoutManifest:
    holdout_id: str
    domain_id: str
    evaluator_id: str
    evaluator_version: str
    payload_sha256: str
    payload_size_bytes: int
    leakage_sentinel_sha256: tuple[str, ...]
    negative_control_ids: tuple[str, ...]
    source_commit: str
    sealed_at_utc: str
    payload_media_type: str = "application/json"

    def validate(self) -> None:
        for field in ("holdout_id", "domain_id", "evaluator_id", "evaluator_version"):
            _require_safe_id(getattr(self, field), field)
        _require_sha256(self.payload_sha256, "payload_sha256")
        if (
            not isinstance(self.payload_size_bytes, int)
            or isinstance(self.payload_size_bytes, bool)
            or self.payload_size_bytes <= 0
        ):
            raise HoldoutError("payload_size_bytes must be a positive integer")
        if len(self.leakage_sentinel_sha256) != len(set(self.leakage_sentinel_sha256)):
            raise HoldoutError("leakage sentinel hashes must be unique")
        for digest in self.leakage_sentinel_sha256:
            _require_sha256(digest, "leakage_sentinel_sha256")
        if len(self.negative_control_ids) != len(set(self.negative_control_ids)):
            raise HoldoutError("negative_control_ids must be unique")
        for control in self.negative_control_ids:
            _require_safe_id(control, "negative_control_ids")
        _require_commit(self.source_commit)
        _require_utc(self.sealed_at_utc, "sealed_at_utc")
        if self.payload_media_type != "application/json":
            raise HoldoutError("v0.1 holdout payloads must use application/json")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["leakage_sentinel_sha256"] = list(self.leakage_sentinel_sha256)
        value["negative_control_ids"] = list(self.negative_control_ids)
        return value


@dataclass(frozen=True)
class HoldoutMaterialization:
    materialization_id: str
    holdout_id: str
    candidate_id: str
    candidate_snapshot_sha256: str
    crucible_ledger_head_sha256: str
    holdout_payload_sha256: str
    actor: str
    source_commit: str
    materialized_at_utc: str

    def validate(self) -> None:
        for field in ("materialization_id", "holdout_id", "candidate_id"):
            _require_safe_id(getattr(self, field), field)
        _require_sha256(self.candidate_snapshot_sha256, "candidate_snapshot_sha256")
        _require_sha256(self.crucible_ledger_head_sha256, "crucible_ledger_head_sha256")
        _require_sha256(self.holdout_payload_sha256, "holdout_payload_sha256")
        _require_text(self.actor, "actor")
        _require_commit(self.source_commit)
        _require_utc(self.materialized_at_utc, "materialized_at_utc")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class HoldoutReleaseReceipt:
    release_id: str
    materialization_id: str
    holdout_id: str
    candidate_id: str
    candidate_snapshot_sha256: str
    holdout_payload_sha256: str
    actor: str
    source_commit: str
    released_at_utc: str

    def validate(self) -> None:
        for field in ("release_id", "materialization_id", "holdout_id", "candidate_id"):
            _require_safe_id(getattr(self, field), field)
        _require_sha256(self.candidate_snapshot_sha256, "candidate_snapshot_sha256")
        _require_sha256(self.holdout_payload_sha256, "holdout_payload_sha256")
        _require_text(self.actor, "actor")
        _require_commit(self.source_commit)
        _require_utc(self.released_at_utc, "released_at_utc")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class AssuranceState:
    assurance_id: str
    candidate_id: str
    schema_admission: str = "not_run"
    deterministic_replay: str = "not_run"
    cross_method_challenge: str = "not_run"
    holdout_evaluation: str = "not_run"
    continuum_bridge: str = "not_run"
    holdout_release_id: str | None = None
    negative_controls: tuple[tuple[str, str], ...] = ()
    notes: str = ""

    def validate(self) -> None:
        _require_safe_id(self.assurance_id, "assurance_id")
        _require_safe_id(self.candidate_id, "candidate_id")
        for field in (
            "schema_admission",
            "deterministic_replay",
            "cross_method_challenge",
            "holdout_evaluation",
        ):
            if getattr(self, field) not in _ASSURANCE:
                raise HoldoutError(f"{field} has invalid assurance state")
        if self.continuum_bridge not in _BRIDGE:
            raise HoldoutError("continuum_bridge has invalid assurance state")
        if self.holdout_evaluation != "not_run":
            if self.holdout_release_id is None:
                raise HoldoutError("holdout evaluation requires an auditable holdout release")
            _require_safe_id(self.holdout_release_id, "holdout_release_id")
            if not self.negative_controls:
                raise HoldoutError("holdout evaluation requires at least one negative control result")
        elif self.holdout_release_id is not None:
            raise HoldoutError("holdout_release_id requires holdout evaluation to be run")
        names = [name for name, _ in self.negative_controls]
        if len(names) != len(set(names)):
            raise HoldoutError("negative control IDs must be unique")
        for name, status in self.negative_controls:
            _require_safe_id(name, "negative_control_id")
            if status not in {"passed", "failed"}:
                raise HoldoutError("negative control status must be passed or failed")
        if self.holdout_evaluation == "passed" and any(
            status != "passed" for _, status in self.negative_controls
        ):
            raise HoldoutError("holdout evaluation cannot pass while a negative control fails")
        if not isinstance(self.notes, str):
            raise HoldoutError("notes must be a string")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "assurance_id": self.assurance_id,
            "candidate_id": self.candidate_id,
            "schema_admission": self.schema_admission,
            "deterministic_replay": self.deterministic_replay,
            "cross_method_challenge": self.cross_method_challenge,
            "holdout_evaluation": self.holdout_evaluation,
            "continuum_bridge": self.continuum_bridge,
            "holdout_release_id": self.holdout_release_id,
            "negative_controls": {name: status for name, status in self.negative_controls},
            "notes": self.notes,
            "authority": {
                "assurance_state_is_domain_truth": False,
                "holdout_success_promotes_claim": False,
                "replay_is_continuum_proof": False,
                "cross_method_agreement_is_continuum_proof": False,
                "formal_or_schema_assurance_is_physical_truth": False,
            },
        }


class SealedHoldoutStore:
    """Filesystem-backed sealed holdout store with an append-only release journal.

    Sealing is an orchestration boundary, not a cryptographic confidentiality
    boundary against a process or operator with direct filesystem access.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.root / ".writer.lock"
        self._lock_handle = self.lock_path.open("a+b")
        self._closed = False
        try:
            fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._lock_handle.close()
            self._closed = True
            raise HoldoutError("sealed holdout store v0.1 is single-writer per root") from exc

        self.payloads = self.root / "sealed" / "sha256"
        self.manifests = self.root / "manifests"
        self.materializations = self.root / "materializations"
        self.releases = self.root / "releases"
        self.assurance = self.root / "assurance"
        self.log = self.root / "holdout.jsonl"
        for path in (
            self.payloads,
            self.manifests,
            self.materializations,
            self.releases,
            self.assurance,
        ):
            path.mkdir(parents=True, exist_ok=True)

        try:
            self.verify()
        except Exception:
            self.close()
            raise

    def _require_open(self) -> None:
        if self._closed:
            raise HoldoutError("sealed holdout store is closed")

    def __enter__(self) -> "SealedHoldoutStore":
        self._require_open()
        return self

    def __exit__(self, *args: Any) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if self._closed:
            return
        try:
            fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._lock_handle.close()
            self._closed = True

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _immutable_write(self, path: Path, data: bytes) -> None:
        self._require_open()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != data:
                raise HoldoutError(f"immutable holdout artifact differs: {path.name}")
            return
        temp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{_hash_bytes(data)[:12]}")
        temp.unlink(missing_ok=True)
        try:
            with temp.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def _journal_events(self) -> list[dict[str, Any]]:
        self._require_open()
        if not self.log.exists():
            return []
        events: list[dict[str, Any]] = []
        previous: str | None = None
        for sequence, line in enumerate(self.log.read_bytes().splitlines(keepends=True), start=1):
            if not line.endswith(b"\n"):
                raise HoldoutError("holdout journal event lacks canonical terminal newline")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HoldoutError("invalid holdout journal JSON") from exc
            if canonical_json_bytes(event) != line:
                raise HoldoutError("holdout journal event is not canonical JSON")
            if event.get("holdout_version") != HOLDOUT_VERSION:
                raise HoldoutError("holdout journal version mismatch")
            if event.get("sequence") != sequence or event.get("previous_event_sha256") != previous:
                raise HoldoutError("holdout journal chain is broken")
            recorded = _require_sha256(event.get("event_sha256"), "event_sha256")
            core = dict(event)
            del core["event_sha256"]
            if _hash_bytes(canonical_json_bytes(core)) != recorded:
                raise HoldoutError("holdout journal event hash mismatch")
            if event.get("action") not in _ACTIONS:
                raise HoldoutError("unsupported holdout journal action")
            _require_text(event.get("actor"), "actor")
            _require_commit(event.get("source_commit"))
            _require_utc(event.get("recorded_at_utc"), "recorded_at_utc")
            _require_safe_id(event.get("logical_id"), "logical_id")
            _require_sha256(event.get("artifact_sha256"), "artifact_sha256")
            previous = recorded
            events.append(event)
        return events

    def _scan_journal(self) -> tuple[int, str | None]:
        events = self._journal_events()
        return len(events), events[-1]["event_sha256"] if events else None

    def _append_event(
        self,
        *,
        action: str,
        logical_id: str,
        artifact_sha256: str,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        self._require_open()
        if action not in _ACTIONS:
            raise HoldoutError("unsupported holdout journal action")
        _require_safe_id(logical_id, "logical_id")
        _require_sha256(artifact_sha256, "artifact_sha256")
        _require_text(actor, "actor")
        _require_commit(source_commit)
        _require_utc(recorded_at_utc, "recorded_at_utc")
        count, head = self._scan_journal()
        core = {
            "holdout_version": HOLDOUT_VERSION,
            "sequence": count + 1,
            "previous_event_sha256": head,
            "action": action,
            "logical_id": logical_id,
            "artifact_sha256": artifact_sha256,
            "actor": actor,
            "source_commit": source_commit,
            "recorded_at_utc": recorded_at_utc,
        }
        event = dict(core)
        event["event_sha256"] = _hash_bytes(canonical_json_bytes(core))
        with self.log.open("ab") as handle:
            handle.write(canonical_json_bytes(event))
            handle.flush()
            os.fsync(handle.fileno())
        return event["event_sha256"]

    def _manifest_path(self, holdout_id: str) -> Path:
        return self.manifests / f"{_require_safe_id(holdout_id, 'holdout_id')}.json"

    def _payload_path(self, payload_sha256: str) -> Path:
        digest = _require_sha256(payload_sha256, "payload_sha256")
        return self.payloads / digest[:2] / f"{digest[2:]}.json"

    @staticmethod
    def _json_files(root: Path) -> set[Path]:
        return {path for path in root.rglob("*.json") if path.is_file()}

    def _load_manifest_unchecked(self, holdout_id: str) -> HoldoutManifest:
        path = self._manifest_path(holdout_id)
        if not path.is_file():
            raise HoldoutError(f"unknown holdout: {holdout_id}")
        raw_bytes = path.read_bytes()
        try:
            raw = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise HoldoutError("holdout manifest is invalid JSON") from exc
        if canonical_json_bytes(raw) != raw_bytes:
            raise HoldoutError("holdout manifest is not canonical JSON")
        try:
            manifest = HoldoutManifest(
                **{
                    **raw,
                    "leakage_sentinel_sha256": tuple(raw["leakage_sentinel_sha256"]),
                    "negative_control_ids": tuple(raw["negative_control_ids"]),
                }
            )
        except (KeyError, TypeError) as exc:
            raise HoldoutError("holdout manifest structure is invalid") from exc
        manifest.validate()
        payload_path = self._payload_path(manifest.payload_sha256)
        if not payload_path.is_file() or _hash_bytes(payload_path.read_bytes()) != manifest.payload_sha256:
            raise HoldoutError("sealed holdout payload is missing or hash-mismatched")
        if payload_path.stat().st_size != manifest.payload_size_bytes:
            raise HoldoutError("sealed holdout payload size does not match manifest")
        return manifest

    def _load_payload(self, manifest: HoldoutManifest) -> dict[str, Any]:
        raw_bytes = self._payload_path(manifest.payload_sha256).read_bytes()
        if _hash_bytes(raw_bytes) != manifest.payload_sha256:
            raise HoldoutError("sealed holdout payload hash mismatch")
        try:
            payload = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise HoldoutError("sealed holdout payload is invalid JSON") from exc
        if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw_bytes:
            raise HoldoutError("sealed holdout payload must be a canonical JSON object")
        return payload

    def _load_materialization_unchecked(self, materialization_id: str) -> HoldoutMaterialization:
        path = self.materializations / f"{_require_safe_id(materialization_id, 'materialization_id')}.json"
        if not path.is_file():
            raise HoldoutError("unknown holdout materialization")
        raw_bytes = path.read_bytes()
        try:
            raw = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise HoldoutError("materialization is invalid JSON") from exc
        if canonical_json_bytes(raw) != raw_bytes:
            raise HoldoutError("materialization is not canonical JSON")
        try:
            value = HoldoutMaterialization(**raw)
        except TypeError as exc:
            raise HoldoutError("materialization structure is invalid") from exc
        value.validate()
        return value

    def _load_release_unchecked(self, release_id: str) -> HoldoutReleaseReceipt:
        path = self.releases / f"{_require_safe_id(release_id, 'release_id')}.json"
        if not path.is_file():
            raise HoldoutError("unknown holdout release")
        raw_bytes = path.read_bytes()
        try:
            raw = json.loads(raw_bytes)
        except json.JSONDecodeError as exc:
            raise HoldoutError("release receipt is invalid JSON") from exc
        if canonical_json_bytes(raw) != raw_bytes:
            raise HoldoutError("release receipt is not canonical JSON")
        try:
            value = HoldoutReleaseReceipt(**raw)
        except TypeError as exc:
            raise HoldoutError("release receipt structure is invalid") from exc
        value.validate()
        return value

    def _released_holdout_ids(self, events: list[dict[str, Any]] | None = None) -> set[str]:
        source = events if events is not None else self._journal_events()
        return {
            self._load_release_unchecked(str(event["logical_id"])).holdout_id
            for event in source
            if event["action"] == "release_holdout"
        }

    def _released_materialization_ids(self, events: list[dict[str, Any]] | None = None) -> set[str]:
        source = events if events is not None else self._journal_events()
        return {
            self._load_release_unchecked(str(event["logical_id"])).materialization_id
            for event in source
            if event["action"] == "release_holdout"
        }

    def manifest(self, holdout_id: str) -> HoldoutManifest:
        self._require_open()
        self.verify()
        return self._load_manifest_unchecked(holdout_id)

    def seal(
        self,
        *,
        holdout_id: str,
        domain_id: str,
        evaluator_id: str,
        evaluator_version: str,
        payload: Mapping[str, Any],
        negative_control_ids: tuple[str, ...],
        actor: str,
        source_commit: str,
        sealed_at_utc: str,
    ) -> HoldoutManifest:
        self._require_open()
        self.verify()
        _require_safe_id(holdout_id, "holdout_id")
        if self._manifest_path(holdout_id).exists():
            raise HoldoutError("holdout_id is immutable and already sealed")
        if not isinstance(payload, Mapping):
            raise HoldoutError("holdout payload must be a JSON object")
        payload_value = dict(payload)
        sentinels = payload_value.get("leakage_sentinels", [])
        if not isinstance(sentinels, list) or any(
            not isinstance(item, str) or not item for item in sentinels
        ):
            raise HoldoutError("leakage_sentinels must be a list of non-empty strings")
        if len(sentinels) != len(set(sentinels)):
            raise HoldoutError("leakage_sentinels must be unique")
        payload_bytes = canonical_json_bytes(payload_value)
        payload_digest = _hash_bytes(payload_bytes)
        payload_path = self._payload_path(payload_digest)
        self._immutable_write(payload_path, payload_bytes)
        manifest = HoldoutManifest(
            holdout_id=holdout_id,
            domain_id=domain_id,
            evaluator_id=evaluator_id,
            evaluator_version=evaluator_version,
            payload_sha256=payload_digest,
            payload_size_bytes=len(payload_bytes),
            leakage_sentinel_sha256=tuple(
                _hash_bytes(item.encode("utf-8")) for item in sentinels
            ),
            negative_control_ids=tuple(negative_control_ids),
            source_commit=_require_commit(source_commit),
            sealed_at_utc=_require_utc(sealed_at_utc, "sealed_at_utc"),
        )
        manifest_bytes = canonical_json_bytes(manifest.to_dict())
        self._immutable_write(self._manifest_path(holdout_id), manifest_bytes)
        self._append_event(
            action="seal_holdout",
            logical_id=holdout_id,
            artifact_sha256=_hash_bytes(manifest_bytes),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=sealed_at_utc,
        )
        return manifest

    @staticmethod
    def _require_frozen_candidate(candidate: Candidate) -> str:
        candidate.validate()
        if candidate.status != "frozen" or candidate.frozen is not True:
            raise HoldoutError("holdout materialization requires status=frozen and frozen=true")
        return canonical_sha256(candidate.to_dict())

    def assert_context_clean(self, context: Any, *, holdout_id: str) -> None:
        self._require_open()
        self.verify()
        manifest = self._load_manifest_unchecked(holdout_id)
        payload = self._load_payload(manifest)
        sentinels = payload.get("leakage_sentinels", [])
        if not isinstance(sentinels, list) or any(not isinstance(item, str) or not item for item in sentinels):
            raise HoldoutError("sealed payload leakage_sentinels are invalid")
        sentinel_hashes = tuple(_hash_bytes(item.encode("utf-8")) for item in sentinels)
        if sentinel_hashes != manifest.leakage_sentinel_sha256:
            raise HoldoutError("sealed payload leakage sentinels do not match manifest")
        for scalar in _string_scalars(context):
            if manifest.payload_sha256 in scalar or any(sentinel in scalar for sentinel in sentinels):
                raise HoldoutLeakageError(
                    "pre-release context contains sealed holdout material or its payload identity"
                )

    def materialize(
        self,
        *,
        materialization_id: str,
        holdout_id: str,
        candidate: Candidate,
        crucible_ledger_head_sha256: str,
        pre_release_context: Any,
        actor: str,
        source_commit: str,
        materialized_at_utc: str,
    ) -> HoldoutMaterialization:
        self._require_open()
        replay = self.verify()
        events = self._journal_events()
        manifest = self._load_manifest_unchecked(holdout_id)
        if holdout_id in self._released_holdout_ids(events):
            raise HoldoutError("holdout has already been released; new materializations are forbidden")
        candidate_digest = self._require_frozen_candidate(candidate)
        if candidate.domain_id != manifest.domain_id:
            raise HoldoutError("candidate domain does not match holdout domain")
        _require_sha256(crucible_ledger_head_sha256, "crucible_ledger_head_sha256")
        if replay["head_event_sha256"] is None and self.log.exists():
            raise HoldoutError("holdout journal head is unavailable")
        self.assert_context_clean(pre_release_context, holdout_id=holdout_id)
        materialization = HoldoutMaterialization(
            materialization_id=materialization_id,
            holdout_id=holdout_id,
            candidate_id=candidate.candidate_id,
            candidate_snapshot_sha256=candidate_digest,
            crucible_ledger_head_sha256=crucible_ledger_head_sha256,
            holdout_payload_sha256=manifest.payload_sha256,
            actor=actor,
            source_commit=source_commit,
            materialized_at_utc=materialized_at_utc,
        )
        data = canonical_json_bytes(materialization.to_dict())
        path = self.materializations / f"{_require_safe_id(materialization_id, 'materialization_id')}.json"
        if path.exists():
            raise HoldoutError("materialization_id is immutable and already recorded")
        self._immutable_write(path, data)
        self._append_event(
            action="materialize_holdout",
            logical_id=materialization_id,
            artifact_sha256=_hash_bytes(data),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=materialized_at_utc,
        )
        return materialization

    def release(
        self,
        *,
        release_id: str,
        materialization_id: str,
        candidate: Candidate,
        actor: str,
        source_commit: str,
        released_at_utc: str,
    ) -> tuple[dict[str, Any], HoldoutReleaseReceipt]:
        self._require_open()
        self.verify()
        events = self._journal_events()
        if materialization_id in self._released_materialization_ids(events):
            raise HoldoutError("holdout materialization has already been released")
        materialization = self._load_materialization_unchecked(materialization_id)
        candidate_digest = self._require_frozen_candidate(candidate)
        if candidate.candidate_id != materialization.candidate_id:
            raise HoldoutError("release candidate does not match materialization")
        if candidate_digest != materialization.candidate_snapshot_sha256:
            raise HoldoutError("candidate changed after holdout materialization")
        manifest = self._load_manifest_unchecked(materialization.holdout_id)
        if manifest.payload_sha256 != materialization.holdout_payload_sha256:
            raise HoldoutError("holdout payload identity drifted after materialization")
        payload = self._load_payload(manifest)
        receipt = HoldoutReleaseReceipt(
            release_id=release_id,
            materialization_id=materialization_id,
            holdout_id=materialization.holdout_id,
            candidate_id=candidate.candidate_id,
            candidate_snapshot_sha256=candidate_digest,
            holdout_payload_sha256=manifest.payload_sha256,
            actor=actor,
            source_commit=source_commit,
            released_at_utc=released_at_utc,
        )
        data = canonical_json_bytes(receipt.to_dict())
        receipt_path = self.releases / f"{_require_safe_id(release_id, 'release_id')}.json"
        if receipt_path.exists():
            raise HoldoutError("release_id is immutable and already recorded")
        self._immutable_write(receipt_path, data)
        self._append_event(
            action="release_holdout",
            logical_id=release_id,
            artifact_sha256=_hash_bytes(data),
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=released_at_utc,
        )
        return payload, receipt

    def record_assurance(
        self,
        state: AssuranceState,
        *,
        manifest: HoldoutManifest | None,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        self._require_open()
        self.verify()
        state.validate()
        if state.holdout_evaluation != "not_run":
            assert state.holdout_release_id is not None
            release = self._load_release_unchecked(state.holdout_release_id)
            if release.candidate_id != state.candidate_id:
                raise HoldoutError("assurance candidate does not match holdout release")
            persisted_manifest = self._load_manifest_unchecked(release.holdout_id)
            if manifest is not None:
                manifest.validate()
                if manifest.to_dict() != persisted_manifest.to_dict():
                    raise HoldoutError("caller-supplied manifest does not match persisted holdout manifest")
            if release.holdout_payload_sha256 != persisted_manifest.payload_sha256:
                raise HoldoutError("assurance release payload identity does not match persisted manifest")
            expected = set(persisted_manifest.negative_control_ids)
            if not expected:
                raise HoldoutError("holdout evaluation requires at least one declared negative control")
            observed = {name for name, _ in state.negative_controls}
            if observed != expected:
                raise HoldoutError(
                    "holdout evaluation must report every declared negative control exactly once"
                )
        data = canonical_json_bytes(state.to_dict())
        path = self.assurance / f"{_require_safe_id(state.assurance_id, 'assurance_id')}.json"
        if path.exists():
            raise HoldoutError("assurance_id is immutable and already recorded")
        self._immutable_write(path, data)
        digest = _hash_bytes(data)
        self._append_event(
            action="record_assurance",
            logical_id=state.assurance_id,
            artifact_sha256=digest,
            actor=actor,
            source_commit=source_commit,
            recorded_at_utc=recorded_at_utc,
        )
        return digest

    def verify(self) -> dict[str, Any]:
        self._require_open()
        events = self._journal_events()
        seen: set[tuple[str, str]] = set()
        expected_manifests: set[Path] = set()
        expected_materializations: set[Path] = set()
        expected_releases: set[Path] = set()
        expected_assurance: set[Path] = set()
        expected_payloads: set[Path] = set()

        for event in events:
            action = str(event["action"])
            logical_id = str(event["logical_id"])
            key = (action, logical_id)
            if key in seen:
                raise HoldoutError("holdout journal reuses an immutable logical ID for the same action")
            seen.add(key)

            if action == "seal_holdout":
                path = self._manifest_path(logical_id)
                expected_manifests.add(path)
            elif action == "materialize_holdout":
                path = self.materializations / f"{logical_id}.json"
                expected_materializations.add(path)
            elif action == "release_holdout":
                path = self.releases / f"{logical_id}.json"
                expected_releases.add(path)
            else:
                path = self.assurance / f"{logical_id}.json"
                expected_assurance.add(path)

            if not path.is_file() or _hash_bytes(path.read_bytes()) != event["artifact_sha256"]:
                raise HoldoutError("holdout journal artifact hash mismatch")

            if action == "seal_holdout":
                manifest = self._load_manifest_unchecked(logical_id)
                expected_payloads.add(self._payload_path(manifest.payload_sha256))
            elif action == "materialize_holdout":
                self._load_materialization_unchecked(logical_id)
            elif action == "release_holdout":
                self._load_release_unchecked(logical_id)
            else:
                try:
                    raw = json.loads(path.read_bytes())
                except json.JSONDecodeError as exc:
                    raise HoldoutError("assurance artifact is invalid JSON") from exc
                if canonical_json_bytes(raw) != path.read_bytes():
                    raise HoldoutError("assurance artifact is not canonical JSON")

        artifact_sets = (
            ("manifest", self._json_files(self.manifests), expected_manifests),
            ("materialization", self._json_files(self.materializations), expected_materializations),
            ("release", self._json_files(self.releases), expected_releases),
            ("assurance", self._json_files(self.assurance), expected_assurance),
            ("sealed payload", self._json_files(self.payloads), expected_payloads),
        )
        for label, actual, expected in artifact_sets:
            if actual != expected:
                extras = sorted(str(path.relative_to(self.root)) for path in actual - expected)
                missing = sorted(str(path.relative_to(self.root)) for path in expected - actual)
                raise HoldoutError(
                    f"holdout journal/artifact reconciliation failed for {label}: "
                    f"orphan={extras}, missing={missing}"
                )

        return {
            "event_count": len(events),
            "head_event_sha256": events[-1]["event_sha256"] if events else None,
            "authority": {
                "sealed_storage_is_cryptographic_confidentiality": False,
                "holdout_success_promotes_claim": False,
                "holdout_success_selects_winner": False,
                "replay_or_assurance_is_continuum_proof": False,
            },
        }
