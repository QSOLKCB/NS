<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Experiment Contract

An experiment may be promoted beyond exploratory status only if its manifest records the following fields.

## Identity

- `experiment_id`
- `source_commit`
- `created_at_utc`
- `operator_or_agent`
- `purpose`
- `hypothesis`
- `claim_level`

## PDE definition

- spatial domain;
- boundary conditions;
- initial velocity field definition;
- proof or diagnostic of divergence-free admissibility when required;
- viscosity;
- forcing;
- nondimensionalization/scaling convention;
- solution quantity being measured.

## Numerical method

- solver and version;
- spatial discretization;
- time integrator;
- time-step/adaptivity policy;
- resolution;
- precision/data type;
- tolerances;
- dealiasing/filtering/regularization;
- interpolation/remeshing;
- random seed or explicit `null`.

## Runtime identity

- operating system/container identity;
- compiler/interpreter;
- dependency lock or exact versions;
- hardware features that may affect numerics;
- thread/process count when relevant.

## Evidence

- input hashes;
- output hashes;
- diagnostics requested before execution;
- termination reason;
- warnings/errors;
- wall-clock-independent step counts where useful;
- raw outputs or a content-addressed pointer to them.

## Singularity-oriented runs

A blow-up-like signature must not be promoted on one resolution alone. Record convergence/resolution behavior, precision sensitivity, conservation/balance residuals, timestep sensitivity and a competing numerical-failure explanation.

## Mutation rule

An executed manifest is immutable. Changed parameters create a new experiment identity; they do not overwrite the prior run.
