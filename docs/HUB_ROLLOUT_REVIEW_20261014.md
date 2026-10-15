# Hub rollout review

## Updated container and budget gates

OS repair build76510b57-38b2-48fd-8bf8-9a990cd23df7 SUCCESS; use digest
fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06,
not the superseded4cc2f391 candidate. Runtime source remains5a3ac86. Read
HUB_CONTAINER_REVIEW_20261014.md for available fixes and residual findings.
Final repaired-image scan is required before rollout.

Google Billing now independently viewed after reauthentication and browser
recovery: Projects – this month shows enterprise-gemma2 subtotal USD21.79 for
October1–14, gross USD23.34 and USD1.54 savings. This is reported month-to-date
usage, subject to billing delay, not a real-time total or the remaining10-day
allowance. It is within the authorized USD150 October8–17 development budget.
Existing USD50 notification was inspected and left unchanged; it is not a cap.
No new standing infrastructure/GPU, capacity expansion or customer sends.
Private screenshot .local-data/hub-evidence/billing-project.png; Cloud Shell
budget-review.txt retains the numeric checkpoint. Earlier billing-blocked note
below is historical.

## October 14 rollout authorization and preflight

Ray replied "all approved let's go" to the remaining scan/schema/backup/budget
and public API activation review. This authorizes the bounded on-demand image
scan and this documented rollout, including admin-issued scoped read-only keys.
No real key issuance, customer export, SMS, media call or model call is needed.
Google On-Demand Scanning was enabled for one explicit image scan; automatic
registry scanning was not enabled. Record actual findings before deployment.

Fresh read-only live schema comparison: no incompatible existing columns.
Six hub tables are absent as expected. Static extraction also reports two
inactive purchase tables; app.py does not import/mount Purchases, so they are
not part of this migration. Fresh SQL backup1792027808755 is SUCCESSFUL.
Billing report requires Google account verification; current spending is not
independently verified yet. Existing budget notification remains USD50; it is
an alert threshold, not a spend cap. User-authorized development limit remains
USD150 for October8–17. Do not silently relabel the notification as that limit.

Release-only helpers: deploy_organization_hub.sh preserves full runtime spec
except image and verifies the zero-traffic candidate. cutover_organization_hub.sh
checks exact static hashes, access/origin/Google auth boundaries and restores
the prior Daily revision if a public gate fails. Runtime image/source unchanged.

## Application change

Release source5a3ac868085685a5e71169ceac21fa618cc405e9 adds the organization admin
landing page, notes and shortcut preferences, corrected security headers, patched
FastAPI/Starlette dependencies and a scoped read-only integration API. The earlier
650aa5a source is superseded by the invalid-key lock-contention repair. Exact
final cloud PostgreSQL596 PASS/no failures/errors/skips; existing Node96 PASS.

## Security-sensitive activation to review before public rollout

Organization admins would gain the ability to issue up to10 active API credentials
per organization, scoped to orders:read and/or schedule:read, lasting1–90 days
(default30). Each key can read the selected organization's projected job addresses
and schedule details through the server API. No member can issue these credentials.
Keys cannot authenticate app sessions, edit records or read another organization.
Creator demotion/removal, organization deactivation, expiry and revocation disable
access; unknown credentials are rejected without the shared write lock. Tokens are
shown once and stored hashed. No external connector, credential or customer export
is created merely by deploying this code.

Browser-control policy requires applicable confirmation at the action that makes
these new access paths public. This document and a successful build are not that
confirmation. Keep live traffic unchanged until rollout is authorized.

## Schema, configuration and safety gates

Deployment applies six additive startup tables and one index in
scripts/organization_hub_schema_review.sql. Old records are not altered/deleted.
Review current live schema, create/confirm a fresh successful SQL backup, and record
remaining budget before deploying even a zero-traffic revision (startup executes DDL).
Image dependencies must match the patched inventory; verify source-library hashes,
non-root UID, image package audit and OS-image coverage separately. No Python audit
alone establishes malware-free uploads or SOC2 compliance.

Preserve existing environment/secrets, service identity, ingress/invoker policy,
resource limits, concurrency, timeouts, Daily policies and Maps origins. No new
IAM grant, DNS change or runtime secret is needed for the hub. Twilio stays in its
existing restricted mode; no SMS/Meet/media/model/customer test sends occur.

## Proposed release sequence

1. Resolve image build/audit gates and save immutable digest and complete evidence.
2. Complete current backup/schema/budget review and applicable activation approval.
3. Deploy the digest to the existing accounts service with zero traffic; compare
   configuration to the saved before-service snapshot and verify ready status.
4. Shift traffic only after reviewing the candidate. Public checks: root and new
   static assets match the exact source; anonymous dashboard/key-management/export
   requests401, untrusted origin403, direct run.app access still blocked; existing
   authentication, Maps and Daily policy paths retained.
5. Real admin/member/Core/Enterprise and mobile dashboard acceptance with Ray;
   record actual feature gaps (billing/security status feeds default amber,
   vendor-specific connectors, malware scanning, prior deferred integrations).

## Rollback

Route traffic to the saved prior Daily revision. Retain additive tables and audit
records. Revoke any newly issued API credentials before retiring API support, and
review keys before any later restoration. Old runtime restores known dependency
advisory exposure: prefer a tested forward fix; document emergency rollback reason
and duration. Never discard source documents or customer records to roll back UI.
