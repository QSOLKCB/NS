{
  "schema_version": "1.0.0",
  "document_type": "qsol_ns_agent_contract",
  "serialization": "json",
  "repository": "QSOLKCB/NS",
  "default_branch": "main",
  "human_operator": {
    "role": "final_authority",
    "required_for": [
      "public_solution_claim",
      "license_scope_change",
      "history_rewrite",
      "deletion_of_evidentiary_artifacts",
      "release_or_archive_publication"
    ]
  },
  "agent_boot_sequence": [
    "parse_AGENTS_md_as_JSON",
    "validate_against_AGENTS_schema_json",
    "read_README_md",
    "read_docs_PROBLEM_STATEMENT_md",
    "read_docs_CLAIM_LEVELS_md",
    "read_docs_EXPERIMENT_CONTRACT_md",
    "read_docs_REPRODUCIBILITY_md",
    "read_docs_PUBLICATION_GATE_md",
    "inspect_current_branch_and_head_commit",
    "inspect_worktree_or_target_diff_before_mutation"
  ],
  "branch_policy": {
    "direct_main_write": false,
    "agent_branch_prefix": "agent/",
    "default_delivery": "draft_pull_request",
    "force_push": false,
    "history_rewrite": false
  },
  "research_invariants": [
    "numerical_blowup_signature_is_not_proof_of_blowup",
    "absence_of_observed_blowup_is_not_proof_of_global_regularity",
    "formal_verification_is_not_physical_truth",
    "candidate_lemma_is_not_verified_theorem",
    "private_experiment_is_not_public_claim",
    "official_clay_problem_is_not_redefined_by_repository_text",
    "negative_and_null_results_are_preserved",
    "solver_failure_is_not_mathematical_singularity",
    "floating_point_overflow_is_not_mathematical_singularity",
    "resolution_instability_is_not_mathematical_singularity",
    "claim_status_must_never_exceed_evidence_status"
  ],
  "claim_levels": [
    "exploratory",
    "reproduced_numerical",
    "candidate_lemma",
    "proved_lemma",
    "externally_checked_theorem",
    "publication_candidate",
    "public_solution_claim"
  ],
  "claim_promotion": {
    "monotonic": true,
    "automatic_promotion_allowed": false,
    "public_solution_claim_requires_human_operator": true,
    "public_solution_claim_requires_external_mathematical_review": true,
    "numerics_can_promote_to": "reproduced_numerical",
    "formal_checker_can_promote_to": "proved_lemma",
    "formal_checker_scope": "encoded_statement_only"
  },
  "experiment_requirements": {
    "required_fields": [
      "experiment_id",
      "purpose",
      "hypothesis",
      "initial_data_definition",
      "domain",
      "boundary_conditions",
      "viscosity",
      "forcing",
      "solver",
      "solver_version",
      "discretization",
      "precision",
      "tolerances",
      "time_step_policy",
      "resolution",
      "random_seed_or_null",
      "runtime_identity",
      "source_commit",
      "input_hashes",
      "output_hashes",
      "diagnostics",
      "termination_reason",
      "claim_level"
    ],
    "raw_outputs_preserved": true,
    "failed_runs_preserved_when_informative": true,
    "silent_parameter_changes_forbidden": true
  },
  "proof_requirements": {
    "explicit_hypotheses": true,
    "explicit_domain": true,
    "explicit_regularization_or_approximation": true,
    "external_theorem_dependencies_cited": true,
    "proof_gap_markers_forbidden_in_verified_status": [
      "sorry",
      "admit",
      "assume_without_source",
      "numerically_obvious",
      "physically_obvious"
    ]
  },
  "licensing": {
    "software_spdx": "Apache-2.0",
    "machine_policy_spdx": "Apache-2.0",
    "research_prose_spdx": "CC-BY-4.0",
    "license_scope_authority": "LICENSES.md",
    "license_mutation_requires_human_operator": true
  },
  "file_policy": {
    "immutable_without_explicit_reason": [
      "LICENSE",
      "LICENSES.md",
      "NOTICE",
      "CITATION.cff",
      "AGENTS.md",
      "AGENTS.schema.json"
    ],
    "generated_artifacts_must_record_generator": true,
    "binary_results_require_manifest_entry": true,
    "secrets_forbidden": true
  },
  "language_policy": {
    "solution_language_forbidden_unless_status_is_public_solution_claim": [
      "solved",
      "solution established",
      "millennium problem resolved",
      "proof complete"
    ],
    "required_uncertainty_label_for_exploratory_results": true
  },
  "review_policy": {
    "adversarial_review": true,
    "check_prior_art_before_novelty_claim": true,
    "check_scaling_and_units": true,
    "check_boundary_and_initial_conditions": true,
    "check_discrete_continuum_gap": true,
    "check_roundoff_and_resolution_sensitivity": true,
    "check_circular_reasoning": true,
    "check_hidden_regularization": true
  },
  "completion_contract": {
    "summarize_changed_files": true,
    "report_validation_performed": true,
    "report_unresolved_risks": true,
    "report_exact_head_commit": true,
    "never_claim_background_work": true
  }
}
