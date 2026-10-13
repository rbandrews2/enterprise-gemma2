# Public V2 release — preparation October 12, acceptance October 13, 2026

## Applied public release

Ray approved public cutover and scoped Twilio setup. Public revision00041-pem serves
100% through wzos-v2-public-backend at https://app.workzoneos.org. Production
origins/passkey RP configured; load-balancer-only ingress preserved. Organization
policy rejected allUsers; Google's service-only `--no-invoker-iam-check` public
setting was used instead, without changing organization policy. Application identity,
tenant and role checks remain enforced. See PUBLIC_ROLLBACK.md for reversal.

Public HTTP acceptance PASS: root and six assets200; seven private APIs401;
cross-origin403; direct run.app404. Browser confirms public WZOS sign-in. Initial
HTTP probe timed out during propagation; later complete retry passed. Twilio
three secret bindings/accessor grants applied, SMS test mode restricted to the
approved recipient. No SMS sent; delivery acceptance remains open. Live Atlas
inference and checkout are still unfinished. All sections below describe preparation
history; their earlier not-applied statements are superseded by this checkpoint.

## Exact candidate and accepted evidence

- Application: 13f089edcbf767338ab01ee14b96f29418cf2927, origin/codex/preproduction-modules.
- Full Node90 passed locally. Exact native PostgreSQL546 passed, zero skips; independently
  read in internal Cloud Shell. Native test cluster cleanup verified.
- Live schema read: no conflicts; absent activation_entitlements,
  organization_entitlements, purchase_events, purchase_requests. First two initialize
  with Accounts; sandbox commerce remains disconnected from the default runtime.
- Successful backup1791784800000; live SQL RUNNABLE/db-g1-small/backups enabled.
- Build77d268d6-eea8-4adc-bf80-644d5a4a56c6 SUCCESS. Selected runtime177 files/3.8MiB;
  inherited frozen agency library verified in build.
- Image: us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:503dd7649550382f920e4e2fc7159cf65d846da4650996588fca508ac241c6d4
- Linked billing account overview October1-12:20.27 before savings,1.52 savings,
  net18.75USD. Account display with lag, not exact project/approved-window ledger.

## Prepared public-routing change (not yet applied)

Current app.workzoneos.org host/path matcher points to gemma-assistant-api-backend,
IAP enabled, serverless NEG gemma-assistant-api-neg targets V1 gemma-assistant-api.
Keep the current backend/NEG and exported URL map for rollback. Create separate V2
serverless NEG/backend; route only app.workzoneos.org's existing matcher to V2.
Other/default routing and certificate remain unchanged. Public V2 uses verified
Google app login and organization/role/edition permissions. Retire tester@test.org
(shared test password) before public routing. Never deploy synthetic local auth.

Configure production origin https://app.workzoneos.org and matching passkey RP.
Existing preview-domain passkeys do not authenticate at the new domain; password
sign-in remains available and users enroll production-domain passkeys themselves.
First deploy private/no main traffic, verify assets/APIs/config, then apply public
routing only after the required action-time confirmation for public access changes.
Public path must use load-balancer-only ingress, maintain private storage, and verify
unauthenticated protected API401/403 and direct run.app access blocked. Rollback
restores saved URL map, service ingress/access policy and prior traffic/image.

## Capabilities that cannot be called complete

Atlas inference service is absent in live us-central1. Current runtime inference
flag is disabled. Prior cold trial is historical, not active production intelligence.
Three Twilio secrets exist; not bound in current runtime. Sender/carrier delivery
acceptance remains separate; no customer send or AIRA voice-hook change authorized
by this document. Live checkout prices, credentials and recurring lifecycle remain
unaccepted; sandbox commerce must remain disabled. Saved meetings use Google Meet
links; no automatic conference creation. Map renderer/Routes adapter are present;
production-origin interactive rendering must be verified after deployment.

## Connection state

Internal embedded Shell input initially rejected focus. Standalone shell restored
input and completed gate/schema/build/inventory reads. It disconnected after build;
reconnection underway. No new service revision/public change yet at this checkpoint.

## Accepted private release and precise public-access decision

Private revision wzos-v2-accounts-00040-qod Ready; tag release-13f089e. HTML200,
exact byte matches for navigation.js/team-modules.js/account.js/workspace.css/
install.js/manifest. Verified-account mode exposes no synthetic identity selector.
Seven protected endpoints return401 without user login; unauthenticated tagged
run.app403. Main traffic remains00031-h5t100%. Initial probe incorrectly checked
/api/employees (404); corrected to /api/account/employees and reran acceptance.
Fresh backup1791863718996 SUCCESSFUL. The real admin remains verified/active with
one admin/Enterprise membership in Molecular Project Development LLC. Shared
identity tester@test.org disabled, refresh tokens revoked, its one active membership
retired with operator audit. No real admin password or membership changed.

Public-access action requiring confirmation at execution time:

1. Use separate wzos-v2-public-neg/serverless backend wzos-v2-public-backend
   (EXTERNAL_MANAGED), pointing to wzos-v2-accounts. Keep old V1 resources intact.
2. Set only production app origin/passkey origin/RP to app.workzoneos.org; keep
   max2,min0 and existing storage/database identities. Users enroll new-domain keys.
3. Restrict ingress to internal-and-cloud-load-balancing; add only allUsers
   roles/run.invoker on this one application service so the public login can load.
   The application still requires Google identity, verified email and tenant roles.
4. Move app.workzoneos.org's existing host/path matcher to the separate backend.
   Keep V1 default/unmatched routing, TLS certificate and other domains unchanged.
5. Check HTTPS root/assets200, private API401, cross-origin403 and direct run.app
   inaccessible; roll back host routing first on failure.

Optional separate permission decision: grant the runtime secretAccessor on only the
three named Twilio secrets. Current project roles do not grant this access. Bind
credentials with SMS test mode limited to the previously approved test recipient;
no automatic customer sends, AIRA voice-hook changes or blanket live SMS enablement.
This does not resolve carrier delivery acceptance or missing live AI/checkout.
