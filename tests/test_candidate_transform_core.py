# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import crucible_core as cc
D="navier_stokes_3d_incompressible";H="NS_PRIMARY_COMPETITION";R="NS_GLOBAL_REGULARITY";B="NS_FINITE_TIME_BREAKDOWN";C="a"*40;T="2026-08-13T22:00:00Z";P="b"*64

def cand(i,track=R,extra=("smooth solution","critical scale estimate"),claim="exploratory",status="active",frozen=False):return cc.Candidate(candidate_id=i,domain_id=D,hypothesis_set_id=H,hypothesis=f"Mechanism {i}",claim_level=claim,generation_method="fixture",assumptions=(*extra,f"target_track={track}"),status=status,frozen=frozen)
def persist(l,c):return cc.TransformParent(c,l.persist_candidate(c,actor="test",source_commit=C,recorded_at_utc=T))
def prop(i="child",track=R,**kw):
 v={"proposal_id":i,"target_hypothesis":track,"precise_statement":f"Transformed {i}","assumptions":["smooth solution","repaired critical estimate"],"claimed_dependencies":["T1"],"suggested_tests":["check scaling"],"possible_failure_modes":["estimate may fail"],"parent_assumptions_removed":[],"addressed_failure_ids":[],"operator_notes":"bounded transform"};v.update(kw);return json.dumps(v)
def setup(tmp_path,operator="repair_scaling_defect",target=R,tracks=(R,),output=None,with_failure=False):
 l=cc.ContentAddressedLedger(tmp_path/"ledger");parents=tuple(persist(l,cand(f"p{i}",x)) for i,x in enumerate(tracks));fails=()
 if with_failure:
  f=cc.FailureRecord(failure_id="failure-p0",candidate_id="p0",domain_id=D,failed_constraint="CIRCULAR_REGULARITY",failure_class="circular_estimate",evidence_ids=(),reusable_lesson="replace circular estimate",claim_level_before="exploratory",claim_level_after="exploratory",recorded_by="test");fo=l.persist_failure(f,actor="test",source_commit=C,recorded_at_utc=T);fails=(cc.TransformFailure(f,fo),)
 replay=l.verify();ctx=cc.TransformContextPacket(D,H,operator,target,parents,fails,("T1",),("PB1",),tuple(p.candidate.candidate_id for p in parents),replay.event_count,replay.head_event_sha256,C,"bounded transform");j=cc.TransformAttemptJournal(tmp_path/"journal");ids={p.candidate.candidate_id for p in parents};gate=cc.CandidateTransformEngine(domain_id=D,hypothesis_set_id=H,allowed_target_hypotheses={R,B},required_proof_barrier_ids={"PB1"},known_candidate_ids=ids,frontier_candidate_ids=ids,known_theorem_ids={"T1"},journal=j);d=gate.run(backend=cc.DeterministicTransformFixtureBackend(output or prop(track=target)),context=ctx,ledger_replay=l.verify(),attempt_id="attempt",prompt_template_sha256=P,actor="test",source_commit=C,recorded_at_utc=T);return l,parents,ctx,j,gate,d

def test_transform_child_is_new_exploratory_candidate_and_commits(tmp_path:Path):
 l,parents,ctx,j,g,d=setup(tmp_path);assert d.accepted and d.candidate.claim_level=="exploratory" and d.candidate.status=="active" and not d.candidate.frozen;assert d.candidate.parent_candidate_ids==("p0",);oid=g.commit_candidate(decision=d,context=ctx,ledger=l,actor="test",source_commit=C,recorded_at_utc=T);assert oid==d.candidate_object_id_if_committed;j.close()
def test_crossover_requires_two_same_track_frontier_parents(tmp_path:Path):
 *_,j,_,d=setup(tmp_path,operator="crossover_survivors",tracks=(R,B));assert not d.accepted;j.close()
 *_,j2,_,d2=setup(tmp_path/"ok",operator="crossover_survivors",tracks=(R,R));assert d2.accepted and d2.candidate.parent_candidate_ids==("p0","p1");j2.close()
def test_reverse_track_requires_change(tmp_path:Path):
 *_,j,_,d=setup(tmp_path,operator="reverse_track_perspective",target=R);assert not d.accepted;j.close()
 *_,j2,_,d2=setup(tmp_path/"ok",operator="reverse_track_perspective",target=B,output=prop(track=B));assert d2.accepted;j2.close()
def test_weaken_assumption_requires_declared_parent_removal(tmp_path:Path):
 *_,j,_,d=setup(tmp_path,operator="weaken_assumption");assert not d.accepted and "invalid_operator_semantics" in d.rejection_reasons;j.close()
 out=prop(assumptions=["smooth solution"],parent_assumptions_removed=["critical scale estimate"]);*_,j2,_,d2=setup(tmp_path/"ok",operator="weaken_assumption",output=out);assert d2.accepted;j2.close()
def test_replace_failed_estimate_requires_failure_receipt(tmp_path:Path):
 *_,j,_,d=setup(tmp_path,operator="replace_failed_estimate");assert not d.accepted;j.close()
 out=prop(addressed_failure_ids=["failure-p0"]);*_,j2,_,d2=setup(tmp_path/"ok",operator="replace_failed_estimate",with_failure=True,output=out);assert d2.accepted;j2.close()
