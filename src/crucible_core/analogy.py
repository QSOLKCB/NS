# SPDX-License-Identifier: Apache-2.0
"""Cross-domain analogy firewall for Crucible candidate generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .models import Candidate

FIREWALL_VERSION = "0.1.0"

MappingClass = Literal[
    "exact_correspondence",
    "operator_correspondence",
    "structural_analogy",
    "heuristic_analogy",
    "visual_resemblance",
    "explicit_non_correspondence",
]

_ALLOWED_MAPPING_CLASSES = {
    "exact_correspondence",
    "operator_correspondence",
    "structural_analogy",
    "heuristic_analogy",
    "visual_resemblance",
    "explicit_non_correspondence",
}
_ALLOWED_USES = {"candidate_generation", "negative_control"}
_GLOBALLY_FORBIDDEN_USES = {
    "domain_evidence",
    "claim_promotion",
    "proof_barrier_satisfaction",
    "domain_equivalence_claim",
    "winner_selection",
}
_POSITIVE_TRANSFER_CLASSES = {
    "exact_correspondence",
    "operator_correspondence",
    "structural_analogy",
    "heuristic_analogy",
}


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_unique_text(values: tuple[str, ...], field: str, *, allow_empty: bool = False) -> None:
    if not allow_empty and not values:
        raise ValueError(f"{field} must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{field} must contain unique values")
    for value in values:
        _require_text(value, field)


class AnalogyFirewallError(ValueError):
    """Raised when a cross-domain transfer would exceed analogy authority."""


@dataclass(frozen=True)
class AnalogyRecord:
    """A provenance-bearing cross-domain relationship declaration."""

    analogy_id: str
    source_domain: str
    target_domain: str
    mapping_class: MappingClass
    shared_structure: str
    assumptions: tuple[str, ...]
    known_differences: tuple[str, ...]
    allowed_uses: tuple[str, ...]
    forbidden_inferences: tuple[str, ...]
    provenance_ref: str

    def validate(self) -> None:
        for field in (
            "analogy_id",
            "source_domain",
            "target_domain",
            "shared_structure",
            "provenance_ref",
        ):
            _require_text(getattr(self, field), field)
        if self.mapping_class not in _ALLOWED_MAPPING_CLASSES:
            raise ValueError("invalid mapping_class")
        _require_unique_text(self.assumptions, "assumptions", allow_empty=True)
        _require_unique_text(self.known_differences, "known_differences")
        _require_unique_text(self.allowed_uses, "allowed_uses")
        _require_unique_text(self.forbidden_inferences, "forbidden_inferences")
        unknown_uses = set(self.allowed_uses) - _ALLOWED_USES
        if unknown_uses:
            raise ValueError(f"unsupported allowed_uses: {sorted(unknown_uses)}")
        if self.mapping_class in {"visual_resemblance", "explicit_non_correspondence"}:
            if "candidate_generation" in self.allowed_uses:
                raise ValueError(
                    f"{self.mapping_class} may not authorize positive candidate generation"
                )
        elif "candidate_generation" not in self.allowed_uses:
            raise ValueError(
                "positive transfer classes must explicitly allow candidate_generation"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for key in ("assumptions", "known_differences", "allowed_uses", "forbidden_inferences"):
            value[key] = list(value[key])
        return value


class AnalogyFirewall:
    """Domain-neutral transfer gate.

    The firewall may authorize a cross-domain relationship for *candidate
    generation only*. It never turns an analogy into domain evidence, a claim
    promotion, proof-barrier satisfaction, a winner, or domain equivalence.
    """

    def __init__(self, *, target_domain: str, initial_claim_level: str = "exploratory") -> None:
        _require_text(target_domain, "target_domain")
        _require_text(initial_claim_level, "initial_claim_level")
        if initial_claim_level != "exploratory":
            raise AnalogyFirewallError(
                "analogy-derived candidates must start at exploratory claim level"
            )
        self.target_domain = target_domain
        self.initial_claim_level = "exploratory"
        self._records: dict[str, AnalogyRecord] = {}

    def register(self, record: AnalogyRecord) -> None:
        record.validate()
        if record.analogy_id in self._records:
            raise AnalogyFirewallError("analogy_id already registered")
        self._records[record.analogy_id] = record

    def authorize_use(self, analogy_id: str, use: str) -> None:
        _require_text(use, "use")
        record = self._require_record(analogy_id)
        if record.target_domain != self.target_domain:
            raise AnalogyFirewallError(
                "analogy target domain does not match this firewall target"
            )
        if use in _GLOBALLY_FORBIDDEN_USES:
            raise AnalogyFirewallError(
                f"analogy firewall forbids {use}; target-domain validation is required"
            )
        if use not in _ALLOWED_USES:
            raise AnalogyFirewallError(f"unknown analogy use: {use}")
        if use not in record.allowed_uses:
            raise AnalogyFirewallError(
                f"analogy {analogy_id} does not authorize use={use}"
            )
        if use == "candidate_generation" and record.mapping_class not in _POSITIVE_TRANSFER_CLASSES:
            raise AnalogyFirewallError(
                f"mapping class {record.mapping_class} cannot generate a positive candidate"
            )

    def issue_candidate(
        self,
        *,
        analogy_id: str,
        candidate_id: str,
        hypothesis_set_id: str,
        hypothesis: str,
        generation_method: str,
        parent_candidate_ids: tuple[str, ...] = (),
        assumptions: tuple[str, ...] = (),
    ) -> Candidate:
        """Create an exploratory target-domain candidate from an authorized analogy."""
        record = self._require_record(analogy_id)
        self.authorize_use(analogy_id, "candidate_generation")
        inherited = (
            f"analogy_source={analogy_id}",
            f"mapping_class={record.mapping_class}",
            "cross_domain_transfer_requires_target_domain_validation",
        )
        candidate = Candidate(
            candidate_id=candidate_id,
            domain_id=self.target_domain,
            hypothesis_set_id=hypothesis_set_id,
            hypothesis=hypothesis,
            claim_level="exploratory",
            generation_method=f"cross_domain_transfer:{analogy_id}:{generation_method}",
            parent_candidate_ids=parent_candidate_ids,
            assumptions=tuple(assumptions) + inherited,
        )
        try:
            candidate.validate_for_registration()
        except ValueError as exc:
            raise AnalogyFirewallError(
                f"analogy-derived candidate is not registration-valid: {exc}"
            ) from exc
        return candidate

    def export_registry(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._records[key].to_dict() for key in sorted(self._records))

    def authority_snapshot(self) -> dict[str, Any]:
        return {
            "candidate_generation": True,
            "domain_evidence": False,
            "claim_promotion": False,
            "proof_barrier_satisfaction": False,
            "domain_equivalence_claim": False,
            "winner_selection": False,
            "target_domain_validation_required": True,
            "source_proof_status_inherited": False,
            "source_evidence_status_inherited": False,
            "initial_claim_level": "exploratory",
        }

    def _require_record(self, analogy_id: str) -> AnalogyRecord:
        try:
            return self._records[analogy_id]
        except KeyError as exc:
            raise AnalogyFirewallError(f"unknown analogy: {analogy_id}") from exc
