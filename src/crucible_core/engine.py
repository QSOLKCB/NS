# SPDX-License-Identifier: Apache-2.0
"""State machine for candidate competition, holdouts and failure memory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

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

    def __init__(self, *, domain_id: str, allowed_claim_levels: tuple[str, ...]) -> None:
        if not domain_id:
            raise ValueError("domain_id is required")
        if not allowed_claim_levels or len(allowed_claim_levels) != len(set(allowed_claim_levels)):
            raise ValueError("allowed_claim_levels must be non-empty and unique")
        self.domain_id = domain_id
        self.allowed_claim_levels = allowed_claim_levels
        self._candidates: dict[str, Candidate] = {}
        self._hypothesis_sets: dict[str, HypothesisSet] = {}
        self._evidence: dict[str, EvidenceRecord] = {}
        self._constraint_results: dict[str, ConstraintResult] = {}
        self._failure_ledger: list[FailureRecord] = []

    def register_candidate(self, candidate: Candidate) -> None:
        candidate.validate()
        if candidate.domain_id != self.domain_id:
            raise CrucibleStateError("candidate domain does not match Crucible domain")
        if candidate.claim_level not in self.allowed_claim_levels:
            raise CrucibleStateError("candidate claim level is not declared by the domain")
        if candidate.candidate_id in self._candidates:
            raise CrucibleStateError("candidate_id already registered")
        missing_parents = [
            parent for parent in candidate.parent_candidate_ids if parent not in self._candidates
        ]
        if missing_parents:
            raise CrucibleStateError(f"parent candidates not registered: {missing_parents}")
        self._candidates[candidate.candidate_id] = candidate

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
        result.validate()
        candidate = self._require_candidate(result.candidate_id)
        if result.domain_id != self.domain_id:
            raise CrucibleStateError("constraint-result domain does not match")
        if result.result_id in self._constraint_results:
            raise CrucibleStateError("constraint result already registered")
        missing_evidence = [eid for eid in result.evidence_ids if eid not in self._evidence]
        if missing_evidence:
            raise CrucibleStateError(f"constraint result references unknown evidence: {missing_evidence}")

        if result.outcome == "fail" and result.severity == "hard":
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

        self._constraint_results[result.result_id] = result
        if result.outcome != "fail" or result.severity != "hard":
            return None

        assert failure_id is not None
        if any(item.failure_id == failure_id for item in self._failure_ledger):
            raise CrucibleStateError("failure_id already recorded")
        assert claim_level_after is not None
        if claim_level_after not in self.allowed_claim_levels:
            raise CrucibleStateError("failure downgrade target is not a domain claim level")

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
        self._failure_ledger.append(failure)
        self._candidates[candidate.candidate_id] = replace(
            candidate.reject(), claim_level=claim_level_after
        )
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
