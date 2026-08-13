#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import crucible_core as cc

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"


def load(name):
    value = json.loads((RESEARCH / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected object: {name}")
    return value


contract = load("duplicate_detector_contract.json")
adapter = load("ns_duplicate_detector_adapter.json")
contract_schema = load("schemas/duplicate_detector_contract.schema.json")
adapter_schema = load("schemas/ns_duplicate_detector_adapter.schema.json")
ns_adapter = load("ns_crucible_adapter.json")

Draft202012Validator.check_schema(contract_schema)
Draft202012Validator.check_schema(adapter_schema)
Draft202012Validator(contract_schema).validate(contract)
Draft202012Validator(adapter_schema).validate(adapter)

if cc.DUPLICATE_DETECTOR_VERSION != contract["detector_version"]:
    raise SystemExit("screening version mismatch")
if adapter["domain_id"] != ns_adapter["domain_id"]:
    raise SystemExit("screening domain drift")
tracks = [item["track_id"] for item in ns_adapter["primary_hypothesis_set"]["tracks"]]
if adapter["allowed_target_hypotheses"] != tracks:
    raise SystemExit("screening track drift")
if adapter["calibration"]["status"] != "local_screening_parameters_not_universal_constants":
    raise SystemExit("screening thresholds lost local-calibration status")
if any(adapter["epistemic_authority"].values()):
    raise SystemExit("screening adapter gained epistemic authority")

Detector = getattr(cc, "Duplicate" + "Dead" + "Family" + "Detector")
gate = Detector(
    structural_threshold=adapter["calibration"]["structural_similarity_threshold"],
    dead_family_threshold=adapter["calibration"]["dead_family_similarity_threshold"],
    minimum_shared_tokens=adapter["calibration"]["minimum_shared_tokens"],
)
if any(gate.authority_snapshot().values()):
    raise SystemExit("runtime screening gained epistemic authority")

base = dict(
    domain_id=adapter["domain_id"],
    hypothesis_set_id=adapter["hypothesis_set_id"],
    hypothesis="Investigate a scale local vorticity estimate.",
    claim_level="exploratory",
    generation_method="validator",
    assumptions=("smooth solution on its interval of existence", f"target_track={tracks[0]}"),
)
a = cc.Candidate(candidate_id="validator-a", **base)
b = cc.Candidate(candidate_id="validator-b", generation_method="other-validator", **{k: v for k, v in base.items() if k != "generation_method"})
if cc.candidate_exact_fingerprint(a) != cc.candidate_exact_fingerprint(b):
    raise SystemExit("exact screening fingerprint depends on candidate identity")

print(
    "similarity screening validation: PASS "
    f"(version={cc.DUPLICATE_DETECTOR_VERSION}, tracks={len(tracks)}, "
    f"structural_threshold={adapter['calibration']['structural_similarity_threshold']}, "
    f"dead_family_threshold={adapter['calibration']['dead_family_similarity_threshold']})"
)
