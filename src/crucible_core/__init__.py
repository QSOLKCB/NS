# SPDX-License-Identifier: Apache-2.0
"""Domain-neutral hypothesis/falsification orchestration for QSOL Crucible."""

from .engine import Crucible, CrucibleStateError
from .models import (
    Candidate,
    ConstraintResult,
    EvidenceRecord,
    FailureRecord,
    HypothesisSet,
)

CORE_VERSION = "0.1.0"

__all__ = [
    "CORE_VERSION",
    "Candidate",
    "ConstraintResult",
    "Crucible",
    "CrucibleStateError",
    "EvidenceRecord",
    "FailureRecord",
    "HypothesisSet",
]
