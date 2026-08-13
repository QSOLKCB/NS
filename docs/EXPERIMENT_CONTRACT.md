<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Experiment Contract

An experiment may be promoted beyond `exploratory` only if its manifest records every field required by the machine contract.

## Canonical field authority

`AGENTS.md` → `experiment_requirements.required_fields` is the canonical machine-readable definition for general promoted-experiment manifest fields.

This document mirrors those exact field names for humans. If this document and `AGENTS.md` ever disagree, the mismatch is a governance defect that must be fixed before promotion; agents must not invent aliases or silently choose one vocabulary.

## Identity

- `experiment_id`
- `source_commit`
- `created_at_utc`
- `operator_or_agent`
- `purpose`
- `hypothesis`
- `claim_level`

## PDE definition

- `spatial_domain`
- `boundary_conditions`
- `initial_velocity_field_definition`
- `divergence_free_admissibility`
- `viscosity`
- `forcing`
- `scaling_convention`
- `measured_solution_quantity`

## Numerical method

- `solver`
- `solver_version`
- `spatial_discretization`
- `time_integrator`
- `time_step_policy`
- `resolution`
- `precision`
- `tolerances`
- `filtering_regularization`
- `interpolation_remeshing`
- `random_seed_or_null`

## Runtime identity

- `operating_system_or_container_identity`
- `compiler_or_interpreter`
- `dependency_lock_or_exact_versions`
- `numerics_relevant_hardware_features`
- `thread_or_process_count`

## Evidence

- `input_hashes`
- `output_hashes`
- `diagnostics`
- `termination_reason`
- `warnings_or_errors`
- `wall_clock_independent_step_counts`
- `raw_outputs_or_content_addressed_pointer`

Fields that are inapplicable must be present with an explicit `null`, empty collection, or other schema-valid no-value representation rather than silently omitted.

## Singularity-oriented runs

In addition to the general fields above, any run used to support a blow-up or singularity-oriented claim must record every field in `AGENTS.md` → `experiment_requirements.singularity_run_required_fields`:

- `convergence_resolution_behavior`
- `precision_sensitivity`
- `conservation_balance_residuals`
- `timestep_sensitivity`
- `competing_numerical_failure_explanation`

A blow-up-like signature must not be promoted on one resolution alone.

## Mutation rule

An executed manifest is immutable. Changed parameters create a new experiment identity; they do not overwrite the prior run.
