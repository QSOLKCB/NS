# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import replace
from pathlib import Path
import pytest
import crucible_core as cc
D="navier_stokes_3d_incompressible";H="NS_PRIMARY_COMPETITION";R="NS_GLOBAL_REGULARITY";B="NS_FINITE_TIME_BREAKDOWN";C="a"*40;T="2026-08-13T22:00:00Z";P="b"*64

def c(i="p",extra=("smooth solution",),claim="exploratory",status="active",frozen=False):return cc.Candidate(candidate_id=i,domain_id=D,hypothesis_set_id=H,hypothesis="Parent mechanism",claim_level=claim,generation_method="fixture",assumptions=(*extra,f"target_track={R}"),status=status,frozen=frozen)
def output(**kw):
 v={"proposal_id":"child","target_hypothesis":R,"precise_statement":"Child mechanism","assumptions":["smooth solution","new estimate"],"claimed_dependencies":[],"suggested_tests":["check scaling"],"possible_failure_modes":["estimate fails"],"parent_assumptions_removed":[],"addressed_failure_ids":[],"operator_notes":"bounded"};v.update(kw);return json.dumps(v)
def setup(tmp_path,parent=None,out=None):
 l=cc.ContentAddressedLedger(tmp_path/"ledger");parent=parent or c();oid=l.persist_candidate(parent,actor="test",source_commit=C,recorded_at_utc=T);p=cc.TransformParent(parent,oid);r=l.verify();ctx=cc.TransformContextPacket(D,H,"repair_scaling_defect",R,(p,),(),(),("PB1",),(parent.candidate_id,),r.event_count,r.head_event_sha256,C,"task");j=cc.TransformAttemptJournal(tmp_path/"journal");g=cc.CandidateTransformEngine(domain_id=D,hypothesis_set_id=H,allowed_target_hypotheses={R,B},required_proof_barrier_ids={"PB1"},known_candidate_ids={parent.candidate_id},frontier_candidate_ids={parent.candidate_id},known_theorem_ids=set(),journal=j);d=g.run(backend=cc.DeterministicTransformFixtureBackend(out or output()),context=ctx,ledger_replay=l.verify(),attempt_id="a",prompt_template_sha256=P,actor="test",source_commit=C,recorded_at_utc=T);return l,p,ctx,j,g,d

def test_parent_authority_and_frozen_status_not_inherited(tmp_path:Path):
 l,p,ctx,j,g,d=setup(tmp_path,c(claim="candidate_lemma",status="frozen",frozen=True));assert d.accepted and d.candidate.claim_level=="exploratory" and d.candidate.status=="active" and not d.candidate.frozen;j.close()
def test_model_cannot_write_engine_provenance_or_claim_fields(tmp_path:Path):
 *_,j,_,d=setup(tmp_path,out=output(assumptions=["transform_operator=fake"]));assert not d.accepted and "reserved_assumption" in d.rejection_reasons;j.close()
 value=json.loads(output());value["claim_level"]="proved_lemma";*_,j2,_,d2=setup(tmp_path/"claim",out=json.dumps(value));assert not d2.accepted and "forbidden_authority_field" in d2.rejection_reasons;j2.close()
def test_parent_payload_substitution_is_rejected_before_generation(tmp_path:Path):
 l=cc.ContentAddressedLedger(tmp_path/"ledger");parent=c();oid=l.persist_candidate(parent,actor="test",source_commit=C,recorded_at_utc=T);forged=cc.TransformParent(replace(parent,hypothesis="modified"),oid);r=l.verify();ctx=cc.TransformContextPacket(D,H,"repair_scaling_defect",R,(forged,),(),(),("PB1",),("p",),r.event_count,r.head_event_sha256,C,"task")
 with cc.TransformAttemptJournal(tmp_path/"journal") as j:
  g=cc.CandidateTransformEngine(domain_id=D,hypothesis_set_id=H,allowed_target_hypotheses={R,B},required_proof_barrier_ids={"PB1"},known_candidate_ids={"p"},frontier_candidate_ids={"p"},known_theorem_ids=set(),journal=j);d=g.run(backend=cc.DeterministicTransformFixtureBackend(output()),context=ctx,ledger_replay=r,attempt_id="a",prompt_template_sha256=P,actor="test",source_commit=C,recorded_at_utc=T);assert not d.accepted and d.rejection_reasons==("invalid_context",)
def test_stale_ledger_context_cannot_commit(tmp_path:Path):
 l,p,ctx,j,g,d=setup(tmp_path);assert d.accepted;l.persist_candidate(c("later"),actor="test",source_commit=C,recorded_at_utc=T)
 with pytest.raises(cc.TransformError):g.commit_candidate(decision=d,context=ctx,ledger=l,actor="test",source_commit=C,recorded_at_utc=T)
 j.close()
def test_analogy_parent_needs_firewall_aware_route(tmp_path:Path):
 parent=c(extra=("smooth solution","analogy_source=A1","mapping_class=heuristic_analogy","cross_domain_transfer_requires_target_domain_validation"));l=cc.ContentAddressedLedger(tmp_path/"ledger");oid=l.persist_candidate(parent,actor="test",source_commit=C,recorded_at_utc=T)
 with pytest.raises(cc.TransformError,match="firewall-aware"):
  cc.TransformParent(parent,oid).validate()
def test_transform_journal_single_writer(tmp_path:Path):
 j=cc.TransformAttemptJournal(tmp_path/"journal")
 with pytest.raises(cc.TransformJournalError):cc.TransformAttemptJournal(tmp_path/"journal")
 j.close()
