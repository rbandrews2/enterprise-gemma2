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
