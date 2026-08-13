# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import replace
import pytest
import crucible_core as cc

D="navier_stokes_3d_incompressible"; H="NS_PRIMARY_COMPETITION"; R="NS_GLOBAL_REGULARITY"; B="NS_FINITE_TIME_BREAKDOWN"; C="a"*40; T="2026-08-13T12:00:00Z"; P={"actor":"unit-test","source_commit":C,"recorded_at_utc":T}
def cand(i,text,track=R,extra=("smooth solution",)):
    a=(*extra,f"generator_context_sha256={'b'*64}",f"generation_attempt_id=attempt-{i}")
    if track is not None:a=(*a,f"target_track={track}")
    return cc.Candidate(i,D,H,text,"exploratory",f"fixture:{i}",assumptions=a)
def persist(l,c): return cc.CandidateReference(c,l.persist_candidate(c,**P))
def origin(r,k="exact_domain_construction"): return cc.CandidateOriginClassification(f"origin-{r.candidate.candidate_id}",r.candidate.candidate_id,r.candidate_object_id,k,("unit-test",),"screening provenance")
def gate(): return cc.DuplicateDeadFamilyDetector(structural_threshold=.6,dead_family_threshold=.6,minimum_shared_tokens=3)
def fail(i): return cc.FailureRecord(f"failure-{i}",i,D,"CIRCULAR_REGULARITY","circular_estimate",(),"Do not assume the estimate that must be proved.","exploratory","exploratory","unit-test")

def test_fingerprint_ignores_identity_and_machine_provenance():
    assert cc.candidate_exact_fingerprint(cand("a","Investigate scale local vorticity."))==cc.candidate_exact_fingerprint(cand("b","  INVESTIGATE scale local vorticity. "))
def test_exact_and_near_matches_are_review_only(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); p=persist(l,cand("p","Investigate scale local vorticity.")); q=persist(l,cand("q","INVESTIGATE scale local vorticity.")); r=gate().screen(report_id="exact",candidate=q,origin=origin(q),prior_candidates=(p,),dead_families=())
    assert r.primary_classification=="exact_duplicate" and r.review_required and not r.automatic_rejection and not r.mathematical_equivalence_established
    p2=persist(l,cand("p2","Investigate scale local vorticity control through a critical continuation estimate.",extra=("bound critical vorticity without circular smoothness",))); q2=persist(l,cand("q2","Investigate scale local vorticity control using a critical continuation estimate.",extra=("bound critical vorticity without assuming smoothness",))); r2=gate().screen(report_id="near",candidate=q2,origin=origin(q2),prior_candidates=(p2,),dead_families=()); assert r2.primary_classification=="structural_near_duplicate" and not r2.mathematical_equivalence_established
def test_cross_track_text_is_not_collapsed(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); p=persist(l,cand("p","Same mechanism.",B)); q=persist(l,cand("q","Same mechanism.",R)); r=gate().screen(report_id="cross",candidate=q,origin=origin(q),prior_candidates=(p,),dead_families=()); assert r.primary_classification=="novel_to_screening_memory"
def test_failure_family_match_is_review_only(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); p=persist(l,cand("failed","Investigate critical bootstrap vorticity control.",extra=("close critical vorticity by bootstrap bound",))); f=fail("failed"); fo=l.persist_failure(f,**P); fam=cc.DeadFamilyRecord.from_failure_candidate(family_id="family",candidate=p.candidate,candidate_object_id=p.candidate_object_id,failures=(f,),failure_object_ids=(fo,))
    with cc.DuplicateScreeningJournal(tmp_path/"s") as j: oid=j.record_dead_family(fam,ledger_replay=l.verify(),**P)
    q=persist(l,cand("q","Investigate critical bootstrap vorticity control.",extra=("close critical vorticity using bootstrap bound",))); r=gate().screen(report_id="fm",candidate=q,origin=origin(q),prior_candidates=(),dead_families=((fam,oid),)); assert r.primary_classification=="dead_family_match" and r.review_required and not r.proof_of_falsehood
def test_authority_and_threshold_mutations_fail(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); q=persist(l,cand("q","Pressure decomposition.")); r=gate().screen(report_id="r",candidate=q,origin=origin(q,"heuristic"),prior_candidates=(),dead_families=())
    for bad in (replace(r,automatic_rejection=True),replace(r,mathematical_equivalence_established=True),replace(r,claim_level_effect="promote")):
        with pytest.raises(cc.DuplicateDetectorError): bad.validate()
    with pytest.raises(cc.DuplicateDetectorError): cc.DuplicateDeadFamilyDetector(structural_threshold=0,dead_family_threshold=.6,minimum_shared_tokens=3)

def test_candidate_payload_must_match_content_addressed_object(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); ref=persist(l,cand("same","Original mechanism.")); bad=cc.CandidateReference(replace(ref.candidate,hypothesis="Modified mechanism."),ref.candidate_object_id)
    with pytest.raises(cc.DuplicateDetectorError): bad.validate()
def test_failure_payload_must_match_failure_object(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); a=persist(l,cand("a","A mechanism.")); persist(l,cand("b","B mechanism.")); fa=fail("a"); wrong=l.persist_failure(fail("b"),**P)
    with pytest.raises(cc.DuplicateDetectorError): cc.DeadFamilyRecord.from_failure_candidate(family_id="mismatch",candidate=a.candidate,candidate_object_id=a.candidate_object_id,failures=(fa,),failure_object_ids=(wrong,))
def test_report_classification_must_match_flags_and_matches(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); q=persist(l,cand("q","One mechanism.")); r=gate().screen(report_id="coherent",candidate=q,origin=origin(q),prior_candidates=(),dead_families=())
    with pytest.raises(cc.DuplicateDetectorError): replace(r,primary_classification="exact_duplicate").validate()
    with pytest.raises(cc.DuplicateDetectorError): replace(r,flags=("exact_duplicate",),review_required=True).validate()
def test_missing_target_track_is_rejected(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); q=persist(l,cand("q","Unclassified.",None)); p=persist(l,cand("p","Unclassified.",None))
    with pytest.raises(cc.DuplicateDetectorError): gate().screen(report_id="trackless",candidate=q,origin=origin(q),prior_candidates=(p,),dead_families=())
def test_screening_event_provenance_and_bad_provenance(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); ref=persist(l,cand("q","One mechanism.")); root=tmp_path/"s"
    with cc.DuplicateScreeningJournal(root) as j:
        j.record_origin(origin(ref),ledger_replay=l.verify(),**P); event=json.loads(j.log_path.read_text()); assert (event["actor"],event["source_commit"],event["recorded_at_utc"])==("unit-test",C,T)
    with cc.DuplicateScreeningJournal(tmp_path/"bad") as j:
        with pytest.raises(cc.DuplicateMemoryError): j.record_origin(origin(ref),ledger_replay=l.verify(),actor="unit-test",source_commit="bad",recorded_at_utc=T)
def test_missing_ref_recovers_from_fsynced_event(tmp_path):
    l=cc.ContentAddressedLedger(tmp_path/"l"); ref=persist(l,cand("q","One mechanism.")); root=tmp_path/"s"; j=cc.DuplicateScreeningJournal(root); original=j._materialize_ref
    def fail_ref(event): raise OSError("simulated ref publication failure")
    j._materialize_ref=fail_ref
    with pytest.raises(OSError): j.record_origin(origin(ref),ledger_replay=l.verify(),**P)
    j._materialize_ref=original; j.close()
    with cc.DuplicateScreeningJournal(root) as recovered:
        count,_,refs=recovered.verify(); assert count==1 and "origin_classification:origin-q" in refs
def test_second_writer_is_rejected(tmp_path):
    root=tmp_path/"s"; first=cc.DuplicateScreeningJournal(root)
    try:
        with pytest.raises(cc.DuplicateMemoryError): cc.DuplicateScreeningJournal(root)
    finally: first.close()
