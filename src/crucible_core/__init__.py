# SPDX-License-Identifier: Apache-2.0
"""Domain-neutral hypothesis/falsification orchestration for QSOL Crucible."""

from .analogy import AnalogyFirewall, AnalogyFirewallError, AnalogyRecord, FIREWALL_VERSION
from .duplicate import (
    DUPLICATE_DETECTOR_VERSION,
    FINGERPRINT_ALGORITHM,
    SIMILARITY_ALGORITHM,
    CandidateOriginClassification,
    CandidateReference,
    DeadFamilyRecord,
    DuplicateDeadFamilyDetector,
    DuplicateDetectorError,
    SimilarityReport,
    candidate_exact_fingerprint,
    candidate_mechanism_tokens,
)
from .duplicate_memory import DuplicateMemoryError, DuplicateScreeningJournal, SCREENING_MEMORY_VERSION
from .engine import Crucible, CrucibleStateError
from .generator import (
    GENERATOR_VERSION,
    CandidateIntakeDecision,
    CandidateProposal,
    DeterministicFixtureBackend,
    GeneratorAirlock,
    GeneratorAirlockError,
    GeneratorAttemptJournal,
    GeneratorBackend,
    GeneratorContextPacket,
)
from .ledger import LEDGER_VERSION, ContentAddressedLedger, LedgerError, LedgerReplay, TransferTicket
from .models import Candidate, ConstraintResult, EvidenceRecord, FailureRecord, HypothesisSet

CORE_VERSION = "0.1.0"

__all__ = [
    "CORE_VERSION", "FIREWALL_VERSION", "GENERATOR_VERSION", "LEDGER_VERSION",
    "DUPLICATE_DETECTOR_VERSION", "SCREENING_MEMORY_VERSION", "FINGERPRINT_ALGORITHM", "SIMILARITY_ALGORITHM",
    "AnalogyFirewall", "AnalogyFirewallError", "AnalogyRecord", "Candidate", "CandidateIntakeDecision",
    "CandidateOriginClassification", "CandidateProposal", "CandidateReference", "ConstraintResult",
    "ContentAddressedLedger", "Crucible", "CrucibleStateError", "DeadFamilyRecord",
    "DeterministicFixtureBackend", "DuplicateDeadFamilyDetector", "DuplicateDetectorError", "DuplicateMemoryError",
    "DuplicateScreeningJournal", "EvidenceRecord", "FailureRecord", "GeneratorAirlock", "GeneratorAirlockError",
    "GeneratorAttemptJournal", "GeneratorBackend", "GeneratorContextPacket", "HypothesisSet", "LedgerError",
    "LedgerReplay", "SimilarityReport", "TransferTicket", "candidate_exact_fingerprint", "candidate_mechanism_tokens",
]
