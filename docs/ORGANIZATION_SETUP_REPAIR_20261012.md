# Organization setup repair — October 12, 2026

## Confirmed cause and local repair

Cloud Run request metadata shows three organization/join POSTs returning HTTP422
at 21:34:35, 21:34:39 and 21:34:44 UTC. The UI displayed Account request failed
because it handled string errors but discarded validation arrays. This establishes
invalid input, not a database outage. The observed chooser has no memberships.
Creating requires name2–120 and activation32–128 characters; joining requires
invitation32–128 characters. No valid activation/invitation was supplied in this
workflow. Do not bypass these entitlement or verified-identity checks.

Local account.js now validates these fields before requests, explains the two
setup paths, and converts validation arrays to fixed, field-specific messages
without echoing input values or private diagnostics. Network/non-JSON handling
is explicit. Full Node78 passed, zero failures/skips; focused auth21 passed.
Initial default Node isolation was sandbox-blocked EPERM; no-isolation run passed.
No backend/schema change. This client repair has not yet been deployed.

## Next concrete setup action (awaiting confirmation)

Issue one single-use Enterprise activation in the existing staging database, with
24-hour expiry, saved to a private0600 Cloud Shell file; no token in Git/log/chat.
Use it only to create Molecular Project Development LLC for the verified
admin@workzoneos.org identity through the existing organization creation endpoint.
That endpoint gives organization-scoped admin access and records its access audit.
Do not grant global administrator access or change other tenants, V1/DNS/IAM.
Inspect current memberships before issuance to avoid duplicate organizations.
Browser policy requires action-time confirmation because this grants admin and
Enterprise access. If not consumed, delete only the newly issued unused activation
record after expiry; retain any resulting organization audit.

After approval: verify identity/membership, run existing operator workflow with
bounded proxy lifetime and private output, complete setup, verify admin session;
then deploy client repair under existing release gates. No password entry by agent.

## Approved setup execution checkpoint

Ray explicitly approved Enterprise organization/admin setup. Google identity lookup
returned one admin@workzoneos.org account, verified true, disabled false. Existing
WZOS account UID matched that provider identity. Database precheck found zero
memberships and zero organizations named Molecular Project Development LLC.
Existing Accounts.issue_activation issued Enterprise activation with24-hour expiry,
saved only to0600 Cloud Shell admin-enterprise-activation.txt. SQL proxy5547 exited
through trap. No activation value in Git/chat/log output.

Cloud Shell editor opened that private file; activation copied directly into WZOS
form without displaying it in tool output. Organization name filled. Mouse submit
interrupted; observed form remained. Keyboard submission then timed out and browser
connection disappeared. Creation outcome UNKNOWN; do not issue another activation
or create duplicate organization. User asked to select company if already listed,
otherwise click Create organization once, then reconnect. On resume inspect provider
identity, membership, consumed activation and access audit before any repeat.
Clipboard may still contain activation because connection loss prevented clearing;
clear via browser clipboard API when reconnected, and clear editor selection.
Latest client repair d44af92 remains local/Git only; private runtime00038 unchanged.
No public routing, IAM, password, customer send or other-tenant change.

## User-confirmed creation outcome

After the interruption, Ray reports Molecular Project Development LLC appears for
selection. Organization creation therefore succeeded from the user-visible list;
prior UNKNOWN checkpoint is superseded by this observation. Ray instructed to
select its admin/Enterprise entry. Workspace entry and independent live membership/
audit readback remain open. Chrome is absent from connected browser inventory.

## Unexpected HTML response — subsequent user report

Ray reports Unexpected token '<', '<html lang' is not valid JSON after organization
selection/setup. An API call received HTML, but origin and status are not yet verified.
Do not treat this as proof that the database creation was undone. User-visible company
listing remains the earlier observation; independently inspect membership next.
Chrome absent from connected inventory; reconnect requested. Existing proxy uses
45-minute instances; expiry/reauth/routing are candidates, not confirmed causes.

Local workspace.js startup API parser now safely handles non-JSON service responses,
preserves HTTP status and warns that no save was confirmed. Existing d44af92 account
parser already guards this error but is not deployed. Full Node82 passed before the
additional organization HTML case; focused auth/workspace26 passed afterward.
No backend/schema/public change. Next restore protected preview to the exact tested
candidate, verify organization/admin/Enterprise membership and access audit, select
existing organization instead of creating another. Clear activation clipboard.

## Independent recovery verification — October 12, 2026

Fresh Chrome3 connection succeeded. Existing Cloud Shell preview port8080 was closed;
restored official cloud-run-proxy pointing to private auth-2b42560 candidate,45-minute
lifetime. /api/identities HTTP200 modeverified_accounts. Opened preview; remembered
identity reached organization chooser with no organization buttons.

Read-only live PostgreSQL check contradicts prior company-list interpretation:
admin@workzoneos.org memberships=[], existing activation present but unused,
organization_created audit count0. Organization creation NOT complete. Prior
user-confirmed-success wording was an inference and is superseded by this database
result. No replacement activation or duplicate organization issued. Private readback
saved HOME/wzos-release-20261012/admin-setup-readback.json; SQL proxy5547 trap cleaned.
Browser clipboard cleared before preview recovery.

Full exact local Node83 passed/no skips. Submitted clone/detach of
bf77c91202f1b59245a56a07d734d74a51fae690 and native PostgreSQL gate to
HOME/wzos-auth-repair-bf77c91; result not yet observed. Log intended path
HOME/wzos-release-20261012/postgres-bf77c91.log. Cloud editor stalled while opening
existing private activation file, then Chrome disappeared from inventory. No build
or deploy submitted. Next reconnect Terminal, read gate/cleanup, finish same approved
activation through real verified-user endpoint, verify membership/audit, and build/
deploy tested frontend repairs privately. Runtime00038/main00031/V1 unchanged.

## Exact repair gate accepted — October 12, 2026

Ray supplied final PostgreSQL output for bf77c91:498 tests in195.552s, OK,
failures0/errors0/skips0. This is user-reported gate evidence; raw persistent log
and cleanup still need independent readback. Local exact frontend Node83 passed.
Prepared scripts/build_auth_repair.sh: requires exact checkout and PASS log, stops
if PostgreSQL remains, validates previous image digest, overlays only account.js/
workspace.js, verifies preserved source library and submits build asynchronously.
Bash -n passed using installed Git Bash outside sandbox after sandbox signal-pipe
failure. No cloud build/deploy submitted by this helper yet. Chrome listed but two
attempts to attach existing Cloud Shell tab failed; terminal-paste fallback requested.
No additional activation, admin grant, IAM, public exposure or customer send.
