# SPDX-License-Identifier: Apache-2.0
"""Orchestrator for controlled candidate transformation and crossover."""
from __future__ import annotations
import hashlib
from .ledger import ContentAddressedLedger, LedgerReplay
from .transform_common import TransformError, commit, digest, safe_id, sha256, utc
from .transform_journal import TransformAttemptJournal
from .transform_models import TransformBackend, TransformContextPacket, TransformDecision
from .transform_policy import build_candidate, parse_proposal, proposal_reasons, receipt, validate_context

class CandidateTransformEngine:
    def __init__(self,*,domain_id:str,hypothesis_set_id:str,allowed_target_hypotheses:set[str],required_proof_barrier_ids:set[str],known_candidate_ids:set[str],frontier_candidate_ids:set[str],known_theorem_ids:set[str],journal:TransformAttemptJournal)->None:
        safe_id(domain_id,"domain_id");safe_id(hypothesis_set_id,"hypothesis_set_id")
        if not allowed_target_hypotheses or not required_proof_barrier_ids: raise TransformError("target hypotheses and proof barriers must be non-empty")
        for name,values in (("allowed_target_hypotheses",allowed_target_hypotheses),("required_proof_barrier_ids",required_proof_barrier_ids),("known_candidate_ids",known_candidate_ids),("frontier_candidate_ids",frontier_candidate_ids),("known_theorem_ids",known_theorem_ids)):
            for value in values:safe_id(value,name)
        if frontier_candidate_ids-known_candidate_ids: raise TransformError("frontier must be a subset of known candidates")
        self.domain_id=domain_id;self.hypothesis_set_id=hypothesis_set_id;self.allowed=frozenset(allowed_target_hypotheses);self.barriers=frozenset(required_proof_barrier_ids);self.known=frozenset(known_candidate_ids);self.frontier=frozenset(frontier_candidate_ids);self.theorems=frozenset(known_theorem_ids);self.journal=journal
    def _context(self,context:TransformContextPacket,replay:LedgerReplay)->None:
        validate_context(context,replay,domain_id=self.domain_id,hypothesis_set_id=self.hypothesis_set_id,allowed=self.allowed,barriers=self.barriers,known=self.known,frontier=self.frontier,theorems=self.theorems)
    def _record(self,*,attempt_id:str,accepted:bool,reasons:tuple[str,...],parse_status:str,backend:TransformBackend,context_sha:str,prompt_sha:str,raw_sha:str,receipt_value:dict,receipt_sha:str,proposal,candidate,predicted,actor:str,source_commit:str,recorded_at_utc:str)->str:
        payload={"attempt_id":attempt_id,"accepted":accepted,"rejection_reasons":list(reasons),"parse_status":parse_status,"backend_id":backend.backend_id,"model_id":backend.model_id,"context_sha256":context_sha,"prompt_template_sha256":prompt_sha,"raw_output_sha256":raw_sha,"receipt_sha256":receipt_sha,"receipt":receipt_value,"proposal":proposal.to_dict() if proposal else None,"candidate":candidate.to_dict() if candidate else None,"candidate_object_id_if_committed":predicted,"recorded_at_utc":recorded_at_utc,"authority":{"creates_domain_evidence":False,"promotes_claim":False,"inherits_parent_claim_level":False,"inherits_parent_evidence":False,"inherits_parent_survival_status":False,"selects_winner":False}}
        return self.journal.record(attempt_id=attempt_id,payload=payload,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
    def _rejected(self,*,attempt_id:str,reasons:tuple[str,...],parse_status:str,backend:TransformBackend,context:TransformContextPacket|None,context_sha:str,prompt_sha:str,raw_sha:str,proposal,actor:str,source_commit:str,recorded_at_utc:str)->TransformDecision:
        r=receipt(attempt_id=attempt_id,context=context,context_sha=context_sha,backend=backend,prompt_sha=prompt_sha,raw_sha=raw_sha,proposal=proposal,accepted=False,reasons=reasons);rsha=digest(r)
        obj=self._record(attempt_id=attempt_id,accepted=False,reasons=reasons,parse_status=parse_status,backend=backend,context_sha=context_sha,prompt_sha=prompt_sha,raw_sha=raw_sha,receipt_value=r,receipt_sha=rsha,proposal=proposal,candidate=None,predicted=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        d=TransformDecision(attempt_id,False,reasons,context_sha,raw_sha,rsha,obj,None,None);d.validate();return d
    def run(self,*,backend:TransformBackend,context:TransformContextPacket,ledger_replay:LedgerReplay,attempt_id:str,prompt_template_sha256:str,actor:str,source_commit:str,recorded_at_utc:str)->TransformDecision:
        safe_id(attempt_id,"attempt_id");sha256(prompt_template_sha256,"prompt_template_sha256");safe_id(backend.backend_id,"backend_id");safe_id(backend.model_id,"model_id");commit(source_commit);utc(recorded_at_utc)
        try:self._context(context,ledger_replay);valid=source_commit==context.source_commit
        except TransformError:valid=False
        context_sha=context.sha256() if valid else digest({"invalid_context":True,"attempt_id":attempt_id})
        empty=hashlib.sha256(b"").hexdigest()
        if not valid:return self._rejected(attempt_id=attempt_id,reasons=("invalid_context",),parse_status="not_attempted",backend=backend,context=None,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=empty,proposal=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        try:raw=backend.generate(context.to_dict())
        except Exception:raw=None
        if not isinstance(raw,str):return self._rejected(attempt_id=attempt_id,reasons=("provider_failure",),parse_status="not_attempted",backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=empty,proposal=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        raw_sha=hashlib.sha256(raw.encode("utf-8")).hexdigest();proposal,reasons,parse_status=parse_proposal(raw)
        if proposal is not None and not reasons:reasons=proposal_reasons(proposal,context,known=self.known,theorems=self.theorems)
        if proposal is None or reasons:return self._rejected(attempt_id=attempt_id,reasons=reasons or ("schema_failure",),parse_status=parse_status,backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        r=receipt(attempt_id=attempt_id,context=context,context_sha=context_sha,backend=backend,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,accepted=True,reasons=());rsha=digest(r)
        try:candidate,predicted=build_candidate(proposal=proposal,context=context,backend=backend,attempt_id=attempt_id,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,receipt_sha=rsha,domain_id=self.domain_id,hypothesis_set_id=self.hypothesis_set_id)
        except (TransformError,ValueError):return self._rejected(attempt_id=attempt_id,reasons=("candidate_validation_failure",),parse_status=parse_status,backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        obj=self._record(attempt_id=attempt_id,accepted=True,reasons=(),parse_status=parse_status,backend=backend,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,receipt_value=r,receipt_sha=rsha,proposal=proposal,candidate=candidate,predicted=predicted,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        d=TransformDecision(attempt_id,True,(),context_sha,raw_sha,rsha,obj,candidate,predicted);d.validate();return d
    def commit_candidate(self,*,decision:TransformDecision,context:TransformContextPacket,ledger:ContentAddressedLedger,actor:str,source_commit:str,recorded_at_utc:str)->str:
        decision.validate();commit(source_commit);utc(recorded_at_utc)
        if not decision.accepted or decision.candidate is None or decision.candidate_object_id_if_committed is None: raise TransformError("only accepted transform decisions may be committed")
        self._context(context,ledger.verify())
        if context.sha256()!=decision.context_sha256 or source_commit!=context.source_commit: raise TransformError("commit provenance does not match transform context")
        if self.journal.attempt_object_sha256(decision.attempt_id)!=decision.attempt_object_sha256: raise TransformError("decision does not match recorded transform attempt")
        if decision.candidate.parent_candidate_ids!=tuple(p.candidate.candidate_id for p in context.parents): raise TransformError("child parentage does not match transform context")
        markers={f"transform_operator={context.operator}",f"transform_context_sha256={decision.context_sha256}",f"transform_attempt_id={decision.attempt_id}",f"transform_receipt_sha256={decision.receipt_sha256}"}
        if not markers.issubset(set(decision.candidate.assumptions)): raise TransformError("child is missing transform provenance")
        oid=ledger.persist_candidate(decision.candidate,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        if oid!=decision.candidate_object_id_if_committed: raise TransformError("persisted child identity differs from predicted identity")
        return oid
    def authority_snapshot(self)->dict[str,bool]:return {"transform_output_is_domain_evidence":False,"transform_may_promote_claim":False,"transform_inherits_parent_claim_level":False,"transform_inherits_parent_evidence":False,"transform_inherits_parent_survival_status":False,"transform_may_select_winner":False,"operator_label_is_mathematical_validation":False}
