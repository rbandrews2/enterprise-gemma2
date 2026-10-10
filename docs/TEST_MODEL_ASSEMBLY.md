# Operational test-model assembly

Updated October 10, 2026. Candidate: `codex/preproduction-modules` in the owned
`integration-release` checkout. This document supersedes older module availability
summaries; it does not declare production readiness.

## Assembled internal workflows

| Area | Available in the candidate | Remaining integration |
|---|---|---|
| Accounts | Google-backed identity interfaces, organizations, invitations, admin/member roles, employee profiles, qualifications and availability | Real recovery/invitation delivery, entitlement lifecycle and broad user acceptance |
| Work orders | Saved versioned drafts, job details and measured geometry | Assigned employee access to appropriate job documents without exposing private drafts |
| Dispatch | Enterprise admin proposals, eligibility/conflict checks, approval, frozen assignment details, in-app notifications, My jobs and explicit confirmation | Closed-app push delivery and cancellation/change notification experience |
| Time Clock | Own shifts/breaks/tasks, timesheets, CSV, admin corrections, offline draft review; dispatched jobs now selectable | Exact-candidate PostgreSQL/cloud and field/offline acceptance |
| Forms | Team library/uploads, printable templates, persisted incident/DVIR/JSA drafts, immutable internal submissions and admin review | Durable completed printable forms, attachments/signatures and approved external delivery |
| Schedule | Admin schedule management, assignments and conflict checks | Unified calendar display of dispatched jobs and meeting changes |
| Navigation | Address/coordinate navigation links, assigned destination list and limited saved destination notes | Real Maps imagery and field/offline acceptance |
| Messaging | Organization-scoped stored messages, Twilio adapter/outbox, consent/verification and status handling | Actual provider configuration and controlled delivery acceptance |
| Meetings | Google Meet link scheduling; admins manage, members join | Organizer OAuth and automatic meeting creation; Google Meet remains external |
| Training | Admin content/assignment management, member progress and assessments; separate study/qualification review | Reviewed playable media and end-to-end qualification policy acceptance |
| Atlas/report | Source retrieval, module guidance, draft recommendations, geometry/imagery interfaces, saved report PDF | Reviewed source applicability, connected imagery and reliable live inference/report delivery |

## Next assembly passes, in order

1. Complete assigned-job integration across own forms and
   schedule display. Keep an explicit read/write permission contract for each
   connection; a dispatched summary must not unlock private originals.
2. Complete durable form instances, attachments and signatures, with revisioned
   submissions/private exports; reuse existing storage and form APIs.
3. Complete assignment update/cancellation and in-app notification behavior;
   implement a provider-neutral closed-app push subscription/delivery contract.
4. Run complete internal admin/member and Core/Enterprise scenarios across two
   organizations; fix failures and document actual unavailable functions.
5. Connect providers and run controlled integration tests as the next phase.
6. Run the restricted pilot, restore/rollback/security/load checks and resolve
   the production checklist before requesting cutover approval.

## Provider connection phase

Use Google Secret Manager/runtime identity and existing adapters. Audit credential
**metadata** first; neither a code binding nor an old inventory proves a usable key.
Never put keys in Git or chat. Synthetic adapters are local test tools and must
not appear as successful real delivery, imagery, inference or meeting creation.

- Twilio: account/API credentials, approved sender or Messaging Service,
  verification/consent, signed callbacks, bounded retries and test recipients.
- Maps: existing restricted V2 browser key, enabled APIs, exact staging origins,
  imagery usage/attribution and server credentials where required.
- Google Meet: organizer OAuth client, redirect URI/scopes and organization setup.
- Authentication/email: authorized domains, recovery/verification/invitation sender.
- Atlas: private inference URL, runtime invoker IAM and bounded capacity/cost.
- Push: application-server credentials, private tenant/user subscriptions, opt-in,
  service worker, revocation and real-phone delivery checks.

## Evidence and release boundaries

The previous full candidate passed450 Python tests with122 PostgreSQL skips, and
42 Node tests. Those results predate assigned-job Time Clock changes. The prior
444-test zero-skip PostgreSQL run predates the My jobs increment. Neither is an
exact-candidate database acceptance result for this new increment.

Current focused Python regression:66 tests,36 passed,30 PostgreSQL skips,
zero failures/errors (211.147s). Current full Node suite:44 passed,zero failures
or skips. Synthetic member browser clock-in/clock-out/timesheet and dispatched
Navigation destination passed. The browser used seeded example assignments;
the API tests exercised actual approval and permission enforcement.

Navigation deduplicates upcoming assigned destinations by job, preferring the
frozen dispatched address. Its in-memory offline cache is account/organization/
edition scoped; cached destinations are explicitly unverified. It does not store
map tiles or provide WZOS turn-by-turn routing. New tests cover late responses,
organization switches and Core access. Browser evidence is ignored locally at
`.local-data/assigned-time-preview.jpg` and `assigned-navigation-preview.jpg`.
No new schema or provider provisioning is required for this link. Exact-candidate
full Python/PostgreSQL and real-device acceptance remain required before merge
or shared staging deployment. V1, public DNS and production remain unchanged.
