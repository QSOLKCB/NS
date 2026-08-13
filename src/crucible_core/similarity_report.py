# SPDX-License-Identifier: Apache-2.0
"""Coherent advisory similarity reports."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .similarity_common import (
    DuplicateDetectorError,
    FINGERPRINT_ALGORITHM,
    ORIGIN_CLASSES,
    OriginClass,
    PrimaryClassification,
    SIMILARITY_ALGORITHM,
    require_object_id,
    require_safe_id,
    require_unique_object_ids,
    require_unique_text,
)

@dataclass(frozen=True)
class SimilarityReport:
    report_id: str
    candidate_id: str
    candidate_object_id: str
    origin_class: OriginClass
    origin_classification_object_id: str | None
    exact_fingerprint_sha256: str
    primary_classification: PrimaryClassification
    flags: tuple[str,...]
    matched_candidate_ids: tuple[str,...]
    matched_candidate_object_ids: tuple[str,...]
    matched_dead_family_ids: tuple[str,...]
    matched_dead_family_object_ids: tuple[str,...]
    max_structural_score: float
    max_dead_family_score: float
    structural_threshold: float
    dead_family_threshold: float
    minimum_shared_tokens: int
    fingerprint_algorithm: str = FINGERPRINT_ALGORITHM
    similarity_algorithm: str = SIMILARITY_ALGORITHM
    review_required: bool = False
    automatic_rejection: bool = False
    mathematical_equivalence_established: bool = False
    proof_of_falsehood: bool = False
    claim_level_effect: Literal["none"] = "none"
    evidence_effect: Literal["none"] = "none"

    def validate(self) -> None:
        require_safe_id(self.report_id,"report_id"); require_safe_id(self.candidate_id,"candidate_id"); require_object_id(self.candidate_object_id,"candidate_object_id")
        if self.origin_class not in ORIGIN_CLASSES: raise DuplicateDetectorError("unsupported origin_class")
        if self.origin_classification_object_id is not None: require_object_id(self.origin_classification_object_id,"origin_classification_object_id")
        if not re.fullmatch(r"[0-9a-f]{64}",self.exact_fingerprint_sha256): raise DuplicateDetectorError("exact_fingerprint_sha256 must be lowercase 64-hex")
        allowed={"exact_duplicate","structural_near_duplicate","dead_family_match"}
        require_unique_text(self.flags,"flags"); flags=set(self.flags)
        if flags-allowed: raise DuplicateDetectorError("unsupported similarity flag")
        require_unique_text(self.matched_candidate_ids,"matched_candidate_ids"); require_unique_object_ids(self.matched_candidate_object_ids,"matched_candidate_object_ids")
        if len(self.matched_candidate_ids)!=len(self.matched_candidate_object_ids): raise DuplicateDetectorError("matched candidate IDs/object IDs must align")
        require_unique_text(self.matched_dead_family_ids,"matched_dead_family_ids"); require_unique_object_ids(self.matched_dead_family_object_ids,"matched_dead_family_object_ids")
        if len(self.matched_dead_family_ids)!=len(self.matched_dead_family_object_ids): raise DuplicateDetectorError("matched family IDs/object IDs must align")
        for score,field in ((self.max_structural_score,"max_structural_score"),(self.max_dead_family_score,"max_dead_family_score"),(self.structural_threshold,"structural_threshold"),(self.dead_family_threshold,"dead_family_threshold")):
            if not isinstance(score,(int,float)) or isinstance(score,bool) or not 0.0<=float(score)<=1.0: raise DuplicateDetectorError(f"{field} must be within [0,1]")
        if not isinstance(self.minimum_shared_tokens,int) or isinstance(self.minimum_shared_tokens,bool) or self.minimum_shared_tokens<1: raise DuplicateDetectorError("minimum_shared_tokens must be a positive integer")
        if self.fingerprint_algorithm!=FINGERPRINT_ALGORITHM or self.similarity_algorithm!=SIMILARITY_ALGORITHM: raise DuplicateDetectorError("screening algorithm identity drift")

        candidate_flagged=bool(flags & {"exact_duplicate","structural_near_duplicate"})
        if bool(self.matched_candidate_ids)!=candidate_flagged: raise DuplicateDetectorError("candidate matches must agree with candidate flags")
        if bool(self.matched_dead_family_ids)!=("dead_family_match" in flags): raise DuplicateDetectorError("family matches must agree with family flag")
        if "structural_near_duplicate" in flags:
            if self.max_structural_score < self.structural_threshold: raise DuplicateDetectorError("structural flag requires threshold-satisfying score")
        elif self.max_structural_score >= self.structural_threshold:
            raise DuplicateDetectorError("unflagged structural score may not meet threshold")
        if "dead_family_match" in flags:
            if self.max_dead_family_score < self.dead_family_threshold: raise DuplicateDetectorError("family flag requires threshold-satisfying score")
        elif self.max_dead_family_score >= self.dead_family_threshold:
            raise DuplicateDetectorError("unflagged family score may not meet threshold")
        if "exact_duplicate" in flags: expected: PrimaryClassification="exact_duplicate"
        elif "dead_family_match" in flags: expected="dead_family_match"
        elif "structural_near_duplicate" in flags: expected="structural_near_duplicate"
        else: expected="novel_to_screening_memory"
        if self.primary_classification!=expected: raise DuplicateDetectorError("primary classification contradicts flags/matches")
        if self.review_required is not bool(flags): raise DuplicateDetectorError("flagged screening reports must require review")
        if any((self.automatic_rejection,self.mathematical_equivalence_established,self.proof_of_falsehood)): raise DuplicateDetectorError("similarity screening may not reject or establish mathematical authority")
        if self.claim_level_effect!="none" or self.evidence_effect!="none": raise DuplicateDetectorError("similarity screening may not alter claim/evidence authority")

    def to_dict(self) -> dict[str,Any]:
        self.validate(); value=asdict(self)
        for key in ("flags","matched_candidate_ids","matched_candidate_object_ids","matched_dead_family_ids","matched_dead_family_object_ids"):
            value[key]=list(getattr(self,key))
        return value
