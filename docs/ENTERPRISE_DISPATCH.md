# Enterprise dispatch through Messaging

Requested by Ray on 2026-09-24. Product requirement, not an implemented feature.
WZOS serves many independent companies; every employee, job, recommendation,
assignment and delivery record must stay within its organization.

## Intended workflow

1. Organization admin completes setup: employee name, employee number, address,
   verified contact number, qualifications/certifications and expiration dates.
   Collect shifts, availability, assigned jobs, agreed starting location, travel
   limits and relevant equipment/vehicle eligibility. Missing data is explicit.
2. Work orders record jobsite, scheduled start/end, required crew size/roles,
   qualifications, equipment and any location-specific requirements.
3. Enterprise admin selects **Let Atlas plan assignments** in Messaging /
   Dispatch. Atlas produces a proposed crew-to-job assignment plan with reasons,
   missing information, conflicts and unfilled roles. It must not silently infer
   that an employee is qualified or available.
4. Admin reviews/adjusts the proposal, then uses **Approve and send assignments**.
   This is the default release flow; automatic sending would be a separate,
   explicit organization setting with separate acceptance tests.
5. Each assigned employee receives the assignment in WZOS Messaging and, when
   enabled for that recipient, Twilio SMS or MMS. Track queued, provider-accepted,
   delivered/failed, and employee acknowledged as distinct states.
6. Changed/cancelled assignments create new versions and clear stale approvals.
   Reassignment rechecks current employee availability and all job requirements.

## Assignment method and boundaries

- Enforce hard requirements first: organization, active employee, verified and
  current qualifications, availability, no overlapping assignments, required
  crew roles, travel feasibility and applicable configured work-hour limits.
- Rank eligible candidates by travel time from their agreed start location,
  schedule fit, relevant experience and balanced workload. Show the inputs and
  reasons; permit admin overrides with recorded justification. No protected
  demographic traits or inferred personal characteristics enter the ranking.
- Use deterministic validation/optimization for constraints. Atlas explains the
  plan and asks about gaps; model prose is never the source of credential facts
  or the authority to bypass conflicts.
- An address alone does not establish live location. Prefer an agreed depot or
  starting point; using a home address requires clear employee-facing handling.
  Keep home addresses/contact details visible only to authorized roles. Do not
  copy coworkers' private information into assignment messages or model context.
- Snapshot employee, qualification, work-order and schedule revisions. Recheck
  them transactionally before approval/dispatch to prevent stale assignments.
- Enforce Enterprise entitlement on every dispatch API/worker action as well as
  in the interface. Core messaging remains available, but dispatch planning and
  automated assignment generation are Enterprise-only.

## Implementation tasks

- [ ] Add organization setup / employee directory, unique employee numbers per
  organization, access controls, qualification evidence, expiry and review state.
- [ ] Add work-order staffing requirements and schedule availability inputs.
- [ ] Add organization-scoped dispatch batch, assignment revisions, proposal
  explanations, approval history, and per-recipient delivery/acknowledgement data.
- [ ] Build eligibility/conflict engine, then assignment ranking/optimization.
- [ ] Add Atlas planning button, editable review screen, and approval/send action.
- [ ] Add Twilio delivery outbox and signed status callbacks; consent/opt-out,
  number/registration configuration, retries and ambiguous-timeout reconciliation.
- [ ] Add SMS/MMS templates with job, time, role, navigation and secure report link.
  Do not expose private report attachments as permanent public media URLs.
- [ ] Test Core denial, organization isolation, expired/missing qualifications,
  overlapping jobs, travel infeasibility, unfilled jobs, stale approval, duplicate
  sends, failed delivery, cancellation, overrides and employee acknowledgement.
- [ ] Load-test representative multi-company dispatch batches and set usage limits
  and measured pricing for Maps routes, model calls and SMS/MMS.

Dependency order: durable accounts/storage -> employee setup + job requirements
-> dispatch proposals -> reviewed sending + Twilio -> production acceptance.
No live employee assignment or external message is authorized merely by this plan.
