# SPDX-License-Identifier: Apache-2.0
"""Deterministic duplicate and dead-family screening for Crucible candidates.

This module is a search-efficiency layer, not a theorem prover. Similarity can
flag a candidate for review; it cannot establish mathematical equivalence,
falsehood, evidentiary status, claim promotion, or automatic rejection.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

from .engine import canonical_json_bytes
from .models import Candidate, FailureRecord

DUPLICATE_DETECTOR_VERSION = "0.1.0"
FINGERPRINT_ALGORITHM = "normalized_declared_mechanism_sha256_v1"
SIMILARITY_ALGORITHM = "token_jaccard_v1"

OriginClass = Literal[
    "exact_domain_construction",
    "established_bridge",
    "source_described",
    "structural_transfer",
    "heuristic",
    "schematic",
]
PrimaryClassification = Literal[
    "novel_to_screening_memory",
    "exact_duplicate",
    "structural_near_duplicate",
    "dead_family_match",
]

_ORIGIN_CLASSES = {
    "exact_domain_construction",
    "established_bridge",
    "source_described",
    "structural_transfer",
    "heuristic",
    "schematic",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_OBJECT = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN = re.compile(r"\w+", flags=re.UNICODE)
_PROVENANCE_ASSUMPTION_PREFIXES = (
    "generator_context_sha256=",
    "generation_attempt_id=",
    "analogy_source=",
    "mapping_class=",
)
_PROVENANCE_ASSUMPTION_EXACT = {
    "cross_domain_transfer_requires_target_domain_validation",
}


class DuplicateDetectorError(ValueError):
    """Raised when duplicate-screening inputs or authority boundaries are invalid."""


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DuplicateDetectorError(f"{field} must be a non-empty string")


def _require_safe_id(value: str, field: str) -> None:
    _require_text(value, field)
    if not _SAFE_ID.fullmatch(value):
        raise DuplicateDetectorError(
            f"{field} must be a component-safe ID of at most 128 characters"
        )


def _require_object_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA256_OBJECT.fullmatch(value):
        raise DuplicateDetectorError(f"{field} must be sha256:<64 lowercase hex>")


def _require_unique_text(values: tuple[str, ...], field: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise DuplicateDetectorError(f"{field} must be non-empty")
    for value in values:
        _require_text(value, field)
    if len(values) != len(set(values)):
        raise DuplicateDetectorError(f"{field} must contain unique values")


def _require_unique_object_ids(values: tuple[str, ...], field: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise DuplicateDetectorError(f"{field} must be non-empty")
    for value in values:
        _require_object_id(value, field)
    if len(values) != len(set(values)):
        raise DuplicateDetectorError(f"{field} must contain unique values")


def _normalize_text(text: str) -> str:
    _require_text(text, "text")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def _tokens(texts: Iterable[str]) -> tuple[str, ...]:
    values: set[str] = set()
    for text in texts:
        normalized = _normalize_text(text)
        values.update(token for token in _TOKEN.findall(normalized) if token)
    return tuple(sorted(values))


def _target_track(candidate: Candidate) -> str | None:
    tracks = [
        item.split("=", 1)[1]
        for item in candidate.assumptions
        if item.startswith("target_track=") and "=" in item
    ]
    if len(tracks) > 1:
        raise DuplicateDetectorError("candidate declares multiple target_track markers")
    return tracks[0] if tracks else None


def _semantic_assumptions(candidate: Candidate) -> tuple[str, ...]:
    kept = []
    for assumption in candidate.assumptions:
        if assumption in _PROVENANCE_ASSUMPTION_EXACT:
            continue
        if assumption.startswith("target_track="):
            continue
        if assumption.startswith(_PROVENANCE_ASSUMPTION_PREFIXES):
            continue
        kept.append(_normalize_text(assumption))
    return tuple(sorted(set(kept)))


def candidate_mechanism_tokens(candidate: Candidate) -> tuple[str, ...]:
    """Return deterministic lexical screening tokens for the declared mechanism."""
    candidate.validate()
    return _tokens((candidate.hypothesis, *_semantic_assumptions(candidate)))


def candidate_exact_fingerprint(candidate: Candidate) -> str:
    """Hash normalized declared mechanism fields, excluding identity/provenance metadata."""
    candidate.validate()
    payload = {
        "algorithm": FINGERPRINT_ALGORITHM,
        "domain_id": candidate.domain_id,
        "hypothesis_set_id": candidate.hypothesis_set_id,
        "target_track": _target_track(candidate),
        "hypothesis": _normalize_text(candidate.hypothesis),
        "semantic_assumptions": list(_semantic_assumptions(candidate)),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _jaccard(a: tuple[str, ...], b: tuple[str, ...], minimum_shared_tokens: int) -> float:
    left, right = set(a), set(b)
    if not left or not right:
        return 0.0
    intersection = left & right
    if len(intersection) < minimum_shared_tokens:
        return 0.0
    return len(intersection) / len(left | right)


@dataclass(frozen=True)
class CandidateReference:
    candidate: Candidate
    candidate_object_id: str

    def validate(self) -> None:
        self.candidate.validate()
        _require_object_id(self.candidate_object_id, "candidate_object_id")


@dataclass(frozen=True)
class CandidateOriginClassification:
    origin_id: str
    candidate_id: str
    candidate_object_id: str
    origin_class: OriginClass
    source_refs: tuple[str, ...]
    rationale: str
    claim_level_effect: Literal["none"] = "none"
    evidence_effect: Literal["none"] = "none"

    def validate(self) -> None:
        _require_safe_id(self.origin_id, "origin_id")
        _require_safe_id(self.candidate_id, "candidate_id")
        _require_object_id(self.candidate_object_id, "candidate_object_id")
        if self.origin_class not in _ORIGIN_CLASSES:
            raise DuplicateDetectorError("unsupported origin_class")
        _require_unique_text(self.source_refs, "source_refs")
        _require_text(self.rationale, "rationale")
        if self.claim_level_effect != "none" or self.evidence_effect != "none":
            raise DuplicateDetectorError("origin classification may not alter claim/evidence authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        value["source_refs"] = list(self.source_refs)
        return value


@dataclass(frozen=True)
class DeadFamilyRecord:
    family_id: str
    domain_id: str
    hypothesis_set_id: str
    target_hypothesis: str
    failed_candidate_id: str
    failed_candidate_object_id: str
    failure_object_ids: tuple[str, ...]
    failed_constraint_ids: tuple[str, ...]
    failure_classes: tuple[str, ...]
    mechanism_tokens: tuple[str, ...]
    reusable_lessons: tuple[str, ...]
    screening_only: bool = True
    proof_of_falsehood: bool = False

    def validate(self) -> None:
        for field in (
            "family_id",
            "domain_id",
            "hypothesis_set_id",
            "target_hypothesis",
            "failed_candidate_id",
        ):
            _require_safe_id(getattr(self, field), field)
        _require_object_id(self.failed_candidate_object_id, "failed_candidate_object_id")
        _require_unique_object_ids(self.failure_object_ids, "failure_object_ids", nonempty=True)
        _require_unique_text(self.failed_constraint_ids, "failed_constraint_ids", nonempty=True)
        _require_unique_text(self.failure_classes, "failure_classes", nonempty=True)
        _require_unique_text(self.mechanism_tokens, "mechanism_tokens", nonempty=True)
        _require_unique_text(self.reusable_lessons, "reusable_lessons", nonempty=True)
        if tuple(sorted(self.mechanism_tokens)) != self.mechanism_tokens:
            raise DuplicateDetectorError("mechanism_tokens must be sorted canonical tokens")
        if self.screening_only is not True or self.proof_of_falsehood is not False:
            raise DuplicateDetectorError("dead-family memory is screening-only, never proof of falsehood")

    @classmethod
    def from_failure_candidate(
        cls,
        *,
        family_id: str,
        candidate: Candidate,
        candidate_object_id: str,
        failures: tuple[FailureRecord, ...],
        failure_object_ids: tuple[str, ...],
    ) -> "DeadFamilyRecord":
        candidate.validate()
        if not failures or len(failures) != len(failure_object_ids):
            raise DuplicateDetectorError("dead family requires aligned failure records/object IDs")
        track = _target_track(candidate)
        if track is None:
            raise DuplicateDetectorError("dead-family source candidate must declare target_track")
        for failure in failures:
            failure.validate()
            if failure.candidate_id != candidate.candidate_id or failure.domain_id != candidate.domain_id:
                raise DuplicateDetectorError("failure record does not belong to dead-family source candidate")
        record = cls(
            family_id=family_id,
            domain_id=candidate.domain_id,
            hypothesis_set_id=candidate.hypothesis_set_id,
            target_hypothesis=track,
            failed_candidate_id=candidate.candidate_id,
            failed_candidate_object_id=candidate_object_id,
            failure_object_ids=failure_object_ids,
            failed_constraint_ids=tuple(sorted({item.failed_constraint for item in failures})),
            failure_classes=tuple(sorted({item.failure_class for item in failures})),
            mechanism_tokens=candidate_mechanism_tokens(candidate),
            reusable_lessons=tuple(sorted({item.reusable_lesson for item in failures})),
        )
        record.validate()
        return record

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for key in (
            "failure_object_ids",
            "failed_constraint_ids",
            "failure_classes",
            "mechanism_tokens",
            "reusable_lessons",
        ):
            value[key] = list(value[key])
        return value


@dataclass(frozen=True)
class SimilarityReport:
    report_id: str
    candidate_id: str
    candidate_object_id: str
    origin_class: OriginClass
    origin_classification_object_id: str | None
    exact_fingerprint_sha256: str
    primary_classification: PrimaryClassification
    flags: tuple[str, ...]
    matched_candidate_ids: tuple[str, ...]
    matched_candidate_object_ids: tuple[str, ...]
    matched_dead_family_ids: tuple[str, ...]
    matched_dead_family_object_ids: tuple[str, ...]
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
        _require_safe_id(self.report_id, "report_id")
        _require_safe_id(self.candidate_id, "candidate_id")
        _require_object_id(self.candidate_object_id, "candidate_object_id")
        if self.origin_class not in _ORIGIN_CLASSES:
            raise DuplicateDetectorError("unsupported origin_class")
        if self.origin_classification_object_id is not None:
            _require_object_id(self.origin_classification_object_id, "origin_classification_object_id")
        if not re.fullmatch(r"[0-9a-f]{64}", self.exact_fingerprint_sha256):
            raise DuplicateDetectorError("exact_fingerprint_sha256 must be lowercase 64-hex")
        if self.primary_classification not in {
            "novel_to_screening_memory",
            "exact_duplicate",
            "structural_near_duplicate",
            "dead_family_match",
        }:
            raise DuplicateDetectorError("unsupported primary_classification")
        _require_unique_text(self.flags, "flags")
        allowed_flags = {"exact_duplicate", "structural_near_duplicate", "dead_family_match"}
        if set(self.flags) - allowed_flags:
            raise DuplicateDetectorError("unsupported similarity flag")
        _require_unique_text(self.matched_candidate_ids, "matched_candidate_ids")
        _require_unique_object_ids(self.matched_candidate_object_ids, "matched_candidate_object_ids")
        if len(self.matched_candidate_ids) != len(self.matched_candidate_object_ids):
            raise DuplicateDetectorError("matched candidate IDs/object IDs must align")
        _require_unique_text(self.matched_dead_family_ids, "matched_dead_family_ids")
        _require_unique_object_ids(self.matched_dead_family_object_ids, "matched_dead_family_object_ids")
        if len(self.matched_dead_family_ids) != len(self.matched_dead_family_object_ids):
            raise DuplicateDetectorError("matched dead-family IDs/object IDs must align")
        for score, field in (
            (self.max_structural_score, "max_structural_score"),
            (self.max_dead_family_score, "max_dead_family_score"),
            (self.structural_threshold, "structural_threshold"),
            (self.dead_family_threshold, "dead_family_threshold"),
        ):
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0.0 <= float(score) <= 1.0:
                raise DuplicateDetectorError(f"{field} must be within [0,1]")
        if not isinstance(self.minimum_shared_tokens, int) or self.minimum_shared_tokens < 1:
            raise DuplicateDetectorError("minimum_shared_tokens must be a positive integer")
        if self.fingerprint_algorithm != FINGERPRINT_ALGORITHM or self.similarity_algorithm != SIMILARITY_ALGORITHM:
            raise DuplicateDetectorError("screening algorithm identity drift")
        expected_review = bool(self.flags)
        if self.review_required is not expected_review:
            raise DuplicateDetectorError("flagged screening reports must require review")
        if any((self.automatic_rejection, self.mathematical_equivalence_established, self.proof_of_falsehood)):
            raise DuplicateDetectorError("similarity screening may not reject or establish mathematical authority")
        if self.claim_level_effect != "none" or self.evidence_effect != "none":
            raise DuplicateDetectorError("similarity screening may not alter claim/evidence authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for key in (
            "flags",
            "matched_candidate_ids",
            "matched_candidate_object_ids",
            "matched_dead_family_ids",
            "matched_dead_family_object_ids",
        ):
            value[key] = list(value[key])
        return value


class DuplicateDeadFamilyDetector:
    """Deterministic, locally calibrated screening against prior candidates/failures."""

    def __init__(
        self,
        *,
        structural_threshold: float,
        dead_family_threshold: float,
        minimum_shared_tokens: int,
    ) -> None:
        for value, field in (
            (structural_threshold, "structural_threshold"),
            (dead_family_threshold, "dead_family_threshold"),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 < float(value) <= 1.0:
                raise DuplicateDetectorError(f"{field} must be within (0,1]")
        if not isinstance(minimum_shared_tokens, int) or minimum_shared_tokens < 1:
            raise DuplicateDetectorError("minimum_shared_tokens must be a positive integer")
        self.structural_threshold = float(structural_threshold)
        self.dead_family_threshold = float(dead_family_threshold)
        self.minimum_shared_tokens = minimum_shared_tokens

    def screen(
        self,
        *,
        report_id: str,
        candidate: CandidateReference,
        origin: CandidateOriginClassification,
        prior_candidates: tuple[CandidateReference, ...],
        dead_families: tuple[tuple[DeadFamilyRecord, str], ...],
        origin_classification_object_id: str | None = None,
    ) -> SimilarityReport:
        _require_safe_id(report_id, "report_id")
        candidate.validate()
        origin.validate()
        if origin.candidate_id != candidate.candidate.candidate_id or origin.candidate_object_id != candidate.candidate_object_id:
            raise DuplicateDetectorError("origin classification does not bind the screened candidate")
        if origin_classification_object_id is not None:
            _require_object_id(origin_classification_object_id, "origin_classification_object_id")

        current = candidate.candidate
        current_track = _target_track(current)
        current_fingerprint = candidate_exact_fingerprint(current)
        current_tokens = candidate_mechanism_tokens(current)

        exact_matches: list[CandidateReference] = []
        structural_matches: list[tuple[CandidateReference, float]] = []
        max_structural = 0.0

        seen_candidate_objects: set[str] = set()
        for prior in prior_candidates:
            prior.validate()
            if prior.candidate_object_id == candidate.candidate_object_id:
                continue
            if prior.candidate_object_id in seen_candidate_objects:
                raise DuplicateDetectorError("prior candidate object IDs must be unique")
            seen_candidate_objects.add(prior.candidate_object_id)
            other = prior.candidate
            if other.domain_id != current.domain_id or other.hypothesis_set_id != current.hypothesis_set_id:
                continue
            if _target_track(other) != current_track:
                continue
            if candidate_exact_fingerprint(other) == current_fingerprint:
                exact_matches.append(prior)
                continue
            score = _jaccard(current_tokens, candidate_mechanism_tokens(other), self.minimum_shared_tokens)
            max_structural = max(max_structural, score)
            if score >= self.structural_threshold:
                structural_matches.append((prior, score))

        dead_matches: list[tuple[DeadFamilyRecord, str, float]] = []
        max_dead = 0.0
        seen_family_objects: set[str] = set()
        for family, family_object_id in dead_families:
            family.validate()
            _require_object_id(family_object_id, "dead_family_object_id")
            if family_object_id in seen_family_objects:
                raise DuplicateDetectorError("dead-family object IDs must be unique")
            seen_family_objects.add(family_object_id)
            if family.domain_id != current.domain_id or family.hypothesis_set_id != current.hypothesis_set_id:
                continue
            if family.target_hypothesis != current_track:
                continue
            score = _jaccard(current_tokens, family.mechanism_tokens, self.minimum_shared_tokens)
            max_dead = max(max_dead, score)
            if score >= self.dead_family_threshold:
                dead_matches.append((family, family_object_id, score))

        flags: list[str] = []
        if exact_matches:
            flags.append("exact_duplicate")
        if structural_matches:
            flags.append("structural_near_duplicate")
        if dead_matches:
            flags.append("dead_family_match")

        if exact_matches:
            primary: PrimaryClassification = "exact_duplicate"
        elif dead_matches:
            primary = "dead_family_match"
        elif structural_matches:
            primary = "structural_near_duplicate"
        else:
            primary = "novel_to_screening_memory"

        matched_candidates = sorted(
            [*exact_matches, *(item[0] for item in structural_matches)],
            key=lambda item: (item.candidate.candidate_id, item.candidate_object_id),
        )
        # A candidate may appear in only one bucket because exact matches skip scoring.
        matched_dead = sorted(dead_matches, key=lambda item: (item[0].family_id, item[1]))

        report = SimilarityReport(
            report_id=report_id,
            candidate_id=current.candidate_id,
            candidate_object_id=candidate.candidate_object_id,
            origin_class=origin.origin_class,
            origin_classification_object_id=origin_classification_object_id,
            exact_fingerprint_sha256=current_fingerprint,
            primary_classification=primary,
            flags=tuple(flags),
            matched_candidate_ids=tuple(item.candidate.candidate_id for item in matched_candidates),
            matched_candidate_object_ids=tuple(item.candidate_object_id for item in matched_candidates),
            matched_dead_family_ids=tuple(item[0].family_id for item in matched_dead),
            matched_dead_family_object_ids=tuple(item[1] for item in matched_dead),
            max_structural_score=max_structural,
            max_dead_family_score=max_dead,
            structural_threshold=self.structural_threshold,
            dead_family_threshold=self.dead_family_threshold,
            minimum_shared_tokens=self.minimum_shared_tokens,
            review_required=bool(flags),
        )
        report.validate()
        return report

    def authority_snapshot(self) -> dict[str, bool]:
        return {
            "similarity_establishes_mathematical_equivalence": False,
            "dead_family_match_proves_falsehood": False,
            "screening_may_reject_candidate": False,
            "screening_may_change_claim_level": False,
            "screening_may_create_domain_evidence": False,
            "screening_may_select_winner": False,
        }
