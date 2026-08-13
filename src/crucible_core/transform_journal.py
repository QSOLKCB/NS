# SPDX-License-Identifier: Apache-2.0
"""Content-addressed single-writer journal for candidate-transform attempts."""
from __future__ import annotations
import fcntl, hashlib, json, os
from pathlib import Path
from typing import Any, Mapping
from .engine import canonical_json_bytes
from .transform_common import TRANSFORM_VERSION, TransformError, commit, safe_id, sha256, utc

class TransformJournalError(TransformError): pass

def _hash(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def _load(data:bytes,label:str)->dict[str,Any]:
    try: value=json.loads(data.decode("utf-8"),parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
    except Exception as exc: raise TransformJournalError(f"invalid {label} JSON") from exc
    if not isinstance(value,dict) or canonical_json_bytes(value)!=data: raise TransformJournalError(f"{label} must be canonical JSON")
    return value

class TransformAttemptJournal:
    def __init__(self,root:Path|str)->None:
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.objects=self.root/"objects"/"sha256"; self.objects.mkdir(parents=True,exist_ok=True)
        self.log=self.root/"transform.jsonl"; self.lock=self.root/".writer.lock"
        self._closed=False; self._fh=self.lock.open("a+b")
        try: fcntl.flock(self._fh.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._fh.close(); self._closed=True; raise TransformJournalError("transform journal v0.1 is single-writer per root") from exc
        self._count=0; self._head=None; self._attempts={}; self._scan()
    def __enter__(self): return self
    def __exit__(self,*args): self.close(); return False
    def close(self):
        if self._closed:return
        try: fcntl.flock(self._fh.fileno(),fcntl.LOCK_UN)
        finally:self._fh.close();self._closed=True
    def __del__(self):
        try:self.close()
        except Exception:pass
    def _path(self,d:str)->Path:
        sha256(d,"attempt object digest"); return self.objects/d[:2]/f"{d[2:]}.json"
    def _store(self,payload:Mapping[str,Any])->str:
        envelope={"transform_version":TRANSFORM_VERSION,"object_type":"transform_attempt","payload":dict(payload)}
        data=canonical_json_bytes(envelope); d=_hash(data); path=self._path(d); path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()!=data: raise TransformJournalError("immutable transform object differs")
            return d
        tmp=path.with_name(f".{path.name}.tmp-{os.getpid()}")
        with tmp.open("xb") as h:h.write(data);h.flush();os.fsync(h.fileno())
        os.replace(tmp,path); return d
    def _verify_object(self,d:str)->None:
        path=self._path(d)
        if not path.is_file() or _hash(path.read_bytes())!=d: raise TransformJournalError("transform object missing or hash-mismatched")
        obj=_load(path.read_bytes(),"transform object")
        if obj.get("transform_version")!=TRANSFORM_VERSION or obj.get("object_type")!="transform_attempt": raise TransformJournalError("transform object version/type mismatch")
        payload=obj.get("payload")
        if not isinstance(payload,dict) or payload.get("parse_status") not in {"not_attempted","not_parsed","parsed"}: raise TransformJournalError("invalid transform attempt payload")
        utc(payload.get("recorded_at_utc"))
    def _scan(self)->None:
        if not self.log.exists(): self._count=0;self._head=None;self._attempts={};return
        previous=None; attempts={}; raw=self.log.read_bytes()
        for seq,line in enumerate(raw.splitlines(keepends=True),1):
            if not line.endswith(b"\n"): raise TransformJournalError("transform event lacks canonical newline")
            e=_load(line,"transform event")
            if e.get("sequence")!=seq or e.get("previous_event_sha256")!=previous: raise TransformJournalError("transform event chain broken")
            if e.get("transform_version")!=TRANSFORM_VERSION or e.get("action")!="record_transform_attempt": raise TransformJournalError("unsupported transform event")
            aid=safe_id(e.get("attempt_id"),"attempt_id"); d=sha256(e.get("attempt_object_sha256"),"attempt_object_sha256")
            if aid in attempts: raise TransformJournalError("duplicate transform attempt_id")
            commit(e.get("source_commit")); utc(e.get("recorded_at_utc"))
            if not isinstance(e.get("actor"),str) or not e["actor"].strip(): raise TransformJournalError("actor is required")
            event_sha=sha256(e.get("event_sha256"),"event_sha256"); core=dict(e); del core["event_sha256"]
            if _hash(canonical_json_bytes(core))!=event_sha: raise TransformJournalError("transform event hash mismatch")
            self._verify_object(d); attempts[aid]=d; previous=event_sha
        self._count=len(attempts); self._head=previous; self._attempts=attempts
    def record(self,*,attempt_id:str,payload:Mapping[str,Any],actor:str,source_commit:str,recorded_at_utc:str)->str:
        if self._closed: raise TransformJournalError("transform journal is closed")
        safe_id(attempt_id,"attempt_id"); commit(source_commit); utc(recorded_at_utc)
        if not isinstance(actor,str) or not actor.strip(): raise TransformJournalError("actor is required")
        if payload.get("parse_status") not in {"not_attempted","not_parsed","parsed"}: raise TransformJournalError("invalid parse_status")
        self._scan()
        if attempt_id in self._attempts: raise TransformJournalError("transform attempt_id already recorded")
        d=self._store(payload); core={"transform_version":TRANSFORM_VERSION,"sequence":self._count+1,"previous_event_sha256":self._head,"action":"record_transform_attempt","attempt_id":attempt_id,"attempt_object_sha256":d,"actor":actor,"source_commit":source_commit,"recorded_at_utc":recorded_at_utc}
        event=dict(core);event["event_sha256"]=_hash(canonical_json_bytes(core))
        with self.log.open("ab") as h:h.write(canonical_json_bytes(event));h.flush();os.fsync(h.fileno())
        self._count+=1;self._head=event["event_sha256"];self._attempts[attempt_id]=d;return d
    def attempt_object_sha256(self,attempt_id:str)->str:
        safe_id(attempt_id,"attempt_id")
        if attempt_id not in self._attempts: raise TransformJournalError("unknown transform attempt")
        return self._attempts[attempt_id]
    def verify(self)->tuple[int,str|None,Mapping[str,str]]: self._scan();return self._count,self._head,dict(self._attempts)
    def authority_snapshot(self)->dict[str,bool]: return {"transform_attempt_is_domain_evidence":False,"transform_attempt_promotes_claim":False,"transform_attempt_selects_winner":False,"transform_attempt_inherits_parent_authority":False}
