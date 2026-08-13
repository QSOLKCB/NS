# SPDX-License-Identifier: Apache-2.0
"""Schema-constrained ML generator airlock for Crucible candidate proposals.

Models propose untrusted JSON. The airlock may turn a valid proposal into an
*exploratory* Candidate, but it never grants evidence, proof, claim promotion,
or winner-selection authority. Every provider/model attempt is retained in a
separate content-addressed, tamper-evident generation journal anchored to the
Crucible ledger state used to construct the context packet.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from .engine import canonical_json_bytes
from .ledger import ContentAddressedLedger, LedgerError
from .models import Candidate

GENERATOR_VERSION = "0.1.0"
_MAX_SAFE_ID_LENGTH = 128
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_REQUIRED_PROPOSAL_FIELDS = {
    "proposal_id",
    "target_hypothesis",
    "precise_statement",
    "motivation",
    "assumptions",
    "claimed_dependencies",
    "suggested_tests",
    "possible_failure_modes",
    "analogy_sources",
    "parent_candidate_ids",
    "generator_notes",
}
_FORBIDDEN_STRUCTURED_FIELDS = {
    "claim_level",
    "claim_status",
    "evidence_status",
    "proof_status",
    "proved",
    "solves_clay",
    "winner",
    "confidence",
    "confidence_score",
    "truth_probability",
}
_FORBIDDEN_AUTHORITY_PHRASES = (
    "public_solution_claim",
    "solution established",
    "millennium problem resolved",
    "proof complete",
    "solves clay",
)
_REJECTION_CODES = {
    "invalid_json",
    "proposal_not_object",
    "schema_failure",
    "forbidden_authority_field",
    "forbidden_authority_language",
    "unknown_hypothesis",
    "unknown_parent",
    "parent_not_in_context",
    "unknown_theorem_dependency",
    "theorem_dependency_not_in_context",
    "unregistered_analogy",
    "analogy_requires_firewall_route",
    "duplicate_candidate_id",
    "invalid_context",
    "provider_failure",
    "candidate_validation_failure",
}
_PARSE_STATUSES = {"not_attempted", "not_parsed", "parsed"}


class GeneratorAirlockError(ValueError):
    """Raised when generator orchestration itself is invalid."""


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise GeneratorAirlockError(f"{field} must be a non-empty string")


def _require_safe_id(value: str, field: str) -> None:
    _require_text(value, field)
    if len(value) > _MAX_SAFE_ID_LENGTH:
        raise GeneratorAirlockError(
            f"{field} exceeds {_MAX_SAFE_ID_LENGTH}-character component-safe limit"
        )
    if not _SAFE_ID.fullmatch(value):
        raise GeneratorAirlockError(f"{field} contains unsupported characters")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise GeneratorAirlockError(f"{field} must be lowercase 64-hex SHA-256")


def _require_commit(value: str) -> None:
    if not isinstance(value, str) or not _COMMIT.fullmatch(value):
        raise GeneratorAirlockError("source_commit must be exact lowercase 40-hex")


def _require_utc_timestamp(value: str) -> None:
    _require_text(value, "recorded_at_utc")
    if not _UTC_Z.fullmatch(value):
        raise GeneratorAirlockError("recorded_at_utc must be ISO-8601 UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GeneratorAirlockError("recorded_at_utc must be a valid UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise GeneratorAirlockError("recorded_at_utc must carry UTC timezone information")


def _require_unique_text(
    values: tuple[str, ...], field: str, *, allow_empty: bool = True
) -> None:
    if not allow_empty and not values:
        raise GeneratorAirlockError(f"{field} must be non-empty")
    # Validate element types before hashing/uniqueness. Untrusted JSON may contain
    # dictionaries/lists, which are rejected rather than allowed to raise TypeError.
    for value in values:
        _require_text(value, field)
    if len(values) != len(set(values)):
        raise GeneratorAirlockError(f"{field} must contain unique values")


def _contains_forbidden_authority_language(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in _FORBIDDEN_AUTHORITY_PHRASES)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json_loads(raw: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    return json.loads(raw, parse_constant=reject_constant)


@dataclass(frozen=True)
class GeneratorContextPacket:
    """Bounded, hashable research context supplied to an untrusted generator."""

    domain_id: str
    hypothesis_set_id: str
    target_hypotheses: tuple[str, ...]
    theorem_ids: tuple[str, ...]
    proof_barrier_ids: tuple[str, ...]
    frontier_candidate_ids: tuple[str, ...]
    failure_lessons: tuple[str, ...]
    permitted_analogy_ids: tuple[str, ...]
    ledger_event_count: int
    ledger_head_event_sha256: str | None
    source_commit: str
    task: str

    def validate(self) -> None:
        for field in ("domain_id", "hypothesis_set_id", "task"):
            _require_text(getattr(self, field), field)
        _require_unique_text(
            self.target_hypotheses, "target_hypotheses", allow_empty=False
        )
        _require_unique_text(self.theorem_ids, "theorem_ids")
        _require_unique_text(self.proof_barrier_ids, "proof_barrier_ids")
        _require_unique_text(self.frontier_candidate_ids, "frontier_candidate_ids")
        _require_unique_text(self.failure_lessons, "failure_lessons")
        _require_unique_text(self.permitted_analogy_ids, "permitted_analogy_ids")
        if not isinstance(self.ledger_event_count, int) or self.ledger_event_count < 0:
            raise GeneratorAirlockError(
                "ledger_event_count must be a non-negative integer"
            )
        if self.ledger_head_event_sha256 is None:
            if self.ledger_event_count != 0:
                raise GeneratorAirlockError(
                    "non-empty ledger context requires a head digest"
                )
        else:
            _require_sha256(
                self.ledger_head_event_sha256, "ledger_head_event_sha256"
            )
            if self.ledger_event_count == 0:
                raise GeneratorAirlockError(
                    "empty ledger context must not declare a head digest"
                )
        _require_commit(self.source_commit)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for key in (
            "target_hypotheses",
            "theorem_ids",
            "proof_barrier_ids",
            "frontier_candidate_ids",
            "failure_lessons",
            "permitted_analogy_ids",
        ):
            value[key] = list(value[key])
        return value

    def sha256(self) -> str:
        return _sha256_bytes(canonical_json_bytes(self.to_dict()))


@dataclass(frozen=True)
class CandidateProposal:
    """Untrusted model proposal after strict structural validation."""

    proposal_id: str
    target_hypothesis: str
    precise_statement: str
    motivation: str
    assumptions: tuple[str, ...]
    claimed_dependencies: tuple[str, ...]
    suggested_tests: tuple[str, ...]
    possible_failure_modes: tuple[str, ...]
    analogy_sources: tuple[str, ...]
    parent_candidate_ids: tuple[str, ...]
    generator_notes: str

    def validate(self) -> None:
        for field in (
            "proposal_id",
            "target_hypothesis",
            "precise_statement",
            "motivation",
            "generator_notes",
        ):
            _require_text(getattr(self, field), field)
        _require_safe_id(self.proposal_id, "proposal_id")
        _require_safe_id(self.target_hypothesis, "target_hypothesis")
        _require_unique_text(self.assumptions, "assumptions", allow_empty=False)
        _require_unique_text(self.claimed_dependencies, "claimed_dependencies")
        _require_unique_text(self.suggested_tests, "suggested_tests", allow_empty=False)
        _require_unique_text(
            self.possible_failure_modes,
            "possible_failure_modes",
            allow_empty=False,
        )
        _require_unique_text(self.analogy_sources, "analogy_sources")
        _require_unique_text(self.parent_candidate_ids, "parent_candidate_ids")

        # Scan every model-supplied string, including list elements, so authority
        # language cannot be hidden in assumptions/tests/failure modes.
        all_text = (
            self.proposal_id,
            self.target_hypothesis,
            self.precise_statement,
            self.motivation,
            self.generator_notes,
            *self.assumptions,
            *self.claimed_dependencies,
            *self.suggested_tests,
            *self.possible_failure_modes,
            *self.analogy_sources,
            *self.parent_candidate_ids,
        )
        if any(_contains_forbidden_authority_language(text) for text in all_text):
            raise GeneratorAirlockError(
                "proposal contains forbidden authority language"
            )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = asdict(self)
        for key in (
            "assumptions",
            "claimed_dependencies",
            "suggested_tests",
            "possible_failure_modes",
            "analogy_sources",
            "parent_candidate_ids",
        ):
            value[key] = list(value[key])
        return value


class GeneratorBackend(Protocol):
    """Provider-neutral generation protocol."""

    @property
    def backend_id(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def generate(self, context_packet: Mapping[str, Any]) -> str: ...


@dataclass(frozen=True)
class DeterministicFixtureBackend:
    """Deterministic backend used for CI and replay tests."""

    output: str
    backend_id: str = "fixture"
    model_id: str = "deterministic-fixture-v1"

    def generate(self, context_packet: Mapping[str, Any]) -> str:
        del context_packet
        return self.output


@dataclass(frozen=True)
class CandidateIntakeDecision:
    attempt_id: str
    accepted: bool
    rejection_reasons: tuple[str, ...]
    context_sha256: str
    raw_output_sha256: str
    candidate: Candidate | None

    def validate(self) -> None:
        _require_safe_id(self.attempt_id, "attempt_id")
        _require_sha256(self.context_sha256, "context_sha256")
        _require_sha256(self.raw_output_sha256, "raw_output_sha256")
        _require_unique_text(self.rejection_reasons, "rejection_reasons")
        unknown = set(self.rejection_reasons) - _REJECTION_CODES
        if unknown:
            raise GeneratorAirlockError(
                f"unknown rejection reason(s): {sorted(unknown)}"
            )
        if self.accepted:
            if self.rejection_reasons or self.candidate is None:
                raise GeneratorAirlockError(
                    "accepted decision must contain only a candidate"
                )
            self.candidate.validate_for_registration()
            if self.candidate.claim_level != "exploratory":
                raise GeneratorAirlockError(
                    "accepted ML candidate must remain exploratory"
                )
        elif self.candidate is not None:
            raise GeneratorAirlockError(
                "rejected decision may not contain a candidate"
            )


class GeneratorAttemptJournal:
    """Tamper-evident content-addressed journal for every generator attempt."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.objects_root = self.root / "objects" / "sha256"
        self.log_path = self.root / "generation.jsonl"
        self.objects_root.mkdir(parents=True, exist_ok=True)
        self._count = 0
        self._head: str | None = None
        self._attempt_ids: set[str] = set()
        self._initialize()

    def _object_path(self, digest: str) -> Path:
        _require_sha256(digest, "attempt object digest")
        return self.objects_root / digest[:2] / f"{digest[2:]}.json"

    def _write_immutable(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != data:
                raise GeneratorAirlockError(
                    "immutable generation object differs"
                )
            return
        temp = path.with_name(
            f".{path.name}.tmp-{os.getpid()}-{_sha256_bytes(data)[:12]}"
        )
        temp.unlink(missing_ok=True)
        try:
            with temp.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def _read_attempt_object(self, digest: str) -> dict[str, Any]:
        path = self._object_path(digest)
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != digest:
            raise GeneratorAirlockError(
                "generation attempt object missing or hash-mismatched"
            )
        try:
            value = _strict_json_loads(path.read_text("utf-8"))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            raise GeneratorAirlockError(
                "generation attempt object contains invalid JSON"
            ) from exc
        if not isinstance(value, dict) or canonical_json_bytes(value) != path.read_bytes():
            raise GeneratorAirlockError(
                "generation attempt object is not canonical JSON"
            )
        if value.get("generator_version") != GENERATOR_VERSION:
            raise GeneratorAirlockError(
                "generation attempt object version mismatch"
            )
        if value.get("object_type") != "generation_attempt":
            raise GeneratorAirlockError(
                "generation attempt object type mismatch"
            )
        payload = value.get("payload")
        if not isinstance(payload, dict):
            raise GeneratorAirlockError(
                "generation attempt payload must be an object"
            )
        _require_utc_timestamp(payload.get("recorded_at_utc"))
        if payload.get("parse_status") not in _PARSE_STATUSES:
            raise GeneratorAirlockError("invalid generation parse_status")
        return value

    def _initialize(self) -> None:
        if not self.log_path.exists():
            return
        raw = self.log_path.read_bytes()
        if not raw:
            return
        previous: str | None = None
        seen: set[str] = set()
        for sequence, line in enumerate(raw.splitlines(keepends=True), start=1):
            if not line.endswith(b"\n"):
                raise GeneratorAirlockError(
                    "generation journal line lacks canonical newline"
                )
            try:
                event = _strict_json_loads(line.decode("utf-8"))
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
                raise GeneratorAirlockError(
                    "generation journal contains invalid JSON"
                ) from exc
            if not isinstance(event, dict) or canonical_json_bytes(event) != line:
                raise GeneratorAirlockError(
                    "generation journal event is not canonical JSON"
                )
            if (
                event.get("sequence") != sequence
                or event.get("previous_event_sha256") != previous
            ):
                raise GeneratorAirlockError(
                    "generation journal sequence/hash chain is broken"
                )
            event_sha = event.get("event_sha256")
            _require_sha256(event_sha, "event_sha256")
            core = dict(event)
            del core["event_sha256"]
            if _sha256_bytes(canonical_json_bytes(core)) != event_sha:
                raise GeneratorAirlockError(
                    "generation journal event hash mismatch"
                )
            attempt_id = event.get("attempt_id")
            _require_safe_id(attempt_id, "attempt_id")
            if attempt_id in seen:
                raise GeneratorAirlockError(
                    "generation journal contains duplicate attempt_id"
                )
            digest = event.get("attempt_object_sha256")
            _require_sha256(digest, "attempt_object_sha256")
            self._read_attempt_object(digest)
            previous = event_sha
            seen.add(attempt_id)
        self._count = len(seen)
        self._head = previous
        self._attempt_ids = seen

    def record(self, *, attempt_id: str, payload: Mapping[str, Any]) -> str:
        _require_safe_id(attempt_id, "attempt_id")
        _require_utc_timestamp(payload.get("recorded_at_utc"))
        if payload.get("parse_status") not in _PARSE_STATUSES:
            raise GeneratorAirlockError("invalid generation parse_status")
        if attempt_id in self._attempt_ids:
            raise GeneratorAirlockError("attempt_id already recorded")
        envelope = {
            "generator_version": GENERATOR_VERSION,
            "object_type": "generation_attempt",
            "payload": dict(payload),
        }
        data = canonical_json_bytes(envelope)
        digest = _sha256_bytes(data)
        self._write_immutable(self._object_path(digest), data)
        core = {
            "generator_version": GENERATOR_VERSION,
            "sequence": self._count + 1,
            "previous_event_sha256": self._head,
            "attempt_id": attempt_id,
            "attempt_object_sha256": digest,
        }
        event = dict(core)
        event["event_sha256"] = _sha256_bytes(canonical_json_bytes(core))
        self.root.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("ab") as handle:
            handle.write(canonical_json_bytes(event))
            handle.flush()
            os.fsync(handle.fileno())
        self._count += 1
        self._head = event["event_sha256"]
        self._attempt_ids.add(attempt_id)
        return digest

    def verify(self) -> tuple[int, str | None]:
        fresh = GeneratorAttemptJournal(self.root)
        return fresh._count, fresh._head


class GeneratorAirlock:
    """Turns untrusted generator JSON into at most an exploratory Candidate."""

    def __init__(
        self,
        *,
        domain_id: str,
        hypothesis_set_id: str,
        allowed_target_hypotheses: set[str],
        required_proof_barrier_ids: set[str],
        known_candidate_ids: set[str],
        known_theorem_ids: set[str],
        known_analogy_ids: set[str],
        journal: GeneratorAttemptJournal,
    ) -> None:
        _require_text(domain_id, "domain_id")
        _require_text(hypothesis_set_id, "hypothesis_set_id")
        if not allowed_target_hypotheses:
            raise GeneratorAirlockError(
                "allowed_target_hypotheses must be non-empty"
            )
        for collection, field in (
            (allowed_target_hypotheses, "allowed_target_hypotheses"),
            (required_proof_barrier_ids, "required_proof_barrier_ids"),
            (known_candidate_ids, "known_candidate_ids"),
            (known_theorem_ids, "known_theorem_ids"),
            (known_analogy_ids, "known_analogy_ids"),
        ):
            for value in collection:
                _require_safe_id(value, field)
        self.domain_id = domain_id
        self.hypothesis_set_id = hypothesis_set_id
        self.allowed_target_hypotheses = frozenset(allowed_target_hypotheses)
        self.required_proof_barrier_ids = frozenset(required_proof_barrier_ids)
        self.known_candidate_ids = frozenset(known_candidate_ids)
        self.known_theorem_ids = frozenset(known_theorem_ids)
        self.known_analogy_ids = frozenset(known_analogy_ids)
        self.journal = journal

    def _parse_proposal(
        self, raw_output: str
    ) -> tuple[CandidateProposal | None, list[str], str]:
        reasons: list[str] = []
        try:
            parsed = _strict_json_loads(raw_output)
        except (ValueError, json.JSONDecodeError):
            return None, ["invalid_json"], "not_parsed"
        if not isinstance(parsed, dict):
            return None, ["proposal_not_object"], "parsed"
        keys = set(parsed)
        if keys & _FORBIDDEN_STRUCTURED_FIELDS:
            reasons.append("forbidden_authority_field")
        if keys != _REQUIRED_PROPOSAL_FIELDS:
            reasons.append("schema_failure")
        if reasons:
            return None, sorted(set(reasons)), "parsed"
        list_fields = (
            "assumptions",
            "claimed_dependencies",
            "suggested_tests",
            "possible_failure_modes",
            "analogy_sources",
            "parent_candidate_ids",
        )
        if any(not isinstance(parsed[field], list) for field in list_fields):
            return None, ["schema_failure"], "parsed"
        if any(
            not isinstance(item, str)
            for field in list_fields
            for item in parsed[field]
        ):
            return None, ["schema_failure"], "parsed"
        try:
            proposal = CandidateProposal(
                proposal_id=parsed["proposal_id"],
                target_hypothesis=parsed["target_hypothesis"],
                precise_statement=parsed["precise_statement"],
                motivation=parsed["motivation"],
                assumptions=tuple(parsed["assumptions"]),
                claimed_dependencies=tuple(parsed["claimed_dependencies"]),
                suggested_tests=tuple(parsed["suggested_tests"]),
                possible_failure_modes=tuple(parsed["possible_failure_modes"]),
                analogy_sources=tuple(parsed["analogy_sources"]),
                parent_candidate_ids=tuple(parsed["parent_candidate_ids"]),
                generator_notes=parsed["generator_notes"],
            )
            proposal.validate()
        except GeneratorAirlockError as exc:
            if "authority language" in str(exc):
                return None, ["forbidden_authority_language"], "parsed"
            return None, ["schema_failure"], "parsed"
        return proposal, [], "parsed"

    def _candidate_from_proposal(
        self,
        proposal: CandidateProposal,
        *,
        context: GeneratorContextPacket,
        backend_id: str,
        model_id: str,
        context_sha256: str,
        attempt_id: str,
    ) -> tuple[Candidate | None, list[str]]:
        reasons: list[str] = []
        if proposal.target_hypothesis not in self.allowed_target_hypotheses:
            reasons.append("unknown_hypothesis")
        if proposal.proposal_id in self.known_candidate_ids:
            reasons.append("duplicate_candidate_id")

        parents = set(proposal.parent_candidate_ids)
        if parents - self.known_candidate_ids:
            reasons.append("unknown_parent")
        if parents - set(context.frontier_candidate_ids):
            reasons.append("parent_not_in_context")

        dependencies = set(proposal.claimed_dependencies)
        if dependencies - self.known_theorem_ids:
            reasons.append("unknown_theorem_dependency")
        if dependencies - set(context.theorem_ids):
            reasons.append("theorem_dependency_not_in_context")

        if set(proposal.analogy_sources) - self.known_analogy_ids:
            reasons.append("unregistered_analogy")
        elif proposal.analogy_sources:
            # Direct ML intake may not bypass PR #6. Cross-domain proposals must
            # be re-issued through AnalogyFirewall so transfer-ticket provenance
            # is created by the existing authority boundary.
            reasons.append("analogy_requires_firewall_route")
        if reasons:
            return None, sorted(set(reasons))

        assumptions = proposal.assumptions + (
            f"target_track={proposal.target_hypothesis}",
            f"generator_context_sha256={context_sha256}",
            f"generation_attempt_id={attempt_id}",
        )
        candidate = Candidate(
            candidate_id=proposal.proposal_id,
            domain_id=self.domain_id,
            hypothesis_set_id=self.hypothesis_set_id,
            hypothesis=proposal.precise_statement,
            claim_level="exploratory",
            generation_method=(
                f"ml_generator:{backend_id}:{model_id}:proposal={proposal.proposal_id}"
            ),
            parent_candidate_ids=proposal.parent_candidate_ids,
            assumptions=assumptions,
        )
        try:
            candidate.validate_for_registration()
        except ValueError:
            return None, ["candidate_validation_failure"]
        return candidate, []

    def _validate_context(self, context: GeneratorContextPacket) -> None:
        context.validate()
        if (
            context.domain_id != self.domain_id
            or context.hypothesis_set_id != self.hypothesis_set_id
        ):
            raise GeneratorAirlockError(
                "context targets the wrong domain or hypothesis set"
            )
        if set(context.target_hypotheses) != set(self.allowed_target_hypotheses):
            raise GeneratorAirlockError(
                "context target tracks must exactly match the adapter-bound competition"
            )
        if set(context.proof_barrier_ids) != set(self.required_proof_barrier_ids):
            raise GeneratorAirlockError(
                "context proof barriers must exactly match the adapter-bound registry"
            )
        if not set(context.theorem_ids).issubset(self.known_theorem_ids):
            raise GeneratorAirlockError("context contains unknown theorem IDs")
        if not set(context.frontier_candidate_ids).issubset(self.known_candidate_ids):
            raise GeneratorAirlockError(
                "context contains unknown frontier candidate IDs"
            )
        if not set(context.permitted_analogy_ids).issubset(self.known_analogy_ids):
            raise GeneratorAirlockError("context contains unknown analogy IDs")

    def run(
        self,
        *,
        backend: GeneratorBackend,
        context: GeneratorContextPacket,
        attempt_id: str,
        prompt_template_sha256: str,
        recorded_at_utc: str,
    ) -> CandidateIntakeDecision:
        """Run one backend attempt and persist its receipt regardless of outcome."""
        _require_safe_id(attempt_id, "attempt_id")
        _require_sha256(prompt_template_sha256, "prompt_template_sha256")
        _require_utc_timestamp(recorded_at_utc)
        _require_safe_id(backend.backend_id, "backend_id")
        _require_safe_id(backend.model_id, "model_id")

        try:
            self._validate_context(context)
        except GeneratorAirlockError:
            raw_output = ""
            decision = CandidateIntakeDecision(
                attempt_id=attempt_id,
                accepted=False,
                rejection_reasons=("invalid_context",),
                context_sha256=_sha256_bytes(
                    canonical_json_bytes(
                        {"invalid": True, "attempt_id": attempt_id}
                    )
                ),
                raw_output_sha256=_sha256_bytes(b""),
                candidate=None,
            )
            decision.validate()
            self._record_attempt(
                decision=decision,
                backend=backend,
                context=None,
                prompt_template_sha256=prompt_template_sha256,
                raw_output=raw_output,
                proposal=None,
                parse_status="not_attempted",
                recorded_at_utc=recorded_at_utc,
            )
            return decision

        context_sha = context.sha256()
        try:
            raw_output = backend.generate(context.to_dict())
        except Exception:
            # Provider/SDK exception text may contain secrets or transport detail;
            # preserve the failure as a rejection code without persisting the message.
            raw_output = ""
            decision = CandidateIntakeDecision(
                attempt_id=attempt_id,
                accepted=False,
                rejection_reasons=("provider_failure",),
                context_sha256=context_sha,
                raw_output_sha256=_sha256_bytes(b""),
                candidate=None,
            )
            decision.validate()
            self._record_attempt(
                decision=decision,
                backend=backend,
                context=context,
                prompt_template_sha256=prompt_template_sha256,
                raw_output=raw_output,
                proposal=None,
                parse_status="not_attempted",
                recorded_at_utc=recorded_at_utc,
            )
            return decision

        if not isinstance(raw_output, str):
            decision = CandidateIntakeDecision(
                attempt_id=attempt_id,
                accepted=False,
                rejection_reasons=("provider_failure",),
                context_sha256=context_sha,
                raw_output_sha256=_sha256_bytes(b""),
                candidate=None,
            )
            decision.validate()
            self._record_attempt(
                decision=decision,
                backend=backend,
                context=context,
                prompt_template_sha256=prompt_template_sha256,
                raw_output="",
                proposal=None,
                parse_status="not_attempted",
                recorded_at_utc=recorded_at_utc,
            )
            return decision

        raw_sha = _sha256_bytes(raw_output.encode("utf-8"))
        proposal, reasons, parse_status = self._parse_proposal(raw_output)
        candidate: Candidate | None = None
        if proposal is not None and not reasons:
            candidate, reasons = self._candidate_from_proposal(
                proposal,
                context=context,
                backend_id=backend.backend_id,
                model_id=backend.model_id,
                context_sha256=context_sha,
                attempt_id=attempt_id,
            )
        decision = CandidateIntakeDecision(
            attempt_id=attempt_id,
            accepted=not reasons and candidate is not None,
            rejection_reasons=tuple(reasons),
            context_sha256=context_sha,
            raw_output_sha256=raw_sha,
            candidate=candidate if not reasons else None,
        )
        decision.validate()
        self._record_attempt(
            decision=decision,
            backend=backend,
            context=context,
            prompt_template_sha256=prompt_template_sha256,
            raw_output=raw_output,
            proposal=proposal,
            parse_status=parse_status,
            recorded_at_utc=recorded_at_utc,
        )
        return decision

    def _record_attempt(
        self,
        *,
        decision: CandidateIntakeDecision,
        backend: GeneratorBackend,
        context: GeneratorContextPacket | None,
        prompt_template_sha256: str,
        raw_output: str,
        proposal: CandidateProposal | None,
        parse_status: str,
        recorded_at_utc: str,
    ) -> None:
        if parse_status not in _PARSE_STATUSES:
            raise GeneratorAirlockError("invalid generation parse_status")
        _require_utc_timestamp(recorded_at_utc)
        payload = {
            "attempt_id": decision.attempt_id,
            "generator_version": GENERATOR_VERSION,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "prompt_template_sha256": prompt_template_sha256,
            "context_sha256": decision.context_sha256,
            "context": context.to_dict() if context is not None else None,
            "raw_output_sha256": decision.raw_output_sha256,
            "raw_output": raw_output,
            "parse_status": parse_status,
            "validation_status": "accepted" if decision.accepted else "rejected",
            "rejection_reasons": list(decision.rejection_reasons),
            "proposal": proposal.to_dict() if proposal is not None else None,
            "candidate": (
                decision.candidate.to_dict()
                if decision.candidate is not None
                else None
            ),
            "recorded_at_utc": recorded_at_utc,
            "authority": {
                "generator_output_is_domain_evidence": False,
                "generator_may_promote_claim": False,
                "generator_may_select_winner": False,
                "accepted_candidate_initial_claim_level": "exploratory",
                "generator_rejection_is_mathematical_failure": False,
            },
        }
        self.journal.record(attempt_id=decision.attempt_id, payload=payload)

    @staticmethod
    def commit_candidate(
        decision: CandidateIntakeDecision,
        *,
        ledger: ContentAddressedLedger,
        actor: str,
        source_commit: str,
        recorded_at_utc: str,
    ) -> str:
        """Explicitly commit an accepted candidate after the model-facing airlock."""
        decision.validate()
        if not decision.accepted or decision.candidate is None:
            raise GeneratorAirlockError(
                "only an accepted decision may be committed"
            )
        try:
            return ledger.persist_candidate(
                decision.candidate,
                actor=actor,
                source_commit=source_commit,
                recorded_at_utc=recorded_at_utc,
            )
        except LedgerError as exc:
            raise GeneratorAirlockError(
                f"candidate ledger commit failed: {exc}"
            ) from exc

    def authority_snapshot(self) -> dict[str, Any]:
        return {
            "proposal_generation": True,
            "candidate_intake": True,
            "candidate_initial_claim_level": "exploratory",
            "domain_evidence": False,
            "claim_promotion": False,
            "proof_status_assignment": False,
            "winner_selection": False,
            "confidence_as_authority": False,
            "direct_analogy_bypass": False,
            "rejection_is_mathematical_failure": False,
        }
