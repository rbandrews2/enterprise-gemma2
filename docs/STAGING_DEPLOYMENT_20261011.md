# Restricted staging deployment — October 11, 2026

## Accepted

Frozen application cf357802f6d979667225ebb0eed3ce5cea19d826 passed the
previous exact PostgreSQL gate (465 tests, no failures/errors/skips) and Node
regression (47 passed). Read-only live schema comparison found no incompatible
existing columns. Reviewed additive startup tables were deployed; no manual
destructive migration was performed. Backup 1791698400000 succeeded.

The 80 MB ZIP upload stalled and was cancelled. Build instead inherited preserved
source binaries from the immutable rollback image and copied exact candidate code
from Git archive. Extracted application permissions were repaired for the non-root
runtime after failed builds. Source-file hashes, SQLite integrity and the exact
frozen snapshot hash passed in successful build
019b8eed-bcda-4e03-b2a5-8d2f025c8654.

New image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:db768fa05d2320c5cc0e6c345ace622f46605600aede855d4d77694f9f4df93f`

Snapshot SHA256:
`070ec5e461a56fbdf60ad81c0b91a699e87316d500af7dc6245b94e81a3dcd4`.

Revision wzos-v2-accounts-00031-h5t was deployed without traffic, tested through
an IAM-protected tag, then promoted to 100% restricted staging traffic. Runtime
identity, environment, resources, revision annotations and IAM bindings matched
the saved configuration before the subsequent Maps change. Anonymous access
returned 403; IAM-authenticated configuration returned 200; IAM alone could not
access an app session (401); sign-in HTML returned 200.

Real-provider acceptance passed sign-in, refresh, verified-email enforcement,
admin/member restrictions, cross-organization denial and last-admin protection.
Synthetic users were disabled, tokens revoked and organizations disabled. Both
temporary SQL proxies stopped; port 5544 had no listener after acceptance.

The protected mobile proxy returned HTTP 200 and the browser rendered managed
sign-in with persistent-session and passkey options. The existing synthetic admin
signed in and reached organization selection. Full module/device acceptance is
separate. Preview lifetime is 45 minutes without automatic restart. Screenshot is
ignored at `.local-data/mobile-staging-20261011.jpg`.

## Maps: configured candidate, acceptance pending

Existing WZOS V2 Browser Maps key and enabled Maps JavaScript API were found.
Ray approved adding exactly
`https://8080-cs-1002772085547-default.cs-us-east1-pkhd.cloudshell.dev/*`.
Existing localhost/127.0.0.1 port 8081 and app.workzoneos.org restrictions remain;
API restriction remains maps-backend.googleapis.com. No key value was printed
or committed.

The existing browser key was bound through an environment-only update. Revision
wzos-v2-accounts-00032-9rw was deployed with zero main traffic; the private
release-cf35780 tag points to it. Last verified main traffic is still 100% on
00031-h5t. Next verify exact environment delta, IAM, authenticated Maps config,
CSP and actual map/Street View rendering before promoting 00032.

## Provider setup and recovery point

Inspected Secret Manager metadata listed GOOGLE_MAPS_API_KEY and staging
authentication/database secrets; no Twilio/SendGrid secret names were found.
Ray will enter credentials himself in the official Secret Manager console:

- wzos-v2-twilio-account-sid
- wzos-v2-twilio-auth-token
- wzos-v2-twilio-messaging-service-sid OR wzos-v2-twilio-from-number

Controlled email/phone test recipients were authorized in chat; keep their private
details out of Git. Read secret metadata only after entry. New runtime secret-access
IAM grants require the applicable confirmation. Twilio needs a signed HTTPS status
callback reachable without exposing the whole private account service. SendGrid
has no active delivery adapter in the inspected Python code and needs its own
API key and verified sender if selected. Google Meet automatic creation needs
organizer OAuth; existing external links are a separate capability.

Browser control timed out twice while opening Secret Manager. The official
create-secret page was queued in the Codex panel and linked for direct user entry.
Do not read or capture credential-entry fields. Resume with secret metadata,
Maps acceptance, private-file/module checks, callbacks/delivery and bounded Atlas
acceptance. Durable completed forms/signatures/attachments and closed-app push
remain open; menus alone do not establish feature completion.

Private cloud evidence is under `/home/admin_/wzos-release-20261011`; schema evidence
is under `/home/admin_/wzos-schema-20261011.iinTcucv`. Keep these outside Git.

## Budget, production and rollback

Development cap remains $150 for October 8–17. Ray reports approximately $35 billed,
leaving about $115 planning headroom subject to lag, not an independently reconciled
ledger. No GPU or new infrastructure was provisioned. Reconcile costs before
further paid tests.

Ray now requests V1 replacement after acceptance. app.workzoneos.org currently
reaches gemma-assistant-api through gemma-assistant-api-neg and the IAP-enabled
gemma-assistant-api-backend load balancer. No V1 backend, DNS or production traffic
was changed. Provider/workflow/security gates, production passkey origin and
reviewable routing rollback precede cutover.

Staging rollback: route 100% to wzos-v2-accounts-00030-c6h. Its immutable image is
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:13cb755a8973dc9923c76ea4eed229a57b16ba357db2f19178ea8ca953222284`.
Additive tables remain after code rollback; do not drop them. Reverting Maps removes
only the new staging referrer/browser-key binding and preserves prior settings.
