<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Roadmap

## Phase 0 — Governance and target lock — COMPLETE

- [x] freeze canonical problem authority;
- [x] establish claim levels;
- [x] establish experiment/reproducibility contracts;
- [x] establish machine-readable agent rules;
- [x] establish licensing and citation metadata.

## Phase 1 — Known-boundary reconstruction — IN PROGRESS

Initial PR #2 foundation:

- [x] encode the exact official A-D Clay target and errata;
- [x] establish primary/official source authority rules;
- [x] create machine-readable theorem and proof-barrier registries;
- [x] define baseline analytic identities for Phase 2 diagnostics;
- [x] add schemas, cross-registry validation and hostile mutation probes;
- [x] make AI agents load the boundary map before research work;
- [ ] continue expanding the theorem landscape with primary-source verification;
- [ ] map geometric/vorticity depletion criteria in detail;
- [ ] map concentration/compactness and refined blow-up exclusions;
- [ ] map rigorous/computer-assisted PDE verification methods;
- [ ] maintain a queue of unresolved source checks and errata.

Phase 1 remains iterative. The initial registry is a conservative spine, not an exhaustive literature claim.

## Phase 2 — Deterministic PDE laboratory — IN PROGRESS

PR #3 reference-lab foundation:

- [x] implement periodic pseudo-spectral reference solver and Taylor-Green baseline;
- [x] add strict 2/3 de-aliasing and spectral divergence-free projection;
- [x] use fixed-step RK4 with explicit solver/version identity;
- [x] bind all six baseline identities to executable diagnostics;
- [x] emit exact experiment manifests/content hashes and deterministic raw output;
- [x] add replay, timestep and resolution sensitivity helpers;
- [x] preserve numerical failures and keep singularity-oriented promotion disabled.

PR #4 precision-referee foundation:

- [x] add independent arbitrary-precision arithmetic for the `N=8` Taylor-Green reference family;
- [x] construct referee Fourier coefficients analytically and evaluate direct modal convolution;
- [x] add 50-to-80-decimal-digit precision ladder;
- [x] compare retained coefficients, kinetic energy and enstrophy with the NumPy/FFT path;
- [x] preserve failed float64 executions while continuing the referee path when possible;
- [x] emit provenance-complete referee evidence bundles;
- [x] machine-lock that the referee is not an independent spatial discretization or proof engine;
- [ ] scale precision checking beyond the low-resolution reference family;
- [ ] add alternate initial-data families with exact admissibility records;
- [ ] add a genuinely different numerical method for cross-method comparison;
- [ ] add spectral-transfer and scale-local diagnostics;
- [ ] add longer-run checkpoint/restart with content-addressed state identity.

## Phase 2.5 — Crucible Core and ML-search architecture — IN PROGRESS

PR #5 v0.1 foundation:

- [x] extract domain-neutral candidate/evidence/constraint/failure objects;
- [x] make competing hypothesis sets first-class and unresolved by default;
- [x] preserve candidate parentage and generation method;
- [x] add training/development/holdout evidence stages;
- [x] require candidate freeze before holdout access;
- [x] add append-only failure records with reusable lessons;
- [x] expose a deterministic survivor frontier without a universal confidence score;
- [x] forbid Crucible Core from defining domain truth, promoting claims or selecting a winner;
- [x] add NS domain adapter mapping regularity to Clay A/B and breakdown to C/D;
- [x] bind every registered NS proof barrier into Crucible screening;
- [x] retain existing numerical evidence ceilings and Clay correspondence requirements;
- [x] harden claim downgrades, reciprocal hypothesis membership, per-candidate evidence provenance and adapter-owned constraint severities;
- [x] add agent boot requirements, hostile-mutation validation and Python 3.11/3.13 CI.

PR #6 Analogy Firewall foundation:

- [x] add a domain-neutral cross-domain mapping registry;
- [x] classify mappings as exact/operator/structural/heuristic/visual/non-correspondence;
- [x] permit only the first four classes to seed positive exploratory candidates;
- [x] make visual resemblance and explicit non-correspondence negative-control-only;
- [x] forbid analogy records from becoming target-domain evidence;
- [x] forbid analogy-driven claim promotion, proof-barrier satisfaction, winner selection and domain-equivalence claims;
- [x] prevent inheritance of source-domain proof/evidence status;
- [x] require target-domain revalidation under the NS adapter and every existing proof barrier;
- [x] preserve mapping class, analogy ID, differences and forbidden inferences as transfer provenance;
- [x] add an initial fluid/stochastic/generative-model transfer registry from hashed design input;
- [x] add hostile mutation tests and Python 3.11/3.13 Analogy Firewall CI.

PR #7 Content-Addressed Crucible Ledger foundation:

- [x] add persistent SHA-256 addressed candidate/evidence/failure/analogy objects;
- [x] add immutable logical refs with rebinding forbidden;
- [x] add a canonical append-only SHA-chained event log;
- [x] require actor, exact source commit and UTC timestamp on ledger events;
- [x] add replay verification for object hashes, canonical serialization, event chain and refs;
- [x] add content-addressed snapshots of verified ledger state;
- [x] add persistent transfer tickets for analogy-derived exploratory candidates;
- [x] machine-lock that persistence/replay cannot define truth, create evidence, promote claims or select winners;
- [x] explicitly scope v0.1 to a single writer process;
- [x] add hostile tamper/rebinding/authority tests and Python 3.11/3.13 ledger CI.

PR #8 Schema-Constrained ML Generator foundation:

- [x] add a provider-neutral `GeneratorBackend` protocol and deterministic CI fixture backend;
- [x] add canonical SHA-256 identified generator context packets bound to domain, tracks, registries, ledger head and source commit;
- [x] define strict candidate-proposal JSON with no model-controlled claim/evidence/proof/confidence fields;
- [x] reject malformed JSON, non-finite JSON, unknown tracks, parents, theorem dependencies and analogies;
- [x] route all analogy-bearing proposals back through the existing Analogy Firewall rather than creating a bypass;
- [x] hard-code accepted generated candidates to `exploratory`, `active`, and unfrozen;
- [x] preserve context/attempt identity in candidate provenance;
- [x] add a content-addressed SHA-chained generation-attempt journal retaining accepted and rejected attempts;
- [x] keep model-facing generation separate from explicit Crucible-ledger candidate commit;
- [x] machine-lock that generator output is not evidence, proof, claim promotion, winner selection or mathematical failure;
- [x] harden provider-failure retention, exact NS track/proof-barrier context, context-scoped references, UTC provenance, parse/schema state separation, authority-language scanning and component-safe proposal IDs;
- [x] add hostile authority-smuggling tests and Python 3.11/3.13 ML-generator CI.

PR #9 Candidate Similarity Screening foundation:

- [x] add normalized declared-mechanism SHA-256 fingerprints for deterministic exact-repeat screening;
- [x] add deterministic token-Jaccard screening for structural near-matches and prior-failure mechanism-family matches;
- [x] require same domain, hypothesis set and target track before candidate comparisons;
- [x] classify candidate origin separately from claim level using exact/bridge/source/transfer/heuristic/schematic provenance classes;
- [x] build prior-failure mechanism families only from a candidate plus one or more failure records belonging to that candidate;
- [x] bind screening candidate/failure references to content-addressed identities from a verified Crucible Ledger replay;
- [x] add a separate content-addressed SHA-chained screening journal with immutable logical refs;
- [x] make every flagged result advisory and review-required, with no automatic candidate rejection;
- [x] machine-lock that similarity does not establish mathematical equivalence, falsehood, evidence status, claim promotion or winner selection;
- [x] record thresholds as local NS screening calibration rather than universal constants;
- [x] add machine contracts, schemas, validator, behavioral regressions, documentation and Python 3.11/3.13 CI.

Next ML-search engineering:

- [x] add duplicate/prior-failure-family detection against accumulated Crucible history;
- [ ] add controlled candidate mutation/crossover provenance;
- [ ] add sealed holdout materialization with auditable release events;
- [ ] add target-domain reviewers capable of rejecting analogy families before expensive evaluation;
- [ ] add provider adapters only after the provider-neutral generator semantics remain stable;
- [ ] add multi-process/concurrent writer coordination without weakening append-only history;
- [ ] add explicit orphan-object audit/retention policy without deleting evidentiary history;
- [ ] extract the generic Crucible package into its own repository only after the NS reference implementation stabilizes.

### Planned PR sequence and cross-repository design borrowing

The following work may borrow **software architecture, falsification methods, provenance patterns, observer contracts and candidate-generation heuristics** from other QSOL repositories. Those sources do not become Navier-Stokes evidence by reuse. Mathematical or scientific ideas imported from another domain must still enter through the Analogy Firewall and satisfy the NS domain adapter, theorem boundary and proof barriers.

**PR #9 — Candidate Similarity Screening — IMPLEMENTED IN THIS PR.**

- [x] classify candidate origin separately from claim level, adapting the useful editorial separation in `QSOLKCB/synergetics2`;
- [x] distinguish normalized exact repeats, structural near-matches and prior-failure mechanism-family matches without treating similarity as mathematical equivalence;
- [x] use only locally calibrated thresholds, following the calibration discipline used in `QSOLKCB/res-rag` rather than promoting local thresholds to universal constants;
- [x] bind screening decisions to content-addressed candidate/failure identities and preserve false-positive review paths;
- [x] machine-lock `SIMILAR_CANDIDATE != MATHEMATICALLY_EQUIVALENT_CANDIDATE` and `DEAD_FAMILY_MATCH != PROOF_OF_FALSEHOOD`.

**PR #10 — Controlled Mutation & Crossover Engine.**

- [ ] borrow the role-separated cognitive-mode idea from `QSOLKCB/QSOL-NEXUS` to define explicit mutation operators rather than generic "try again" prompting;
- [ ] support transformations such as weaken assumption, repair scaling defect, replace failed estimate, reverse regularity/breakdown perspective, adversarially attack a parent, and combine two surviving parent mechanisms;
- [ ] preserve parentage, mutation operator, source context, generator receipt and resulting candidate identity in the Crucible Ledger;
- [ ] forbid mutation/crossover from inheriting parent claim level, evidence status or survival status.

**PR #11 — Sealed Holdout & Adversarial Evaluation.**

- [ ] borrow the freeze-before-observation and fail-closed admission discipline from `QSOLKCB/UFF` SPECTRAL/QEC-style workflows;
- [ ] materialize sealed holdout packets only after candidate freeze and record auditable reveal/release events;
- [ ] separate schema admission, deterministic replay, cross-method challenge, holdout evaluation and continuum-bridge obligations into distinct assurance states;
- [ ] preserve the UFF-style principle that replay/calibration/formal assurance are different from physical or mathematical truth;
- [ ] add negative controls and leakage tests for the evaluation machinery itself.

**PR #12 — Multi-Model Crucible Council.**

- [ ] borrow the NEXUS rule that models propose/participate while the runtime owns state, evidence identity and validated transitions;
- [ ] give independent model actors frozen question/context/evidence packets and role-separated review tasks such as scaling critic, theorem-boundary critic, circularity hunter, numerical skeptic, regularity advocate and breakdown advocate;
- [ ] preserve minority reports and disagreements instead of collapsing them into one synthetic answer;
- [ ] keep provider/model size/account tier/performance history from creating epistemic privilege;
- [ ] machine-lock `COUNCIL_CONSENSUS != EVIDENCE_STATUS` and require all actual evidence transitions to remain Crucible/domain-adapter operations.

**PR #13 — Crucible Atlas & Observer Bus.**

- [ ] borrow the searchable atlas/pathway presentation ideas from `QSOLKCB/synergetics2` for candidate ancestry, theorem dependencies, proof barriers, prior-failure families and surviving frontier visualization;
- [ ] borrow the strict canonical-versus-interpretive observation split from `QSOLKCB/E8_MUSIC`;
- [ ] define canonical deterministic observers for numerical fields/diagnostics with frozen transforms and receipt chains, while keeping creative visualization/sonification in a separately labelled interpretive receiver;
- [ ] fail closed rather than silently clipping, normalizing or remapping canonical observer data;
- [ ] machine-lock `OBSERVER_ARTIFACT != DOMAIN_EVIDENCE` and `INTERPRETIVE_RENDERING != PHYSICAL_MECHANISM`.

**Cross-domain research lenses after the above infrastructure stabilizes.**

- [ ] investigate Wasserstein/transport diagnostics inspired by `QSOLKCB/res-rag` for normalized energy, enstrophy or vorticity distributions across time, resolution and numerical method; treat any such construction as a diagnostic/search lens until an explicit NS mathematical bridge is established;
- [ ] admit Haken-style order-parameter/instability ideas or Fuller/Synergetics coordinate/geometric ideas only as classified candidate-generation sources through the Analogy Firewall;
- [ ] admit motifs from other speculative/formal QSOL frameworks only as provenance-labelled candidate reservoirs, never by importing their physical interpretation or evidentiary status;
- [ ] consider a later Lean 4 assurance layer, following the bounded formal-assurance discipline used in `QSOLKCB/UFF` and `QSOLKCB/E8_MUSIC`, to prove selected software/epistemic invariants without presenting formal verification as a Navier-Stokes proof.

Crucible Core is an orchestration/falsification engine, not a truth engine. The Analogy Firewall broadens candidate generation without broadening evidentiary authority. The Content-Addressed Crucible Ledger makes the resulting search history durable without increasing its claim level. The ML Generator permits bounded model proposals without granting the model a write path to research authority. Similarity screening reduces repeated search without deciding mathematical equivalence or falsehood. Cross-repository borrowing may expand search strategy and instrumentation, but it does not bypass target-domain validation. Each future domain adapter must define its own epistemic standard.

## Phase 3 — Competing mechanism search

### Regularity track

Use the Crucible frontier to search for sharpened a priori bounds, monotone/coercive quantities, geometric depletion mechanisms, continuation criteria or concentration exclusions. Every candidate must be checked against the theorem registry and proof barriers before novelty language is permitted.

### Breakdown track

Use the same machinery to search for admissible initial-data/forcing families, concentration mechanisms, scaling scenarios or rigorous reductions capable of satisfying Clay C or D. Numerical blow-up signatures remain exploratory until a continuum bridge is proved.

Future ML search should generate candidates on both tracks through the schema-constrained airlock, preserve failed families, use the persistent failure ledger and similarity screening memory to reduce repeated exploration of already-rejected mechanisms, route cross-domain ideas through the Analogy Firewall, and retain every generation/intake/screening/failure/survival decision in auditable history.

## Phase 4 — Proof extraction

Promote only precise candidate lemmas. Attempt analytic proof, symbolic checking, interval methods or proof-assistant formalization where appropriate. Preserve correspondence between any formal object and the exact mathematical statement.

## Phase 5 — Adversarial review

Try to break every promoted result with edge cases, scaling checks, hidden assumptions, known theorems, alternate discretizations, proof-barrier matching, analogy-authority audits, ledger-provenance audits, generator-authority audits, similarity-screening audits and independent reviewers.

## Phase 6 — Publication/archive

Only after the publication gate: freeze exact commit/tag, generate citation metadata, archive artifacts, and publish wording that matches the actual claim level.
