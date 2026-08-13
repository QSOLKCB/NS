# SPDX-License-Identifier: Apache-2.0
"""Shared validation primitives for controlled candidate transforms."""
from __future__ import annotations
import hashlib, re
from datetime import datetime, timezone
from typing import Any
from .engine import canonical_json_bytes
from .ledger import LEDGER_VERSION

TRANSFORM_VERSION="0.1.0"
OPERATORS=("weaken_assumption","repair_scaling_defect","replace_failed_estimate","reverse_track_perspective","adversarial_attack","crossover_survivors")
SAFE_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256=re.compile(r"^[0-9a-f]{64}$")
COMMIT=re.compile(r"^[0-9a-f]{40}$")
UTC_Z=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
FORBIDDEN_AUTHORITY=("public_solution_claim","solution established","millennium problem resolved","proof complete","solves clay")
RESERVED_ASSUMPTION_PREFIXES=("target_track=","transform_","mutation_","analogy_source=","mapping_class=","generator_context_sha256=","generation_attempt_id=")

class TransformError(ValueError): pass

def text(value:Any,field:str)->str:
    if not isinstance(value,str) or not value.strip(): raise TransformError(f"{field} must be a non-empty string")
    return value

def safe_id(value:Any,field:str)->str:
    text(value,field)
    if not SAFE_ID.fullmatch(value): raise TransformError(f"{field} must be a component-safe ID of at most 128 characters")
    return value

def sha256(value:Any,field:str)->str:
    if not isinstance(value,str) or not SHA256.fullmatch(value): raise TransformError(f"{field} must be lowercase 64-hex SHA-256")
    return value

def commit(value:Any)->str:
    if not isinstance(value,str) or not COMMIT.fullmatch(value): raise TransformError("source_commit must be exact lowercase 40-hex")
    return value

def utc(value:Any)->str:
    if not isinstance(value,str) or not UTC_Z.fullmatch(value): raise TransformError("recorded_at_utc must be ISO-8601 UTC ending in Z")
    try: parsed=datetime.fromisoformat(value[:-1]+"+00:00")
    except ValueError as exc: raise TransformError("recorded_at_utc must be valid UTC") from exc
    if parsed.utcoffset()!=timezone.utc.utcoffset(parsed): raise TransformError("recorded_at_utc must carry UTC timezone information")
    return value

def unique_text(values:tuple[str,...],field:str,nonempty:bool=False)->None:
    if nonempty and not values: raise TransformError(f"{field} must be non-empty")
    for v in values: text(v,field)
    if len(values)!=len(set(values)): raise TransformError(f"{field} must contain unique values")

def digest(value:Any)->str: return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
def ledger_object_id(object_type:str,payload:dict[str,Any])->str:
    return "sha256:"+digest({"ledger_version":LEDGER_VERSION,"object_type":object_type,"payload":payload})
def target_track(candidate)->str:
    tracks=[x.split("=",1)[1] for x in candidate.assumptions if x.startswith("target_track=") and "=" in x]
    if len(tracks)!=1 or not tracks[0].strip(): raise TransformError("candidate must declare exactly one target_track before transformation")
    return tracks[0]
def contains_authority(text_value:str)->bool:
    lower=text_value.lower(); return any(x in lower for x in FORBIDDEN_AUTHORITY)
def semantic_assumptions(candidate)->tuple[str,...]:
    return tuple(x for x in candidate.assumptions if not x.startswith(RESERVED_ASSUMPTION_PREFIXES) and x!="cross_domain_transfer_requires_target_domain_validation")
