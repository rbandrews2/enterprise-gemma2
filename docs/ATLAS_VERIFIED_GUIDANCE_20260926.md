# Atlas local integration checkpoint - September 26, 2026

## Implemented

App-owned guidance now answers narrowly recognized questions about saving work orders, clock controls and own saved clock status, vehicle inspection drafts, schedule permissions, training study status, delivery limitations, navigation and saved checklist revisions. Authentication, tenant/edition boundaries and expected job revisions are checked first. Checklist answers distinguish missing, stale and matching revisions; a matching revision never implies field approval.

Responses expose `response_kind`, `guidance_topic` and `model_called`. The browser labels verified guidance separately from generated replies. Ambiguous, multi-topic and regulatory questions remain on the model path. This is not general compliance intelligence. Atlas performs no attendance changes, dispatch or external delivery.

Non-admin runtime roles now consistently report member, including account sessions. Existing synthetic fixture IDs remain unchanged. Navigation honors unsaved-change cancellation and Core/Enterprise boundaries. Unrelated module questions no longer include personal clock context.

## Validation

- Full Python suite: 168 tests, 152 passed, 16 PostgreSQL tests skipped locally.
- Five Node tests passed, including actual navigation functions and existing account-refresh checks.
- Eight verified-guide real HTTP scenarios returned 200 in 0.00-0.14 seconds, with no model call.
- Three open-ended actual inference scenarios returned 200 in 19.91-39.11 seconds. One inbox response added irrelevant payroll information; context was subsequently minimized.
- Fresh inbox inference after context minimization: 200 in 17.72 seconds. Correctly identified absent SMS/MMS/email integration, but added unsupported incomplete-data/certification claims. General model quality remains unaccepted.
- Browser verified Core member identity and correct admin-only schedule-edit guidance, with the readable verified/no-generation label. Earlier browser check confirmed stale saved-checklist revision reporting.
- Raw HTTP evidence and model logs are under ignored `.local-data/atlas-runtime`; these are not GitHub-backed.

## Private Cloud Run adapter - prepared only

The opt-in Ollama-compatible adapter requires `WZOS_ATLAS_PROVIDER=cloud_run`, `WZOS_ATLAS_CLOUD_ENABLED=1` and `WZOS_ATLAS_CLOUD_RUN_URL` set to the exact canonical HTTPS run.app service origin. Existing reviewed model allowlist still applies. Local launch/evaluation scripts force local mode and disable cloud mode.

Inside Cloud Run, the adapter requests a short-lived runtime-identity ID token with the service origin as audience. No service-account key, browser token, redirect, proxy or fallback provider is used. Metadata replies are bounded and errors sanitized. The runtime identity will need invoker permission scoped to the chosen inference service. This follows [Google service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).

Five mocked adapter tests verify URL/enablement checks, identity-response validation, bounded transport, no redirects and authorization before model authentication. No live cloud token, IAM invocation, deployment or paid inference has been tested or provisioned in this pass.

## Next checkpoint

When Google access is available, inspect surviving inference resources first, price a stronger-model restricted trial, then run real authenticated latency and answer-quality evaluations. Preserve member/admin and Core/Enterprise boundaries. Keep production release blocked on grounded source citations, correct permissions, stale-data handling and qualified review of work-zone recommendations. Current local 1B inference is a development fallback only.

Local preview: http://127.0.0.1:8083/ . V1, public DNS and Google Cloud deployments remain unchanged. No customer email, SMS or MMS was sent.
