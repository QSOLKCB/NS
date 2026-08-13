#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import copy,json
from pathlib import Path
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
import crucible_core as cc
R=Path(__file__).resolve().parents[1]/"research"
def j(name):return json.loads((R/name).read_text(encoding="utf-8"))
c=j("candidate_transform_contract.json");a=j("ns_candidate_transform_adapter.json");cs=j("schemas/candidate_transform_contract.schema.json");ads=j("schemas/ns_candidate_transform_adapter.schema.json");ns=j("ns_crucible_adapter.json");pb=j("proof_barriers.json")
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
print("candidate transform validation: PASS")
