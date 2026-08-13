# SPDX-License-Identifier: Apache-2.0
"""Failure-backed mechanism-family records for similarity screening."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import Candidate, FailureRecord
from .similarity_common import (
    CandidateReference,
    DuplicateDetectorError,
    candidate_mechanism_tokens,
    ledger_payload_object_id,
    require_object_id,
    require_safe_id,
    require_target_track,
    require_unique_object_ids,
    require_unique_text,
)

@dataclass(frozen=True)
class DeadFamilyRecord:
    family_id: str
    domain_id: str
    hypothesis_set_id: str
    target_hypothesis: str
    failed_candidate_id: str
    failed_candidate_object_id: str
    failure_object_ids: tuple[str,...]
    backing_failures: tuple[FailureRecord,...]
    failed_constraint_ids: tuple[str,...]
    failure_classes: tuple[str,...]
    mechanism_tokens: tuple[str,...]
    reusable_lessons: tuple[str,...]
    screening_only: bool = True
    proof_of_falsehood: bool = False

    def validate(self) -> None:
        for field in ("family_id","domain_id","hypothesis_set_id","target_hypothesis","failed_candidate_id"):
            require_safe_id(getattr(self,field),field)
        require_object_id(self.failed_candidate_object_id,"failed_candidate_object_id")
        require_unique_object_ids(self.failure_object_ids,"failure_object_ids",nonempty=True)
        if len(self.backing_failures) != len(self.failure_object_ids):
            raise DuplicateDetectorError("backing failure records/object IDs must align")
        failure_ids=[]
        for failure, object_id in zip(self.backing_failures,self.failure_object_ids,strict=True):
            failure.validate(); failure_ids.append(failure.failure_id)
            if failure.candidate_id != self.failed_candidate_id or failure.domain_id != self.domain_id:
                raise DuplicateDetectorError("backing failure does not belong to source candidate")
            if object_id != ledger_payload_object_id("failure",failure.to_dict()):
                raise DuplicateDetectorError("backing failure payload does not match content-addressed object ID")
        if len(failure_ids) != len(set(failure_ids)):
            raise DuplicateDetectorError("backing failure IDs must be unique")
        require_unique_text(self.failed_constraint_ids,"failed_constraint_ids",nonempty=True)
        require_unique_text(self.failure_classes,"failure_classes",nonempty=True)
        require_unique_text(self.mechanism_tokens,"mechanism_tokens",nonempty=True)
        require_unique_text(self.reusable_lessons,"reusable_lessons",nonempty=True)
        if tuple(sorted(self.mechanism_tokens)) != self.mechanism_tokens:
            raise DuplicateDetectorError("mechanism_tokens must be sorted canonical tokens")
        if self.failed_constraint_ids != tuple(sorted({x.failed_constraint for x in self.backing_failures})):
            raise DuplicateDetectorError("family constraints do not match backing failures")
        if self.failure_classes != tuple(sorted({x.failure_class for x in self.backing_failures})):
            raise DuplicateDetectorError("family classes do not match backing failures")
        if self.reusable_lessons != tuple(sorted({x.reusable_lesson for x in self.backing_failures})):
            raise DuplicateDetectorError("family lessons do not match backing failures")
        if self.screening_only is not True or self.proof_of_falsehood is not False:
            raise DuplicateDetectorError("failure-family memory is screening-only, never proof of falsehood")

    @classmethod
    def from_failure_candidate(
        cls, *, family_id: str, candidate: Candidate, candidate_object_id: str,
        failures: tuple[FailureRecord,...], failure_object_ids: tuple[str,...]
    ) -> "DeadFamilyRecord":
        CandidateReference(candidate,candidate_object_id).validate()
        if not failures or len(failures) != len(failure_object_ids):
            raise DuplicateDetectorError("failure family requires aligned failure records/object IDs")
        track=require_target_track(candidate)
        record=cls(
            family_id=family_id,
            domain_id=candidate.domain_id,
            hypothesis_set_id=candidate.hypothesis_set_id,
            target_hypothesis=track,
            failed_candidate_id=candidate.candidate_id,
            failed_candidate_object_id=candidate_object_id,
            failure_object_ids=failure_object_ids,
            backing_failures=failures,
            failed_constraint_ids=tuple(sorted({x.failed_constraint for x in failures})),
            failure_classes=tuple(sorted({x.failure_class for x in failures})),
            mechanism_tokens=candidate_mechanism_tokens(candidate),
            reusable_lessons=tuple(sorted({x.reusable_lesson for x in failures})),
        )
        record.validate(); return record

    def to_dict(self) -> dict[str,Any]:
        self.validate(); value=asdict(self)
        value["failure_object_ids"]=list(self.failure_object_ids)
        value["backing_failures"]=[x.to_dict() for x in self.backing_failures]
        for key in ("failed_constraint_ids","failure_classes","mechanism_tokens","reusable_lessons"):
            value[key]=list(getattr(self,key))
        return value
