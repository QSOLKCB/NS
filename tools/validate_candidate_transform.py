#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import copy,json
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
import crucible_core as cc
ROOT=Path(__file__).resolve().parents[1];R=ROOT/"research"
def j(name):return json.loads((R/name).read_text(encoding="utf-8"))
c=j("candidate_transform_contract.json");a=j("ns_candidate_transform_adapter.json");cs=j("schemas/candidate_transform_contract.schema.json");ads=j("schemas/ns_candidate_transform_adapter.schema.json");ns=j("ns_crucible_adapter.json");pb=j("proof_barriers.json");agents=json.loads((ROOT/"AGENTS.md").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(cs);Draft202012Validator.check_schema(ads);cv=Draft202012Validator(cs);cv.validate(c);Draft202012Validator(ads).validate(a)
assert cc.TRANSFORM_VERSION==c["transform_version"]
assert list(cc.TRANSFORM_OPERATORS)==c["operators"]
tracks=[x["track_id"] for x in ns["primary_hypothesis_set"]["tracks"]]
assert a["allowed_target_hypotheses"]==tracks
assert a["domain_id"]==ns["domain_id"] and a["hypothesis_set_id"]==ns["primary_hypothesis_set"]["hypothesis_set_id"]
assert not any(a["epistemic_authority"].values())
expected_authority={"transform_output_is_domain_evidence":False,"transform_may_promote_claim":False,"transform_may_select_winner":False,"crossover_is_proof_synthesis":False}
assert c["authority"]==expected_authority
for field in expected_authority:
    mutated=copy.deepcopy(c);mutated["authority"][field]=True
    try:cv.validate(mutated)
    except ValidationError:pass
    else:raise SystemExit(f"transform authority mutation accepted: {field}=true")
mutated=copy.deepcopy(c);del mutated["authority"]["transform_may_promote_claim"]
try:cv.validate(mutated)
except ValidationError:pass
else:raise SystemExit("transform authority schema accepted missing key")
mutated=copy.deepcopy(c);mutated["authority"]["unexpected_authority"]=False
try:cv.validate(mutated)
except ValidationError:pass
else:raise SystemExit("transform authority schema accepted unknown key")
assert c["child_policy"]["initial_claim_level"]=="exploratory" and c["child_policy"]["initial_status"]=="active" and c["child_policy"]["initial_frozen"] is False
assert c["child_policy"]["parent_claim_level_inherited"] is False and c["child_policy"]["parent_evidence_inherited"] is False and c["child_policy"]["parent_survival_status_inherited"] is False
assert c["commit_policy"]["model_facing_run_may_mutate_crucible_ledger"] is False
assert c["receipt_policy"]["single_writer_process_only_v0_1"] is True
assert {x["barrier_id"] for x in pb["barriers"]}
assert agents["schema_version"]=="1.9.0"
for step in ("run_tools_validate_candidate_transform_py","read_research_candidate_transform_contract_json","read_research_ns_candidate_transform_adapter_json"):
    assert step in agents["agent_boot_sequence"]
for invariant in ("transform_output_is_not_domain_evidence","transform_child_does_not_inherit_parent_authority","parent_claim_level_is_not_child_claim_level","parent_evidence_is_not_child_evidence","parent_survival_is_not_child_survival","operator_label_is_not_mathematical_validation","crossover_is_not_proof_synthesis","transform_run_is_not_ledger_commit"):
    assert invariant in agents["research_invariants"]
tp=agents["transform_policy"]
assert tp["contract"]=="research/candidate_transform_contract.json" and tp["domain_adapter"]=="research/ns_candidate_transform_adapter.json" and tp["validator"]=="tools/validate_candidate_transform.py"
assert tp["runtime_owns_operator_and_parent_selection"] is True and tp["accepted_candidate_requires_explicit_commit"] is True and tp["commit_must_match_recorded_attempt"] is True
assert tp["accepted_child_initial_claim_level"]=="exploratory" and tp["accepted_child_initial_status"]=="active" and tp["accepted_child_initial_frozen"] is False
for field in ("parent_claim_level_inherited","parent_evidence_inherited","parent_survival_status_inherited","model_may_write_engine_provenance_fields","model_facing_transform_may_mutate_crucible_ledger"):
    assert tp[field] is False
assert tp["analogy_derived_parent_requires_firewall_aware_route"] is True
assert agents["review_policy"]["check_candidate_transform_authority"] is True and agents["review_policy"]["check_transform_attempt_provenance"] is True
print("candidate transform validation: PASS")
