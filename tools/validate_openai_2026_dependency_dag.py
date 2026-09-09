#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Phase 3A Gate 2: OpenAI 2026 analytical dependency DAG."""

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

PR13_MERGE = "52fcdb1b4ec0eb561fd80e3dbdfab3f0e87465cf"
PAPER_URL = "https://cdn.openai.com/pdf/32d9f210-8b73-45e0-91bc-82a30aef8a9a/navier-stokes.pdf"
PAPER_SHA256 = "0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f"
LEAN_REPOSITORY = "openai/NavierStokesAndEuler"
LEAN_COMMIT = "8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538"
GATE_STATUS = "analytical_dependency_graph_partial"
PROGRAMME_OBLIGATION_PRECISIONS = {
    "programme_obligation",
    "exact_label_plus_programme_obligation",
}

EXPECTED_AUTHORITY = {
    "clay_target": "research/clay_target.json",
    "external_claim_registry": "research/external_claim_registry.json",
    "statement_correspondence": "research/openai_2026_correspondence.json",
    "verification_programme": "docs/OPENAI_2026_INDEPENDENT_VERIFICATION.md",
    "openai_paper_source_id": "OPENAI_NS_BLOWUP_2026",
    "openai_formalization_source_id": "OPENAI_NS_LEAN_2026",
}

EXPECTED_AUDITED_FILES = [
    {"path": "NavierStokes/ComparatorSolution.lean", "blob_sha": "cc232068cd384dbbddce2753b1fc4a4017c0f2d7"},
    {"path": "NavierStokes/ComparatorR3Theorem.lean", "blob_sha": "eb98522380b91b209421bf7519f34bc68ba95c1d"},
    {"path": "NavierStokes/ComparatorTheorem.lean", "blob_sha": "8105493534a5007c689c59e22bc252623bcbe901"},
    {"path": "NavierStokes/R3ActualCandidate.lean", "blob_sha": "5a1d79b69591388af6b4bfceb3566cb797e4fb8a"},
    {"path": "NavierStokes/R3CompactCandidate.lean", "blob_sha": "97082e900e4334c703617ebde8ecb58dfc2f1590"},
    {"path": "NavierStokes/R3FiniteEnergyComparison.lean", "blob_sha": "43dfeab5d087a92474b90c0ab9ee38d57ba25481"},
    {"path": "NavierStokes/MaximalLifespan.lean", "blob_sha": "83968db431a7327110e9ea10c6196dc3e39d5323"},
    {"path": "NavierStokes/ActualCandidateConstruction.lean", "blob_sha": "fa13ab444390073c072f27af11fb0c698107da14"},
    {"path": "NavierStokes/ActualCandidateAssembly.lean", "blob_sha": "820bd414afdb55d4d74a78be357311e6b234a2e4"},
    {"path": "NavierStokes/JointResidualLimits.lean", "blob_sha": "95ead906911262e6c11255ba1ea4c48c588e3d17"},
    {"path": "NavierStokes/PeriodicResidualLimits.lean", "blob_sha": "a3b23182ae3c46680dff325c632c96ee7826eef1"},
    {"path": "NavierStokes/CandidateConsequences.lean", "blob_sha": "5f3eae72b029ea2503f9c2eaa20a1b11685062ff"},
    {"path": "NavierStokes/ConeAlgebra.lean", "blob_sha": "5660522cacbb72674c72575bfd5eeb0a5f2a5f22"},
    {"path": "NavierStokes/CurlGeometry.lean", "blob_sha": "d458ffaaf5c31c049b6018bcc7c36453248c3073"},
    {"path": "NavierStokes/SignedCovariance.lean", "blob_sha": "a2bb9d7b79a64a1e9265f50ec5dd3d8c7578e043"},
    {"path": "NavierStokes/ExponentLedger.lean", "blob_sha": "5156db4f970f9cc28163c06a8a1c5108f4a04c09"},
]

EXPECTED_SOURCE_PINS = {
    "paper": {"url": PAPER_URL, "sha256": PAPER_SHA256},
    "lean": {"repository": LEAN_REPOSITORY, "commit": LEAN_COMMIT, "audited_files": EXPECTED_AUDITED_FILES},
}

EXPECTED_SCOPE = {
    "formulations": ["C", "D"],
    "dependency_graph_only": True,
    "lemma_level_dependency_indexing_complete": False,
    "local_proof_reconstruction_complete": False,
    "proof_validity_assessed": False,
    "lean_build_replayed_by_qsol": False,
    "comparator_replayed_by_qsol": False,
    "theorem_registry_promotion": False,
    "edge_semantics": "from_node depends on to_node",
}

EXPECTED_REQUIRED_CLASSES = [
    "concentrating_axisymmetric_leading_profile",
    "self_similar_scaling_and_velocity_growth",
    "annular_residual_stress",
    "admissible_stress_cone",
    "oscillatory_pulse_covariance",
    "divergence_free_curl",
    "correction_cycle",
    "residual_flatness_and_summation",
    "spatial_localization_and_smooth_force",
    "bounded_energy_and_dissipation",
    "uniqueness_and_continuation",
    "periodicization",
]


def node(node_id: str, node_class: str, dependency_class: str | None, title: str,
         paper_anchor: str, precision: str, formal_modules: list[str], obligation: str) -> dict:
    return {
        "node_id": node_id,
        "node_class": node_class,
        "dependency_class": dependency_class,
        "title": title,
        "paper_anchor": paper_anchor,
        "paper_anchor_precision": precision,
        "formal_modules": formal_modules,
        "obligation": obligation,
        "audit_status": "indexed_not_reconstructed",
    }


EXPECTED_NODES = [
    node("G2_ROOT_C", "claim_root", None, "Theorem 1.1 to Fefferman C", "Theorem 1.1", "exact_label",
         ["NavierStokes/ComparatorSolution.lean", "NavierStokes/ComparatorR3Theorem.lean"],
         "derive the exact C existential/non-existence target from the constructed whole-space candidate for every positive viscosity"),
    node("G2_ROOT_D", "claim_root", None, "Corollary 10.6 to Fefferman D", "Corollary 10.6", "exact_label",
         ["NavierStokes/ComparatorSolution.lean", "NavierStokes/ComparatorTheorem.lean"],
         "derive the exact D existential/non-existence target from the periodic candidate for every positive viscosity"),
    node("G2_C_BRIDGE", "target_bridge", "uniqueness_and_continuation", "Whole-space candidate-to-C bridge",
         "Theorem 1.1 comparison/non-existence step", "programme_obligation",
         ["NavierStokes/ComparatorR3Theorem.lean", "NavierStokes/R3FiniteEnergyComparison.lean"],
         "show zero initial data and the compact force satisfy comparator decay conditions and that a hypothetical global finite-energy solution contradicts the compact candidate"),
    node("G2_D_BRIDGE", "target_bridge", "periodicization", "Periodic candidate-to-D bridge",
         "Corollary 10.6 periodic breakdown step", "exact_label_plus_programme_obligation",
         ["NavierStokes/ComparatorTheorem.lean", "NavierStokes/CandidateConsequences.lean"],
         "show the viscosity-rescaled zero-data periodic force satisfies the comparator and that any global periodic solution contradicts the candidate maximal-lifespan result"),
    node("G2_WHOLE_SPACE_UNIQUENESS", "comparison", "uniqueness_and_continuation", "Whole-space finite-energy uniqueness/comparison",
         "final uniqueness/continuation argument for C", "programme_obligation",
         ["NavierStokes/R3FiniteEnergyComparison.lean", "NavierStokes/R3/WholeSpaceUniqueness.lean"],
         "prove equality of the compact candidate and any comparator-admissible global solution on every compact interval before blowup, using finite energy and compact support"),
    node("G2_PERIODIC_MAX_LIFESPAN", "comparison", "uniqueness_and_continuation", "Periodic uniqueness and maximal classical lifespan",
         "final uniqueness/continuation argument for D", "programme_obligation",
         ["NavierStokes/MaximalLifespan.lean", "NavierStokes/PeriodicUniqueness.lean"],
         "prove candidate lifespan one and exclude any strictly longer periodic classical solution without importing a general existence theorem"),
    node("G2_R3_COMPACT_CANDIDATE", "candidate_extraction", "spatial_localization_and_smooth_force", "Compact whole-space candidate",
         "spatial localization and compact forcing step", "programme_obligation",
         ["NavierStokes/R3ActualCandidate.lean", "NavierStokes/R3CompactCandidate.lean", "NavierStokes/CompactSpatialForceDecay.lean"],
         "extract smooth compactly supported whole-space velocity, pressure and force with zero initial velocity, exact PDE, divergence-free flow and unbounded speed"),
    node("G2_PERIODIC_CANDIDATE", "candidate_extraction", "periodicization", "Periodic candidate",
         "periodicization step used for D", "programme_obligation",
         ["NavierStokes/ActualCandidateAssembly.lean", "NavierStokes/CandidateConsequences.lean", "NavierStokes/MixedPeriodicAssembly.lean"],
         "assemble the periodic candidate properties including smoothness, periodicity, zero initial velocity, compact future-time force support and blowup"),
    node("G2_ACTUAL_ASSEMBLY", "construction", None, "Literal candidate assembly", "Sections 8-10 construction assembly", "section_family",
         ["NavierStokes/ActualCandidateAssembly.lean"],
         "assemble the initialized base, mean, oscillatory, correction and pressure fields into the selected witness with coherent support and endpoint properties"),
    node("G2_LEADING_PROFILE", "construction", "concentrating_axisymmetric_leading_profile", "Concentrating axisymmetric leading profile",
         "concentrating axisymmetric leading-profile construction", "programme_obligation",
         ["NavierStokes/FinalSlowBase.lean", "NavierStokes/PreparedOutgoing.lean", "NavierStokes/ReferenceBounds.lean"],
         "construct the leading axisymmetric profile and preserve the sign, support and cone geometry required by later corrections"),
    node("G2_SCALING", "estimate", "self_similar_scaling_and_velocity_growth", "Self-similar scales and exponent ledger",
         "Proposition 10.3; sections 8.1 and 10.2", "exact_labels_from_formalization_comments",
         ["NavierStokes/ExponentLedger.lean", "NavierStokes/ChartScales.lean"],
         "track the radial/axial concentration, velocity growth and residual-improvement exponents without converting arithmetic checks into analytic estimates"),
    node("G2_ANNULAR_STRESS", "construction", "annular_residual_stress", "Annular residual stress and signed exterior target",
         "annular residual-stress construction and support", "programme_obligation",
         ["NavierStokes/ActualSignedExterior.lean", "NavierStokes/ModulatedCone.lean", "NavierStokes/SignedCovariance.lean"],
         "construct the residual stress on the intended annular/support region and keep its sign/orientation conventions consistent with the wave covariance target"),
    node("G2_STRESS_CONE", "estimate", "admissible_stress_cone", "Admissible stress-cone argument",
         "Lemma 3.5 and equation (11)", "exact_labels_from_formalization_comments",
         ["NavierStokes/ConeAlgebra.lean", "NavierStokes/UniformCone.lean", "NavierStokes/OutgoingCone.lean", "NavierStokes/ModulatedCone.lean"],
         "establish the exact algebraic cone criterion and uniform positive margins needed for the physical stress profiles"),
    node("G2_PULSE_COVARIANCE", "construction", "oscillatory_pulse_covariance", "Two pulse families and covariance realization",
         "section 10.2 covariance realization", "section_label_from_formalization_comments",
         ["NavierStokes/PulseCovariance.lean", "NavierStokes/PartitionedCovariance.lean", "NavierStokes/SignedCovariance.lean", "NavierStokes/ActualPrimaryCovariance.lean"],
         "realize the target covariance with separated signed pulse families while controlling cross-copy and signed-square terms"),
    node("G2_DIVERGENCE_FREE_CURL", "construction", "divergence_free_curl", "Exact divergence-free curl realization",
         "Lemma 8.8", "exact_label_from_formalization_comment",
         ["NavierStokes/CurlGeometry.lean", "NavierStokes/OscillatoryCurl.lean", "NavierStokes/CurrentSignedCurl.lean", "NavierStokes/PhysicalCurlCovariance.lean"],
         "realize the oscillatory velocity as an exact curl, prove the principal-symbol identities and preserve divergence cancellation through the physical construction"),
    node("G2_CORRECTION_CYCLE", "iteration", "correction_cycle", "Initialized correction cycle",
         "iterative correction cycle in sections 8-10", "section_family",
         ["NavierStokes/ActualCandidateConstruction.lean", "NavierStokes/ActualCycleParameters.lean", "NavierStokes/ActualIterationLedger.lean"],
         "iterate the fixed correction parameters while preserving carrier geometry, coefficients, pressure reconstruction and improving residual bands"),
    node("G2_RESIDUAL_FLATNESS", "limit", "residual_flatness_and_summation", "Shrinking-cutoff summation and infinite-order residual flatness",
         "summation with shrinking cutoffs and terminal residual flatness", "programme_obligation",
         ["NavierStokes/JointResidualLimits.lean", "NavierStokes/PeriodicResidualLimits.lean", "NavierStokes/GlobalBaseError.lean", "NavierStokes/ExponentLedger.lean"],
         "show the actual residual jets vanish jointly at the singular endpoint and extend smoothly away from the singular point without assuming the desired limit"),
    node("G2_LOCALIZATION", "localization", "spatial_localization_and_smooth_force", "Spatial localization, periodization and smooth force",
         "spatial localization and smooth compact forcing", "programme_obligation",
         ["NavierStokes/SpatialLocalization.lean", "NavierStokes/PeriodicResidualLimits.lean", "NavierStokes/CompactSpatialForceDecay.lean", "NavierStokes/R3CompactCandidate.lean"],
         "cut and periodize the physical fields using derivative locality, prove smooth residual/force extension, and retain exact support and PDE identities"),
    node("G2_ENERGY", "estimate", "bounded_energy_and_dissipation", "Bounded energy and finite-energy comparison inputs",
         "bounded kinetic energy and integrated-dissipation requirement", "programme_obligation",
         ["NavierStokes/R3CompactEnergy.lean", "NavierStokes/R3EnergyNorms.lean", "NavierStokes/R3UniformBounds.lean", "NavierStokes/R3FiniteEnergyComparison.lean"],
         "establish the finite/uniform energy controls used by C and by the whole-space uniqueness comparison, separately from the speed blowup"),
    node("G2_PERIODIZATION", "localization", "periodicization", "Periodicization and periodic force decay",
         "Corollary 10.6 periodicization step", "exact_label_plus_programme_obligation",
         ["NavierStokes/PeriodicResidualLimits.lean", "NavierStokes/MixedPeriodicAssembly.lean", "NavierStokes/CandidateConsequences.lean"],
         "periodize the localized candidate, retain velocity and pressure periodicity, and derive all-order future-time force decay from smooth compact time support"),
]

EXPECTED_EDGES = [
    {"from": "G2_ROOT_C", "to": "G2_C_BRIDGE"},
    {"from": "G2_C_BRIDGE", "to": "G2_R3_COMPACT_CANDIDATE"},
    {"from": "G2_C_BRIDGE", "to": "G2_WHOLE_SPACE_UNIQUENESS"},
    {"from": "G2_WHOLE_SPACE_UNIQUENESS", "to": "G2_ENERGY"},
    {"from": "G2_WHOLE_SPACE_UNIQUENESS", "to": "G2_LOCALIZATION"},
    {"from": "G2_R3_COMPACT_CANDIDATE", "to": "G2_LOCALIZATION"},
    {"from": "G2_R3_COMPACT_CANDIDATE", "to": "G2_ENERGY"},
    {"from": "G2_R3_COMPACT_CANDIDATE", "to": "G2_ACTUAL_ASSEMBLY"},
    {"from": "G2_ROOT_D", "to": "G2_D_BRIDGE"},
    {"from": "G2_D_BRIDGE", "to": "G2_PERIODIC_CANDIDATE"},
    {"from": "G2_D_BRIDGE", "to": "G2_PERIODIC_MAX_LIFESPAN"},
    {"from": "G2_PERIODIC_MAX_LIFESPAN", "to": "G2_PERIODIC_CANDIDATE"},
    {"from": "G2_PERIODIC_CANDIDATE", "to": "G2_PERIODIZATION"},
    {"from": "G2_PERIODIC_CANDIDATE", "to": "G2_ACTUAL_ASSEMBLY"},
    {"from": "G2_PERIODIZATION", "to": "G2_LOCALIZATION"},
    {"from": "G2_PERIODIZATION", "to": "G2_RESIDUAL_FLATNESS"},
    {"from": "G2_LOCALIZATION", "to": "G2_RESIDUAL_FLATNESS"},
    {"from": "G2_LOCALIZATION", "to": "G2_DIVERGENCE_FREE_CURL"},
    {"from": "G2_ENERGY", "to": "G2_SCALING"},
    {"from": "G2_ENERGY", "to": "G2_LOCALIZATION"},
    {"from": "G2_ACTUAL_ASSEMBLY", "to": "G2_RESIDUAL_FLATNESS"},
    {"from": "G2_ACTUAL_ASSEMBLY", "to": "G2_LEADING_PROFILE"},
    {"from": "G2_RESIDUAL_FLATNESS", "to": "G2_CORRECTION_CYCLE"},
    {"from": "G2_RESIDUAL_FLATNESS", "to": "G2_SCALING"},
    {"from": "G2_CORRECTION_CYCLE", "to": "G2_ANNULAR_STRESS"},
    {"from": "G2_CORRECTION_CYCLE", "to": "G2_DIVERGENCE_FREE_CURL"},
    {"from": "G2_CORRECTION_CYCLE", "to": "G2_PULSE_COVARIANCE"},
    {"from": "G2_ANNULAR_STRESS", "to": "G2_STRESS_CONE"},
    {"from": "G2_PULSE_COVARIANCE", "to": "G2_ANNULAR_STRESS"},
    {"from": "G2_PULSE_COVARIANCE", "to": "G2_STRESS_CONE"},
    {"from": "G2_STRESS_CONE", "to": "G2_LEADING_PROFILE"},
    {"from": "G2_LEADING_PROFILE", "to": "G2_SCALING"},
]

EXPECTED_DISPOSITION = {
    "dependency_classes_accounted_for": True,
    "rooted_C_and_D_paths_accounted_for": True,
    "graph_acyclic_required": True,
    "orphan_nodes_forbidden": True,
    "lemma_level_dependency_indexing_complete": False,
    "programme_obligation_nodes_remaining": 12,
    "pass_condition_met": False,
    "local_estimate_correctness_assessed": False,
    "next_step": "3A_gate_2_expand_lemma_proposition_index",
}

EXPECTED_INVARIANTS = [
    "DEPENDENCY_CLASS_COVERAGE != GATE2_COMPLETION",
    "PROGRAMME_OBLIGATION_ANCHOR != EXPLICIT_LEMMA_PROPOSITION_INDEX",
    "FORMAL_MODULE_ANCHOR != ANALYTIC_RECONSTRUCTION",
    "PAPER_LABEL_OR_SECTION != VERIFIED_LEMMA",
    "GRAPH_EDGE != PROVED_IMPLICATION",
    "GATE2_PARTIAL != GATE2_PASS",
    "GATE2_PARTIAL != LEAN_REPLAY",
    "GATE2_PARTIAL != INDEPENDENT_VERIFICATION_COMPLETE",
    "C_AND_D_DEPENDENCY_PATHS_DO_NOT_RESOLVE_A_OR_B",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def reject_schema(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"dependency-DAG schema regression: forbidden mutation accepted: {label}")


def reject_cross(candidate: dict, external: dict, correspondence: dict, label: str) -> None:
    try:
        validate_cross(candidate, external, correspondence)
    except SystemExit:
        return
    raise SystemExit(f"dependency-DAG regression: forbidden mutation accepted: {label}")


def claim(external: dict, formulation_id: str) -> dict:
    matches = [item for item in external["claims"] if item["formulation_id"] == formulation_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one external claim for {formulation_id}")
    return matches[0]


def assert_acyclic(node_ids: set[str], edges: list[dict]) -> None:
    graph = {node_id: [] for node_id in node_ids}
    for edge in edges:
        graph[edge["from"]].append(edge["to"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise SystemExit(f"dependency DAG contains a cycle at {node_id}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in graph[node_id]:
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(node_ids):
        visit(node_id)


def reachable(root: str, edges: list[dict]) -> set[str]:
    graph: dict[str, list[str]] = {}
    for edge in edges:
        graph.setdefault(edge["from"], []).append(edge["to"])
    seen: set[str] = set()
    stack = [root]
    while stack:
        node_id = stack.pop()
        if node_id in seen:
            continue
        seen.add(node_id)
        stack.extend(graph.get(node_id, []))
    return seen


def validate_cross(dag: dict, external: dict, correspondence: dict) -> None:
    if dag["pr13_merge_baseline"] != PR13_MERGE:
        raise SystemExit("PR #13 merge baseline drift")
    if dag["gate_status"] != GATE_STATUS:
        raise SystemExit("Gate 2 must remain partial until lemma/proposition indexing closes")
    if dag["authority"] != EXPECTED_AUTHORITY:
        raise SystemExit("Gate 2 authority map drift")
    if dag["source_pins"] != EXPECTED_SOURCE_PINS:
        raise SystemExit("Gate 2 source-pin drift")
    if dag["scope"] != EXPECTED_SCOPE:
        raise SystemExit("Gate 2 scope/authority drift")
    if dag["required_dependency_classes"] != EXPECTED_REQUIRED_CLASSES:
        raise SystemExit("required dependency-class set/order drift")
    if dag["roots"] != {"C": "G2_ROOT_C", "D": "G2_ROOT_D"}:
        raise SystemExit("C/D root identity drift")
    if dag["nodes"] != EXPECTED_NODES:
        raise SystemExit("audited dependency-node semantics drift")
    if dag["edges"] != EXPECTED_EDGES:
        raise SystemExit("audited dependency-edge semantics drift")
    if dag["gate_2_disposition"] != EXPECTED_DISPOSITION:
        raise SystemExit("Gate 2 disposition drift")
    if dag["machine_invariants"] != EXPECTED_INVARIANTS:
        raise SystemExit("Gate 2 machine-invariant set drift")

    if correspondence["gate_status"] != "statement_correspondence_confirmed":
        raise SystemExit("Gate 1 correspondence is no longer confirmed")
    if correspondence["formal_artifact_pin"]["commit"] != LEAN_COMMIT:
        raise SystemExit("Gate 1 Lean pin diverges from Gate 2")
    if correspondence["pr12_merge_baseline"] != "ef48a7d7f195f475e9a0a792edbb750e74d210f0":
        raise SystemExit("Gate 1 correspondence baseline drift")

    external_paper = external["artifact_pins"]["OPENAI_NS_BLOWUP_2026"]
    external_lean = external["artifact_pins"]["OPENAI_NS_LEAN_2026"]
    if external_paper != {"url": PAPER_URL, "sha256": PAPER_SHA256}:
        raise SystemExit("external paper pin diverges from Gate 2")
    if external_lean["repository"] != LEAN_REPOSITORY or external_lean["commit"] != LEAN_COMMIT:
        raise SystemExit("external Lean pin diverges from Gate 2")

    for formulation_id in ("C", "D"):
        ext = claim(external, formulation_id)
        if ext["qsol_status"] != "external_claim_pending_independent_verification":
            raise SystemExit(f"external {formulation_id} status no longer pending independent verification")
    for formulation_id in ("A", "B"):
        if claim(external, formulation_id)["qsol_status"] != "not_resolved":
            raise SystemExit(f"unforced formulation {formulation_id} was silently resolved")

    node_ids = [item["node_id"] for item in dag["nodes"]]
    if len(node_ids) != len(set(node_ids)):
        raise SystemExit("duplicate Gate 2 node IDs")
    node_set = set(node_ids)
    for edge in dag["edges"]:
        if edge["from"] not in node_set or edge["to"] not in node_set:
            raise SystemExit(f"edge references unknown node: {edge}")
        if edge["from"] == edge["to"]:
            raise SystemExit(f"self dependency forbidden: {edge}")
    assert_acyclic(node_set, dag["edges"])

    incoming = {node_id: 0 for node_id in node_set}
    for edge in dag["edges"]:
        incoming[edge["to"]] += 1
    allowed_zero_incoming = {dag["roots"]["C"], dag["roots"]["D"]}
    unexpected_orphans = {node_id for node_id, degree in incoming.items() if degree == 0} - allowed_zero_incoming
    if unexpected_orphans:
        raise SystemExit(f"orphan Gate 2 nodes: {sorted(unexpected_orphans)}")

    reachable_union = reachable(dag["roots"]["C"], dag["edges"]) | reachable(dag["roots"]["D"], dag["edges"])
    if reachable_union != node_set:
        raise SystemExit(f"nodes not reachable from C/D roots: {sorted(node_set - reachable_union)}")

    present_classes = {item["dependency_class"] for item in dag["nodes"] if item["dependency_class"] is not None}
    missing = set(EXPECTED_REQUIRED_CLASSES) - present_classes
    if missing:
        raise SystemExit(f"required dependency classes missing: {sorted(missing)}")

    programme_obligation_nodes = sum(
        item["paper_anchor_precision"] in PROGRAMME_OBLIGATION_PRECISIONS
        for item in dag["nodes"]
    )
    if programme_obligation_nodes != EXPECTED_DISPOSITION["programme_obligation_nodes_remaining"]:
        raise SystemExit("programme-obligation-bearing anchor count drift")
    if dag["scope"]["lemma_level_dependency_indexing_complete"]:
        raise SystemExit("lemma-level indexing cannot be complete while programme obligations remain")
    if dag["gate_2_disposition"]["pass_condition_met"]:
        raise SystemExit("Gate 2 pass condition cannot be true for the partial graph")


def run_negative_probes(dag: dict, external: dict, correspondence: dict,
                        validator: Draft202012Validator) -> None:
    mutated = copy.deepcopy(dag)
    mutated["as_of"] = "not-a-date"
    reject_schema(validator, mutated, "malformed Gate 2 audit date")

    mutated = copy.deepcopy(dag)
    mutated["gate_status"] = "analytical_dependency_graph_complete"
    reject_schema(validator, mutated, "Gate 2 marked complete before lemma-level indexing")

    mutated = copy.deepcopy(dag)
    mutated["scope"]["lemma_level_dependency_indexing_complete"] = True
    reject_schema(validator, mutated, "lemma-level indexing falsely marked complete")

    mutated = copy.deepcopy(dag)
    mutated["gate_2_disposition"]["pass_condition_met"] = True
    reject_schema(validator, mutated, "Gate 2 pass condition falsely marked met")

    mutated = copy.deepcopy(dag)
    mutated["scope"]["proof_validity_assessed"] = True
    reject_schema(validator, mutated, "dependency graph promoted to proof-validity assessment")

    mutated = copy.deepcopy(dag)
    mutated["nodes"][10]["obligation"] = "The exponent arithmetic proves the PDE estimates."
    reject_cross(mutated, external, correspondence, "scaling obligation corrupted into proof claim")

    mutated = copy.deepcopy(dag)
    mutated["nodes"][12]["paper_anchor"] = "unrelated lemma"
    reject_cross(mutated, external, correspondence, "stress-cone source anchor rewritten")

    mutated = copy.deepcopy(dag)
    mutated["nodes"][14]["formal_modules"] = ["NavierStokes/CurlGeometry.lean"]
    reject_cross(mutated, external, correspondence, "curl formal-module spine truncated")

    mutated = copy.deepcopy(dag)
    mutated["edges"].pop()
    reject_cross(mutated, external, correspondence, "audited dependency edge removed")

    mutated = copy.deepcopy(dag)
    pulse_to_stress = mutated["edges"].index({"from": "G2_PULSE_COVARIANCE", "to": "G2_ANNULAR_STRESS"})
    mutated["edges"][pulse_to_stress] = {"from": "G2_ANNULAR_STRESS", "to": "G2_PULSE_COVARIANCE"}
    reject_cross(mutated, external, correspondence, "residual-stress/covariance dependency reversed")

    mutated = copy.deepcopy(dag)
    mutated["edges"].append({"from": "G2_SCALING", "to": "G2_ROOT_C"})
    reject_cross(mutated, external, correspondence, "cycle injected into dependency graph")

    mutated = copy.deepcopy(dag)
    mutated["required_dependency_classes"].remove("bounded_energy_and_dissipation")
    reject_cross(mutated, external, correspondence, "required energy dependency class removed")

    mutated = copy.deepcopy(dag)
    mutated["source_pins"]["lean"]["commit"] = "0" * 40
    reject_cross(mutated, external, correspondence, "Lean pin rewritten")

    mutated_external = copy.deepcopy(external)
    claim(mutated_external, "C")["qsol_status"] = "independent_verification_complete"
    reject_cross(dag, mutated_external, correspondence, "external C status promoted by Gate 2")

    mutated_corr = copy.deepcopy(correspondence)
    mutated_corr["gate_status"] = "not_assessed"
    reject_cross(dag, external, mutated_corr, "Gate 1 prerequisite removed")


def main() -> None:
    dag = load_json(RESEARCH / "openai_2026_dependency_dag.json")
    schema = load_json(SCHEMAS / "openai_2026_dependency_dag.schema.json")
    external = load_json(RESEARCH / "external_claim_registry.json")
    correspondence = load_json(RESEARCH / "openai_2026_correspondence.json")

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    validator.validate(dag)

    validate_cross(dag, external, correspondence)
    run_negative_probes(dag, external, correspondence, validator)

    print(
        "OpenAI 2026 analytical dependency DAG validation: PASS "
        f"(Gate 2={dag['gate_status']}, nodes={len(dag['nodes'])}, "
        f"edges={len(dag['edges'])}, classes={len(dag['required_dependency_classes'])}, "
        f"programme_obligations={dag['gate_2_disposition']['programme_obligation_nodes_remaining']}, "
        f"Lean={LEAN_COMMIT[:12]})"
    )


if __name__ == "__main__":
    main()