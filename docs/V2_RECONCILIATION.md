# V2 reconciliation and repair priorities

Reviewed on 2026-09-17 using verified local recovery files and the original Cloud Build source archives. This is a source review, not an end-to-end cloud test. Infrastructure status observations refer to the 2026-09-15 snapshot; source-object retrieval and integrity checks were performed September 17.

## Baseline decision

Keep the GitHub baseline `390bb2a` as the starting application implementation. Local `main.py` parses successfully and matches that baseline after accounting for Windows line endings. The `main.py` in the preserved API v17 build input matches the baseline Git blob exactly. The recovered Cloud Shell outer `main.py` fails parsing; its useful additions must be extracted selectively. The nested checkout is a historical reference and its commit matches the missing submodule pointer. All of these source copies are now preserved locally with verified hashes.

Preserve the existing API behavior until a separate V2 skeleton boots. Preserve archived assets, backup sources, and history independently of which code is selected for V2.

## Recovered version comparison

- Of the 22 outer Cloud Shell working-tree files, **17 match the GitHub baseline exactly**; five differ: `main.py`, `deploy.sh`, `requirements.txt`, `Dockerfile`, and `cloudrun-service.yaml`.
- Outer commit `88232a9` branches from common ancestor `67c0355`; it changes three files and includes pasted patch text. It is not a clean successor to the current GitHub baseline. Preserve its history; do not merge it wholesale.
- The API v17 build has 15 regular files. Its main application, Dockerfile, and requirements match the GitHub baseline; its frontend and some operational/support files differ. The baseline already contains the later dashboard changes.
- The inference build's original Dockerfile is clean, unlike the 1,171-byte Cloud Shell working copy. It starts an OpenAI-compatible vLLM server with a historical Gemma 2 2B default and a mutable `latest` base image. A reproducible replacement needs a tested pinned image/model combination and an adapter for its response contract. The current application uses a Vertex-specific response contract.

### Useful feature drafts retained for V2

The damaged outer `main.py` retains substantial design work. The references below are to its preserved Cloud Shell file, not the active `main.py`.

| Candidate | Source evidence | What must be completed |
| --- | --- | --- |
| Corridor planning | `CorridorEndpoint`, `TrafficInputs`, `CorridorWorkZoneRequest`; `fetch_corridor_route_context`; corridor package/image routes | Validate route and traffic inputs, distinguish live from supplied data, and integrate with the approved package workflow |
| Source-based guidance | `load_knowledge_base`, source filtering, and prompt context builders | The referenced `knowledge_base/work_zone_sources.json` is absent from the recovered working trees. Recover or curate authoritative sources with provenance, revisions, and tested retrieval |
| Offline draft preparation | `build_offline_corridor_package` provides a deterministic draft template | Design actual client-side offline storage and later sync. A server endpoint called offline is not evidence that the user's device can operate without connectivity |
| Communication handoffs | `queue_offline_action` records provider status and a payload in `/tmp/gemma-offline-actions` | Replace temporary local files with durable, organization-scoped queueing and explicit reviewed send/sync actions. No sending implementation is present in this draft |
| Capability/readiness reporting | `get_capability_matrix`, `get_production_readiness`, `get_ui_config` and related routes | Replace configuration-presence claims with meaningful service checks and clear unavailable states |

These are candidates for product prioritization, not claims of working recovered features or additions to the initial release scope.

## Prioritized findings

| Priority | Evidence in current source | Repair direction and acceptance check |
| --- | --- | --- |
| Release blocker | `call_model()` posts to one Vertex URL and expects `predictions[0]`. Deployment files hardcode a legacy endpoint; September 15 regional inventory returned none. | Introduce an inference interface and explicit backend configuration. Verify a valid response, timeout, unavailable backend, malformed response, and empty response with a deterministic test backend before connecting a live model. |
| Release blocker | `PACKAGE_BUCKET` defaults to `gemma_think`. September 15 inventory showed `gemma_think_v2`, not the configured bucket in this project. | Require explicit storage configuration for cloud execution. Validate the chosen bucket, region, access, and signing identity in staging before migrating data or switching traffic. |
| Release blocker for a multi-organization product | `verified_user()` checks an identity header's email-domain suffix; package list/read functions use shared `packages/` paths without an organization or ownership check. Cloud IAM/IAP is part of the existing trust boundary. | Specify trusted identity verification and WZOS organization membership, then authorize every package read/write. Test that one organization cannot retrieve another's packages. Header acceptance is not, by itself, evidence of a publicly exploitable bypass; actual ingress and IAM matter. |
| High | `/compliance-package-json` requests JSON in its prompt but returns `call_model()` output without parsing or schema validation. V13 stores the returned text and uses it for its PDF. | Define a typed output contract, validate it, and distinguish invalid generation from a successful package. Test malformed JSON, missing fields, and invalid field values. |
| High | V13 calls three text-generation routes, Imagen, Street View, PDF generation, uploads, and URL signing in one synchronous request. A fresh UUID is created on each call. | Introduce a durable job state and idempotency key for costly workflows; persist completed stages. Test a late-stage failure and retry without regenerating already completed paid assets. Measure stage latency and cost before optimizing or combining prompts. |
| High | Signed links expire after 120 minutes in V13 and are persisted in `manifest-with-assets.json`. `get_package()` returns that stored JSON without refreshing links. | Persist stable object identifiers and issue short-lived links on authorized retrieval. Test retrieval after the original links expire. |
| High | V13 uploads `manifest-with-assets.json` before appending that manifest's own URI and signed URL to the response dictionary. | Define a stable stored manifest schema and a separate response containing generated links. Test that persisted records and retrieval responses satisfy their respective contracts. |
| High | Generated PNG/PDF/temp JSON files use `/tmp` and no cleanup is present. Multiple remote stages can fail after earlier work succeeds. | Use scoped temporary directories and explicit success/failure cleanup, while persisting durable job progress. Validate cleanup after both successful completion and injected failures. |
| High | `/deliver-package` records `provider=gmail_api`, `mode=draft_first`, and `status=preview_ready`; it makes no Gmail API call. | Model delivery states honestly: prepared, reviewed, queued, sent, failed. Keep actual sending behind an explicit reviewed delivery action and implement provider integration separately. |
| Medium | `list_package_manifests()` scans matching objects, downloads manifests, sorts all results, then slices; malformed entries are silently skipped. `/packages` reports `min(limit,25)` rather than the returned list length and accepts negative limits. | Add bounded, validated pagination and an index/query strategy. Return actual counts and observable errors. Verify empty, small, and multi-page collections. |
| Medium | `ChatRequest` has unconstrained `max_tokens`, `temperature`, and message length; coordinates and other numeric inputs have no bounds. | Add documented request limits and geographic/numeric validation appropriate to each workflow. Test boundary values and incomplete locations. |
| Medium | `/health` always returns `status=ok`; errors can relay provider response bodies; new storage clients and refreshed credentials are repeatedly created within a workflow. | Separate process liveness from configuration/dependency readiness. Return stable user-facing errors with correlation IDs. Measure client/credential overhead and reuse supported clients appropriately. |
| Product/design | Prompts, PDFs, and emails retain Superior Consultation branding; the backend monolith and frontend serve several historical route generations. | Centralize approved branding and version the V2 contract. Keep backward compatibility decisions explicit. Map initial WZOS workflows before changing the user interface. |

## What can be reused

### Step 2 extension: WZOS requirements and dependencies

The September 17 [capability map](WZOS_GEMMA_REQUIREMENTS.md) adds explicit acceptance checks for Ray's requirements and distinguishes the broader Atlas role from the first package workflow. Additional source inspection confirms:

- `draw_workzone_overlay()` uses hardcoded pixel locations for every scene. Reuse its drawing concepts, but replace placement with editable, image-relative annotations and retain the original photograph. It is not a surveyed layout engine.
- `build_package_pdf()` writes text lines with ReportLab; it does not embed the actual imagery, annotated figures, or versioned form templates. Reuse the rendering dependency and rebuild document composition around structured package data.
- Free-text speed/volume inputs are not verified traffic measurements. Replace their V2 contracts with typed, dated, sourced observations; retain unknown states.
- The recovered state-based source draft cannot provide jurisdiction coverage without the missing source catalog, reviewed official documents, and locality/road-authority resolution.

The eight pinned direct dependencies in `requirements.txt` cover FastAPI/Uvicorn, HTTP requests, Google authentication/Vertex/storage, ReportLab, and Pillow. They support candidate components, but do not establish a WZOS integration, jurisdiction retrieval, durable job queue, or actual email delivery. Google auth alone does not implement an email provider. No dependency upgrades, vulnerability-clearance claims, successful installation claims, or provider compatibility claims are made by this static review. Build the separate V2 environment and check its chosen dependency set during the skeleton milestone; preserve V1 pins for reproducibility.

- Existing request shapes and prompt concepts as input to a cleaner, versioned contract.
- PDF, Street View overlay, image-generation, and GCS helper logic after extracting and validating each component.
- Static dashboard assets as a reference for user flows; they do not determine the final WZOS integration design.
- IAP deployment experience and configuration as evidence for the existing trust boundary.
- Preserved PDFs and PNGs as historical examples for output comparison, not as proof of current correctness.

## Migration sequence

1. Recovery and initial source comparison are complete for the identified source sets; retain the verified archives while selecting individual reusable components.
2. Agree on an initial workflow and measurable quality, latency, and cost targets.
3. Add a separate API skeleton, validated settings, and inference/storage interfaces with local implementations.
4. Migrate one typed generation workflow and verify its failure paths, access checks, and review state.
5. Integrate real providers in staging, benchmark configurations, and determine operating cost from measurements.
6. Review rollout readiness and production timing with Ray.

## Limits of this review

No production generation requests, paid model calls, email sends, deployments, or cloud configuration mutations were performed. Cloud Storage source archives were read and copied for recovery. No model choice, provider price estimate, or throughput claim is established here. Historical working-source damage alone does not identify the deployed inference image's startup failure; runtime diagnosis remains a separate task.
