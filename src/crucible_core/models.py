# SPDX-License-Identifier: Apache-2.0
"""Pure data models for domain-neutral Crucible orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Literal

ClaimLevel = str
CandidateStatus = Literal["active", "frozen", "rejected_by_domain_constraint"]
EvidenceKind = Literal["supporting", "challenging", "neutral"]
EvidenceStage = Literal["training", "development", "holdout"]
ConstraintOutcome = Literal["pass", "fail", "blocked", "not_run"]
ConstraintSeverity = Literal["hard", "soft"]


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_unique_text(values: tuple[str, ...], field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field} must contain unique values")
    for value in values:
        _require_text(value, field)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    domain_id: str
    hypothesis_set_id: str
    hypothesis: str
    claim_level: ClaimLevel
    generation_method: str
    parent_candidate_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    status: CandidateStatus = "active"
    frozen: bool = False

    def validate(self) -> None:
        for field in (
            "candidate_id", "domain_id", "hypothesis_set_id", "hypothesis",
            "claim_level", "generation_method",
        ):
            _require_text(getattr(self, field), field)
        _require_unique_text(self.parent_candidate_ids, "parent_candidate_ids")
        _require_unique_text(self.assumptions, "assumptions")
        if self.candidate_id in self.parent_candidate_ids:
            raise ValueError("candidate cannot be its own parent")
        if self.status == "frozen" and not self.frozen:
            raise ValueError("status=frozen requires frozen=true")
        if self.status == "rejected_by_domain_constraint" and not self.frozen:
            raise ValueError("rejected candidates must remain frozen")

    def validate_for_registration(self) -> None:
        """Reject imported terminal state unless a future state-import API restores its ledger."""
        self.validate()
        if self.status != "active" or self.frozen:
            raise ValueError("candidate registration requires active status and frozen=false")

    def freeze(self) -> "Candidate":
        self.validate()
        if self.status == "rejected_by_domain_constraint":
            return self
        return replace(self, status="frozen", frozen=True)

    def reject(self) -> "Candidate":
        self.validate()
        return replace(self, status="rejected_by_domain_constraint", frozen=True)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["parent_candidate_ids"] = list(self.parent_candidate_ids)
        value["assumptions"] = list(self.assumptions)
        return value


@dataclass(frozen=True)
class HypothesisSet:
    hypothesis_set_id: str
    domain_id: str
    candidate_ids: tuple[str, ...]
    selection_state: Literal["unresolved"] = "unresolved"
    preferred_candidate_id: None = None

    def validate(self) -> None:
        _require_text(self.hypothesis_set_id, "hypothesis_set_id")
        _require_text(self.domain_id, "domain_id")
        _require_unique_text(self.candidate_ids, "candidate_ids")
        if len(self.candidate_ids) < 2:
            raise ValueError("a competing hypothesis set requires at least two candidates")
        if self.preferred_candidate_id is not None:
            raise ValueError("Crucible Core may not assign a preferred candidate")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["candidate_ids"] = list(self.candidate_ids)
        return value


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    domain_id: str
    candidate_id: str
    evidence_kind: EvidenceKind
    stage: EvidenceStage
    source_ref: str
    provenance_ref: str
    summary: str
    reproducible: bool

    def validate(self) -> None:
        for field in (
            "evidence_id", "domain_id", "candidate_id", "source_ref",
            "provenance_ref", "summary",
        ):
            _require_text(getattr(self, field), field)
        if self.evidence_kind not in {"supporting", "challenging", "neutral"}:
            raise ValueError("invalid evidence_kind")
        if self.stage not in {"training", "development", "holdout"}:
            raise ValueError("invalid evidence stage")
        if not isinstance(self.reproducible, bool):
            raise ValueError("reproducible must be boolean")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class ConstraintResult:
    result_id: str
    domain_id: str
    candidate_id: str
    constraint_id: str
    outcome: ConstraintOutcome
    severity: ConstraintSeverity
    evidence_ids: tuple[str, ...]
    explanation: str

    def validate(self) -> None:
        for field in ("result_id", "domain_id", "candidate_id", "constraint_id", "explanation"):
            _require_text(getattr(self, field), field)
        if self.outcome not in {"pass", "fail", "blocked", "not_run"}:
            raise ValueError("invalid constraint outcome")
        if self.severity not in {"hard", "soft"}:
            raise ValueError("invalid constraint severity")
        _require_unique_text(self.evidence_ids, "evidence_ids")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        return value


@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    candidate_id: str
    domain_id: str
    failed_constraint: str
    failure_class: str
    evidence_ids: tuple[str, ...]
    reusable_lesson: str
    claim_level_before: str
    claim_level_after: str
    recorded_by: str

    def validate(self) -> None:
        for field in (
            "failure_id", "candidate_id", "domain_id", "failed_constraint",
            "failure_class", "reusable_lesson", "claim_level_before",
            "claim_level_after", "recorded_by",
        ):
            _require_text(getattr(self, field), field)
        _require_unique_text(self.evidence_ids, "evidence_ids")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        return value
