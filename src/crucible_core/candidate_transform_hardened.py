# SPDX-License-Identifier: Apache-2.0
"""Hardened public candidate-transform engine."""
from __future__ import annotations
import hashlib
from .candidate_transform_base import CandidateTransformBase
from .transform_common import TransformError, commit, digest, safe_id, sha256, utc
from .transform_hardening import raw_output_sha256, verify_recorded_decision
from .transform_models import TransformBackend, TransformContextPacket, TransformDecision
from .transform_policy import build_candidate, parse_proposal, proposal_reasons, receipt

class CandidateTransformEngine(CandidateTransformBase):
    def run(self,*,backend:TransformBackend,context:TransformContextPacket,ledger_replay,attempt_id:str,prompt_template_sha256:str,actor:str,source_commit:str,recorded_at_utc:str)->TransformDecision:
        safe_id(attempt_id,"attempt_id");sha256(prompt_template_sha256,"prompt_template_sha256");safe_id(backend.backend_id,"backend_id");safe_id(backend.model_id,"model_id");commit(source_commit);utc(recorded_at_utc)
        try:self._context(context,ledger_replay);valid=source_commit==context.source_commit
        except TransformError:valid=False
        context_sha=context.sha256() if valid else digest({"invalid_context":True,"attempt_id":attempt_id})
        empty=hashlib.sha256(b"").hexdigest()
        if not valid:return self._rejected(attempt_id=attempt_id,reasons=("invalid_context",),parse_status="not_attempted",backend=backend,context=None,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=empty,proposal=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        try:raw=backend.generate(context.to_dict())
        except Exception:raw=None
        if not isinstance(raw,str):return self._rejected(attempt_id=attempt_id,reasons=("provider_failure",),parse_status="not_attempted",backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=empty,proposal=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        raw_sha,valid_utf8=raw_output_sha256(raw)
        if not valid_utf8:return self._rejected(attempt_id=attempt_id,reasons=("invalid_utf8",),parse_status="not_parsed",backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=None,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        proposal,reasons,parse_status=parse_proposal(raw)
        if proposal is not None and not reasons:reasons=proposal_reasons(proposal,context,known=self.known,theorems=self.theorems)
        if proposal is None or reasons:return self._rejected(attempt_id=attempt_id,reasons=reasons or ("schema_failure",),parse_status=parse_status,backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        r=receipt(attempt_id=attempt_id,context=context,context_sha=context_sha,backend=backend,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,accepted=True,reasons=());rsha=digest(r)
        try:candidate,predicted=build_candidate(proposal=proposal,context=context,backend=backend,attempt_id=attempt_id,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,receipt_sha=rsha,domain_id=self.domain_id,hypothesis_set_id=self.hypothesis_set_id)
        except (TransformError,ValueError):return self._rejected(attempt_id=attempt_id,reasons=("candidate_validation_failure",),parse_status=parse_status,backend=backend,context=context,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,proposal=proposal,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        obj=self._record(attempt_id=attempt_id,accepted=True,reasons=(),parse_status=parse_status,backend=backend,context_sha=context_sha,prompt_sha=prompt_template_sha256,raw_sha=raw_sha,receipt_value=r,receipt_sha=rsha,proposal=proposal,candidate=candidate,predicted=predicted,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        d=TransformDecision(attempt_id,True,(),context_sha,raw_sha,rsha,obj,candidate,predicted);d.validate();return d
    def commit_candidate(self,*,decision,context,ledger,actor:str,source_commit:str,recorded_at_utc:str)->str:
        decision.validate();commit(source_commit);utc(recorded_at_utc)
        if not decision.accepted or decision.candidate is None or decision.candidate_object_id_if_committed is None:raise TransformError("only accepted transform decisions may be committed")
        self._context(context,ledger.verify())
        if context.sha256()!=decision.context_sha256 or source_commit!=context.source_commit:raise TransformError("commit provenance does not match transform context")
        verify_recorded_decision(journal=self.journal,decision=decision,context=context)
        if decision.candidate.parent_candidate_ids!=tuple(p.candidate.candidate_id for p in context.parents):raise TransformError("child parentage does not match transform context")
        markers={f"transform_operator={context.operator}",f"transform_context_sha256={decision.context_sha256}",f"transform_attempt_id={decision.attempt_id}",f"transform_receipt_sha256={decision.receipt_sha256}"}
        if not markers.issubset(set(decision.candidate.assumptions)):raise TransformError("child is missing transform provenance")
        oid=ledger.persist_candidate(decision.candidate,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc)
        if oid!=decision.candidate_object_id_if_committed:raise TransformError("persisted child identity differs from predicted identity")
        return oid
