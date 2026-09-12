#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate Phase 3A Gate 2 formal-declaration index slice 1."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SCHEMAS = RESEARCH / "schemas"
INDEX = RESEARCH / "openai_2026_formal_index"
FORMAT_CHECKER = FormatChecker()

PR14_MERGE = "66206230bc8504dc57808468adac6f1b5ffd39b4"
LEAN_REPOSITORY = "openai/NavierStokesAndEuler"
LEAN_COMMIT = "8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538"
PROGRAMME_PRECISIONS = {"programme_obligation", "exact_label_plus_programme_obligation"}
RAW_SOURCE_BASE = f"https://raw.githubusercontent.com/{LEAN_REPOSITORY}/{LEAN_COMMIT}/"
DECLARATION_RE = re.compile(
    r"(?m)^[ \t]*(?:(?:private|protected|noncomputable)\s+)*"
    r"(?P<kind>theorem|lemma|def|abbrev|structure)\s+"
    r"(?P<name>[A-Za-z0-9_'.]+)\b"
)

EXPECTED_INDEXED_PARENTS = [
    "G2_C_BRIDGE",
    "G2_D_BRIDGE",
    "G2_WHOLE_SPACE_UNIQUENESS",
    "G2_PERIODIC_MAX_LIFESPAN",
    "G2_R3_COMPACT_CANDIDATE",
    "G2_PERIODIC_CANDIDATE",
]
EXPECTED_REMAINING_PARENTS = [
    "G2_LEADING_PROFILE",
    "G2_ANNULAR_STRESS",
    "G2_RESIDUAL_FLATNESS",
    "G2_LOCALIZATION",
    "G2_ENERGY",
    "G2_PERIODIZATION",
]
EXPECTED_NODE_FILES = [
    {"parent_node_id": "G2_C_BRIDGE", "path": "research/openai_2026_formal_index/c_bridge.json", "semantic_sha256": "e90bf98d59e0b28489b881ade355b06796615dd2cde90b0007985b07005530df"},
    {"parent_node_id": "G2_D_BRIDGE", "path": "research/openai_2026_formal_index/d_bridge.json", "semantic_sha256": "992759b23ca2a0ca96c46179a874657222fc53d2d3bb56ad438f5eaf8f65aec0"},
    {"parent_node_id": "G2_WHOLE_SPACE_UNIQUENESS", "path": "research/openai_2026_formal_index/whole_space_uniqueness.json", "semantic_sha256": "7a7b78735347cac72014a074cbec6396b0ccf8ee770170fd38ea282597cdb2e8"},
    {"parent_node_id": "G2_PERIODIC_MAX_LIFESPAN", "path": "research/openai_2026_formal_index/periodic_max_lifespan.json", "semantic_sha256": "1cd743bd0edbce09533652f3924f74846ab905606fe83091a9e7aad248790f44"},
    {"parent_node_id": "G2_R3_COMPACT_CANDIDATE", "path": "research/openai_2026_formal_index/r3_compact_candidate.json", "semantic_sha256": "038dcbb33232fc1db570af96c654098716bca66a709efdc9d71c52ec8b2a47f6"},
    {"parent_node_id": "G2_PERIODIC_CANDIDATE", "path": "research/openai_2026_formal_index/periodic_candidate.json", "semantic_sha256": "a586cd25710fa8219cf067cdcce568f78811416cacb1672db1b86db8accadd6a"},
]
EXPECTED_MODULE_PINS = [
    {"path": "NavierStokes/ActualCandidateAssembly.lean", "blob_sha": "820bd414afdb55d4d74a78be357311e6b234a2e4"},
    {"path": "NavierStokes/CandidateConsequences.lean", "blob_sha": "5f3eae72b029ea2503f9c2eaa20a1b11685062ff"},
    {"path": "NavierStokes/CompactSpatialForceDecay.lean", "blob_sha": "aaeb4f7f35f43527f6e71f3a581c186c81dd80f2"},
    {"path": "NavierStokes/ComparatorR3Theorem.lean", "blob_sha": "eb98522380b91b209421bf7519f34bc68ba95c1d"},
    {"path": "NavierStokes/ComparatorTheorem.lean", "blob_sha": "8105493534a5007c689c59e22bc252623bcbe901"},
    {"path": "NavierStokes/MaximalLifespan.lean", "blob_sha": "83968db431a7327110e9ea10c6196dc3e39d5323"},
    {"path": "NavierStokes/MixedPeriodicAssembly.lean", "blob_sha": "cdf0ce21933fa2770e91f0ae0542c73782186b97"},
    {"path": "NavierStokes/PeriodicUniqueness.lean", "blob_sha": "20577dc723b0e82766f885f7261bc40a827219d6"},
    {"path": "NavierStokes/R3/WholeSpaceUniqueness.lean", "blob_sha": "ad83465eedc6b723fb01d10603453234cf7f84b4"},
    {"path": "NavierStokes/R3ActualCandidate.lean", "blob_sha": "5a1d79b69591388af6b4bfceb3566cb797e4fb8a"},
    {"path": "NavierStokes/R3CompactCandidate.lean", "blob_sha": "97082e900e4334c703617ebde8ecb58dfc2f1590"},
    {"path": "NavierStokes/R3FiniteEnergyComparison.lean", "blob_sha": "43dfeab5d087a92474b90c0ab9ee38d57ba25481"},
]
EXPECTED_DAG_SHARED_MODULE_PATHS = {
    "NavierStokes/ActualCandidateAssembly.lean",
    "NavierStokes/CandidateConsequences.lean",
    "NavierStokes/ComparatorR3Theorem.lean",
    "NavierStokes/ComparatorTheorem.lean",
    "NavierStokes/MaximalLifespan.lean",
    "NavierStokes/R3ActualCandidate.lean",
    "NavierStokes/R3CompactCandidate.lean",
    "NavierStokes/R3FiniteEnergyComparison.lean",
}
EXPECTED_EDGES = [
    {"from": "NavierStokes.ComparatorBridge.navier_stokes_breakdown_R3", "to": "NavierStokes.R3CompactCandidate.selected_compact_candidate", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.navier_stokes_breakdown_R3", "to": "NavierStokes.ComparatorBridge.option_C_of_compact_candidate", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.option_C_of_compact_candidate", "to": "NavierStokes.CompactSpatialForceDecay.forceConditionDecay", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.option_C_of_compact_candidate", "to": "NavierStokes.ComparatorBridge.compact_candidate_excludes_global_solution", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.navier_stokes_breakdown_periodic", "to": "NavierStokes.ActualCandidateAssembly.selected_candidate", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.navier_stokes_breakdown_periodic", "to": "NavierStokes.ComparatorBridge.option_D_of_candidate", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.option_D_of_candidate", "to": "NavierStokes.CandidateConsequences.futureJet_decay", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.option_D_of_candidate", "to": "NavierStokes.MaximalLifespan.candidate_excludes_global_solution", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.compact_candidate_excludes_global_solution", "to": "NavierStokesR3.WholeSpaceUniqueness.classical_uniqueness_on_Icc", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.compact_candidate_excludes_global_solution", "to": "NavierStokes.ComparatorBridge.GlobalSolutionRn.uniformFiniteEnergy", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ComparatorBridge.compact_candidate_excludes_global_solution", "to": "NavierStokes.R3CompactCandidate.Properties.not_global_agreement", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_excludes_global_solution", "to": "NavierStokes.MaximalLifespan.candidate_no_solution_after_one", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_no_solution_after_one", "to": "NavierStokes.MaximalLifespan.candidate_agree_on_overlap", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_agree_on_overlap", "to": "NavierStokes.MaximalLifespan.ClassicalSolution.agree_on_overlap", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_agree_on_overlap", "to": "NavierStokes.MaximalLifespan.candidate_is_classical_solution", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.ClassicalSolution.agree_on_overlap", "to": "NavierStokes.PeriodicUniqueness.classical_uniqueness_on_Icc", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_is_maximal", "to": "NavierStokes.MaximalLifespan.candidate_is_classical_solution", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.MaximalLifespan.candidate_is_maximal", "to": "NavierStokes.MaximalLifespan.candidate_no_solution_after_one", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.selected_compact_candidate", "to": "NavierStokes.ActualCandidateAssembly.selected_witness", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.selected_compact_candidate", "to": "NavierStokes.R3CompactCandidate.of_localized_fields", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.of_localized_fields", "to": "NavierStokes.R3CompactCandidate.of_periodic_local_model", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.of_periodic_local_model", "to": "NavierStokes.R3CompactCandidate.compactForce_smooth", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.of_periodic_local_model", "to": "NavierStokes.R3CompactCandidate.local_model_divergence", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.R3CompactCandidate.of_periodic_local_model", "to": "NavierStokes.R3CompactCandidate.local_model_equation", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ActualCandidateAssembly.selected_candidate", "to": "NavierStokes.ActualCandidateAssembly.selected_witness", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.ActualCandidateAssembly.selected_witness", "to": "NavierStokes.ActualCandidateAssembly.witness", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.CandidateConsequences.consequences_of_candidate", "to": "NavierStokes.MaximalLifespan.candidate_is_maximal", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.CandidateConsequences.consequences_of_candidate", "to": "NavierStokes.CandidateConsequences.futureJet_decay", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.CandidateConsequences.mixed_exists_force_with_consequences", "to": "NavierStokes.MixedPeriodicAssembly.exists_candidate_force", "basis": "direct_body_reference_in_pinned_source"},
    {"from": "NavierStokes.CandidateConsequences.mixed_exists_force_with_consequences", "to": "NavierStokes.CandidateConsequences.consequences_of_candidate", "basis": "direct_body_reference_in_pinned_source"},
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def semantic_sha256(value: dict) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def reject_schema(validator: Draft202012Validator, candidate: dict, label: str) -> None:
    try:
        validator.validate(candidate)
    except ValidationError:
        return
    raise SystemExit(f"formal-index schema regression: forbidden mutation accepted: {label}")


def reject_cross(candidate_manifest: dict, nodes: list[dict], dag: dict, external: dict,
                 correspondence: dict, label: str) -> None:
    try:
        validate_cross(candidate_manifest, nodes, dag, external, correspondence)
    except SystemExit:
        return
    raise SystemExit(f"formal-index regression: forbidden cross-registry mutation accepted: {label}")


def claim(external: dict, formulation_id: str) -> dict:
    matches = [item for item in external["claims"] if item["formulation_id"] == formulation_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one external claim for {formulation_id}")
    return matches[0]


def validate_manifest_node_binding(entry: dict, node_data: dict) -> None:
    if node_data["parent_node_id"] != entry["parent_node_id"]:
        raise SystemExit(
            f"formal-index manifest path/parent mismatch: {entry['path']} declares "
            f"{node_data['parent_node_id']}, expected {entry['parent_node_id']}"
        )
    if semantic_sha256(node_data) != entry["semantic_sha256"]:
        raise SystemExit(f"formal-index manifest path/semantic hash mismatch: {entry['path']}")


@lru_cache(maxsize=None)
def fetch_pinned_module(path: str, blob_sha: str) -> str:
    url = RAW_SOURCE_BASE + quote(path, safe="/")
    request = Request(url, headers={"User-Agent": "QSOL-NS-formal-index-validator/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SystemExit(f"unable to fetch pinned Lean module {path}: {exc}") from exc
    actual = git_blob_sha1(raw)
    if actual != blob_sha:
        raise SystemExit(f"pinned Lean module blob mismatch for {path}: {actual} != {blob_sha}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"pinned Lean module is not UTF-8: {path}") from exc


def strip_lean_comments(text: str) -> str:
    """Remove nested block and line comments while preserving token separation."""
    out: list[str] = []
    i = 0
    block_depth = 0
    line_comment = False
    while i < len(text):
        if line_comment:
            if text[i] == "\n":
                line_comment = False
                out.append("\n")
            else:
                out.append(" ")
            i += 1
            continue
        if block_depth:
            if text.startswith("/-", i):
                block_depth += 1
                out.extend("  ")
                i += 2
            elif text.startswith("-/", i):
                block_depth -= 1
                out.extend("  ")
                i += 2
            else:
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            continue
        if text.startswith("--", i):
            line_comment = True
            out.extend("  ")
            i += 2
        elif text.startswith("/-", i):
            block_depth = 1
            out.extend("  ")
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def declaration_source_record(source: str, fully_qualified_name: str, expected_kind: str) -> tuple[str, str]:
    matches = list(DECLARATION_RE.finditer(source))
    candidates: list[tuple[int, int, re.Match[str]]] = []
    for index, match in enumerate(matches):
        local_name = match.group("name")
        if fully_qualified_name == local_name or fully_qualified_name.endswith("." + local_name):
            candidates.append((len(local_name), index, match))
    if not candidates:
        raise SystemExit(f"indexed declaration absent from pinned Lean source: {fully_qualified_name}")
    longest = max(item[0] for item in candidates)
    best = [item for item in candidates if item[0] == longest]
    if len(best) != 1:
        raise SystemExit(f"ambiguous declaration match in pinned Lean source: {fully_qualified_name}")
    _, index, match = best[0]
    if match.group("kind") != expected_kind:
        raise SystemExit(
            f"declaration kind drift for {fully_qualified_name}: "
            f"source={match.group('kind')} index={expected_kind}"
        )
    end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
    declaration_tail = source[match.end():end]
    assign = declaration_tail.find(":=")
    body = declaration_tail[assign + 2:] if assign >= 0 else ""
    return match.group("name"), strip_lean_comments(body)


def contains_lean_identifier(text: str, token: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_']){re.escape(token)}(?![A-Za-z0-9_'])"
    return re.search(pattern, text) is not None


def validate_pinned_source_edges(manifest: dict, nodes: list[dict]) -> None:
    pin_by_path = {item["path"]: item["blob_sha"] for item in manifest["source_pin"]["module_pins"]}
    declarations: dict[str, dict] = {}
    for node_data in nodes:
        for declaration in node_data["declarations"]:
            name = declaration["fully_qualified_name"]
            identity = {"module": declaration["module"], "kind": declaration["kind"]}
            if name in declarations and declarations[name] != identity:
                raise SystemExit(f"conflicting indexed declaration identity: {name}")
            declarations[name] = identity

    source_records: dict[str, tuple[str, str]] = {}
    for name, declaration in declarations.items():
        module = declaration["module"]
        if module not in pin_by_path:
            raise SystemExit(f"declaration source module is not pinned: {name} -> {module}")
        source = fetch_pinned_module(module, pin_by_path[module])
        source_records[name] = declaration_source_record(source, name, declaration["kind"])

    for edge in manifest["formal_edges"]:
        if edge["basis"] != "direct_body_reference_in_pinned_source":
            raise SystemExit(f"unsupported formal-edge basis: {edge}")
        source_name = edge["from"]
        target_name = edge["to"]
        if source_name not in source_records or target_name not in source_records:
            raise SystemExit(f"formal edge endpoint absent from source-backed declaration index: {edge}")
        _, body = source_records[source_name]
        target_local, _ = source_records[target_name]
        reference_tokens = [target_local, target_local.rsplit(".", 1)[-1]]
        if not any(contains_lean_identifier(body, token) for token in dict.fromkeys(reference_tokens)):
            raise SystemExit(
                f"direct formal edge not witnessed in pinned Lean declaration body: "
                f"{source_name} -> {target_name}"
            )


def validate_dag_source_pin_alignment(manifest: dict, dag: dict) -> None:
    manifest_lean = manifest["source_pin"]
    dag_lean = dag["source_pins"]["lean"]
    if dag_lean["repository"] != manifest_lean["repository"]:
        raise SystemExit("Gate 2 DAG Lean repository diverges from formal index")
    if dag_lean["commit"] != manifest_lean["commit"]:
        raise SystemExit("Gate 2 DAG Lean commit diverges from formal index")
    manifest_pins = {item["path"]: item["blob_sha"] for item in manifest_lean["module_pins"]}
    dag_pins = {item["path"]: item["blob_sha"] for item in dag_lean["audited_files"]}
    shared = set(manifest_pins) & set(dag_pins)
    if shared != EXPECTED_DAG_SHARED_MODULE_PATHS:
        raise SystemExit(f"Gate 2 DAG/formal-index shared module set drift: {sorted(shared)}")
    for path in sorted(shared):
        if dag_pins[path] != manifest_pins[path]:
            raise SystemExit(f"Gate 2 DAG/formal-index blob pin divergence: {path}")


def validate_cross(manifest: dict, nodes: list[dict], dag: dict, external: dict, correspondence: dict) -> None:
    if manifest["pr14_merge_baseline"] != PR14_MERGE:
        raise SystemExit("PR #14 merge baseline drift")
    if manifest["source_pin"]["repository"] != LEAN_REPOSITORY or manifest["source_pin"]["commit"] != LEAN_COMMIT:
        raise SystemExit("formal-index Lean source pin drift")
    if manifest["source_pin"]["module_pins"] != EXPECTED_MODULE_PINS:
        raise SystemExit("formal-index module pin drift")
    if manifest["node_files"] != EXPECTED_NODE_FILES:
        raise SystemExit("formal-index node-file lock drift")
    if manifest["formal_edges"] != EXPECTED_EDGES:
        raise SystemExit("formal-index direct-edge semantics drift")

    validate_dag_source_pin_alignment(manifest, dag)

    if dag["gate_status"] != "analytical_dependency_graph_partial":
        raise SystemExit("Gate 2 DAG must remain partial during formal-index slice 1")
    if dag["scope"]["lemma_level_dependency_indexing_complete"]:
        raise SystemExit("coarse DAG unexpectedly claims lemma-level completion")
    if dag["gate_2_disposition"]["pass_condition_met"]:
        raise SystemExit("coarse DAG unexpectedly claims Gate 2 pass")

    programme_parents = [
        item["node_id"] for item in dag["nodes"]
        if item["paper_anchor_precision"] in PROGRAMME_PRECISIONS
    ]
    if len(programme_parents) != 12:
        raise SystemExit(f"expected 12 programme-obligation-bearing DAG parents, got {len(programme_parents)}")
    if set(programme_parents) != set(EXPECTED_INDEXED_PARENTS + EXPECTED_REMAINING_PARENTS):
        raise SystemExit("programme-obligation parent identity drift")
    if manifest["scope"]["parent_nodes_indexed_in_slice"] != EXPECTED_INDEXED_PARENTS:
        raise SystemExit("formal-index slice parent set/order drift")
    if manifest["scope"]["parent_nodes_remaining_after_slice"] != EXPECTED_REMAINING_PARENTS:
        raise SystemExit("formal-index remaining parent set/order drift")

    dag_by_id = {item["node_id"]: item for item in dag["nodes"]}
    manifest_by_parent = {item["parent_node_id"]: item for item in manifest["node_files"]}
    if len(manifest_by_parent) != len(EXPECTED_INDEXED_PARENTS):
        raise SystemExit("duplicate formal-index parent binding")

    module_paths = {item["path"] for item in EXPECTED_MODULE_PINS}
    all_declarations: set[str] = set()
    binding_count = 0
    for node_data in nodes:
        parent = node_data["parent_node_id"]
        if parent not in EXPECTED_INDEXED_PARENTS:
            raise SystemExit(f"unexpected parent in formal-index node: {parent}")
        if node_data["parent_anchor_precision_snapshot"] != dag_by_id[parent]["paper_anchor_precision"]:
            raise SystemExit(f"DAG anchor precision snapshot drift for {parent}")
        if node_data["source_commit"] != LEAN_COMMIT:
            raise SystemExit(f"node Lean commit drift for {parent}")
        expected_hash = manifest_by_parent[parent]["semantic_sha256"]
        if semantic_sha256(node_data) != expected_hash:
            raise SystemExit(f"formal-index semantic identity drift for {parent}")
        names = [item["fully_qualified_name"] for item in node_data["declarations"]]
        if len(names) != len(set(names)):
            raise SystemExit(f"duplicate declaration inside formal-index node {parent}")
        binding_count += len(names)
        all_declarations.update(names)
        for declaration in node_data["declarations"]:
            if declaration["module"] not in module_paths:
                raise SystemExit(f"unpinned formal module referenced by {parent}: {declaration['module']}")
            if declaration["audit_status"] != "indexed_not_reconstructed":
                raise SystemExit(f"formal declaration authority escalation in {parent}")

    if len(all_declarations) != manifest["disposition"]["unique_formal_declarations_indexed"]:
        raise SystemExit("unique formal-declaration count drift")
    if binding_count != manifest["disposition"]["parent_declaration_bindings_indexed"]:
        raise SystemExit("parent/declaration binding count drift")
    if len(manifest["formal_edges"]) != manifest["disposition"]["selected_direct_formal_edges_indexed"]:
        raise SystemExit("selected direct formal-edge count drift")
    for edge in manifest["formal_edges"]:
        if edge["from"] not in all_declarations or edge["to"] not in all_declarations:
            raise SystemExit(f"formal edge references declaration outside indexed union: {edge}")
        if edge["from"] == edge["to"]:
            raise SystemExit(f"self formal edge forbidden: {edge}")

    validate_pinned_source_edges(manifest, nodes)

    if manifest["scope"]["transitive_formal_dependency_closure_complete"]:
        raise SystemExit("slice 1 cannot claim complete transitive formal closure")
    if manifest["scope"]["paper_lemma_proposition_mapping_complete"]:
        raise SystemExit("slice 1 cannot claim complete paper lemma/proposition mapping")
    if manifest["scope"]["local_proof_reconstruction_complete"] or manifest["scope"]["proof_validity_assessed"]:
        raise SystemExit("formal indexing cannot promote to proof reconstruction or proof validity")
    if manifest["scope"]["lean_build_replayed_by_qsol"] or manifest["scope"]["comparator_replayed_by_qsol"]:
        raise SystemExit("formal indexing cannot claim replay")
    if manifest["scope"]["gate_2_pass_condition_met"]:
        raise SystemExit("formal declaration slice 1 cannot close Gate 2")

    if correspondence["gate_status"] != "statement_correspondence_confirmed":
        raise SystemExit("Gate 1 correspondence prerequisite drift")
    if correspondence["formal_artifact_pin"]["commit"] != LEAN_COMMIT:
        raise SystemExit("Gate 1 Lean pin diverges from formal index")
    external_lean = external["artifact_pins"]["OPENAI_NS_LEAN_2026"]
    if external_lean["repository"] != LEAN_REPOSITORY or external_lean["commit"] != LEAN_COMMIT:
        raise SystemExit("external-claim Lean pin diverges from formal index")
    for formulation_id in ("C", "D"):
        if claim(external, formulation_id)["qsol_status"] != "external_claim_pending_independent_verification":
            raise SystemExit(f"external {formulation_id} status promoted during Gate 2 indexing")
    for formulation_id in ("A", "B"):
        if claim(external, formulation_id)["qsol_status"] != "not_resolved":
            raise SystemExit(f"unforced formulation {formulation_id} was silently resolved")


def run_negative_probes(manifest: dict, nodes: list[dict], dag: dict, external: dict,
                        correspondence: dict, manifest_validator: Draft202012Validator,
                        node_validator: Draft202012Validator) -> None:
    mutated = copy.deepcopy(manifest)
    mutated["as_of"] = "not-a-date"
    reject_schema(manifest_validator, mutated, "malformed formal-index date")

    for field in (
        "transitive_formal_dependency_closure_complete",
        "paper_lemma_proposition_mapping_complete",
        "local_proof_reconstruction_complete",
        "proof_validity_assessed",
        "lean_build_replayed_by_qsol",
        "comparator_replayed_by_qsol",
        "gate_2_pass_condition_met",
    ):
        mutated = copy.deepcopy(manifest)
        mutated["scope"][field] = True
        reject_schema(manifest_validator, mutated, f"authority/completion escalation: {field}=true")

    mutated = copy.deepcopy(manifest)
    mutated["source_pin"]["module_pins"][0]["blob_sha"] = "0" * 40
    reject_cross(mutated, nodes, dag, external, correspondence, "module blob pin rewritten")

    mutated_node = copy.deepcopy(nodes[0])
    mutated_node["declarations"][0]["audit_status"] = "verified"
    reject_schema(node_validator, mutated_node, "formal declaration promoted to verified")

    mutated_nodes = copy.deepcopy(nodes)
    mutated_nodes[0]["declarations"][0]["fully_qualified_name"] = "NavierStokes.Fake.proved_everything"
    reject_cross(manifest, mutated_nodes, dag, external, correspondence, "declaration name rewritten")

    mutated = copy.deepcopy(manifest)
    mutated["scope"]["parent_nodes_indexed_in_slice"].pop()
    reject_schema(manifest_validator, mutated, "indexed parent silently removed")

    mutated = copy.deepcopy(manifest)
    mutated["formal_edges"].append(copy.deepcopy(mutated["formal_edges"][0]))
    reject_schema(manifest_validator, mutated, "duplicate formal edge admitted")

    try:
        validate_manifest_node_binding(manifest["node_files"][0], nodes[1])
    except SystemExit:
        pass
    else:
        raise SystemExit("formal-index regression: swapped node file accepted for manifest parent/path binding")

    mutated_dag = copy.deepcopy(dag)
    mutated_dag["source_pins"]["lean"]["commit"] = "0" * 40
    reject_cross(manifest, nodes, mutated_dag, external, correspondence, "DAG Lean commit repinned")

    mutated_dag = copy.deepcopy(dag)
    shared_path = sorted(EXPECTED_DAG_SHARED_MODULE_PATHS)[0]
    for item in mutated_dag["source_pins"]["lean"]["audited_files"]:
        if item["path"] == shared_path:
            item["blob_sha"] = "0" * 40
            break
    reject_cross(manifest, nodes, mutated_dag, external, correspondence, "DAG shared module blob repinned")

    mutated = copy.deepcopy(manifest)
    mutated["formal_edges"][0]["to"] = "NavierStokes.CandidateConsequences.futureJet_decay"
    try:
        validate_pinned_source_edges(mutated, nodes)
    except SystemExit:
        pass
    else:
        raise SystemExit("formal-index regression: unwitnessed direct-body edge accepted by pinned-source audit")


def main() -> None:
    manifest = load_json(INDEX / "manifest.json")
    manifest_schema = load_json(SCHEMAS / "openai_2026_formal_index_manifest.schema.json")
    node_schema = load_json(SCHEMAS / "openai_2026_formal_index_node.schema.json")
    dag = load_json(RESEARCH / "openai_2026_dependency_dag.json")
    external = load_json(RESEARCH / "external_claim_registry.json")
    correspondence = load_json(RESEARCH / "openai_2026_correspondence.json")

    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator.check_schema(node_schema)
    manifest_validator = Draft202012Validator(manifest_schema, format_checker=FORMAT_CHECKER)
    node_validator = Draft202012Validator(node_schema, format_checker=FORMAT_CHECKER)
    manifest_validator.validate(manifest)

    nodes: list[dict] = []
    for item in manifest["node_files"]:
        path = ROOT / item["path"]
        node_data = load_json(path)
        node_validator.validate(node_data)
        validate_manifest_node_binding(item, node_data)
        nodes.append(node_data)

    validate_cross(manifest, nodes, dag, external, correspondence)
    run_negative_probes(manifest, nodes, dag, external, correspondence, manifest_validator, node_validator)

    print(
        "OpenAI 2026 formal declaration index: PASS "
        f"(slice=1, parents={manifest['disposition']['programme_obligation_parent_nodes_indexed']}/12, "
        f"unique_declarations={manifest['disposition']['unique_formal_declarations_indexed']}, "
        f"direct_edges={manifest['disposition']['selected_direct_formal_edges_indexed']}, "
        f"source_blobs={len(manifest['source_pin']['module_pins'])}, "
        f"Gate2={manifest['disposition']['gate_2_status']}, Lean={LEAN_COMMIT[:12]})"
    )


if __name__ == "__main__":
    main()
