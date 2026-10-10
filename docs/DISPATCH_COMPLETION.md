# Enterprise dispatch: staffing requirements, reviewed proposals, approved sending

October 9, 2026. Claude increment for review. Local synthetic testing only. No cloud
deployment, no migration on a shared database, and no real messages.

- **Branch:** `claude/dispatch`. It is **stacked** on two unmerged branches:
  `codex/integration-release` at `abae32e` (Codex's employee/qualification/availability
  contract) and `claude/messaging` at `99125c9` (merged in as `24ab01d`). It contains
  `enterprise-v2` at `2dc5935`.
- **Commit:** the branch head.
- **PR:** open into `enterprise-v2` only **after** both bases merge; rebase then, and
  the diff reduces to this module. Until then, review with
  `git diff 24ab01d..claude/dispatch`.

I stacked the branch because the collaboration contract says to cut from
`enterprise-v2`, but `enterprise-v2` doesn't yet contain the employee contract that
dispatch must use. Building against it avoids a competing employee directory.

## What it does now

Dispatch lives in **Messaging** for Enterprise organizations, per
`ENTERPRISE_DISPATCH.md` ("Messaging / Dispatch"). Core organizations see nothing new,
and every dispatch API returns 403 for Core.

1. **Staffing requirements** (admin). Each work order gets a timezone-aware start and
   end (at most 7 days apart) and up to 10 roles. Each role has a title, a head count
   and required qualification identifiers. Requirements are versioned with optimistic
   concurrency and idempotent retries.
2. **Deterministic proposals.** There is no model call. Each active member is evaluated
   per role using only recorded facts:
   - **Hard blocks (cannot be overridden):**
     - the person is inactive or no longer a member;
     - a qualification is missing, unreviewed, rejected or expired. The check runs on
       the job's first and last day through Codex's `qualification_state`;
     - an overlapping active dispatch assignment;
     - an overlapping team-schedule entry.
   - **Needs review (override needs a written justification of at least 10
     characters):** availability unknown (gaps, or no profile, through Codex's
     `availability_state`); recorded as unavailable; verified with unknown expiry.
   - **Ranking:** fully eligible first, then lighter workload over the surrounding
     7 days, then name. Nobody with a warning is auto-selected. Unfilled roles are
     listed.
   - **Privacy:** reason codes, names, availability state and counts only. No home
     address, phone or evidence reference appears in plans, messages or the UI.
     Atlas context is unchanged.
3. **Admin review.**
   - Candidates appear with reasons; ineligible people's checkboxes are disabled.
   - Edits are revalidated on the server: no duplicate people, no over-filled roles,
     no hard-blocked people, and overrides need a justification.
   - The plan version is checked.
   - An older draft is flagged stale when the work order or requirements change.
4. **Approve and send.** In one transaction, the server:
   - requires a current plan version;
   - requires unchanged requirement and work-order versions;
   - re-evaluates every assignment and requires identical employee
     profile/qualification snapshot versions (otherwise 409, "record changed after this
     proposal");
   - creates the assignments;
   - sends each person a WZOS message (job, role, time in UTC, job-site address) and
     queues an SMS copy through the Messaging outbox (`purpose='dispatch'`). Texts are
     subject to all Messaging consent, opt-out and test-mode gates;
   - supersedes other drafts.

   Approval is idempotent by `request_id`, so the same request never sends twice; a
   different request ID returns 409.
5. **Changes and cancellation.**
   - A new proposal for an order that already has sent assignments treats them as
     replaceable, so the same people aren't counted as conflicting.
   - Approving it marks the earlier assignments `replaced` and the earlier plan
     `superseded`, and sends cancellation notices to people removed.
   - Cancelling a sent plan cancels its assignments and notifies each person with the
     reason. Repeating the cancellation is idempotent.
6. **Employee response.**
   - "My assignments" shows each assignment with **Accept** or **Decline**.
   - A response is recorded once and also marks the underlying message acknowledged.
   - Changing a response afterwards goes through the admin (409).
   - Provider acceptance, delivery and the employee's response stay separate, both in
     the admin plan view and in Messaging.
7. **Audit:** `dispatch_events` records requirement saves, proposals, edits (including
   override counts), approvals, supersessions, cancellations and responses, available
   through `GET /api/dispatch/orders/{id}/events`.

## API (Enterprise only; admin unless noted; organization-scoped)

| Route | Purpose |
|---|---|
| `GET /api/dispatch/orders/{order_id}` | Requirements, last 10 plans (with stale flag, assignment and SMS state), reason labels |
| `PUT /api/dispatch/orders/{order_id}/requirements` | `expected_version`, `starts_at`, `ends_at`, `roles[{id,title,count,qualification_ids}]`, `notes` |
| `POST /api/dispatch/orders/{order_id}/proposals` | Create a draft plan with candidates and reasons |
| `PUT /api/dispatch/plans/{id}` | `expected_version`, `assignments[{role_id,user_id,override_reason}]` |
| `POST /api/dispatch/plans/{id}/approve` | `request_id`, `expected_version` |
| `POST /api/dispatch/plans/{id}/cancel` | `expected_version`, `reason` |
| `GET /api/dispatch/orders/{order_id}/events` | Audit trail (last 100) |
| `GET /api/dispatch/my-assignments` (member/admin) | Own assignments |
| `POST /api/dispatch/assignments/{id}/respond` (assignee) | `response: accepted/declined`, `note` |

## Schema (startup DDL, needs review)

Four additive tables: `dispatch_requirements`, `dispatch_plans`, `dispatch_assignments`,
`dispatch_events`. They are registered only in the account workspace. The SQL is in
[migrations/20261009_enterprise_dispatch.sql](migrations/20261009_enterprise_dispatch.sql).
Rollback means deploying the previous code and keeping the tables as the audit trail.

## Changed files (this module only)

- `services/workspace_preview/dispatch.py` (new)
- `services/workspace_preview/static/dispatch.js` (new)
- `tests/test_dispatch.py` (new)
- `docs/migrations/20261009_enterprise_dispatch.sql` (new), this document
- **Shared, narrow:**
  - `app.py`: `dispatch.register(...)` inside `if accounts:`, plus a `/dispatch.js`
    route (7 lines);
  - `static/index.html`: one script tag;
  - `static/team-modules.js` (Claude's Messaging): one line rendering
    `window.wzosDispatch`.

## Validation (actual results)

- `tests.test_dispatch`: **11 pass**. The 11 PostgreSQL counterparts are **skipped** (no
  test database). Coverage:
  - Core and member denial, cross-organization 404;
  - requirement validation and versions;
  - proposals with expired, missing, unreviewed and unknown-expiry qualifications;
  - unknown availability;
  - privacy (no address, phone or evidence in plans);
  - override rules (hard blocks can't be overridden);
  - send-once approval, member accept, repeat and conflicting responses;
  - stale requirements and changed employee records blocking approval;
  - assignment and schedule conflicts;
  - revision replacing earlier assignments with notices to removed people;
  - idempotent cancellation;
  - SMS copies through Messaging consent: blocked `no_contact` for a member without
    texts, delivered to the verified test number for one with texts.
- Full suites on the stacked branch: **Python 410 tests OK, 102 skipped** (all
  PostgreSQL cases with no test database, including this module's 11); **Node 21/21**.
  `node --check` passes on `dispatch.js` and `team-modules.js`.
- **Browser** (local synthetic multi-user account fixture on loopback port 8081;
  same-origin synthetic sign-in, SMS disabled):
  - The Enterprise admin saved requirements and proposed. The UI correctly showed
    Morgan eligible, Casey needing review (availability unknown), Eli blocked (expires
    before job end) and Avery blocked (no qualification).
  - An older draft was flagged stale after requirements changed.
  - Casey was added with a justification, and both were approved and sent. Text copies
    showed "blocked (sms_disabled)".
  - The member, at 375×812, saw only "My assignments" (no admin panel) and accepted;
    the status showed "Accepted" with a timestamp.
  - My first attempt reported "availability unknown" because the fixture's
    availability date didn't match the job date. That is correct behavior, not a
    defect.
  - Screenshots are outside Git in `C:\Users\MolecularDev\claude-WZOS-2.0\evidence\dispatch\`.
- **Not run:** PostgreSQL, Google sign-in, cloud, real SMS, load testing.

## Remaining gaps and dependencies

- **Atlas:** no "Let Atlas plan" yet. The proposal is deterministic, as the plan
  requires. Atlas explanations of the plan or gaps belong to Codex; the plan payload
  (reason codes, no private data) is the proposed input.
- **Travel and placement:** no travel time or starting-location ranking. Maps is owned
  by Codex. Proposed interface: `travel_minutes(org, user_id, order_id)` returning a
  number or unknown; unknown never blocks and is shown.
- **Rules and inputs not modeled:** work-hour limits, rest rules, equipment/vehicle
  eligibility, recurring availability templates, and member-entered availability.
- **UI limits:**
  - The UI edits only the first role; others are preserved. Multi-role editing is
    API-only.
  - Message times are in UTC; the app UI shows local time.
- **Admin oversight:** no way to see member responses across all orders yet (it's per
  order).
- **Testing and pricing:** load testing and usage limits/pricing for SMS.

## Product questions for Ray (current behavior in brackets)

1. Can admins override "unavailable" or "verified, expiry unknown" with a justification?
   [Yes. Missing, unreviewed, rejected or expired qualifications and conflicts can
   never be overridden.]
2. Should members be able to change an accepted or declined response themselves?
   [No; they ask the admin, who revises the plan.]
3. Should declining automatically reopen the role for a new proposal? [No; the admin
   sees the decline and creates a revision.]
4. Assignment notices include the job-site address and UTC time window. Should times
   use the organization's timezone? [UTC, because no organization timezone setting
   exists yet.]
5. Can admins be assigned? [Yes, if qualified and available; they are evaluated like
   anyone else.]

## Integration and rollback

After `codex/integration-release` and `claude/messaging` merge into `enterprise-v2`:
1. Rebase `claude/dispatch` onto `enterprise-v2`.
2. Rerun `tests.test_dispatch`, plus its PostgreSQL class with
   `WZOS_TEST_DATABASE_URL`, and the full suites.
3. Run browser acceptance with real accounts.

Rollback means reverting the dispatch commits. The tables become inert, and messages
already delivered remain in Messaging history.
