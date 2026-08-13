# SPDX-License-Identifier: Apache-2.0
"""State machine for candidate competition, holdouts and failure memory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any, Mapping

from .models import (
    Candidate,
    ConstraintResult,
    EvidenceRecord,
    FailureRecord,
    HypothesisSet,
)


class CrucibleStateError(ValueError):
    """Raised when an operation would violate a Crucible invariant."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


class Crucible:
    """Domain-neutral orchestration.

    The core never computes truth, confidence, novelty or claim promotion.
    A domain adapter supplies constraints and the domain's epistemic standard.
    """

    def __init__(
        self,
        *,
        domain_id: str,
        allowed_claim_levels: tuple[str, ...],
        constraint_severities: Mapping[str, str] | None = None,
    ) -> None:
        if not domain_id:
            raise ValueError("domain_id is required")
        if not allowed_claim_levels or len(allowed_claim_levels) != len(set(allowed_claim_levels)):
            raise ValueError("allowed_claim_levels must be non-empty and unique")
        severity_map = dict(constraint_severities or {})
        for constraint_id, severity in severity_map.items():
            if not isinstance(constraint_id, str) or not constraint_id.strip():
                raise ValueError("constraint severity IDs must be non-empty strings")
            if severity not in {"hard", "soft"}:
                raise ValueError("constraint severities must be hard or soft")

        self.domain_id = domain_id
        self.allowed_claim_levels = allowed_claim_levels
        self.constraint_severities = severity_map
        self._candidates: dict[str, Candidate] = {}
        self._hypothesis_sets: dict[str, HypothesisSet] = {}
        self._evidence: dict[str, EvidenceRecord] = {}
        self._constraint_results: dict[str, ConstraintResult] = {}
        self._failure_ledger: list[FailureRecord] = []

    def _validate_candidate_registration(
        self,
        candidate: Candidate,
        *,
        allow_existing_hypothesis_set: bool,
    ) -> None:
        try:
            candidate.validate_for_registration()
        except ValueError as exc:
            raise CrucibleStateError(str(exc)) from exc
        if candidate.domain_id != self.domain_id:
            raise CrucibleStateError("candidate domain does not match Crucible domain")
        if candidate.claim_level not in self.allowed_claim_levels:
            raise CrucibleStateError("candidate claim level is not declared by the domain")
        if candidate.candidate_id in self._candidates:
            raise CrucibleStateError("candidate_id already registered")
        if (
            not allow_existing_hypothesis_set
            and candidate.hypothesis_set_id in self._hypothesis_sets
        ):
            raise CrucibleStateError(
                "hypothesis set already registered; use add_candidate_to_hypothesis_set"
            )
        missing_parents = [
            parent for parent in candidate.parent_candidate_ids if parent not in self._candidates
        ]
        if missing_parents:
            raise CrucibleStateError(f"parent candidates not registered: {missing_parents}")

    def register_candidate(self, candidate: Candidate) -> None:
        self._validate_candidate_registration(
            candidate,
            allow_existing_hypothesis_set=False,
        )
        self._candidates[candidate.candidate_id] = candidate

    def add_candidate_to_hypothesis_set(self, candidate: Candidate) -> None:
        """Atomically register a new candidate into an already registered set."""
        self._validate_candidate_registration(
            candidate,
            allow_existing_hypothesis_set=True,
        )
        try:
            hypothesis_set = self._hypothesis_sets[candidate.hypothesis_set_id]
        except KeyError as exc:
            raise CrucibleStateError(
                "hypothesis set is not registered; use register_candidate first"
            ) from exc

        updated = replace(
            hypothesis_set,
            candidate_ids=hypothesis_set.candidate_ids + (candidate.candidate_id,),
        )
        updated.validate()

        self._candidates[candidate.candidate_id] = candidate
        self._hypothesis_sets[hypothesis_set.hypothesis_set_id] = updated

    def register_hypothesis_set(self, hypothesis_set: HypothesisSet) -> None:
        hypothesis_set.validate()
        if hypothesis_set.domain_id != self.domain_id:
            raise CrucibleStateError("hypothesis set domain does not match")
        if hypothesis_set.hypothesis_set_id in self._hypothesis_sets:
            raise CrucibleStateError("hypothesis_set_id already registered")
        missing = [cid for cid in hypothesis_set.candidate_ids if cid not in self._candidates]
        if missing:
            raise CrucibleStateError(f"hypothesis set references unknown candidates: {missing}")
        for cid in hypothesis_set.candidate_ids:
            if self._candidates[cid].hypothesis_set_id != hypothesis_set.hypothesis_set_id:
                raise CrucibleStateError("candidate/hypothesis-set identity mismatch")

        declared_members = {
            cid
            for cid, candidate in self._candidates.items()
            if candidate.hypothesis_set_id == hypothesis_set.hypothesis_set_id
        }
        incoming_members = set(hypothesis_set.candidate_ids)
        if declared_members != incoming_members:
            missing_from_set = sorted(declared_members - incoming_members)
            unexpected_in_set = sorted(incoming_members - declared_members)
            raise CrucibleStateError(
                "hypothesis-set membership must be reciprocal: "
                f"missing_from_set={missing_from_set}, unexpected_in_set={unexpected_in_set}"
            )

        self._hypothesis_sets[hypothesis_set.hypothesis_set_id] = hypothesis_set

    def freeze_candidate(self, candidate_id: str) -> Candidate:
        candidate = self._require_candidate(candidate_id)
        frozen = candidate.freeze()
        self._candidates[candidate_id] = frozen
        return frozen

    def attach_evidence(self, evidence: EvidenceRecord) -> None:
        evidence.validate()
        candidate = self._require_candidate(evidence.candidate_id)
        if evidence.domain_id != self.domain_id:
            raise CrucibleStateError("evidence domain does not match")
        if evidence.evidence_id in self._evidence:
            raise CrucibleStateError("evidence_id already registered")
        if evidence.stage == "holdout" and not candidate.frozen:
            raise CrucibleStateError(
                "sealed holdout evidence may be attached only after candidate freeze"
            )
        self._evidence[evidence.evidence_id] = evidence

    def record_constraint_result(
        self,
        result: ConstraintResult,
        *,
        failure_id: str | None = None,
        failure_class: str | None = None,
        reusable_lesson: str | None = None,
        claim_level_after: str | None = None,
        recorded_by: str | None = None,
    ) -> FailureRecord | None:
        """Validate a constraint transaction completely before mutating state."""
        result.validate()
        candidate = self._require_candidate(result.candidate_id)
        if result.domain_id != self.domain_id:
            raise CrucibleStateError("constraint-result domain does not match")
        if result.result_id in self._constraint_results:
            raise CrucibleStateError("constraint result already registered")

        expected_severity = self.constraint_severities.get(result.constraint_id)
        if expected_severity is not None and result.severity != expected_severity:
            raise CrucibleStateError(
                "constraint severity does not match domain adapter: "
                f"{result.constraint_id} requires {expected_severity}"
            )

        missing_evidence = [eid for eid in result.evidence_ids if eid not in self._evidence]
        if missing_evidence:
            raise CrucibleStateError(
                f"constraint result references unknown evidence: {missing_evidence}"
            )
        mismatched_evidence = [
            eid
            for eid in result.evidence_ids
            if self._evidence[eid].candidate_id != result.candidate_id
        ]
        if mismatched_evidence:
            raise CrucibleStateError(
                "constraint evidence must belong to the same candidate: "
                f"{mismatched_evidence}"
            )

        is_hard_failure = result.outcome == "fail" and result.severity == "hard"
        if not is_hard_failure:
            self._constraint_results[result.result_id] = result
            return None

        required = {
            "failure_id": failure_id,
            "failure_class": failure_class,
            "reusable_lesson": reusable_lesson,
            "claim_level_after": claim_level_after,
            "recorded_by": recorded_by,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise CrucibleStateError(
                f"hard failure requires an append-only failure record; missing {missing}"
            )

        assert failure_id is not None
        if any(item.failure_id == failure_id for item in self._failure_ledger):
            raise CrucibleStateError("failure_id already recorded")

        assert claim_level_after is not None
        if claim_level_after not in self.allowed_claim_levels:
            raise CrucibleStateError("failure downgrade target is not a domain claim level")
        current_level_index = self.allowed_claim_levels.index(candidate.claim_level)
        target_level_index = self.allowed_claim_levels.index(claim_level_after)
        if target_level_index > current_level_index:
            raise CrucibleStateError("recording a failure may not promote a claim level")

        failure = FailureRecord(
            failure_id=failure_id,
            candidate_id=candidate.candidate_id,
            domain_id=self.domain_id,
            failed_constraint=result.constraint_id,
            failure_class=str(failure_class),
            evidence_ids=result.evidence_ids,
            reusable_lesson=str(reusable_lesson),
            claim_level_before=candidate.claim_level,
            claim_level_after=claim_level_after,
            recorded_by=str(recorded_by),
        )
        failure.validate()
        rejected_candidate = replace(
            candidate.reject(),
            claim_level=claim_level_after,
        )
        rejected_candidate.validate()

        # Transaction boundary: all validation above must succeed before any mutation.
        self._constraint_results[result.result_id] = result
        self._failure_ledger.append(failure)
        self._candidates[candidate.candidate_id] = rejected_candidate
        return failure

    def frontier(self) -> tuple[str, ...]:
        """Return candidates not rejected by a declared hard domain constraint."""
        return tuple(
            sorted(
                cid
                for cid, candidate in self._candidates.items()
                if candidate.status != "rejected_by_domain_constraint"
            )
        )

    def failure_ledger(self) -> tuple[FailureRecord, ...]:
        return tuple(self._failure_ledger)

    def export_state(self) -> dict[str, Any]:
        value = {
            "domain_id": self.domain_id,
            "allowed_claim_levels": list(self.allowed_claim_levels),
            "constraint_severities": {
                key: self.constraint_severities[key]
                for key in sorted(self.constraint_severities)
            },
            "hypothesis_sets": [
                self._hypothesis_sets[key].to_dict() for key in sorted(self._hypothesis_sets)
            ],
            "candidates": [self._candidates[key].to_dict() for key in sorted(self._candidates)],
            "evidence": [self._evidence[key].to_dict() for key in sorted(self._evidence)],
            "constraint_results": [
                self._constraint_results[key].to_dict()
                for key in sorted(self._constraint_results)
            ],
            "failure_ledger": [record.to_dict() for record in self._failure_ledger],
            "selection_authority": "domain_adapter_or_human_not_crucible_core",
            "universal_confidence_score": None,
        }
        value["state_sha256"] = canonical_sha256(value)
        return value

    def _require_candidate(self, candidate_id: str) -> Candidate:
        try:
            return self._candidates[candidate_id]
        except KeyError as exc:
            raise CrucibleStateError(f"unknown candidate: {candidate_id}") from exc
