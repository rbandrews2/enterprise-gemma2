# In-app assignments and navigation

Implemented in the owned `codex/preproduction-modules` candidate, October 10.
Ray's Traffio screenshots informed the workflow; no employer records, contact
details or screenshots were copied into test data or Git.

## Workflow

1. Enterprise admin opens Messaging / Dispatch, selects a saved work order and
   enters staffing needs, start, estimated finish, client company, point of
   contact, contact phone and dispatcher notes. Notes are explicitly employee-visible.
2. Admin reviews the proposal and approves. Existing eligibility, stale-version
   and conflict checks still run before assignment creation.
3. WZOS saves each assignment and its in-app message atomically. Optional SMS
   remains an additional existing consent-controlled channel, never the only record.
4. While WZOS is open and visible, a notification badge and status banner check
   pending confirmations every 30 seconds, on organization selection and reconnect.
5. Employee opens **My jobs**, chooses Coming up, Finished / cancelled or All jobs,
   opens a job and reviews location, times, client contact, crew and instructions.
6. **Confirm receipt** saves the response, acknowledges the dispatch message,
   clears that assignment's pending badge and exposes the timestamp to the admin.
   Opening a job alone does not confirm it. Existing Decline remains available.

Assignments and counts are scoped to the signed-in user AND organization. Admins
and members can view/confirm their own assignments. Only Enterprise admins can
create dispatch plans; Core navigation remains available. Admins see team responses
in the existing approved plan. Declined/cancelled/replaced or past-end assignments
are in Finished / cancelled; this is a time/status grouping, not proof work finished.

## Navigation

**Open in Navigation** is available in work-order cards, selected job details,
assignment details and the Navigation module for both roles. It uses Google's
[documented cross-platform Maps directions URL](https://developers.google.com/maps/documentation/urls/get-started),
with encoded destination, driving mode and `dir_action=navigate`. No API key or
automatic device-location read is needed. Maps may show a route preview rather
than turn-by-turn guidance depending on device/location availability. The user
initiates the external navigation link.

## Storage and compatibility

No new tables/startup DDL. New client fields live in the validated requirements
JSON. Approval freezes employee-visible job/client/crew/notes in the existing plan
JSON. Later edits do not rewrite an already-dispatched assignment. Names and job
roles are included; home addresses, employee phone numbers, qualification records
and override explanations are excluded. Historical plans without a snapshot are
explicitly labelled; missing crew/contact data is not invented.

API additions: `GET /api/dispatch/notifications` returns the user's pending count;
`GET /api/dispatch/my-assignments` now returns snapshot details, total/limit/offset,
pending count and optional validated `phase=all|upcoming|finished`; 25 per page.
Existing authenticated response endpoint remains idempotent and rejects replies
by another user or to cancelled/replaced assignments. Rollback to prior code
retains JSON metadata, though older approval code won't create new snapshots.

## Acceptance and remaining gates

- Focused dispatch: 34 tests, 17 passed, 17 PostgreSQL skips, zero failures/errors.
- Full Node: 42 passed, zero failures/skips. New cases cover detail rendering,
  explicit receipt, role visibility, explicit unknown/retry states and safe address/coordinate URL construction.
- Local synthetic member browser passed sign-in, badge1, jobs list, all details,
  receipt confirmation and badge0. Browser displayed a server confirmation time.
- Screenshot: ignored `.local-data/assignment-member-preview.jpg`; synthetic only.
  Requested390px viewport actually reported733px; document width718, no horizontal
  overflow at that actual width. Real-phone390px acceptance remains open.
- Full Python regression passed450 tests in845.845s:328 passed,122 PostgreSQL
  skips, zero failures/errors. Evidence: `.local-data/assignment-full-python.log`.
- Receipt confirmation and badge0 survived reload and fresh synthetic sign-in.
  Refresh/pagination errors and unavailable notification checks are visible; failed
  initial checks remain unknown rather than falsely showing zero assignments.
- Navigation tests also reject over2048-character encoded Maps URLs and malformed
  Unicode safely. No destination is silently truncated.
- This increment's PostgreSQL/cloud deployment acceptance remains pending. Earlier
 444-pass PostgreSQL gate predates this increment and is not its acceptance.
  Chrome tab discovery worked, but accessibility/CDP control failed on repeated
  attempts; no database command for this increment was submitted.

The assignment brief does not expand editing access to the original work order,
private reports or files. Connecting assigned-job access for other modules needs
a separately reviewed read/write authorization contract; do not bypass existing
private-draft rules as a shortcut.

### Must complete before launch

Closed-app/background device push is **not implemented** by an in-app polling
badge. Configure a push provider, permission/opt-in flow, private subscription
storage, service worker, retry/expiry handling and real Android/iOS acceptance.
Until then employees see durable notifications when they open/return to WZOS;
consented SMS is an optional separate channel. Do not claim push delivery, offline
confirmation, or job completion from these tests. No customer texts or provider
calls were sent in this increment; backend tests use a fake provider.

Restart the ignored synthetic preview with `.local-data/assignment_browser_fixture.py
--role member --port 8083` (repo virtualenv). This seeds example assignments directly
for UI testing; it does not prove end-to-end admin proposal generation. Backend
tests exercise the actual proposal/approval/response workflow.
