# SPDX-License-Identifier: Apache-2.0
"""Validation and construction policy for controlled candidate transforms."""
from __future__ import annotations
import json
from typing import Any
from .ledger import LedgerReplay
from .models import Candidate
from .transform_common import TRANSFORM_VERSION, TransformError, digest, ledger_object_id, safe_id, semantic_assumptions
from .transform_hardening import untrusted_text_reason
from .transform_models import TransformBackend, TransformContextPacket, TransformProposal

REQUIRED={"proposal_id","target_hypothesis","precise_statement","assumptions","claimed_dependencies","suggested_tests","possible_failure_modes","parent_assumptions_removed","addressed_failure_ids","operator_notes"}
FORBIDDEN={"claim_level","claim_status","evidence_status","proof_status","proved","solves_clay","winner","confidence","confidence_score","truth_probability"}
CONTEXT_OWNED={"operator","parent_candidate_ids","parent_candidate_object_ids","generation_method","status","frozen"}
LISTS=("assumptions","claimed_dependencies","suggested_tests","possible_failure_modes","parent_assumptions_removed","addressed_failure_ids")
TEXTS=("proposal_id","target_hypothesis","precise_statement","operator_notes")

def validate_context(context:TransformContextPacket,replay:LedgerReplay,*,domain_id:str,hypothesis_set_id:str,allowed:frozenset[str],barriers:frozenset[str],known:frozenset[str],frontier:frozenset[str],theorems:frozenset[str])->None:
    context.validate()
    if context.domain_id!=domain_id or context.hypothesis_set_id!=hypothesis_set_id: raise TransformError("context targets wrong domain or hypothesis set")
    if context.target_hypothesis not in allowed: raise TransformError("context target hypothesis is not adapter-approved")
    if set(context.proof_barrier_ids)!=set(barriers): raise TransformError("context proof barriers must exactly match adapter-bound barriers")
    if set(context.theorem_ids)-theorems: raise TransformError("context contains unknown theorem IDs")
    if set(context.frontier_candidate_ids)!=set(frontier): raise TransformError("context survivor frontier must exactly match engine snapshot")
    if any(p.candidate.candidate_id not in known for p in context.parents): raise TransformError("context contains unknown parent candidate")
    if replay.event_count!=context.ledger_event_count or replay.head_event_sha256!=context.ledger_head_event_sha256: raise TransformError("context ledger identity is stale or mismatched")
    for p in context.parents:
        if replay.refs.get(f"candidate:{p.candidate.candidate_id}")!=p.candidate_object_id: raise TransformError("parent candidate does not match verified Crucible Ledger ref")
    for f in context.failures:
        if replay.refs.get(f"failure:{f.failure.failure_id}")!=f.failure_object_id: raise TransformError("failure does not match verified Crucible Ledger ref")

def parse_proposal(raw:str)->tuple[TransformProposal|None,tuple[str,...],str]:
    try:value=json.loads(raw,parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
    except Exception:return None,("invalid_json",),"not_parsed"
    if not isinstance(value,dict):return None,("proposal_not_object",),"parsed"
    keys=set(value);reasons=[]
    if keys&FORBIDDEN:reasons.append("forbidden_authority_field")
    if keys&CONTEXT_OWNED:reasons.append("context_owned_field")
    if keys!=REQUIRED:reasons.append("schema_failure")
    if reasons:return None,tuple(sorted(set(reasons))),"parsed"
    if any(not isinstance(value[k],list) or any(not isinstance(x,str) for x in value[k]) for k in LISTS):return None,("schema_failure",),"parsed"
    if any(not isinstance(value[k],str) for k in TEXTS):return None,("schema_failure",),"parsed"
    supplied=[value[k] for k in TEXTS]+[x for k in LISTS for x in value[k]]
    text_reasons={r for x in supplied if (r:=untrusted_text_reason(x)) is not None}
    if text_reasons:return None,tuple(sorted(text_reasons)),"parsed"
    try:
        p=TransformProposal(value["proposal_id"],value["target_hypothesis"],value["precise_statement"],tuple(value["assumptions"]),tuple(value["claimed_dependencies"]),tuple(value["suggested_tests"]),tuple(value["possible_failure_modes"]),tuple(value["parent_assumptions_removed"]),tuple(value["addressed_failure_ids"]),value["operator_notes"]);p.validate();return p,(),"parsed"
    except TransformError as exc:
        if "authority language" in str(exc):return None,("forbidden_authority_language",),"parsed"
        if "engine-owned provenance" in str(exc):return None,("reserved_assumption",),"parsed"
        if "valid UTF-8" in str(exc):return None,("invalid_utf8",),"parsed"
        return None,("schema_failure",),"parsed"

def proposal_reasons(p:TransformProposal,context:TransformContextPacket,*,known:frozenset[str],theorems:frozenset[str])->tuple[str,...]:
    reasons=[]
    if p.target_hypothesis!=context.target_hypothesis:reasons.append("unknown_hypothesis")
    if p.proposal_id in known or p.proposal_id in {x.candidate.candidate_id for x in context.parents}:reasons.append("duplicate_candidate_id")
    deps=set(p.claimed_dependencies)
    if deps-theorems:reasons.append("unknown_theorem_dependency")
    if deps-set(context.theorem_ids):reasons.append("theorem_dependency_not_in_context")
    known_failures={f.failure.failure_id for f in context.failures}
    if set(p.addressed_failure_ids)-known_failures:reasons.append("unknown_failure_reference")
    parent_assumptions=set().union(*(set(semantic_assumptions(x.candidate)) for x in context.parents))
    if set(p.parent_assumptions_removed)-parent_assumptions or set(p.parent_assumptions_removed)&set(p.assumptions):reasons.append("invalid_operator_semantics")
    if context.operator=="weaken_assumption" and not p.parent_assumptions_removed:reasons.append("invalid_operator_semantics")
    if context.operator=="replace_failed_estimate" and not p.addressed_failure_ids:reasons.append("invalid_operator_semantics")
    return tuple(sorted(set(reasons)))

def receipt(*,attempt_id:str,context:TransformContextPacket|None,context_sha:str,backend:TransformBackend,prompt_sha:str,raw_sha:str,proposal:TransformProposal|None,accepted:bool,reasons:tuple[str,...])->dict[str,Any]:
    return {"transform_version":TRANSFORM_VERSION,"attempt_id":attempt_id,"operator":context.operator if context else None,"context_sha256":context_sha,"parent_candidate_ids":[p.candidate.candidate_id for p in context.parents] if context else [],"parent_candidate_object_ids":[p.candidate_object_id for p in context.parents] if context else [],"backend_id":backend.backend_id,"model_id":backend.model_id,"prompt_template_sha256":prompt_sha,"raw_output_sha256":raw_sha,"proposal_id":proposal.proposal_id if proposal else None,"accepted":accepted,"rejection_reasons":list(reasons)}

def build_candidate(*,proposal:TransformProposal,context:TransformContextPacket,backend:TransformBackend,attempt_id:str,context_sha:str,prompt_sha:str,raw_sha:str,receipt_sha:str,domain_id:str,hypothesis_set_id:str)->tuple[Candidate,str]:
    prov=(f"target_track={context.target_hypothesis}",f"transform_operator={context.operator}",f"transform_context_sha256={context_sha}",f"transform_attempt_id={attempt_id}",f"transform_receipt_sha256={receipt_sha}",f"transform_prompt_template_sha256={prompt_sha}",f"transform_raw_output_sha256={raw_sha}",*(f"transform_parent_object={p.candidate.candidate_id}:{p.candidate_object_id}" for p in context.parents),*(f"transform_addressed_failure_id={x}" for x in proposal.addressed_failure_ids))
    c=Candidate(candidate_id=proposal.proposal_id,domain_id=domain_id,hypothesis_set_id=hypothesis_set_id,hypothesis=proposal.precise_statement,claim_level="exploratory",generation_method=f"candidate_transform:{context.operator}:{backend.backend_id}:{backend.model_id}:proposal={proposal.proposal_id}",parent_candidate_ids=tuple(p.candidate.candidate_id for p in context.parents),assumptions=proposal.assumptions+prov,status="active",frozen=False)
    c.validate_for_registration();return c,ledger_object_id("candidate",c.to_dict())
