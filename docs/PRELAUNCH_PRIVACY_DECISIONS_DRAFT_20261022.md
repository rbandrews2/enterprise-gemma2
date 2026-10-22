# Data handling and customer terms — product review draft

This is an engineering draft for Ray's approval, not published customer terms.
Do not publish unchosen retention periods, provider guarantees or compliance claims.

## Verified implementation to explain clearly

- Reports and signatures: WZOS stores the report explicitly sent to office, its
  signature if supplied, organization, submitter/reviewer, revisions and audit
  metadata. Opening a report is separate from marking it reviewed.
- Smart Field Voice: recording/transcription is initiated by the worker. Audio is
  sent to Google Speech and the transcript to the configured private Atlas model.
  WZOS processes audio/transcripts transiently; only explicitly saved structured
  drafts and reviewed submissions are persisted. Provider processing/retention must
  be covered by the applicable provider terms; do not promise zero provider retention
  solely because WZOS does not save raw audio.
- Location: the browser controls permission. Setup itself does not start tracking.
  Feature use may obtain location for weather, routes or time records; any saved
  time/location evidence and offline estimates need accurate disclosure. Do not
  promise that browser prompts can never recur.
- Messaging: mobile numbers require consent and verification. Receipt status
  distinguishes provider/carrier acceptance from confirmed delivery. Opt-out is
  preserved after downgrade. Verification codes must not appear in normal stored
  message content or audit views. Replies are not a monitored conversation service.
- Video: Daily handles authorized embedded calls. Recording/transcription are off
  in the current integration; actual two-device media acceptance remains open.
- Integration credentials: read-only orders/schedule scopes, expiry, revocation,
  hashed secret storage and audit/rate controls exist. QuickBooks and Workday are
  not completed connectors and must not be advertised as supported integrations.

## Decisions needed from Product before publication

| Decision | Status / next step |
| --- | --- |
| Report, signature and review-audit retention | Choose retention period and any customer contract requirements; no period selected here. |
| Location/time-record retention | Choose period and authorized viewer roles; retain necessary payroll/contract records under the applicable policy. |
| Media/link handling | Confirm rights language, provider terms and privacy disclosures. |
| Account closure/export/deletion | Choose process, timing, retention exceptions and responsible owner before engineering implements any missing automation. |
| Backup retention and deletion lag | Approve based on actual SQL and object-storage protection; database backup does not contain uploaded object bytes. |
| Support and incident contact | Confirm monitored email/contact, named owner and availability; app footer phone is 844-685-7207. |
| Billing/cancellation/refunds/tax | Approve the existing offer and contract wording, including the established-Core one-time $20 upgrade credit. |
| Subprocessors and processing regions | Confirm Google, Daily, Twilio/Stripe terms and actual active configuration before final notices. |

## Engineering follow-through after decisions

Publish approved notices in onboarding/support/account flows, implement any missing
retention/export/deletion controls, test tenant isolation and preserve mandatory
audit/rollback behavior. Encryption/IAM controls and passing security tests are
evidence of specific safeguards; neither establishes SOC2 certification or a
guarantee against malware, compromise or incorrect AI output.

## Short remaining field checks prepared for the user

1. Phone: draw/clear/type a signature and inspect its actual PDF; record one field
   report, edit/review it and verify its receipt and admin notification.
2. Two consenting devices: meeting audio/video, reconnect, then Leave stops media.
3. Consenting phones: one admin SMS, delivery receipt and opt-out behavior.
4. Authorized billing acceptance: customer-confirmed live purchase/upgrade and tax;
   agree any actual charge before testing. No charge is authorized by this draft.
5. Name support/incident/restore/budget-alert owners and approve the selected terms.
