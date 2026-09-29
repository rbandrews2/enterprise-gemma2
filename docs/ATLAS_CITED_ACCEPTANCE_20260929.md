# Atlas saved-job / candidate-source acceptance — September 29

## Accepted bounded scenario

Private full-size Gemma 4 31B inference revision `wzos-atlas-inference-00001-mbw` and source-enabled account revision `wzos-v2-accounts-00012-vrf` reached Ready. The real app runtime identity invoked the model for a saved synthetic Norfolk underground-utility job.

The successful request took **5.288 seconds** and returned `model_called=true`, the saved job revision, no saved checklist, available source library, three candidate citations, unverified applicability, no performed actions and no field-use approval. Each citation passed revision-hash, HTTPS official URL, page/section and review-status checks.

Candidates: VDOT work-area manual PDF pages 97 and 55, plus the VOSH program section reference; all extraction_checked. These are retrieval candidates, not proof of applicability or that every answer statement is supported. Although the question mentioned FHWA, no FHWA candidate was returned; broader retrieval/citation relevance remains an evaluation gap.

Manual response review: Atlas identified unconfirmed road ownership/authority; missing posted speed evidence, lane count, pedestrian/intersection impacts and work period; missing measured geometry, closure type, work limits and travel directions; and missing permits, contract conditions and approved traffic-control plans. It requested verified documents and measurements for qualified review and explicitly said candidate references are not applicability determinations. It gave no invented placement dimensions. This case does not establish placement accuracy or compliance approval.

## Access and failure evidence

- Fresh synthetic managed-account validation passed: sign-in/refresh, verified email, admin/member, cross-organization and last-admin protection.
- Saved-job creation 201; stale-version denial 409; cross-tenant denial 403.
- First model request returned app 503 caused by an upstream IAM 403. Correct app runtime invoker binding was verified. One retry after the propagation interval succeeded without permission broadening or public access.
- Cloud Shell metadata ADC failed for Firebase and SQL proxy. Operator-only fixture wrapper used the authenticated gcloud access token with explicit enterprise-gemma2 quota project; SQL proxy used its supported gcloud-auth option. These are test-harness credentials, not production runtime changes.
- Earlier local validation of credential-lifetime and safe-evidence changes: 182 tests total, 166 passed/16 database skips. No full-suite rerun was needed for this cloud-only test.

## Evidence and cost boundary

Cloud Shell home `/home/admin_/wzos-grounding-ZCyfzy/` retains deployment/proxy logs, `grounding-20260929.jsonl` (failed request stages), `grounding-20260929-retry.jsonl` (passed stages and complete synthetic response), and the disabled fixture state. Do not commit credential files. Source snapshot/archive remains preserved separately.

Before this session monitoring showed 1,598.554 billable inference-instance seconds, about $1.42 compute at the previously recorded rate. This excludes current session, builds/storage and billing delay; it is not an invoice. Recheck cumulative usage before another paid trial; original $15 trial authorization remains the limit.

## Next acceptance gate

True scale-from-zero, bounded concurrency, client cancellation/provider failure behavior and measured cost remain pending. Startup readiness took multiple minutes and 18 TCP probe attempts; this deployment observation is not an accepted end-to-end cold-start benchmark. Expand grounded evaluations across source relevance, missing/superseded documents and representative Virginia jobs after reliability checks.

No customer messages, production/V1 changes, public DNS changes, model training or model downgrade.

## Verified cleanup

Final source-enabled app revision `wzos-v2-accounts-00013-kmx` Ready=True with Atlas enabled=0. Trial inference service deletion succeeded. Four synthetic users disabled, tokens revoked and fixture organizations disabled. Failed pre-account attempts created no fixture files/users. SQL proxy and 30-minute cleanup guard stopped. Model weights retained.
