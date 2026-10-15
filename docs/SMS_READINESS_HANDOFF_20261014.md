# One-way SMS access readiness — October 14, 2026

Branch: `codex/preproduction-modules`; this increment is not separately deployed.

## Reviewed behavior and repaired gap

The backend already supports admin-sent organization messages with optional
one-way SMS notification copies to a member or admin. Each recipient must opt in
and verify their own number. Provider acceptance, carrier delivery and in-app
acknowledgement remain separate. Test mode and its phone allowlist are retained;
members cannot initiate an SMS copy. Unknown send outcomes require explicit
duplicate-risk acknowledgement before an administrator retries them.

The outbox previously checked current consent/number at send time but did not
recheck organization access after queueing. A delayed retry could therefore send
to a former member or on behalf of a demoted administrator.

`Messaging.blocker()` now checks the recipient's active membership and active
organization in an account workspace, for verification and ordinary messages.
For ordinary notifications it additionally checks that the original sender is
still an active organization administrator. Reasons are returned as
`recipient_inactive` or `sender_inactive`, with user-readable explanations.
Synthetic preview mode remains compatible. Access is checked when claiming a
queued send; this does not cancel a message already handed to the provider.

## Files and schema

- `services/workspace_preview/messaging.py`: claim/enqueue access checks and reasons.
- `tests/test_messaging.py`: three real-account SQLite tests and three equivalent
  PostgreSQL cases inherited through `PostgreSQLAccountSMSAccessTests`.
- This handoff. No DDL, migration, new dependency, secret or configuration change.

## Validation and integration

New SQLite account regressions: **3 passed**, 5.288 seconds. They exercise revoked
recipient access, sender demotion, and organization deactivation while a
verification code is queued, including removal of its stored send secret.
All tests use synthetic identities/phones and a fake provider; no real sends.
Existing messaging/Twilio mock-transport regressions: **21 passed**, 24.221 seconds.
`git diff --check` passed for this increment.

Run the full integrated Python/Node suites and native PostgreSQL gate before
release. PostgreSQL-specific cases have not been run locally. Apply existing
config-preserving build/deploy gates; no activation of live customer texting is
included. Rollback is code-only and retains existing outbox/audit records.

## Remaining acceptance

The next useful SMS step is the controlled consenting-device flow: opt-in,
verification, one administrator notification, carrier callback delivery, STOP
handling and in-app acknowledgement. It requires an approved sender registration
and matching signed callback setup. This review did not inspect current cloud
credentials/provider configuration or send any SMS. Existing live test-mode
restrictions must remain until that acceptance is complete.
