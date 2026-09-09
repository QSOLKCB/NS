#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate fail-closed intake of external Navier-Stokes solution claims."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SCHEMAS = RESEARCH / "schemas"
FORMAT_CHECKER = FormatChecker()

BASELINE_COMMIT = "504180162eb117bc3eb280b93c8ef4df845c0d27"
PDF_SHA256 = "0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f"
LEAN_COMMIT = "8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538"
PDF_URL = "https://cdn.openai.com/pdf/32d9f210-8b73-45e0-91bc-82a30aef8a9a/navier-stokes.pdf"
LEAN_URL = f"https://github.com/openai/NavierStokesAndEuler/tree/{LEAN_COMMIT}"
OPENAI_SOURCE_IDS = ["OPENAI_NS_BLOWUP_2026", "OPENAI_NS_LEAN_2026"]

EXPECTED_ARTIFACT_PINS = {
    "OPENAI_NS_BLOWUP_2026": {"url": PDF_URL, "sha256": PDF_SHA256},
    "OPENAI_NS_LEAN_2026": {
        "repository": "openai/NavierStokesAndEuler",
        "commit": LEAN_COMMIT,
        "url": LEAN_URL,
    },
}

EXPECTED_SOURCE_IDENTITIES = {
    "OPENAI_NS_BLOWUP_2026": {
        "authority_class": "primary_research",
        "authors": ["OpenAI"],
        "year": 2026,
        "title": "Finite time blowup for Navier-Stokes",
        "publisher_or_venue": "OpenAI",
        "doi": None,
        "url": PDF_URL,
        "role": "external_claimed_clay_C_D_construction",
        "required_note_tokens": [PDF_SHA256, "Published 2026-09-08", "alternative C", "Corollary 10.6"],
    },
    "OPENAI_NS_LEAN_2026": {
        "authority_class": "primary_research",
        "authors": ["OpenAI"],
        "year": 2026,
        "title": "NavierStokesAndEuler Lean certificates",
        "publisher_or_venue": "GitHub",
        "doi": None,
        "url": LEAN_URL,
        "role": "external_formalization_artifact_for_claimed_C_D_results",
        "required_note_tokens": [LEAN_COMMIT, "sorry_count 0", "review status self-assessed"],
    },
}

EXPECTED_CLAIM_SEMANTICS = {
    "A": {
        "claim_id": "OPENAI_2026_A",
        "source_ids": OPENAI_SOURCE_IDS,
        "source_position": "not_addressed_by_source",
        "qsol_status": "not_resolved",
        "forcing_relation": "Clay A requires f identically zero; the OpenAI 2026 Navier-Stokes construction is a forced breakdown construction and does not claim A.",
        "statement_summary": "The 2026 OpenAI sources do not claim global smoothness for arbitrary admissible unforced data on R^3.",
        "verification_obligations": [
            "do_not_infer_A_from_C",
            "keep_unforced_global_regularity_separate_from_forced_breakdown",
        ],
    },
    "B": {
        "claim_id": "OPENAI_2026_B",
        "source_ids": OPENAI_SOURCE_IDS,
        "source_position": "not_addressed_by_source",
        "qsol_status": "not_resolved",
        "forcing_relation": "Clay B requires f identically zero; the OpenAI 2026 periodic construction is presented as forced breakdown alternative D and does not claim B.",
        "statement_summary": "The 2026 OpenAI sources do not claim global smoothness for arbitrary admissible unforced periodic data.",
        "verification_obligations": [
            "do_not_infer_B_from_D",
            "preserve_periodic_pressure_and_forcing_requirements",
        ],
    },
    "C": {
        "claim_id": "OPENAI_2026_C",
        "source_ids": OPENAI_SOURCE_IDS,
        "source_position": "claims_satisfied",
        "qsol_status": "external_claim_pending_independent_verification",
        "forcing_relation": "Clay C permits a smooth forcing term. OpenAI Theorem 1.1 constructs smooth compactly supported forcing, starts from zero velocity, keeps kinetic energy uniformly bounded, and makes the velocity L-infinity norm unbounded in finite time.",
        "statement_summary": "OpenAI explicitly states that Theorem 1.1 establishes Fefferman alternative C on R^3.",
        "verification_obligations": [
            "verify_exact_C_statement_correspondence",
            "audit_every_analytic_dependency_of_Theorem_1_1",
            "replay_pinned_Lean_formalization",
            "verify_prose_to_Lean_statement_alignment",
            "obtain_independent_adversarial_review_before_any_QSOL_solution_claim",
        ],
    },
    "D": {
        "claim_id": "OPENAI_2026_D",
        "source_ids": OPENAI_SOURCE_IDS,
        "source_position": "claims_satisfied",
        "qsol_status": "external_claim_pending_independent_verification",
        "forcing_relation": "Clay D permits smooth periodic forcing with the official decay assumptions. OpenAI states that compact support yields the corresponding periodic construction and identifies Corollary 10.6 with alternative D.",
        "statement_summary": "OpenAI explicitly states that its periodic corollary establishes Fefferman alternative D on R^3/Z^3.",
        "verification_obligations": [
            "verify_exact_D_statement_correspondence_including_pressure_periodicity_erratum",
            "audit_periodization_and_localization_arguments",
            "replay_pinned_Lean_formalization",
            "verify_prose_to_Lean_statement_alignment",
            "obtain_independent_adversarial_review_before_any_QSOL_solution_claim",
        ],
    },
}

EXPECTED_MACHINE_INVARIANTS = [
    "EXTERNAL_SOURCE_CLAIM != QSOL_VERIFIED_RESULT",
    "LEAN_BUILD_SUCCESS != INDEPENDENT_MATHEMATICAL_ACCEPTANCE",
    "FORMAL_STATEMENT_CORRESPONDENCE_MUST_BE_AUDITED",
    "C_OR_D_CLAIM_DOES_NOT_RESOLVE_A_OR_B",
    "FORCED_BREAKDOWN != UNFORCED_GLOBAL_REGULARITY_RESULT",
    "THEOREM_REGISTRY_PROMOTION_REQUIRES_EXPLICIT_AUDITED_REVIEW",
    "PUBLICATION_ANNOUNCEMENT != CLAY_ACCEPTANCE",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject_cross(candidate: dict, sources: dict, label: str) -> None:
    try:
        validate_cross(candidate, sources)
    except SystemExit:
        return
    raise SystemExit(f"external-claim regression: forbidden mutation accepted: {label}")


def reject_schema(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"external-claim schema regression: forbidden mutation accepted: {label}")


def validate_source_identity(source_by_id: dict[str, dict], source_id: str) -> None:
    if source_id not in source_by_id:
        raise SystemExit(f"missing required OpenAI intake source: {source_id}")
    source = source_by_id[source_id]
    expected = EXPECTED_SOURCE_IDENTITIES[source_id]
    for field, expected_value in expected.items():
        if field == "required_note_tokens":
            continue
        if source.get(field) != expected_value:
            raise SystemExit(
                f"pinned source identity drift for {source_id}: "
                f"{field}={source.get(field)!r}, expected {expected_value!r}"
            )
    notes = source.get("notes", "")
    for token in expected["required_note_tokens"]:
        if token not in notes:
            raise SystemExit(f"pinned source note identity drift for {source_id}: missing {token!r}")


def validate_cross(claims: dict, sources: dict) -> None:
    if claims["repository_baseline_commit"] != BASELINE_COMMIT:
        raise SystemExit("pre-OpenAI baseline commit drift")
    if claims.get("artifact_pins") != EXPECTED_ARTIFACT_PINS:
        raise SystemExit("external artifact pin set drift")

    source_by_id = {record["source_id"]: record for record in sources["sources"]}
    for source_id in OPENAI_SOURCE_IDS:
        validate_source_identity(source_by_id, source_id)

    records = claims["claims"]
    formulation_ids = [record["formulation_id"] for record in records]
    if formulation_ids != ["A", "B", "C", "D"]:
        raise SystemExit(f"external claim formulation order/identity drift: {formulation_ids}")

    for record in records:
        formulation_id = record["formulation_id"]
        expected = EXPECTED_CLAIM_SEMANTICS[formulation_id]
        actual = {key: record[key] for key in expected}
        if actual != expected:
            raise SystemExit(
                f"external claim semantic drift for formulation {formulation_id}; "
                "update the audited lock only after source review"
            )

    if claims["policy"] != {
        "repository_claim": "no_solution_claim",
        "independent_verification_required": True,
        "formalization_replay_is_not_mathematical_acceptance": True,
        "historical_theorem_registry_unchanged_until_audited_promotion": True,
    }:
        raise SystemExit("external intake policy drift")

    if claims["machine_invariants"] != EXPECTED_MACHINE_INVARIANTS:
        raise SystemExit("external intake machine-invariant set drift")


def run_negative_probes(
    claims: dict,
    sources: dict,
    validator: Draft202012Validator,
) -> None:
    mutated = copy.deepcopy(claims)
    mutated["policy"]["repository_claim"] = "solution_verified"
    reject_schema(validator, mutated, "repository solution claim smuggled into policy")

    mutated = copy.deepcopy(claims)
    mutated["artifact_pins"]["OPENAI_NS_BLOWUP_2026"]["sha256"] = "0" * 64
    reject_schema(validator, mutated, "paper artifact digest rewritten")

    mutated = copy.deepcopy(claims)
    mutated["artifact_pins"]["OPENAI_NS_LEAN_2026"]["commit"] = "0" * 40
    reject_schema(validator, mutated, "Lean artifact commit rewritten")

    mutated = copy.deepcopy(claims)
    mutated["claims"][0]["source_position"] = "claims_satisfied"
    reject_cross(mutated, sources, "OpenAI source promoted to Clay A")

    mutated = copy.deepcopy(claims)
    mutated["claims"][2]["forcing_relation"] = "Clay C requires zero forcing."
    reject_cross(mutated, sources, "Clay C forcing semantics weakened")

    mutated = copy.deepcopy(claims)
    mutated["claims"][2]["statement_summary"] = "QSOL independently verified Clay C."
    reject_cross(mutated, sources, "external claim promoted in statement summary")

    mutated = copy.deepcopy(claims)
    mutated["claims"][2]["verification_obligations"] = ["none"]
    reject_cross(mutated, sources, "Clay C audit obligations replaced")

    mutated = copy.deepcopy(claims)
    mutated["machine_invariants"] = ["EXTERNAL_SOURCE_CLAIM != QSOL_VERIFIED_RESULT"]
    reject_cross(mutated, sources, "external intake machine invariants removed")

    mutated = copy.deepcopy(claims)
    mutated["repository_baseline_commit"] = "0" * 40
    reject_cross(mutated, sources, "historical baseline commit rewritten")

    mutated_sources = copy.deepcopy(sources)
    paper = next(record for record in mutated_sources["sources"] if record["source_id"] == "OPENAI_NS_BLOWUP_2026")
    paper["url"] = "https://example.org/replaced-paper.pdf"
    reject_cross(claims, mutated_sources, "paper URL changed while intake remained pinned")

    mutated_sources = copy.deepcopy(sources)
    paper = next(record for record in mutated_sources["sources"] if record["source_id"] == "OPENAI_NS_BLOWUP_2026")
    paper["notes"] = paper["notes"].replace(PDF_SHA256, "0" * 64)
    reject_cross(claims, mutated_sources, "paper digest note changed while intake remained pinned")

    mutated_sources = copy.deepcopy(sources)
    lean = next(record for record in mutated_sources["sources"] if record["source_id"] == "OPENAI_NS_LEAN_2026")
    lean["url"] = "https://github.com/openai/NavierStokesAndEuler"
    reject_cross(claims, mutated_sources, "Lean pinned URL changed")

    mutated_sources = copy.deepcopy(sources)
    lean = next(record for record in mutated_sources["sources"] if record["source_id"] == "OPENAI_NS_LEAN_2026")
    lean["authority_class"] = "secondary_discovery"
    reject_cross(claims, mutated_sources, "formalization artifact authority downgraded silently")


def main() -> None:
    claims_path = RESEARCH / "external_claim_registry.json"
    schema_path = SCHEMAS / "external_claim_registry.schema.json"
    sources_path = RESEARCH / "source_registry.json"

    claims = load_json(claims_path)
    sources = load_json(sources_path)
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    validator.validate(claims)

    validate_cross(claims, sources)
    run_negative_probes(claims, sources, validator)

    print(
        "External-claim validation: PASS "
        f"({len(claims['claims'])} Clay formulations, baseline {BASELINE_COMMIT[:12]}, "
        f"paper {PDF_SHA256[:12]}, Lean {LEAN_COMMIT[:12]})"
    )


if __name__ == "__main__":
    main()
