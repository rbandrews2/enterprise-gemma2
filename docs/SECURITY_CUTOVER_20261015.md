## HF_TOKEN verified; scanner vulnerability gate blocked - October 15, 2026

Canonical secret HF_TOKEN version1 enabled. Live operator check: identity200,
selected google/gemma-4-31B-it repository access200, fineGrained token. No secret
value displayed or persisted. See HUGGINGFACE_GEMMA_ACCESS_20261015.md.
Failed gemma-inference-00007-njh loaded old google/gemma-2-2b-it and failed
GatedRepoError401 before listening8080; that model returned403 with this token.
Do not broaden token or restart wrong model. Existing Atlas helper uses Google
Storage weights, not HF. Live inference still unaccepted; bind HF_TOKEN only to
an actual HF consumer after narrowly scoped access review.

Completed analysis build27c1de4f-7011-45ff-b6b9-48c0fb3b90f4, scan
projects/enterprise-gemma2/locations/us/scans/eb138154-f833-40b8-bb35-893d3f4b217a.
Build FAILURE was formatting-only (python3 alias absent); findings retrieved
using existing operator access without another scan. Counts:162 total, HIGH18,
MEDIUM8, LOW84, MINIMAL52, CRITICAL0. Six fixAvailable, all pip25.0.1 with highest
reported patched version26.2. High packages:clamav12, acl2, cyrus-sasl2/attr/zlib/
perl one each. Debian trixie ClamAV1.4.3 has relevant parser vulnerabilities.
Image99019f1 is NOT cleared for activation despite functional acceptance.

Approved four-permission scan-only binding was removed automatically and absence
independently verified (IAM result[]). Original expiry2026-10-15T22:24:39Z was
not extended. Custom role remains unbound. No runtime grants/service/deploy made.
Cloud evidence pointer:~/wzos-approved-image-review-retry-latest.txt includes
findings.json,hf-check-result.json,access-removal/launch logs. Earlier pointer
~/wzos-approved-image-review-latest.txt includes redacted Gemma startup diagnosis.

Next: patched supported scanner engine/base and resolve/remove vulnerable build
tooling; immutable rebuild,lifecycle tests,new vulnerability disposition. Do not
mix unstable packages into stable or waive parser risks. New scan IAM window
requires new approval. Then dedicated runtime/invoker approval, live identity/
upload/hold tests,schema/current costs,security-capable rollback and cutover.
Atlas next: selected immutable weights/serving path and real inference acceptance.
CLI formatter now selects SDK bundled interpreter; new config not cloud-rerun.
Existing app gate689/108 unchanged; earlier two focused HF helper tests passed.
Local rerun unavailable:python command currently resolves Windows Store alias.
LandingB remains prototype-only. Production traffic unchanged.

# Atlas Security cutover preparation - October 15, 2026

Status: image/lifecycle acceptance PASSED; live activation and public application
cutover NOT applied. No scanner IAM changes or new runtime services created.

## Verified artifacts and current production

- Scanner source:2cd54853fc1abd320f3f52145493865c9e2a2304.
- Scanner image: `us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:99019f10204758114bc54cf987c4db1a7d881b693cd7d67083f4d346679adb8e`.
- Build32e7be44-f0f1-4ddf-9fab-187c15de5aad SUCCESS.
- Gate harness629f10b; Cloud Builda3aac155-9a1f-433e-8c62-775f2aea21b6 SUCCESS,
  SCANNER_IMAGE_GATE_PASS and image.exit0 independently read.
- Full application regression503dfc3:689 Python/PostgreSQL +108 Node, no failures,
  errors or skips. Subsequent application sources unchanged; packaging/helpers only.
- Current live service `wzos-v2-accounts`, regionus-central1, revision
  `wzos-v2-accounts-hub-5a3ac86` gets100% traffic.
- Current live image: `us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06`.
- Existing application identity: `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`.
- SQL `wzos-v2-staging-db` RUNNABLE/db-g1-small. Backup1792044000000 SUCCESSFUL,
  completed2026-10-15T08:48:21.194Z. Recheck freshness at deployment; this is not
  proof of restore acceptance or permission to restore over current data.

## Accepted container checks

Non-rootUID10001; read-only root; dropped capabilities; no-new-privileges;
private/tmp; 1CPU/4GiB test limit; no published ports, real identities or documents.
Clean synthetic document clean; safe EICAR fixture infected; expanded-limit ZIP
error-held; missing caller identity401; expired worker error-held/recycled.
Normal shutdown exits0. Broken network and missing certificate directory prevent
readiness and exit1. Final negative-test container exited without OOM.
Boots24s/23s; steady memory1.108GiB. These are synthetic Docker observations,
not Cloud Run cold-start, peak-memory, load or live Google identity acceptance.
Packaged engine is official Debian ClamAV1.4.3+dfsg-1 with signature28154;
prior native1.5.4 measurements are separate and must not be substituted.
Full logs: Cloud Build gate above and Cloud Shell
`$HOME/wzos-scanner-cloud-gate-current.log`. Only3 allowlisted harness files
(6.9KiB) uploaded. Source metadata and reviewed immutable image recorded.

Gate uses E2_STANDARD_2 (2vCPU/8GB), timeout1200s. Maximum build compute at
USD0.006/min is USD0.12 before allowances; source/image/log storage is additional.
Pricing verified October15: https://cloud.google.com/build/pricing.
Actual project spend remains to be refreshed before runtime activation; do not
substitute the user's earlier approximate35USD for a current billing report.

## Ordered release gates

1. Complete image OS/dependency vulnerability review, signature/cold-start/resource
   review and current billing check. Capture findings and disposition; no unreviewed
   critical or fixable security findings accepted automatically.
2. Obtain action-time confirmation for the exact private activation below. Prepare
   a bounded cleanup/disable guard before submitting any paid runtime experiment.
3. Proposed service `wzos-v2-scanner`, dedicated identity
   `wzos-v2-scanner-runtime@enterprise-gemma2.iam.gserviceaccount.com`, no database,
   bucket, Secret Manager or project roles. Grant only application caller identity
   service-scoped roles/run.invoker. No allUsers/allAuthenticatedUsers.
4. Proposed pilot: request-based billing, min0/max1, 1vCPU/4GiB, concurrency1,
   request timeout60s, startup TCP8080 probe within240s. Verify Google accepts the
   complete configuration and token audience before proceeding. Use IAM-protected
   HTTPS ingress; do not claim VPC/internal network isolation without configuring
   and validating it. No new VPC connector is proposed.
5. Resolve exact service URL from Google, set WZOS_SCANNER_AUDIENCE to that exact
   origin and WZOS_SCANNER_CALLER to the application identity. Do not guess a URL
   or change the caller/audience to work around failed identity validation.
6. Exercise genuine application identity, rejected anonymous/wrong identity,
   hash/UUID-bound results, stale/failed engine, cold start and concurrent requests
   using synthetic files only. No additional impersonation grant without review.
   Stop if the existing operator cannot run the identity test safely.
7. Review startup DDL in scripts/security_schema_review.sql against the actual
   live schema with scripts/check_staging_schema.py through the existing private
   SQL connection. Snapshot current service config/traffic privately and take a
   fresh backup if required by the release window. Startup applies this migration.
8. Build a separate immutable APPLICATION image from the reviewed integrated
   candidate, retaining current verified account/member/admin/edition controls,
   Daily, Maps, credentials and private storage. The scanner image is NOT the app.
   Review image findings. Deploy no main traffic and compare inherited config;
   no broad env replacement or credential values in logs/Git.
9. Configure WZOS_SCANNER_URL and WZOS_FILE_SCAN_REQUIRED=1 only on the accepted
   security-capable application candidate. Validate upload -> alert -> blocked
   download -> explicit admin rescan/release -> audit, both tenants/roles.
   Define an authenticated pretraffic test route through the existing ingress;
   do not open direct Cloud Run access to make a tagged revision easier to test.
10. Selected landing B still needs real dashboard navigation/entitlement wiring
    and scoped visual validation. Preserve every other module screen/style.
    ArchiveA stays in designs/landing/option-a.html. Do not ship prototype buttons
    or sample organization text as the real customer dashboard.
11. After all applicable gates, shift the existing app.workzoneos.org backend
    traffic to the exact application revision. No DNS/public-access expansion is
    needed. Check login/root/assets, protected APIs401, cross-origin403, direct
    ingress blocked, admin/member/tenant boundaries, file holds and module flows.
    Real Daily two-device media and Twilio delivery remain separate acceptance.

## Rollback and stop conditions

Before security activation, the verified hub revision above is the current
baseline, not an automatic post-activation rollback target. It predates durable
file-hold enforcement; routing back to it could expose held documents.

After any held/quarantined files exist, rollback only to a verified security-capable
revision that preserves download gates, incident/audit data and mandatory scanning.
If none exists, stop the cutover and keep file access unavailable with a clear
service error until that revision or scanner is restored. Never disable mandatory
scanning, clear holds, drop security tables, or restore an old database to recover
availability. Keep the scanner private and retain incident evidence.

Stop on identity failure, missing/current-signature failure, incomplete scan,
resource overrun, unexpected schema/config drift, absent backup or current cost
uncertainty. No customer files in initial scanner pilot; no customer messaging.

## Approval boundary

The user requested preparation, not a new scanner permission grant. New dedicated
service identity and narrowly scoped invocation expand security-sensitive access;
browser-control policy requires exact action-time confirmation before applying.
The public site remains unchanged while these gates are open.

### Image vulnerability review remains open

The existing On-Demand Scanning API was verified enabled. One remote scan was
attempted, but gcloud still needed local package extraction from the remote image
and stalled in Cloud Shell. After observing its exact owned process PID27402 at
222 seconds, stopped only that matching image-scan client with TERM; terminal
confirmed Failed and returned to prompt. No findings/operation receipt obtained;
do not report zero vulnerabilities or completed security review. Next use a
bounded cloud-native extraction/review job with existing permissions; do not
enable APIs or broaden build identity access automatically. The configured API's
listed price is USD0.26 per scanned image (before any allowances):
https://cloud.google.com/artifact-analysis/pricing (verified October15).

### October15 retry and cloud-native review

Requested Cloud Shell retry timed out180s (exit124, no operation/findings).
Prepared cloudbuild.scanner-review.yaml; source archive is only that one public
configuration file, no customer data. Build6b537955-f56b-4abf-900f-343dbe988660
failed because local-extract was absent from the official minimal CLI image.
Buildaa2da117-b1b1-4121-8ff5-0caac6e043e1 showed apt could not locate the
component without the image's runtime package-repository installer.

Repaired using Google's documented COMPONENTS runtime installer, preserving the
image's default entrypoint; pinned actual official CLI image digestee211536...
Sourcea219cec submitted as buildca2222cf-59ba-4cf2-8084-71544fa84f93. Limit900s
E2_STANDARD_2; no IAM/API/service changes. Outcome pending; inspect final log in
$HOME/wzos-security-cutover-20261015/scanner-review-final-build.log. Build compute
capUSD0.09 before allowances plus scanning/storage; no zero-vulnerability claim.
Official guidance: https://github.com/GoogleCloudPlatform/cloud-sdk-docker/blob/master/docs/user_guide.md#installing-additional-packages-or-components-at-runtime

### Confirmed IAM blocker and proposed temporary repair

Buildca2222cf-59ba-4cf2-8084-71544fa84f93 installed official local-extract589.0.0
and COMPLETED package extraction. The service refused analyzePackages for existing
build identity910004733138-compute@developer.gserviceaccount.com. No scan operation
was started and no vulnerability findings exist. Scanner container gate remainsPASS.
No runtime/scanner service exists or IAM was changed.

Prepared scanner-image-review-role.yaml: four scanning-only permissions (analyze
packages, read findings, get/wait operation). Proposed project custom role
projects/enterprise-gemma2/roles/wzosImageReview, bound ONLY to existing build
identity above with request.time < UTC activation-time plus1hour. Remove the exact
conditional binding immediately after review, even if it fails; expiry is a backstop.
Do not grant Editor, Owner, service-agent or project-wide security admin roles.
Do not alter an existing custom role with different permissions; stop for review.

IAM scope is project-level scanning, not one image/job: other workloads using this
same identity could also analyze package inventories/read scan findings during the
one-hour window. The harness submits only the pinned WZOS scanner image. This
does not grant database, bucket, Secret Manager, customer-file or app-user access.
Action-time user approval is REQUIRED before creating/binding this role.
Rollback: remove only the matching role/member/condition binding; retain findings
and evidence. Any subsequent role deletion requires separate review and is not
necessary for removing access. Do not apply an unconditional grant if IAM Conditions
are unsupported. Primary permissions reference:
https://docs.cloud.google.com/iam/docs/roles-permissions/ondemandscanning
