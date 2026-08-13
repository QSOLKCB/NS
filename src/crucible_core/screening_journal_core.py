# SPDX-License-Identifier: Apache-2.0
"""Single-writer hash-chained journal core for similarity screening."""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Any, Mapping

from .engine import canonical_json_bytes
from .screening_memory_common import (
    SCREENING_MEMORY_VERSION, OBJECT_TYPES, SHA256, DuplicateMemoryError,
    canonical_load, digest, expected_ref, object_id, object_path, ref_path,
    require_actor, require_commit, require_object_id, require_safe_id, require_utc,
    write_immutable,
)
from .similarity_common import DUPLICATE_DETECTOR_VERSION

class ScreeningJournalCore:
    def __init__(self, root: Path|str) -> None:
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.objects_root=self.root/"objects"/"sha256"; self.refs_root=self.root/"refs"; self.log_path=self.root/"screening.jsonl"; self.lock_path=self.root/".writer.lock"
        self.objects_root.mkdir(parents=True,exist_ok=True); self.refs_root.mkdir(parents=True,exist_ok=True)
        self._refs: dict[str,str]={}; self._count=0; self._head: str|None=None; self._closed=False
        self._lock_handle=self.lock_path.open("a+b")
        try: fcntl.flock(self._lock_handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._lock_handle.close(); self._closed=True
            raise DuplicateMemoryError("screening journal v0.1 allows only one writer process per root") from exc
        self._initialize()
    def close(self) -> None:
        if self._closed: return
        try: fcntl.flock(self._lock_handle.fileno(),fcntl.LOCK_UN)
        finally: self._lock_handle.close(); self._closed=True
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): self.close(); return False
    def __del__(self):
        try: self.close()
        except Exception: pass
    def _object_path(self, oid: str) -> Path: return object_path(self.objects_root,oid)
    def _ref_path(self, object_type: str, logical_id: str) -> Path: return ref_path(self.refs_root,object_type,logical_id)
    def _store(self, object_type: str, payload: Mapping[str,Any]) -> str:
        envelope={"screening_memory_version":SCREENING_MEMORY_VERSION,"detector_version":DUPLICATE_DETECTOR_VERSION,"object_type":object_type,"payload":dict(payload)}
        data=canonical_json_bytes(envelope); oid=object_id(data); write_immutable(self._object_path(oid),data,"screening object"); return oid
    def _materialize_ref(self, event: Mapping[str,Any]) -> None:
        write_immutable(self._ref_path(event["object_type"],event["logical_id"]),canonical_json_bytes(expected_ref(event)),"screening ref")
    def _initialize(self) -> None:
        if not self.log_path.exists():
            if any(self.refs_root.rglob("*.json")): raise DuplicateMemoryError("screening refs exist without log")
            self._refs={}; self._count=0; self._head=None; return
        raw=self.log_path.read_bytes(); previous: str|None=None; refs: dict[str,str]={}; expected_paths=set()
        for sequence,line in enumerate(raw.splitlines(keepends=True),start=1):
            if not line.endswith(b"\n"): raise DuplicateMemoryError("screening event lacks canonical newline")
            event=canonical_load(line,"screening event")
            if event.get("sequence")!=sequence or event.get("previous_event_sha256")!=previous: raise DuplicateMemoryError("screening event chain is broken")
            if event.get("screening_memory_version")!=SCREENING_MEMORY_VERSION or event.get("detector_version")!=DUPLICATE_DETECTOR_VERSION: raise DuplicateMemoryError("screening version mismatch")
            if event.get("action")!="bind_screening_object" or event.get("object_type") not in OBJECT_TYPES: raise DuplicateMemoryError("unsupported screening event")
            require_safe_id(event.get("logical_id"),"logical_id"); require_object_id(event.get("object_id"),"object_id"); require_actor(event.get("actor")); require_commit(event.get("source_commit")); require_utc(event.get("recorded_at_utc"))
            event_hash=event.get("event_sha256")
            if not isinstance(event_hash,str) or not SHA256.fullmatch(event_hash): raise DuplicateMemoryError("invalid screening event digest")
            core=dict(event); del core["event_sha256"]
            if digest(canonical_json_bytes(core))!=event_hash: raise DuplicateMemoryError("screening event hash mismatch")
            path=self._object_path(event["object_id"])
            if not path.is_file() or object_id(path.read_bytes())!=event["object_id"]: raise DuplicateMemoryError("screening object missing or mismatched")
            envelope=canonical_load(path.read_bytes(),"screening object")
            if envelope.get("screening_memory_version")!=SCREENING_MEMORY_VERSION or envelope.get("detector_version")!=DUPLICATE_DETECTOR_VERSION or envelope.get("object_type")!=event["object_type"] or not isinstance(envelope.get("payload"),dict): raise DuplicateMemoryError("screening object is invalid")
            key=f"{event['object_type']}:{event['logical_id']}"
            if key in refs and refs[key]!=event["object_id"]: raise DuplicateMemoryError("screening ref rebinding in log")
            rp=self._ref_path(event["object_type"],event["logical_id"]); expected_paths.add(rp)
            if not rp.is_file(): self._materialize_ref(event)
            if canonical_load(rp.read_bytes(),"screening ref")!=expected_ref(event): raise DuplicateMemoryError("screening ref mismatch")
            refs[key]=event["object_id"]; previous=event_hash
        actual={p for p in self.refs_root.rglob("*.json") if p.is_file()}
        if actual!=expected_paths: raise DuplicateMemoryError("screening ref set does not match log")
        self._refs=refs; self._count=len(raw.splitlines()) if raw else 0; self._head=previous
    def _append(self, *, object_type: str, logical_id: str, oid: str, actor: str, source_commit: str, recorded_at_utc: str) -> None:
        if self._closed: raise DuplicateMemoryError("screening journal is closed")
        require_actor(actor); require_commit(source_commit); require_utc(recorded_at_utc); self._initialize()
        key=f"{object_type}:{logical_id}"; existing=self._refs.get(key)
        if existing is not None:
            if existing!=oid: raise DuplicateMemoryError("screening logical ref cannot be rebound")
            return
        core={"screening_memory_version":SCREENING_MEMORY_VERSION,"detector_version":DUPLICATE_DETECTOR_VERSION,"sequence":self._count+1,"previous_event_sha256":self._head,"action":"bind_screening_object","object_type":object_type,"logical_id":logical_id,"object_id":oid,"actor":actor,"source_commit":source_commit,"recorded_at_utc":recorded_at_utc}
        event=dict(core); event["event_sha256"]=digest(canonical_json_bytes(core))
        with self.log_path.open("ab") as handle: handle.write(canonical_json_bytes(event)); handle.flush(); os.fsync(handle.fileno())
        self._materialize_ref(event); self._count+=1; self._head=event["event_sha256"]; self._refs[key]=oid
    def verify(self) -> tuple[int,str|None,Mapping[str,str]]:
        self._initialize(); return self._count,self._head,dict(self._refs)
