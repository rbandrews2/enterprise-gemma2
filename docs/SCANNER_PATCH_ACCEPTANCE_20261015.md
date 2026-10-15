# Patched scanner and Atlas artifact verification - October 15, 2026

## Verified repair

- Scanner source2fffe783a47e9b0b445d2081d185fc10fe8b4d75.
- Official Ubuntu26.04 amd64 base inspected via Docker manifest:
  ubuntu:26.04@sha256:88a381d5b5eeb2b35d3ad70925a362c37ce569daf43ede89ff818ec20e4d3794.
- Uses only the supported distro/security feed, applies available OS updates,
  requires engine>=1.5.4 and vendor CVD certificates. No testing/unstable sources.
- Minimal Python venv; dependency consistency checked; pip removed from final
  venv and distro pip wheel removed. No app schema/API/dependency changes.
- Cloud Build40db26b2-9f1b-4f98-8742-348accc66b22 SUCCESS.
- Immutable result:
  us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-scanner@sha256:6190d698438aff6ab92ea9e8de8acce9f9149cd1e94c7e374ab5e0a95903da16.

## Container acceptance

Cloud Build33a26700-bbaa-4460-adea-8db133da5e23 SUCCESS, harness451bfc3.
Explicit SCANNER_IMAGE_GATE_PASS. Engine1.5.4/28154, distro package
1.5.4+dfsg-0ubuntu0.26.04.1, Python3.14.4, non-root10001. Runtime pip absence
asserted. Clean fixture clean, EICAR fixture infected, expanded ZIP limit error,
missing caller401, expired worker error; recycle/shutdown/network and missing
certificate checks pass. Both boots24s; steady1.116GiB under4GiB limit.
This is container behavior acceptance, not vulnerability clearance/deployment.

## Atlas preparation

Live read-only verification compared Google source and retained model object
names, sizes and CRC32C values. All10 objects/62,578,670,545 bytes match.
Saved object generations in cloud evidence atlas-artifacts.json; no weights
redownloaded and no GPU started. Current wzos-atlas-inference service absent;
old gemma-inference has no ready revision. HF_TOKEN access already verified.
Five focused local tests pass:2 HF checks and3 artifact-integrity cases,
including same-size changed checksum and missing-object rejection. Used bundled
Python runtime; Windows Store alias is not an installed Python interpreter.

## Pending

Review buildfd9f372c-a40b-43ea-86ac-7330efba06e9 SUCCESS; review.exit0.
96 findings: HIGH0, CRITICAL0, MEDIUM92, LOW3, MINIMAL1; fixAvailable0.
All18 previous HIGH findings and six fixAvailable pip findings absent. Remaining
lower-severity findings still need applicability review; do not label image clean.
Temporary binding removed; independent IAM lookup returned[]. Role stays unbound.
No scanner service, new runtime identity or production activation performed.
Cloud evidence pointer:~/wzos-scanner-patched-latest.txt.

Primary package evidence:
https://packages.ubuntu.com/search?keywords=clamav&suite=resolute

Existing Atlas subnet wzos-atlas-us-central1 has Private Google Access=true,
10.83.0.0/26; dedicated inference identity exists. These read-only checks do not
establish effective invocation permissions, current cost or live inference.

## Private pilot deployed; identity acceptance pending

Ray approved private synthetic pilot. Service wzos-v2-scanner-00002-sj2 is Ready,
canonical URL https://wzos-v2-scanner-udtvm4rgca-uc.a.run.app. Dedicated identity
wzos-v2-scanner-runtime@enterprise-gemma2.iam.gserviceaccount.com has no project
roles (independent IAM lookup[]). Service policy grants only the existing WZOS
app identity roles/run.invoker; no allUsers/allAuthenticatedUsers. Config min0/
max1,1CPU/4GiB,request billing,concurrency1. Public app config unchanged.
Anonymous real /scan request correctly rejected403. Authorized synthetic file
requests remain BLOCKED before upload: existing operator cannot mint app-principal
ID token (direct IAMCredentials403; sign-in is not expired). No extra access
granted. Do not mark real caller/clean/detection/integrity checks passed.

Proposed narrowly scoped next permission: grant user:admin@workzoneos.org only
roles/iam.serviceAccountOpenIdTokenCreator on the single account
wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com, conditional expiry15min,
remove immediately after test. This permits Google ID tokens acting as the app
for services accepting that identity; no access-token generation, signing,
database/storage/secret roles. Requires action-time approval before granting.
Use direct generateIdToken API in validator; do not replace with broad TokenCreator.

User requested all security/scanning UI credit Atlas. Updated attachment states
and admin security UI, preserving honest pending/unavailable/clean distinctions.
Committed fc85382; not publicly deployed. Node108/108 pass; focused Python5/5.
## Authenticated scanner pilot PASS; live schema compatible - October15

Ray explicitly approved the temporary ID-token test. Narrow SA-scoped
roles/iam.serviceAccountOpenIdTokenCreator grant to admin@workzoneos.org was
conditional until2026-10-15T22:33:15Z. Single synthetic run PASS, test.exit0:
anonymous403; app-principal clean200/clean; EICAR200/infected; altered hash400.
UUID/hash/byte-count response traceability validated. Identity token remained
in process memory only. Grant removed immediately; independent SA IAM read[].
This validates an operator-minted app-principal token, NOT the production app's
metadata-token path or complete browser upload/hold/rescan/release workflow.

Read-only live schema check: compatible_existing_columns=True, conflicts[].
Missing:security_incidents/security_actions/security_file_states/security_alert_reads
(additive reviewed startup migration). Also purchase_requests/purchase_events,
which belong to explicitly instantiated sandbox commerce; not automatic checkout
activation. Owned temporary localhost5544 SQL proxy stopped; process check empty.
Latest backup1792044000000 SUCCESSFUL,2026-10-15T08:48:21.194Z. No schema writes.

Next gate: current billing report. Opened Google Billing; Google requires account
verification for admin@workzoneos.org. User sign-in request pending; no password
requested in chat. Do not claim current spend verified from historic estimates.
Then finish lower-severity disposition, prepare security-capable app candidate,
verify retained source library/config, and test authenticated upload/hold/recovery
through existing ingress before production cutover. Public app still unchanged.
Atlas security UI wording is committed and Node108/108 passed, not live yet.

Cloud evidence:~/wzos-scanner-patched-latest.txt/identity-test/{acceptance.json,
launch.log,condition.txt,removal.log,test.exit}; live-schema.json/schema.log,
schema-proxy.log. Private scanner remains Ready min0/max1, app-only invocation.
Atlas model service remains absent; retained31B weights integrity already verified.
