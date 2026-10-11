# Twilio staging connection — October 11, 2026

## Actual checkpoint

Secret Manager contains enabled version 1 of:

- `wzos-v2-twilio-account-sid`
- `wzos-v2-twilio-auth-token`
- `wzos-v2-twilio-from-number`

Values were inspected only in process memory; no values are recorded here.
The SID has the expected format and the token is nonempty. This does not prove
provider authentication. The sending-number value fails the international-number
format check. Ray has been asked to add a new version containing the Twilio-owned
sender in E.164 format. No provider request or message was sent.

The staging runtime currently lacks access to these three secrets. No new IAM
grant, callback deployment, or account-service traffic change was made in this
increment. V1 and public DNS remain unchanged.

## Implemented locally

`services/workspace_preview/twilio_gateway.py` provides a separate callback
application. It exposes only health and the existing status/inbound POST paths.
It verifies the signature against a configured public origin, query and all form
fields, checks the account SID, and forwards a valid request to a configured
private Cloud Run origin using an IAM identity token. Client forwarding headers
cannot choose the signature origin or upstream. Payloads are bounded to 16 KiB
and 256 fields. Redirects, general proxying and message-send endpoints are absent.
Errors do not expose credentials, upstream response bodies or cookies.

The private application retains its existing signature verification and
idempotent status/opt-out processing. Signature construction follows
[Twilio's security documentation](https://www.twilio.com/docs/usage/security).
No database schema, dependency or existing module behavior changed.

## Proposed access and deployment scope — not applied

1. Give `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`
   `roles/secretmanager.secretAccessor` on only the three named secret resources.
2. Use a separate callback runtime identity. Give it access only to the SID/token
   secrets and `roles/run.invoker` on `wzos-v2-accounts`, with no database or storage
   permissions.
3. Deploy the callback application separately with zero minimum instances and
   one maximum instance. Only that signature-gated service needs public ingress;
   the accounts service remains IAM-restricted.
4. Configure matching `WZOS_PUBLIC_BASE_URL` values on both services, a pinned
   `WZOS_TWILIO_PRIVATE_UPSTREAM`, and version-pinned secret bindings. Keep SMS
   disabled until live callback checks pass; then use test mode and the authorized
   recipient allowlist.

Obtain action-time approval for these scoped IAM grants and public callback
exposure after preparing the exact deployment commands. Do not enable broad
project-level secret access or make the workspace public.

Rollback: disable SMS first; remove the callback service's public invoker binding
and stop/delete that service; remove its private-service invoker and secret
bindings; restore the account-service configuration captured before this change.
Remove only bindings introduced by this increment. Never delete secret versions
or roll back database contents as part of callback rollback.

## Validation

- Gateway focused suite: 11 tests passed after final changes.
- Full local Python gate: 476 tests, zero failures/errors, 126 PostgreSQL-dependent
  skips. This is not a full PostgreSQL acceptance result for the new candidate.
- Full Node suite: 47 passed, zero failures/skips.
- Previously deployed frozen application `cf35780`: 465 PostgreSQL tests passed
  with zero skips. Its acceptance does not substitute for the new candidate gate.

Pending: corrected sender format; read-only Twilio account authentication and
sender ownership/SMS-capability checks; full candidate PostgreSQL gate; scoped
permissions/deployment approval; unsigned/tampered rejection and signed callback
acceptance against the live private backend; one authorized test send and delivery
receipt/opt-out verification. Twilio is not yet accepted as connected.

The approved development cap remains $150 for October 8–17. Ray's approximately
$35 billing report is not an independently reconciled total. Refresh actual
spending before additional paid deployment/tests; retain scale-to-zero and
bounded instances. Separate provider messaging charges must be recorded.
