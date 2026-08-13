# SPDX-License-Identifier: Apache-2.0
"""Typed records for controlled candidate transformation and crossover."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol
from .duplicate import CandidateReference
from .models import Candidate, FailureRecord
from .transform_common import (
    OPERATORS, RESERVED_ASSUMPTION_PREFIXES, TRANSFORM_VERSION, TransformError,
    commit, contains_authority, digest, ledger_object_id, safe_id, semantic_assumptions,
    sha256, target_track, text, unique_text,
)

@dataclass(frozen=True)
class TransformParent:
    candidate: Candidate
    candidate_object_id: str
    def validate(self)->None:
        CandidateReference(self.candidate,self.candidate_object_id).validate()
        target_track(self.candidate)
        if any(x.startswith(("analogy_source=","mapping_class=")) or x=="cross_domain_transfer_requires_target_domain_validation" for x in self.candidate.assumptions):
            raise TransformError("analogy-derived parent requires an explicit firewall-aware transform route")
    def to_dict(self)->dict[str,Any]:
        self.validate()
        return {"candidate_id":self.candidate.candidate_id,"candidate_object_id":self.candidate_object_id,"target_hypothesis":target_track(self.candidate),"hypothesis":self.candidate.hypothesis,"assumptions":list(semantic_assumptions(self.candidate))}

@dataclass(frozen=True)
class TransformFailure:
    failure: FailureRecord
    failure_object_id: str
    def validate(self)->None:
        self.failure.validate(); sha256(self.failure_object_id.removeprefix("sha256:"),"failure object digest")
        if self.failure_object_id!=ledger_object_id("failure",self.failure.to_dict()): raise TransformError("failure payload does not match content-addressed ledger object ID")
    def to_dict(self)->dict[str,Any]:
        self.validate(); f=self.failure
        return {"failure_id":f.failure_id,"failure_object_id":self.failure_object_id,"candidate_id":f.candidate_id,"failed_constraint":f.failed_constraint,"failure_class":f.failure_class,"reusable_lesson":f.reusable_lesson}

@dataclass(frozen=True)
class TransformContextPacket:
    domain_id:str
    hypothesis_set_id:str
    operator:str
    target_hypothesis:str
    parents:tuple[TransformParent,...]
    failures:tuple[TransformFailure,...]
    theorem_ids:tuple[str,...]
    proof_barrier_ids:tuple[str,...]
    frontier_candidate_ids:tuple[str,...]
    ledger_event_count:int
    ledger_head_event_sha256:str|None
    source_commit:str
    task:str
    def validate(self)->None:
        safe_id(self.domain_id,"domain_id");safe_id(self.hypothesis_set_id,"hypothesis_set_id");safe_id(self.target_hypothesis,"target_hypothesis");text(self.task,"task")
        if self.operator not in OPERATORS: raise TransformError("unsupported transform operator")
        if not self.parents: raise TransformError("transform context requires parent candidates")
        for p in self.parents:
            p.validate()
            if p.candidate.domain_id!=self.domain_id or p.candidate.hypothesis_set_id!=self.hypothesis_set_id: raise TransformError("parent domain/hypothesis-set mismatch")
        parent_ids=tuple(p.candidate.candidate_id for p in self.parents); parent_objs=tuple(p.candidate_object_id for p in self.parents)
        unique_text(parent_ids,"parent candidate IDs",True)
        if len(parent_objs)!=len(set(parent_objs)): raise TransformError("parent candidate object IDs must be unique")
        unique_text(self.theorem_ids,"theorem_ids");unique_text(self.proof_barrier_ids,"proof_barrier_ids",True);unique_text(self.frontier_candidate_ids,"frontier_candidate_ids",True)
        if set(parent_ids)-set(self.frontier_candidate_ids): raise TransformError("all transform parents must be on the supplied survivor frontier")
        failure_ids=[]; failure_objs=[]
        for f in self.failures:
            f.validate();failure_ids.append(f.failure.failure_id);failure_objs.append(f.failure_object_id)
            if f.failure.domain_id!=self.domain_id or f.failure.candidate_id not in parent_ids: raise TransformError("transform failure must belong to a parent candidate in the same domain")
        unique_text(tuple(failure_ids),"failure_ids")
        if len(failure_objs)!=len(set(failure_objs)): raise TransformError("failure object IDs must be unique")
        if not isinstance(self.ledger_event_count,int) or isinstance(self.ledger_event_count,bool) or self.ledger_event_count<0: raise TransformError("ledger_event_count must be non-negative integer")
        if self.ledger_head_event_sha256 is None:
            if self.ledger_event_count!=0: raise TransformError("non-empty ledger context requires a head digest")
        else:
            sha256(self.ledger_head_event_sha256,"ledger_head_event_sha256")
            if self.ledger_event_count==0: raise TransformError("empty ledger context must not declare a head digest")
        commit(self.source_commit)
        tracks=tuple(target_track(p.candidate) for p in self.parents)
        if self.operator=="crossover_survivors":
            if len(self.parents)!=2 or len(set(tracks))!=1 or self.target_hypothesis!=tracks[0]: raise TransformError("crossover requires exactly two same-track frontier parents and preserves their track")
        elif len(self.parents)!=1: raise TransformError("non-crossover transform requires exactly one parent")
        elif self.operator=="reverse_track_perspective":
            if self.target_hypothesis==tracks[0]: raise TransformError("reverse-track transform must target a different hypothesis track")
        elif self.target_hypothesis!=tracks[0]: raise TransformError("this transform operator must preserve the parent target track")
        if self.operator=="replace_failed_estimate" and not self.failures: raise TransformError("replace_failed_estimate requires parent failure provenance")
    def to_dict(self)->dict[str,Any]:
        self.validate(); return {"transform_version":TRANSFORM_VERSION,"domain_id":self.domain_id,"hypothesis_set_id":self.hypothesis_set_id,"operator":self.operator,"target_hypothesis":self.target_hypothesis,"parents":[p.to_dict() for p in self.parents],"failures":[f.to_dict() for f in self.failures],"theorem_ids":list(self.theorem_ids),"proof_barrier_ids":list(self.proof_barrier_ids),"frontier_candidate_ids":list(self.frontier_candidate_ids),"ledger_event_count":self.ledger_event_count,"ledger_head_event_sha256":self.ledger_head_event_sha256,"source_commit":self.source_commit,"task":self.task}
    def sha256(self)->str:return digest(self.to_dict())

@dataclass(frozen=True)
class TransformProposal:
    proposal_id:str
    target_hypothesis:str
    precise_statement:str
    assumptions:tuple[str,...]
    claimed_dependencies:tuple[str,...]
    suggested_tests:tuple[str,...]
    possible_failure_modes:tuple[str,...]
    parent_assumptions_removed:tuple[str,...]
    addressed_failure_ids:tuple[str,...]
    operator_notes:str
    def validate(self)->None:
        safe_id(self.proposal_id,"proposal_id");safe_id(self.target_hypothesis,"target_hypothesis");text(self.precise_statement,"precise_statement");text(self.operator_notes,"operator_notes")
        unique_text(self.assumptions,"assumptions",True);unique_text(self.claimed_dependencies,"claimed_dependencies");unique_text(self.suggested_tests,"suggested_tests",True);unique_text(self.possible_failure_modes,"possible_failure_modes",True);unique_text(self.parent_assumptions_removed,"parent_assumptions_removed");unique_text(self.addressed_failure_ids,"addressed_failure_ids")
        if any(x.startswith(RESERVED_ASSUMPTION_PREFIXES) or x=="cross_domain_transfer_requires_target_domain_validation" for x in self.assumptions): raise TransformError("proposal may not write engine-owned provenance assumptions")
        values=(self.proposal_id,self.target_hypothesis,self.precise_statement,self.operator_notes,*self.assumptions,*self.claimed_dependencies,*self.suggested_tests,*self.possible_failure_modes,*self.parent_assumptions_removed,*self.addressed_failure_ids)
        if any(contains_authority(x) for x in values): raise TransformError("proposal contains forbidden authority language")
    def to_dict(self)->dict[str,Any]:
        self.validate();v=asdict(self)
        for key in ("assumptions","claimed_dependencies","suggested_tests","possible_failure_modes","parent_assumptions_removed","addressed_failure_ids"):v[key]=list(v[key])
        return v

class TransformBackend(Protocol):
    @property
    def backend_id(self)->str: ...
    @property
    def model_id(self)->str: ...
    def generate(self,context_packet:Mapping[str,Any])->str: ...

@dataclass(frozen=True)
class DeterministicTransformFixtureBackend:
    output:str
    backend_id:str="fixture"
    model_id:str="deterministic-transform-fixture-v1"
    def generate(self,context_packet:Mapping[str,Any])->str:
        del context_packet;return self.output

@dataclass(frozen=True)
class TransformDecision:
    attempt_id:str
    accepted:bool
    rejection_reasons:tuple[str,...]
    context_sha256:str
    raw_output_sha256:str
    receipt_sha256:str
    attempt_object_sha256:str
    candidate:Candidate|None
    candidate_object_id_if_committed:str|None
    def validate(self)->None:
        safe_id(self.attempt_id,"attempt_id");sha256(self.context_sha256,"context_sha256");sha256(self.raw_output_sha256,"raw_output_sha256");sha256(self.receipt_sha256,"receipt_sha256");sha256(self.attempt_object_sha256,"attempt_object_sha256");unique_text(self.rejection_reasons,"rejection_reasons")
        if self.accepted:
            if self.rejection_reasons or self.candidate is None or self.candidate_object_id_if_committed is None: raise TransformError("accepted transform decision requires only a candidate")
            self.candidate.validate_for_registration()
            if self.candidate.claim_level!="exploratory" or self.candidate.status!="active" or self.candidate.frozen: raise TransformError("transformed candidate must begin exploratory, active and unfrozen")
            if self.candidate_object_id_if_committed!=ledger_object_id("candidate",self.candidate.to_dict()): raise TransformError("predicted child object ID does not match candidate payload")
        elif self.candidate is not None or self.candidate_object_id_if_committed is not None: raise TransformError("rejected transform decision may not contain a candidate")
