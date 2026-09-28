# Atlas source-enabled staging: end-of-day checkpoint

## Completed

- Built and verified a preserved-source snapshot: six extracted sources, 26 hashed files plus manifest. Original documents, extraction hashes, review states and rebuilt SQLite index are retained. No freshness or applicability approval is implied.
- Uploaded the 43,831,588-byte archive to Cloud Shell. SHA-256: `0349759b6ddecb4cd01579ed33312fc046fd4f772e87a5f1b9f3221754c49a91`.
- Added snapshot verification and a reproducible source-enabled account-image build command. Verification ran locally, in Cloud Shell and inside Cloud Build.
- Cloud Build `dc2cbf41-90b2-422a-8a32-eda4418b6a4d` succeeded. Image `us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:e8b31c99d0a1-sources` deployed as `wzos-v2-accounts-00009-222`.
- Added the operator-only saved-job/citation acceptance runner in commit `e2cbea0`.

## Actual validation and limits

Managed-account preparation passed. Saved synthetic Norfolk job creation passed, stale-version rejection returned 409, and cross-organization rejection returned 403. The cited model request returned Cloud Run IAM 401 before application inference. A subsequent identities request also failed; the operator identity token was confirmed expired by 104 seconds. Control-plane credentials still supported cleanup. Do not count this as a successful cited answer or a model-quality failure.

Source-package tests pass (2). A direct unittest module invocation could not resolve the test helper; the repository's discovery invocation passed. Earlier full-suite and browser/model acceptance are recorded separately, not rerun or claimed as new results here.

The inference service was still reporting readiness Unknown at the diagnostic checkpoint. True cold-start, concurrency, cancellation and cited-answer acceptance remain open. No model downgrade, training, customer delivery or production changes.

Coverage remains six sources: five extraction-checked and VDOT known-errors unreviewed. OSHA factsheet missing; locality and applicability gaps remain visible.

## Preserved evidence

- Local ignored `.local-data/source-deployment-20260928/` and matching ZIP.
- Cloud Shell `/home/admin_/source-deployment-20260928.zip` and `/home/admin_/wzos-evidence/source-deployment-20260928/`.
- Cloud Shell trial checkout/logs/disabled fixture state: `/home/admin_/wzos-grounding-ZCyfzy/`.
- Failed test `grounding.jsonl` is empty, not acceptance evidence. Never commit fixture credentials.

Before this trial, monitoring reported 1,117.087 billable instance seconds, approximately $0.99 at the documented compute rate. This is delayed usage, excludes this trial and build/storage charges, and is not an invoice. Recheck cumulative usage against the approved $15 trial before another deployment.

## Resume point

Refresh the Cloud Shell operator identity token and confirm positive remaining lifetime without printing credentials. Verify private app access first. Recheck trial spend, then start the same approved private 31B inference configuration, wait for verified readiness, create fresh disposable fixtures and run one saved-job/citation case. Review the actual answer and revision/page citations before proceeding to bounded cold-start/concurrency/cancellation tests. Disable fixtures and trial inference afterward. V1, public DNS and production remain unchanged.

## Verified shutdown

Synthetic users disabled, tokens revoked and both organizations disabled. Source-enabled app revision `wzos-v2-accounts-00010-sfh` deployed with Atlas enabled=0, 100% traffic; readiness True confirmed. Trial inference service deletion succeeded; subsequent deletion returned service not found, confirming absence. Model weights retained. Cloud Shell reconnected into a fresh session; process inspection found no old trial guard or SQL proxy, and the inference-service listing was empty.
