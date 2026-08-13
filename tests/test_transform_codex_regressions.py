# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import replace
from pathlib import Path
import pytest
import crucible_core as cc
from crucible_core.transform_common import contains_authority, ledger_object_id
D="navier_stokes_3d_incompressible";H="NS_PRIMARY_COMPETITION";R="NS_GLOBAL_REGULARITY";B="NS_FINITE_TIME_BREAKDOWN";C="a"*40;T="2026-08-13T22:00:00Z";P="b"*64

def parent():return cc.Candidate("p",D,H,"Parent mechanism","exploratory","fixture",assumptions=("smooth solution",f"target_track={R}"))
def proposal(statement="Child mechanism"):
 return json.dumps({"proposal_id":"child","target_hypothesis":R,"precise_statement":statement,"assumptions":["smooth solution","new estimate"],"claimed_dependencies":[],"suggested_tests":["check scaling"],"possible_failure_modes":["estimate fails"],"parent_assumptions_removed":[],"addressed_failure_ids":[],"operator_notes":"bounded"})
def setup(tmp_path:Path,raw:str):
 l=cc.ContentAddressedLedger(tmp_path/"ledger");p=parent();oid=l.persist_candidate(p,actor="test",source_commit=C,recorded_at_utc=T);r=l.verify();ctx=cc.TransformContextPacket(D,H,"repair_scaling_defect",R,(cc.TransformParent(p,oid),),(),(),("PB1",),("p",),r.event_count,r.head_event_sha256,C,"task");j=cc.TransformAttemptJournal(tmp_path/"journal");g=cc.CandidateTransformEngine(domain_id=D,hypothesis_set_id=H,allowed_target_hypotheses={R,B},required_proof_barrier_ids={"PB1"},known_candidate_ids={"p"},frontier_candidate_ids={"p"},known_theorem_ids=set(),journal=j);d=g.run(backend=cc.DeterministicTransformFixtureBackend(raw),context=ctx,ledger_replay=r,attempt_id="a",prompt_template_sha256=P,actor="test",source_commit=C,recorded_at_utc=T);return l,ctx,j,g,d

def test_commit_rejects_substituted_candidate(tmp_path:Path):
 l,ctx,j,g,d=setup(tmp_path,proposal());assert d.accepted and d.candidate is not None
 forged=replace(d.candidate,hypothesis="Different child payload")
 forged_d=replace(d,candidate=forged,candidate_object_id_if_committed=ledger_object_id("candidate",forged.to_dict()));forged_d.validate()
 with pytest.raises(cc.TransformError,match="recorded transform attempt"):g.commit_candidate(decision=forged_d,context=ctx,ledger=l,actor="test",source_commit=C,recorded_at_utc=T)
 j.close()

def test_solution_language_is_rejected_and_recorded(tmp_path:Path):
 assert contains_authority("The Clay problem is solved")
 _,_,j,_,d=setup(tmp_path,proposal("The Clay problem is solved"));assert not d.accepted and d.rejection_reasons==("forbidden_authority_language",) and j.verify()[0]==1;j.close()

def test_escaped_surrogate_is_rejected_and_recorded(tmp_path:Path):
 _,_,j,_,d=setup(tmp_path,proposal("\ud800"));assert not d.accepted and d.rejection_reasons==("invalid_utf8",) and j.verify()[0]==1;j.close()

def test_raw_surrogate_is_rejected_and_recorded(tmp_path:Path):
 value=json.loads(proposal());value["precise_statement"]="\ud800";raw=json.dumps(value,ensure_ascii=False)
 _,_,j,_,d=setup(tmp_path,raw);assert not d.accepted and d.rejection_reasons==("invalid_utf8",) and j.verify()[0]==1;j.close()
