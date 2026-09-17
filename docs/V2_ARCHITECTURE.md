# V2 architecture and local milestone

## Decision

Use one modular Python service initially, with replaceable provider interfaces. Avoid separately deployed microservices until load or operational needs justify them. Keep V1 untouched. The first workflow is a Virginia work-zone package assembled from verified evidence, reviewed, and explicitly authorized for delivery.

## Boundaries

- API: validate requests and, before cloud use, verify WZOS identity and organization/job permissions. Never trust a caller-supplied organization ID as authorization.
- Inference: structured input/output behind an adapter. The implemented local adapter is deterministic and generates no guidance. Live model adapters need timeouts, bounded output, validated responses, and failure-path tests.
- Knowledge: the local source backend now ingests catalog-approved documents and exposes agency/source-filtered reference search independently of generation. Source review states and editions are visible; project activity/effective-date applicability selection remains unimplemented. See `knowledge/README.md` for operation and review limits.
- Imagery/documents: retain original actual imagery, store editable annotations separately, and render versioned PDFs. Calculations and placement validation must be deterministic where appropriate.
- Storage/jobs: durable organization-scoped package revisions and stage results, indexed listing, stable object references, authorized temporary links, and idempotency. No storage is implemented in this milestone; preview data is not saved.
- Review/delivery: bind approval to the package revision and recipients. Use a durable outbox and provider reconciliation for uncertain send outcomes. No email endpoint is enabled.

## Implemented contract

`POST /v2/drafts/preview` accepts project name, address, explicit VA state, locality, road authority, and work description. It validates shape and limits only; it does not verify the supplied facts. The response is a local preview with outstanding capabilities and `approved_for_field_use=false`. Full dates, source records, traffic evidence, imagery and review contracts belong to the next workflow increment.

`GET /health/live` checks the running process. `GET /health/ready` reports readiness for local preview and explicitly reports that production and cloud dependencies are unverified.

The app rejects nonlocal configuration. Bind only to loopback with proxy-header handling disabled; this local safeguard is not a substitute for cloud authentication. No CORS policy or external access is enabled for WZOS yet. Do not place this scaffold behind a reverse proxy or deploy it.

## Acceptance and remaining decisions

This milestone requires a real local server startup, successful preview, rejected invalid inputs, sanitized provider failures, and rejection of malformed provider output. These checks use no paid services. Initial development uses Python 3.12 on Windows; the preserved V1 container uses 3.11. Container/runtime parity, dependency security review, live identity, model benchmarking, and source coverage remain required before staging.

Proposed release gates: every factual safety requirement has applicable evidence or a visible coverage gap; no unauthorized cross-organization access; no unreviewed field approval; no duplicate delivery on ambiguous retries. Latency and cost targets remain pending representative project measurements and business review. Do not present them as agreed thresholds.
