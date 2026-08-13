# SPDX-License-Identifier: Apache-2.0
"""Shared deterministic helpers for Crucible similarity screening."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

from .engine import canonical_json_bytes
from .ledger import LEDGER_VERSION
from .models import Candidate

DUPLICATE_DETECTOR_VERSION = "0.1.0"
FINGERPRINT_ALGORITHM = "normalized_declared_mechanism_sha256_v1"
SIMILARITY_ALGORITHM = "token_jaccard_v1"
OriginClass = Literal["exact_domain_construction","established_bridge","source_described","structural_transfer","heuristic","schematic"]
PrimaryClassification = Literal["novel_to_screening_memory","exact_duplicate","structural_near_duplicate","dead_family_match"]
ORIGIN_CLASSES = {"exact_domain_construction","established_bridge","source_described","structural_transfer","heuristic","schematic"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SHA256_OBJECT = re.compile(r"^sha256:[0-9a-f]{64}$")
TOKEN = re.compile(r"\w+", flags=re.UNICODE)
PROVENANCE_PREFIXES = ("generator_context_sha256=","generation_attempt_id=","analogy_source=","mapping_class=")
PROVENANCE_EXACT = {"cross_domain_transfer_requires_target_domain_validation"}

class DuplicateDetectorError(ValueError):
    pass

def require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DuplicateDetectorError(f"{field} must be a non-empty string")

def require_safe_id(value: str, field: str) -> None:
    require_text(value, field)
    if not SAFE_ID.fullmatch(value):
        raise DuplicateDetectorError(f"{field} must be a component-safe ID of at most 128 characters")

def require_object_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not SHA256_OBJECT.fullmatch(value):
        raise DuplicateDetectorError(f"{field} must be sha256:<64 lowercase hex>")

def require_unique_text(values: tuple[str,...], field: str, *, nonempty: bool=False) -> None:
    if nonempty and not values:
        raise DuplicateDetectorError(f"{field} must be non-empty")
    for value in values:
        require_text(value, field)
    if len(values) != len(set(values)):
        raise DuplicateDetectorError(f"{field} must contain unique values")

def require_unique_object_ids(values: tuple[str,...], field: str, *, nonempty: bool=False) -> None:
    if nonempty and not values:
        raise DuplicateDetectorError(f"{field} must be non-empty")
    for value in values:
        require_object_id(value, field)
    if len(values) != len(set(values)):
        raise DuplicateDetectorError(f"{field} must contain unique values")

def normalize_text(text: str) -> str:
    require_text(text, "text")
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

def tokens(texts: Iterable[str]) -> tuple[str,...]:
    out: set[str] = set()
    for text in texts:
        out.update(TOKEN.findall(normalize_text(text)))
    return tuple(sorted(out))

def target_track(candidate: Candidate) -> str | None:
    tracks = [x.split("=",1)[1] for x in candidate.assumptions if x.startswith("target_track=") and "=" in x]
    if len(tracks) > 1:
        raise DuplicateDetectorError("candidate declares multiple target_track markers")
    if tracks and not tracks[0].strip():
        raise DuplicateDetectorError("candidate target_track marker must be non-empty")
    return tracks[0] if tracks else None

def require_target_track(candidate: Candidate) -> str:
    track = target_track(candidate)
    if track is None:
        raise DuplicateDetectorError("candidate must declare target_track before similarity screening")
    return track

def semantic_assumptions(candidate: Candidate) -> tuple[str,...]:
    kept = []
    for item in candidate.assumptions:
        if item in PROVENANCE_EXACT or item.startswith("target_track=") or item.startswith(PROVENANCE_PREFIXES):
            continue
        kept.append(normalize_text(item))
    return tuple(sorted(set(kept)))

def ledger_payload_object_id(object_type: str, payload: dict[str,Any]) -> str:
    envelope = {"ledger_version":LEDGER_VERSION,"object_type":object_type,"payload":payload}
    return "sha256:" + hashlib.sha256(canonical_json_bytes(envelope)).hexdigest()

def candidate_mechanism_tokens(candidate: Candidate) -> tuple[str,...]:
    candidate.validate()
    return tokens((candidate.hypothesis,*semantic_assumptions(candidate)))

def candidate_exact_fingerprint(candidate: Candidate) -> str:
    candidate.validate()
    payload = {"algorithm":FINGERPRINT_ALGORITHM,"domain_id":candidate.domain_id,"hypothesis_set_id":candidate.hypothesis_set_id,"target_track":target_track(candidate),"hypothesis":normalize_text(candidate.hypothesis),"semantic_assumptions":list(semantic_assumptions(candidate))}
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()

def jaccard(left_tokens: tuple[str,...], right_tokens: tuple[str,...], minimum_shared_tokens: int) -> float:
    left, right = set(left_tokens), set(right_tokens)
    if not left or not right:
        return 0.0
    shared = left & right
    if len(shared) < minimum_shared_tokens:
        return 0.0
    return len(shared) / len(left | right)

@dataclass(frozen=True)
class CandidateReference:
    candidate: Candidate
    candidate_object_id: str
    def validate(self) -> None:
        self.candidate.validate()
        require_object_id(self.candidate_object_id,"candidate_object_id")
        if self.candidate_object_id != ledger_payload_object_id("candidate",self.candidate.to_dict()):
            raise DuplicateDetectorError("candidate payload does not match content-addressed ledger object ID")

@dataclass(frozen=True)
class CandidateOriginClassification:
    origin_id: str
    candidate_id: str
    candidate_object_id: str
    origin_class: OriginClass
    source_refs: tuple[str,...]
    rationale: str
    claim_level_effect: Literal["none"] = "none"
    evidence_effect: Literal["none"] = "none"
    def validate(self) -> None:
        require_safe_id(self.origin_id,"origin_id"); require_safe_id(self.candidate_id,"candidate_id"); require_object_id(self.candidate_object_id,"candidate_object_id")
        if self.origin_class not in ORIGIN_CLASSES: raise DuplicateDetectorError("unsupported origin_class")
        require_unique_text(self.source_refs,"source_refs"); require_text(self.rationale,"rationale")
        if self.claim_level_effect != "none" or self.evidence_effect != "none": raise DuplicateDetectorError("origin classification may not alter claim/evidence authority")
    def to_dict(self) -> dict[str,Any]:
        self.validate(); value=asdict(self); value["source_refs"]=list(self.source_refs); return value
