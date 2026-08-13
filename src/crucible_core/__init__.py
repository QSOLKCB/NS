# SPDX-License-Identifier: Apache-2.0
"""Domain-neutral hypothesis/falsification orchestration for QSOL Crucible."""

from .analogy import (
    AnalogyFirewall,
    AnalogyFirewallError,
    AnalogyRecord,
    FIREWALL_VERSION,
)
from .engine import Crucible, CrucibleStateError
from .ledger import (
    LEDGER_VERSION,
    ContentAddressedLedger,
    LedgerError,
    LedgerReplay,
    TransferTicket,
)
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
    "FIREWALL_VERSION",
    "LEDGER_VERSION",
    "AnalogyFirewall",
    "AnalogyFirewallError",
    "AnalogyRecord",
    "Candidate",
    "ConstraintResult",
    "ContentAddressedLedger",
    "Crucible",
    "CrucibleStateError",
    "EvidenceRecord",
    "FailureRecord",
    "HypothesisSet",
    "LedgerError",
    "LedgerReplay",
    "TransferTicket",
]
