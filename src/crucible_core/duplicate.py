# SPDX-License-Identifier: Apache-2.0
"""Compatibility surface for hardened deterministic similarity screening."""
from .similarity_common import (
    DUPLICATE_DETECTOR_VERSION,
    FINGERPRINT_ALGORITHM,
    SIMILARITY_ALGORITHM,
    CandidateOriginClassification,
    CandidateReference,
    DuplicateDetectorError,
    OriginClass,
    PrimaryClassification,
    candidate_exact_fingerprint,
    candidate_mechanism_tokens,
)
from .similarity_detector import DuplicateDeadFamilyDetector
from .similarity_family import DeadFamilyRecord
from .similarity_report import SimilarityReport

__all__ = [
    "DUPLICATE_DETECTOR_VERSION",
    "FINGERPRINT_ALGORITHM",
    "SIMILARITY_ALGORITHM",
    "CandidateOriginClassification",
    "CandidateReference",
    "DeadFamilyRecord",
    "DuplicateDeadFamilyDetector",
    "DuplicateDetectorError",
    "OriginClass",
    "PrimaryClassification",
    "SimilarityReport",
    "candidate_exact_fingerprint",
    "candidate_mechanism_tokens",
]
