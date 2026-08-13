# SPDX-License-Identifier: Apache-2.0
"""Deterministic advisory candidate-similarity detector."""
from __future__ import annotations

from .similarity_common import (
    CandidateOriginClassification,
    CandidateReference,
    DuplicateDetectorError,
    PrimaryClassification,
    candidate_exact_fingerprint,
    candidate_mechanism_tokens,
    jaccard,
    require_object_id,
    require_safe_id,
    require_target_track,
)
from .similarity_family import DeadFamilyRecord
from .similarity_report import SimilarityReport

class DuplicateDeadFamilyDetector:
    def __init__(self, *, structural_threshold: float, dead_family_threshold: float, minimum_shared_tokens: int) -> None:
        for value,field in ((structural_threshold,"structural_threshold"),(dead_family_threshold,"dead_family_threshold")):
            if not isinstance(value,(int,float)) or isinstance(value,bool) or not 0.0<float(value)<=1.0: raise DuplicateDetectorError(f"{field} must be within (0,1]")
        if not isinstance(minimum_shared_tokens,int) or isinstance(minimum_shared_tokens,bool) or minimum_shared_tokens<1: raise DuplicateDetectorError("minimum_shared_tokens must be a positive integer")
        self.structural_threshold=float(structural_threshold); self.dead_family_threshold=float(dead_family_threshold); self.minimum_shared_tokens=minimum_shared_tokens

    def screen(self, *, report_id: str, candidate: CandidateReference, origin: CandidateOriginClassification, prior_candidates: tuple[CandidateReference,...], dead_families: tuple[tuple[DeadFamilyRecord,str],...], origin_classification_object_id: str|None=None) -> SimilarityReport:
        require_safe_id(report_id,"report_id"); candidate.validate(); origin.validate()
        if origin.candidate_id!=candidate.candidate.candidate_id or origin.candidate_object_id!=candidate.candidate_object_id: raise DuplicateDetectorError("origin classification does not bind screened candidate")
        if origin_classification_object_id is not None: require_object_id(origin_classification_object_id,"origin_classification_object_id")
        current=candidate.candidate; current_track=require_target_track(current); current_fingerprint=candidate_exact_fingerprint(current); current_tokens=candidate_mechanism_tokens(current)
        exact=[]; structural=[]; max_structural=0.0; seen_candidates=set()
        for prior in prior_candidates:
            prior.validate(); prior_track=require_target_track(prior.candidate)
            if prior.candidate_object_id==candidate.candidate_object_id: continue
            if prior.candidate_object_id in seen_candidates: raise DuplicateDetectorError("prior candidate object IDs must be unique")
            seen_candidates.add(prior.candidate_object_id); other=prior.candidate
            if other.domain_id!=current.domain_id or other.hypothesis_set_id!=current.hypothesis_set_id or prior_track!=current_track: continue
            if candidate_exact_fingerprint(other)==current_fingerprint: exact.append(prior); continue
            score=jaccard(current_tokens,candidate_mechanism_tokens(other),self.minimum_shared_tokens); max_structural=max(max_structural,score)
            if score>=self.structural_threshold: structural.append((prior,score))
        families=[]; max_family=0.0; seen_families=set()
        for family,object_id in dead_families:
            family.validate(); require_object_id(object_id,"dead_family_object_id")
            if object_id in seen_families: raise DuplicateDetectorError("failure-family object IDs must be unique")
            seen_families.add(object_id)
            if family.domain_id!=current.domain_id or family.hypothesis_set_id!=current.hypothesis_set_id or family.target_hypothesis!=current_track: continue
            score=jaccard(current_tokens,family.mechanism_tokens,self.minimum_shared_tokens); max_family=max(max_family,score)
            if score>=self.dead_family_threshold: families.append((family,object_id,score))
        flags=[]
        if exact: flags.append("exact_duplicate")
        if structural: flags.append("structural_near_duplicate")
        if families: flags.append("dead_family_match")
        if exact: primary: PrimaryClassification="exact_duplicate"
        elif families: primary="dead_family_match"
        elif structural: primary="structural_near_duplicate"
        else: primary="novel_to_screening_memory"
        matched_candidates=sorted([*exact,*(x[0] for x in structural)],key=lambda x:(x.candidate.candidate_id,x.candidate_object_id))
        matched_families=sorted(families,key=lambda x:(x[0].family_id,x[1]))
        report=SimilarityReport(report_id=report_id,candidate_id=current.candidate_id,candidate_object_id=candidate.candidate_object_id,origin_class=origin.origin_class,origin_classification_object_id=origin_classification_object_id,exact_fingerprint_sha256=current_fingerprint,primary_classification=primary,flags=tuple(flags),matched_candidate_ids=tuple(x.candidate.candidate_id for x in matched_candidates),matched_candidate_object_ids=tuple(x.candidate_object_id for x in matched_candidates),matched_dead_family_ids=tuple(x[0].family_id for x in matched_families),matched_dead_family_object_ids=tuple(x[1] for x in matched_families),max_structural_score=max_structural,max_dead_family_score=max_family,structural_threshold=self.structural_threshold,dead_family_threshold=self.dead_family_threshold,minimum_shared_tokens=self.minimum_shared_tokens,review_required=bool(flags))
        report.validate(); return report

    def authority_snapshot(self) -> dict[str,bool]:
        return {"similarity_establishes_mathematical_equivalence":False,"dead_family_match_proves_falsehood":False,"screening_may_reject_candidate":False,"screening_may_change_claim_level":False,"screening_may_create_domain_evidence":False,"screening_may_select_winner":False}
