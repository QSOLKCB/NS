# SPDX-License-Identifier: Apache-2.0
"""Hardening helpers for candidate-transform provenance and untrusted text."""
from __future__ import annotations
import hashlib, re
from .transform_common import TransformError, digest

_SOLVED=re.compile(r"\bsolved\b",re.IGNORECASE)
_FORBIDDEN=("public_solution_claim","solution established","millennium problem resolved","proof complete","solves clay")

def untrusted_text_reason(value:str)->str|None:
    try:value.encode("utf-8","strict")
    except UnicodeEncodeError:return "invalid_utf8"
    lower=value.lower()
    if any(x in lower for x in _FORBIDDEN) or _SOLVED.search(value):return "forbidden_authority_language"
    return None

def raw_output_sha256(raw:str)->tuple[str,bool]:
    try:data=raw.encode("utf-8","strict");return hashlib.sha256(data).hexdigest(),True
    except UnicodeEncodeError:data=raw.encode("utf-8","surrogatepass");return hashlib.sha256(data).hexdigest(),False

def verify_recorded_decision(*,journal,decision,context)->None:
    if journal.attempt_object_sha256(decision.attempt_id)!=decision.attempt_object_sha256:raise TransformError("decision does not match recorded transform attempt")
    recorded=journal.attempt_payload(decision.attempt_id)
    expected={"attempt_id":decision.attempt_id,"accepted":True,"rejection_reasons":[],"context_sha256":decision.context_sha256,"raw_output_sha256":decision.raw_output_sha256,"receipt_sha256":decision.receipt_sha256,"candidate":decision.candidate.to_dict(),"candidate_object_id_if_committed":decision.candidate_object_id_if_committed}
    for key,value in expected.items():
        if recorded.get(key)!=value:raise TransformError("decision candidate/receipt does not match recorded transform attempt")
    r=recorded.get("receipt")
    if not isinstance(r,dict) or digest(r)!=decision.receipt_sha256:raise TransformError("recorded transform receipt digest mismatch")
    if r.get("attempt_id")!=decision.attempt_id or r.get("context_sha256")!=decision.context_sha256 or r.get("operator")!=context.operator:raise TransformError("recorded transform receipt does not match commit context")
    if r.get("parent_candidate_ids")!=[p.candidate.candidate_id for p in context.parents] or r.get("parent_candidate_object_ids")!=[p.candidate_object_id for p in context.parents]:raise TransformError("recorded transform receipt parentage mismatch")
