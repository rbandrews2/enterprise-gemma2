# Enterprise Gemma V2 implementation plan

Owner: Molecular Project Development LLC (formerly Superior Consultation LLC).
Destination product: Work Zone OS (WZOS).
Updated: 2026-09-17.

## Direction

Build a capable, reliable WZOS service with measurable improvements in output quality, latency, cost, and operational stability. Preserve useful prior work; deleting old material is optional, not a project requirement. Model size or the Gemma name alone is not a quality target.

No production date is set. Discuss timing with Ray after the recovery and validation work establishes readiness. Do not run the legacy deployment scripts or push a deployment-triggering branch as part of recovery.

## Numbered tasks and completion criteria

1. **Preserve and inventory surviving work.** Capture the Cloud Shell working trees (including uncommitted source), independent Git history bundles, and the local V1/V2 Git history. Verify archive checksums after transfer. Keep originals intact and recovery archives outside version control. Record sources, commit IDs, exclusions, and unresolved recovery gaps. Status: complete for the identified surviving source sets, metadata snapshot, and API/inference build inputs; long-term backup retention remains an operational follow-up.
2. **Reconcile versions and dependencies against WZOS responsibilities.** Compare Cloud Shell code, GitHub baseline, current local V2, and deployed image configuration. Classify code as reusable, incomplete, or obsolete without overwriting the working V2 tree. Record dependency failures, deployment triggers, storage configuration, and the missing submodule relationship. Map the published WZOS capabilities and Ray's additions to surviving code and acceptance checks in [Gemma requirements](WZOS_GEMMA_REQUIREMENTS.md). Completion: evidence-backed recovery map and prioritized defect list; runtime and provider validation are tracked separately.
3. **Define the first WZOS workflows.** Agree on the first customer-facing outcomes, required inputs, review steps, and WZOS identity/organization boundaries. Build representative evaluation cases and agree on thresholds for quality, latency, and cost per successful workflow. Completion: bounded initial release scope and measurable acceptance criteria.
4. **Design service boundaries.** Separate API contracts, inference, document/visual generation, storage, and delivery. Use validated configuration and provider interfaces; distinguish user/organization authorization from cloud service authentication. Decide which long-running operations require queued jobs and idempotency. Completion: architecture decision record and migration sequence.
5. **Boot a local V2 skeleton.** Implement health/readiness checks and an inference interface with a deterministic local test implementation. Retain V1 unchanged until the skeleton boots and its core contract checks pass. Completion: repeatable setup and meaningful automated checks without paid cloud calls.
6. **Implement one complete workflow.** Migrate request validation, generation, artifact storage, review state, and delivery preparation. Add bounded retries, timeouts, error reporting, and duplicate-request protection where needed. Actual email delivery is a separate explicit integration; V1 preview metadata is not evidence of sending. Completion: end-to-end workflow and failure-path validation.
7. **Measure model and hosting choices.** Compare suitable Gemma configurations and permitted alternatives on the evaluation cases. Measure cold/warm latency, peak memory, output reliability, and cost per successful job. Include idle GPU cost, model loading, storage, network, and image generation. Pin a tested image/model combination and set spending/scale limits. Completion: documented benchmark and cost decision; no provider or hardware commitment solely from historical configuration.
8. **Validate integration and rollout.** Test WZOS integration, organization isolation, signed asset access, review gates, logging, alerting, backup/restore, and rollback. Use a separate staging deployment and limited pilot before production. Completion: readiness review and an agreed production date with Ray.

## Working principles

Job-specific reference increment: `/v2/planning/references` now connects intake context to cited source candidates, with latest-revision checks and explicit missing/stale/superseded-source handling. See [planning references](PLANNING_REFERENCES.md). This is keyword-based discovery; project applicability, required forms, and field placements remain unresolved.

Customer-intake increment: address/coordinate validation, requested outputs, explicit unknown site conditions, proactive JSA recommendation, and rule-based context prompts are implemented at `/v2/intake/assess`. See [customer workflow](CUSTOMER_WORKFLOW.md). Applicable-form selection, traffic evidence, image annotation, and measured placement remain the next workflow increments; workforce modules remain part of the unified WZOS destination.

Source backend milestone: the [operator guide](../knowledge/README.md) and [coverage report](SOURCE_BACKEND_STATUS.md) document the implemented catalog, revision-preserving downloads, page/heading extraction, SQLite search, and read-only API. Six official sources were downloaded; OSHA's fact-sheet request returned 403 and remains unavailable. Source review checks do not constitute project applicability approval. Next: expand missing standards/forms and define project-specific evidence selection before connecting generation.

Local skeleton milestone: the [architecture decision](V2_ARCHITECTURE.md) and [startup instructions](../services/v2/README.md) now accompany a separate API, validated Virginia preview contract, configuration checks, and deterministic inference boundary. Six automated checks pass; an actual loopback HTTP startup and dependency consistency check passed. V1 is unchanged. Task 3's latency/cost thresholds and representative project selection remain open; task 4's boundaries are documented; task 5's local boot is complete. Next implementation work is evidence/source contracts and reviewed Virginia source ingestion, followed by one complete package workflow. No production readiness is implied.

Progress: task 1 has verified local and Cloud Shell source archives/history plus the API v17 and inference v3 build inputs. Task 2 now includes [source reconciliation and repair priorities](V2_RECONCILIATION.md), the [WZOS capability and acceptance map](WZOS_GEMMA_REQUIREMENTS.md), and an initial [official-source register](../knowledge/SOURCE_REGISTER.md). Runtime diagnosis, dependency installation checks, source ingestion, and end-to-end cloud validation remain pending. Next: formalize the proposed reviewed work-zone package workflow and design the locally testable service skeleton.

- Preserve first; compare before replacing code.
- Keep source recovery separate from cloud service changes.
- Evaluate output quality on real workflows rather than marketing claims.
- Prefer small, independently verifiable migrations over a full monolith rewrite.
- Review generated planning material before customer or field use; make review state part of the workflow.
- Treat container readiness, successful builds, and application correctness as separate checks.
