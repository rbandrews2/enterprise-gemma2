# September 30 test model / October 5 production readiness

Requested by Ray September 25, 2026. Dates are delivery targets, not evidence of
readiness or authorization to provision paid resources or cut over DNS.
All existing product requirements remain in scope unless Ray explicitly changes them.

## Dated critical path

| Dates | Deliverable | Acceptance evidence |
|---|---|---|
| Sep 25–26 | Unified demo journeys, release reuse inventory, exact priced Google configuration | Reproducible local dataset, role/edition isolation, reviewed resource configuration; paid setup acceptance required |
| Sep 26–28 | Google identity, PostgreSQL, private files and deployment | Verified sign-in/recovery, no cross-organization access, persistence across instance replacement, backup restore |
| Sep 27–29 | Atlas/source library, report imagery/diagrams/PDF, operational modules | Real inference timing and cited answers; saved site geometry; reproducible draft output; module acceptance matrix |
| Sep 29–30 | Integrated restricted test model | Core/admin, Core/member, Enterprise/admin, Enterprise/member journeys on one test URL; known gaps visible; Ray walkthrough |
| Oct 1–3 | Close remaining launch requirements | Twilio/email delivery, dispatch review, employee qualifications, complete module behaviors, security/concurrency/mobile/failure tests |
| Oct 4 | Release-candidate acceptance | Full regression, restore/rollback drill, cost limits/alerts, resolved blockers and release notes |
| Oct 5 | Production-ready release target | Evidence-backed checklist and Ray's rollout decision; production cutover remains separate |

The schedule is aggressive. External service setup, messaging registration,
qualified placement review, and unresolved module gaps can affect it. Raise any
threat to either milestone as soon as evidence appears; do not hide incomplete
features behind navigation links or treat test-mode sending as real delivery.

## Working test model definition

- Shared app with the approved liquid black/amber/gold design and Atlas companion.
- Four role/edition journeys, private organization data, saved work and attachments.
- Functional work orders, forms, time clock, scheduling, internal messaging,
  training workflow and navigation; remaining advanced behavior explicitly labeled.
- Enterprise report flow with location/geometry, imagery, source-backed Atlas
  recommendations and draft output, with verification/review states visible.
- A documented list of unfinished production gates. This milestone is not a claim
  that all V1 parity, dispatch, certification, payroll or external delivery is complete.

## Production gates that cannot be closed by a date alone

Durable cloud identity/storage; tenant and edition isolation; private-file scanning;
backup restoration; acceptable Atlas latency and grounded-source quality; safe,
reviewable placement recommendations; permitted image use/export; finished PDF and
delivery; verified Twilio/email setup; module parity or explicit scope decisions;
mobile/accessibility; dependency/security review; monitoring, budget and rollback.
Use MUST_COMPLETE_BEFORE_LAUNCH.md for the detailed gates, with newer evidence taking
precedence over its historical status notes.

## Current concrete progress

`scripts/build_unified_demo.py --output <new-local-directory>` creates linked sample
journeys through the existing APIs, never by importing legacy accounts. It refuses
existing destinations and cloud/account runtime markers. Manifest identifies jobs,
forms and the Enterprise report snapshot. Fixed clock timestamps produce a one-hour
sample shift; no live model or external provider is called. Requires development
dependencies. This is test tooling, not production authentication acceptance.

Built `.local-data/unified-demo-20260925` locally. Retain the separate account emulator
workspace; neither dataset should be shipped as real accounts. Useful geometry from
earlier scenarios and a file-level reuse/removal manifest remain next local work.

## Next cloud action

Inspect the authorized Cloud Shell's actual project/service/API state and reuse
existing resources where suitable. Finalize the exact priced staging configuration
before asking Ray to approve paid provisioning. Earlier cost estimates are dated
planning evidence, not a current all-in quote. Do not run historical deployment scripts.
