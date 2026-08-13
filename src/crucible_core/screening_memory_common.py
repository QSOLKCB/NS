# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for content-addressed similarity-screening memory."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .engine import canonical_json_bytes
from .ledger import LedgerReplay

SCREENING_MEMORY_VERSION = "0.1.0"
OBJECT_TYPES = {"origin_classification","dead_family","similarity_report"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")

class DuplicateMemoryError(ValueError):
    pass

def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def object_id(data: bytes) -> str: return f"sha256:{digest(data)}"
def require_safe_id(value: str, field: str) -> None:
    if not isinstance(value,str) or not SAFE_ID.fullmatch(value): raise DuplicateMemoryError(f"{field} must be a component-safe ID")
def require_object_id(value: str, field: str) -> None:
    if not isinstance(value,str) or not value.startswith("sha256:") or not SHA256.fullmatch(value[7:]): raise DuplicateMemoryError(f"{field} must be sha256:<digest>")
def require_actor(value: str) -> None:
    if not isinstance(value,str) or not value.strip(): raise DuplicateMemoryError("actor must be non-empty")
def require_commit(value: str) -> None:
    if not isinstance(value,str) or not COMMIT.fullmatch(value): raise DuplicateMemoryError("source_commit must be exact lowercase 40-hex")
def require_utc(value: str) -> None:
    if not isinstance(value,str) or not value.endswith("Z"): raise DuplicateMemoryError("recorded_at_utc must be UTC ending in Z")
    try: parsed=datetime.fromisoformat(value[:-1]+"+00:00")
    except ValueError as exc: raise DuplicateMemoryError("recorded_at_utc must be valid ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed): raise DuplicateMemoryError("recorded_at_utc must be UTC")
def validate_ledger_ref(replay: LedgerReplay, object_type: str, logical_id: str, oid: str) -> None:
    if replay.refs.get(f"{object_type}:{logical_id}")!=oid: raise DuplicateMemoryError(f"screening record does not match ledger ref {object_type}:{logical_id}")
def object_path(root: Path, oid: str) -> Path:
    require_object_id(oid,"object_id"); d=oid[7:]; return root/d[:2]/f"{d[2:]}.json"
def ref_path(refs_root: Path, object_type: str, logical_id: str) -> Path:
    if object_type not in OBJECT_TYPES: raise DuplicateMemoryError("unsupported screening object type")
    require_safe_id(logical_id,"logical_id"); return refs_root/object_type/f"{logical_id}.json"
def write_immutable(path: Path, data: bytes, label: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise DuplicateMemoryError(f"immutable {label} differs")
        return
    temp=path.with_name(f".{path.name}.tmp-{os.getpid()}-{digest(data)[:12]}"); temp.unlink(missing_ok=True)
    try:
        with temp.open("xb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp,path)
    finally: temp.unlink(missing_ok=True)
def expected_ref(event: Mapping[str,Any]) -> dict[str,Any]:
    return {"screening_memory_version":SCREENING_MEMORY_VERSION,"object_type":event["object_type"],"logical_id":event["logical_id"],"object_id":event["object_id"],"event_sha256":event["event_sha256"]}
def canonical_load(data: bytes, label: str) -> Any:
    try: value=json.loads(data)
    except json.JSONDecodeError as exc: raise DuplicateMemoryError(f"invalid {label} JSON") from exc
    if canonical_json_bytes(value)!=data: raise DuplicateMemoryError(f"{label} is not canonical JSON")
    return value
