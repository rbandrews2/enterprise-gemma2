# Navigation release evidence — October 11, 2026

## Exact candidate accepted at database gate

Candidate `6c78ae80ae8e3cec455f77615c4bba120fc3ebcc`:
full native PostgreSQL492 tests passed, zero failures/errors/skips,133.682s.
Independently observed in Cloud Shell. Disposable Unix-socket cluster used the
existing PostgreSQL16 installation; no paid database or live schema was used.
Local Python492 passed/132 PG skips and Node56 passed/no skips remain recorded.

Cloud evidence directory: `/home/admin_/wzos-release-20261011`.
Gate checkout/log: `/tmp/wzos-navigation-gate.m9mlXXkT/repo` and `../gate.log`.
Exact-source build context: `/tmp/wzos-navigation-build.4NytWvmV`.
Navigation source SHA256 matched between checkout/build context:
`92200d81c99102ca53f402ed2bb7aac1c16c5ba88b4ffbbe513816b7b7b8144b`.
Build inherits the previously verified immutable source-library image and reuses
its source-snapshot integrity checks; no source-original reupload or API ingestion.

## Credential replacement verified

Routes API enabled. Dedicated server key is restricted to `routes.googleapis.com`.
Secret version1 enabled; accessor binding lists only the WZOS staging runtime.
However, the Google key-creation command printed its generated credential despite
the output filter. Do not reuse the exposed value. Ray was asked to replace the
Routes-only key, store the new value as a new secret version and disable the old
key. Browser policy requires user handoff for credential replacement. No key value
is recorded here. Ray completed replacement. Metadata independently confirms new
key UID `3477d665-3fa0-43fd-9ba4-f779716cd00f`, restricted to Routes API only;
secret version2 enabled and version1 disabled. The exposed original key has
deleteTime `2026-10-11T21:37:40.728595Z`. Candidate pins secret version2.

## Pre-deployment freeze (historical checkpoint)

Independently verified main restricted traffic remains100% on00031-h5t;
private `release-cf35780` tag remains00032-9rw. Runtime identity unchanged.
No new routing revision or provider call yet; no V1/DNS/production change.
Disposable PostgreSQL process/directory cleanup independently verified. Build
`736a3f9a-164b-4552-95a6-f58a99d9dc26` succeeded with source-library verification
and frozen snapshot SHA256
`070ec5e461a56fbdf60ad81c0b91a699e87316d500af7dcf6245b94e81a3dcd4`.
Image digest: `sha256:5f6148be357ac02ed96bafaa2efb110ea9a9b1ed9467e903009bd37eab26cd5b`.

Before routing deployment: finish credential replacement verification, quota and
billing review, successful build/source verification, private no-traffic candidate
deployment with pinned secret version, then capped synthetic Google route/map and
Android checks. Twilio remains on hold. Preserve auth, tenant and edition boundaries.

## Private candidate and live acceptance

Revision `wzos-v2-accounts-00036-ray` is Ready under tag `navigation-6c78ae8`,
zero main traffic. Main remains100% on00031-h5t; previous Maps tag00032 retained.
Exact environment comparison against00032 changed only
`WZOS_NAVIGATION_ROUTES_ENABLED` and `WZOS_GOOGLE_ROUTES_API_KEY`.
Identity/resources unchanged: existing staging service account,1 CPU/512Mi,
maxScale2. Existing SQL/auth/storage/Atlas bindings preserved. No new startup DDL.
Service IAM inspection has no public invoker; direct unauthenticated candidate
request returned403. Through the operator-only proxy, anonymous Navigation config
returned401.

Google ComputeRoutes project quota effective limits verified:20/day,6/minute.
Only that metric's daily/minute consumer overrides were added; route-matrix quotas
unchanged. Previous defaults were unlimited/day and3000/minute. Do not restore those
higher limits during testing. Quota metadata is in navigation-quotas.json under the
cloud evidence directory; rollback can delete only these newly created overrides
after routing has been disabled and usage reviewed. Budget alerts are not a hard cap.

One live Calculate click and one Dynamic Map initialization accepted. Synthetic
admin selected existing test organization, saved public destination810 Union Street,
Norfolk VA, revision2, and entered public origin150 Saint Pauls Boulevard.
No device location permission or real employee location used. UI returned0.3 miles,
approximately3 minutes, timestamp5:42:24 PM Eastern, four directions, visible amber
route overlay, Google attribution and terms. Close route removed the panel/map.
The request had no automatic retries. Preserve a total20-route/20-map acceptance
limit; observed usage this Navigation run is1/1, excluding earlier Maps acceptance.

Ignored visual evidence:
`.local-data/navigation-live-map-20261011.png` in the integration checkout.
Proxy binds127.0.0.1:8080 to the private candidate and expires after45 minutes;
PID/log pointers are navigation-proxy.pid/navigation-proxy.log in cloud evidence.
The Cloud Shell preview requires operator access plus WZOS sign-in.

Development cap remains$150 October8–17. Ray's approximately$35 billing is reported,
not a reconciled live ledger; one route/map pair is approximately$0.017 at documented
first paid tiers before allowances, plus the bounded build. No GPU/new infrastructure.

Remaining: Android physical-device/manual-origin checks, live member own/assigned
destination and denied private-job checks, location denial/cancellation lifecycle
acceptance and current billing reconciliation. PostgreSQL role/tenant tests passed,
but do not substitute for those live checks. No production promotion or V1/DNS change.
Rollback: retain00031 main traffic and00032 Maps tag; remove only the Navigation tag
to end candidate access. Disable routing before any quota/key/access rollback.
