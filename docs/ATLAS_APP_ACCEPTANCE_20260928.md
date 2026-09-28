# Authenticated WZOS-to-Atlas acceptance — September 28, 2026

## Completed

Built app source `503824e` as image `wzos-v2-accounts:503824e`.
Cloud Build `5a571613-e34b-44d6-90f3-a6e75d73b6fb` succeeded. Restricted
account revision `wzos-v2-accounts-00007-zqt` served the integration test.
Database, private files and identity settings were preserved by an image/env
update. App request timeout increased from 60 to 300 seconds.

Private inference revision `wzos-atlas-inference-00001-v6m` used the same pinned
Gemma 4 31B configuration as the previous trial. Only the account runtime
identity received a service-level `roles/run.invoker` binding. The app acquired
its own audience-bound metadata identity token; no operator token was passed
through the app to the model.

## Real provider and inference validation

- Disposable admin/member/other-organization/unverified identities created.
- Real sign-in, refresh, verified-email, last-admin and tenant checks passed.
- Other-organization and unverified users received 403 on the assistant endpoint.
- A separately activated synthetic Core organization received 403 for the
  Enterprise report endpoint before inference.
- Three serial app-to-model requests passed with `model_called=true`,
  `response_kind=model`, no actions performed and no field approval.

| Actor / module | Seconds | Reviewed result |
|---|---:|---|
| Member / work orders | 60.969 | Preparation steps and limitations; request overlapped model startup |
| Admin / messaging | 1.691 | Correctly denied real notification delivery |
| Member / report | 1.295 | Declined invented flagger coordinates without verified evidence |

The first latency is not a complete scale-from-zero benchmark: deployment was
already underway. Warm results are a small synthetic sample, not a throughput SLA.

## Browser validation

Signed in through the actual Google identity provider as the synthetic member,
selected the Enterprise organization, opened the persistent Atlas panel, and
submitted a free-form preparation question. The browser displayed a completed
AI-generated reply with limitations. The app-owned **Open job board** button
closed the assistant and focused the Job board heading. Signed out afterward.
No credentials are recorded in this document.

Full local suite: 175 total, 159 passed, 16 PostgreSQL-dependent skips.
Operator runner: `scripts/validate_atlas_live_staging.py` (three bounded calls,
new output path, stops on failure). Raw app responses are in persistent Cloud
Shell home `~/wzos-evidence/20260928-atlas/app-live.jsonl`.

## Cost and remaining work

Before this integration run, Cloud Monitoring returned 669.549 billable instance
seconds across prior inference trials, approximately $0.59 compute at the recorded
rate. Monitoring is delayed and is not the invoice; build/storage costs are extra.
The approved $15 trial scope remains the limit. No customer delivery or V1/public
DNS/production changes occurred.

Remaining: saved-job and citation-grounded end-to-end scenarios, real cold-start
and concurrent-user behavior, timeout/cancellation under the cloud engine, and
broader output quality. Browser prose currently displays Markdown markers as
plain text; improve readable formatting without inserting untrusted HTML. The
readiness message also needs to distinguish an enabled cold model from disabled
inference without sending keep-warm requests. No production acceptance claimed.

Cleanup and final revision are recorded after verification in SESSION_HANDOFF.md.
