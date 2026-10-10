# Messaging: SMS outbox, signed callbacks, consent and acknowledgements

October 9, 2026. Claude increment for review. Local only: no cloud deployment, no
migration applied to a shared database, no real text message sent.

- **Branch:** `claude/messaging`, cut from `enterprise-v2` at `2dc5935`
- **Implementation commit:** `cfbc266`. This document is in the following commit.
- **PR:** opened from `claude/messaging` into `enterprise-v2` (link added by Ray/Codex when opened)

## What it does now

The existing organization message store (`fixture_messages`, same routes) gains:

1. **Separate delivery and acknowledgement states.** A message can ask its recipient to
   acknowledge. Acknowledgement (`message_receipts`) is recorded only when the recipient
   presses **Acknowledge** in WZOS. The text-message copy has its own status: queued,
   sending, accepted by provider, sent to carrier, delivered, undelivered, failed,
   unknown (needs review), not sent (with reason) or cancelled. Neither state implies the
   other.
2. **Member-owned SMS consent.** Only the member can turn texts on, for their own number.
   They see versioned consent wording (`CONSENT_VERSION 2026-10-09`), enter an E.164
   number, and confirm a 6-digit code sent to it. Codes are stored hashed, expire in
   10 minutes, allow 5 attempts, and are limited to 5 sends per day. The code text is
   removed from the outbox after the send attempt. Admins see each member's status with
   a masked number (`•••• 1234`) but cannot opt anyone in. Changing the number requires
   re-verification and blocks texts queued for the old number (`contact_changed`).
3. **Opt-out.** Members can turn texts off in WZOS. A signed inbound STOP-family keyword
   (or Twilio `OptOutType`) opts the number out for every organization, because carrier
   opt-out applies per sender. Provider error `21610` does the same for that
   organization. Queued texts become `blocked/opted_out`. START/UNSTOP restores only a
   previously verified number. Other inbound replies are not stored.
4. **Auditable outbox** (`sms_outbox`, `sms_events`).
   - One row per (organization, purpose, reference, recipient), so a retried
     `/api/messages` request never enqueues or sends twice.
   - Each row is claimed with a 60-second lease. The provider call happens outside the
     database transaction, then the outcome is recorded.
   - Every transition, callback and admin action writes an event.
5. **Retry and idempotency rules.**
   - Retryable: connection failures, HTTP 429 and 503. These back off (30 s × 2ⁿ) up to
     4 attempts, then fail.
   - Ambiguous: read timeouts, other 5xx responses, unexpected errors and expired leases.
     These are **never resent automatically**, because Twilio's Messages API has no
     idempotency key. An admin can mark the text failed, or resend it only after
     confirming that a duplicate is acceptable.
   - Signed callbacks still resolve ambiguous texts: provider evidence overrides an admin
     "mark failed", but never a final provider state.
6. **Signed callbacks.**
   - `X-Twilio-Signature` is checked (HMAC-SHA1 over the configured public URL and sorted
     form parameters) with a constant-time comparison. The implementation reproduces
     Twilio's documented example signature.
   - Callbacks are deduplicated, ignored if their SID doesn't match the stored SID, move
     state forward only, and are capped at 16 KB.
7. **Safe sending gates.**
   - `WZOS_SMS_MODE=disabled` (the default) blocks every text with a visible reason.
   - `test` sends only to `WZOS_SMS_TEST_RECIPIENTS`.
   - `live` is honored only in the account workspace; the synthetic preview downgrades
     it to disabled.
   - Only admins can request a text copy (provisional; see questions).
8. **Configuration readiness without secrets.** `GET /api/messaging/sms/readiness`
   (admin only) lists missing setting *names*, the mode, the number of test recipients
   and the callback URLs. It never returns values.

UI: Messaging (`team-modules.js`) now has:
- **Compose:** recipient, message, "Ask the recipient to acknowledge" and, for admins
  only, "Also send a text message copy" with the recipient's SMS status.
- **Message cards:** names, the SMS status line and the acknowledgement state, with an
  **Acknowledge** button for the recipient.
- **My text message settings:** consent, verify, turn off.
- **Text message delivery (admin):** readiness, team SMS status, recent texts with
  resolve actions, and "Send queued texts now".

All user content is rendered as text only.

## API (all organization-scoped; cross-organization targets return 404)

| Route | Who | Purpose |
|---|---|---|
| `POST /api/messages` | member/admin | Adds optional `request_acknowledgement`, `sms_copy` (admin only; 403 otherwise). Response adds `acknowledgement_requested`, `sms`. Retry identifier conflicts now also compare these flags. |
| `GET /api/messages` | member/admin | Items add `acknowledgement_requested`, `acknowledged_at`, and `sms` (sender only). `external_delivery` now reflects SMS readiness. |
| `POST /api/messages/{id}/acknowledge` | recipient | Idempotent; returns the first acknowledgement time. |
| `GET/PUT /api/messaging/sms/contact` | self | Status + consent text / record consent and request a code (`request_id`, `expected_version`, `phone`, `consent`, `consent_version`). |
| `POST /api/messaging/sms/contact/verify` | self | `{code}`. |
| `POST /api/messaging/sms/contact/opt-out` | self | `{expected_version}`. |
| `GET /api/messaging/sms/contacts` | admin | Team status, masked numbers. |
| `GET /api/messaging/sms/readiness` | admin | Configuration names only. |
| `GET /api/messaging/sms/outbox`, `/{id}/events` | admin | Paged delivery history and audit events. |
| `POST /api/messaging/sms/outbox/{id}/resolve` | admin | `retry` (ambiguous requires `confirm_possible_duplicate`), `mark_failed`, `cancel`. |
| `POST /api/messaging/sms/process` | admin | Processes due texts for the admin's organization. |
| `POST /api/messaging/twilio/status?outbox=…`, `POST /api/messaging/twilio/inbound` | Twilio (signed) | No session; signature required. |

**Interface for Enterprise dispatch:** `app.state.messaging.enqueue(db, organization_id=…,
recipient_id=…, body=…, purpose='dispatch', reference_id=<assignment revision id>,
actor_id=…)` inside the approval transaction, then `process(org, [ids])` after commit.

## Schema (startup DDL, needs review)

Four additive tables: `message_receipts`, `sms_contacts`, `sms_outbox`, `sms_events`. The
reviewable SQL is in [migrations/20261009_messaging_sms.sql](migrations/20261009_messaging_sms.sql).
No existing table or column changes. Deploying this code applies the migration. Rollback
means deploying the previous code: the tables are then ignored and keep consent and
opt-out history, so don't drop them without a retention decision. Messages sent before
this change have no receipt row; they still display, but can't be acknowledged.

## Changed files

- `services/workspace_preview/messaging.py` (new): consent, outbox, processing, callbacks, routes
- `services/workspace_preview/sms_provider.py` (new): Twilio REST transport via the existing `httpx` dependency, signatures, configuration names
- `services/workspace_preview/team_modules.py`: message model/routes extended, registers messaging
- `services/workspace_preview/static/team-modules.js`: Messaging view
- `tests/test_messaging.py` (new), `docs/migrations/20261009_messaging_sms.sql` (new), this document

**Shared files:** none. `app.py`, `index.html`, CSS and the account/auth code are unchanged.
Checkbox sizing uses CSSOM styles inside the module script, so no CSP change is needed.

## Validation (actual results)

- Baseline on `2dc5935` before the change: Python 336 tests OK, 67 skipped (PostgreSQL);
  Node 21/21.
- `tests.test_messaging`: 19 SQLite/provider tests pass. A further 16 PostgreSQL cases
  (`PostgreSQLMessagingTests`) are **skipped** because no `WZOS_TEST_DATABASE_URL` was
  available. Coverage:
  - consent/verification, attempt/expiry/daily limits;
  - admin-only text copies;
  - not-enabled, disabled-mode and outside-test-list blocking;
  - send-once retries;
  - signature rejection, callback ordering/deduplication/SID mismatch;
  - retry backoff and exhaustion, ambiguous handling and confirmation, lease expiry;
  - STOP/START and provider `21610`;
  - member opt-out, number change, cancel/retry;
  - acknowledgement separation, member/admin and cross-organization boundaries;
  - Twilio request shape and outcome mapping;
  - Twilio's documented signature example.
- Full suite after the change: **Python 372 tests OK, 83 skipped** (67 existing + 16 new
  PostgreSQL cases); **Node 21/21 pass**; `node --check` passes on `team-modules.js`.
- Browser (local synthetic preview, fake provider, no network sends):
  - Member enrolled `+15550100001`, received the code through the fake provider log and
    verified.
  - Admin sent a message with acknowledgement and SMS copy and saw "Accepted by
    provider".
  - A signed synthetic `delivered` callback returned 204 and a forged one 403.
  - At 375×812 the member saw no SMS or delivery controls and acknowledged.
  - Admin desktop showed "Delivered to phone" and "Acknowledged …" as separate lines,
    plus masked team status.
  - Two defects found during this run were fixed and rechecked: the checkbox width/form
    styling and the settings panel collapsing while a code was pending.
  - Screenshots are outside Git at `C:\Users\MolecularDev\claude-WZOS-2.0\evidence\messaging\`.
- **Not run:** PostgreSQL suite, private-GCS, a real Twilio account, real phones, and
  hosted/Cloud Run behavior.

## Integration notes for Codex

- **PostgreSQL gate:** run `tests.test_messaging.PostgreSQLMessagingTests` with
  `WZOS_TEST_DATABASE_URL` against a disposable schema.
- **Configuration (Secret Manager/env):**
  - `WZOS_SMS_MODE`, `WZOS_TWILIO_ACCOUNT_SID`, `WZOS_TWILIO_AUTH_TOKEN` (secret),
    `WZOS_TWILIO_MESSAGING_SERVICE_SID` or `WZOS_TWILIO_FROM_NUMBER`,
    `WZOS_PUBLIC_BASE_URL` (https, exactly the host Twilio calls), and
    `WZOS_SMS_TEST_RECIPIENTS` for test mode.
  - Point the Twilio number or messaging service inbound webhook at
    `<base>/api/messaging/twilio/inbound`.
- **Reachability:** the two Twilio routes must be reachable without Cloud Run IAM or the
  restricted-preview proxy. That is a deployment decision; the routes authenticate by
  signature only.
- **Background processing:** sends run in FastAPI background tasks after the response.
  On Cloud Run that needs CPU after the response, or a scheduled authenticated call to
  `POST /api/messaging/sms/process`. A system-wide processor endpoint for a scheduler is
  not added yet.
- **Atlas help (optional):** suggested wording is "Text copies are optional; members
  turn them on for their own number. Delivery and acknowledgement are shown separately."
  Codex decides placement.

## Remaining gaps

- **MMS is not exposed.** Private files must not become permanent public media URLs.
  Needs a Codex-owned short-lived signed media URL interface on the private file store;
  the provider layer can add `MediaUrl` once that exists.
- **Provider not exercised for real:** Twilio account, A2P 10DLC/toll-free registration,
  messaging service and sender number are unverified. No controlled live test has been
  run.
- **Ambiguous texts:** there is no automatic provider lookup to reconcile them. Admins
  decide with the confirmation prompt.
- **Notification preferences** beyond SMS on/off, unread counts and push notifications are
  not built.
- **Retention:** retention and export of message, consent and delivery records are
  undefined.
- **Data consistency:** `sms_contacts.phone` is separate from Codex's
  `employee_profiles.phone`, which that contract says is not verified or consented. A
  future UI could suggest the profile number for the member to confirm.

## Product questions for Ray (provisional behavior in brackets)

1. Can members send text copies to coworkers? [No: admins only.]
2. Should SMS copies be available in Core as well as Enterprise? [Yes: both editions;
   only dispatch is Enterprise-only.]
3. Should texts carry the full message (up to 600 characters) or only a notice to open
   WZOS? [Full text, plus a STOP footer.]
4. Should one sender (number or messaging service) serve all organizations, or should
   each organization register its own? [One platform sender; STOP applies across
   organizations.]
5. Should replying YES by text count as acknowledgement? [No: in-app only. Twilio also
   treats YES as an opt-in keyword.]
6. What are the retention periods for consent, opt-out, delivery events and message
   bodies? [Kept indefinitely.]
