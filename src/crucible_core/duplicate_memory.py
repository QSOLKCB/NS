# SPDX-License-Identifier: Apache-2.0
"""Public content-addressed audit journal for similarity screening."""
from __future__ import annotations

from .duplicate import CandidateOriginClassification, DeadFamilyRecord, SimilarityReport
from .ledger import LedgerReplay
from .screening_journal_core import ScreeningJournalCore
from .screening_memory_common import DuplicateMemoryError, SCREENING_MEMORY_VERSION, validate_ledger_ref

class DuplicateScreeningJournal(ScreeningJournalCore):
    def record_origin(self, origin: CandidateOriginClassification, *, ledger_replay: LedgerReplay, actor: str, source_commit: str, recorded_at_utc: str) -> str:
        origin.validate(); validate_ledger_ref(ledger_replay,"candidate",origin.candidate_id,origin.candidate_object_id)
        oid=self._store("origin_classification",origin.to_dict())
        self._append(object_type="origin_classification",logical_id=origin.origin_id,oid=oid,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc); return oid
    def record_dead_family(self, family: DeadFamilyRecord, *, ledger_replay: LedgerReplay, actor: str, source_commit: str, recorded_at_utc: str) -> str:
        family.validate(); validate_ledger_ref(ledger_replay,"candidate",family.failed_candidate_id,family.failed_candidate_object_id)
        for failure,oid in zip(family.backing_failures,family.failure_object_ids,strict=True): validate_ledger_ref(ledger_replay,"failure",failure.failure_id,oid)
        oid=self._store("dead_family",family.to_dict())
        self._append(object_type="dead_family",logical_id=family.family_id,oid=oid,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc); return oid
    def record_report(self, report: SimilarityReport, *, ledger_replay: LedgerReplay, actor: str, source_commit: str, recorded_at_utc: str) -> str:
        report.validate(); validate_ledger_ref(ledger_replay,"candidate",report.candidate_id,report.candidate_object_id)
        for candidate_id,oid in zip(report.matched_candidate_ids,report.matched_candidate_object_ids,strict=True): validate_ledger_ref(ledger_replay,"candidate",candidate_id,oid)
        if report.origin_classification_object_id is not None:
            origins={oid for key,oid in self._refs.items() if key.startswith("origin_classification:")}
            if report.origin_classification_object_id not in origins: raise DuplicateMemoryError("report origin object is not in screening history")
        families={oid for key,oid in self._refs.items() if key.startswith("dead_family:")}
        if not set(report.matched_dead_family_object_ids).issubset(families): raise DuplicateMemoryError("report references unknown failure-family object")
        oid=self._store("similarity_report",report.to_dict())
        self._append(object_type="similarity_report",logical_id=report.report_id,oid=oid,actor=actor,source_commit=source_commit,recorded_at_utc=recorded_at_utc); return oid
    def authority_snapshot(self) -> dict[str,bool]:
        return {"screening_memory_is_domain_evidence":False,"screening_memory_establishes_equivalence":False,"screening_memory_proves_falsehood":False,"screening_memory_may_reject_candidate":False,"screening_memory_may_promote_claim":False}

__all__=["DuplicateMemoryError","DuplicateScreeningJournal","SCREENING_MEMORY_VERSION"]
