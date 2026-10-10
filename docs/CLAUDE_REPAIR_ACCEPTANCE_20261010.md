# Claude repair acceptance — October 10, 2026

## Integrated candidate

Branch `codex/preproduction-modules`, based on Codex PDF candidate `23ddeba`.
Reviewed Claude checkouts without editing them: Messaging `9fc0294`, Dispatch
`df6d7ba`, Training `358f9b3`, Offline drafts `a87f5bd`. All four are assembled
in the owned integration checkout; enterprise-v2 and live deployments unchanged.

## Repair findings

The five previously reproduced defects are repaired: verification secrets are
excluded from public outbox DTOs and gated by delivery state; acknowledged
clock submissions preserve other drafts; training retries include content
version; admins can explicitly reassign cancelled training with audit history;
dispatch cancellation uses the stored assignment dates including overnight work.

An additional controlled overlapping-storage-read probe exposed a remaining
read/modify/write race in the offline repair. Codex now serializes participating
tabs using a scoped Web Lock and validates action order inside the lock. Without
that capability, new changes remain visibly tab-only and preserved device data
is not overwritten. Pending writes trigger the close warning. Five new tests
cover overlapping writes, duplicate actions, missing/refused locks and account
switches while waiting. All participating tabs must reload the new script;
old tabs do not cooperate with the lock.

Design references: [HTML storage specification](https://html.spec.whatwg.org/multipage/webstorage.html)
says to assume no storage locking; [Web Locks working draft](https://www.w3.org/TR/web-locks/)
describes named exclusive locks. This repair retains the existing draft format.

## Independently run validation

- Messaging: 39 tests, 21 passed, 18 PostgreSQL skips.
- Dispatch: 28 tests, 14 passed, 14 PostgreSQL skips.
- Training: 18 tests, 9 passed, 9 PostgreSQL skips.
- Combined local Python: 444 tests in 201.897s; 325 passed, 119 PostgreSQL skips,
  zero failures/errors.
- Combined Node: 37 passed, zero failures/skips, including the five new cases.
- JavaScript syntax and diff whitespace checks passed.

Full combined disposable PostgreSQL and browser acceptance remain pending.
Local evidence is ignored under `.local-data/module-combined-python.log` and
`.local-data/module-repaired-node.log`; the race probe is also ignored.

## Schema and release boundaries

Reviewable startup DDL is in migrations/20261009_messaging_sms.sql,
migrations/20261009_enterprise_dispatch.sql and migrations/20261009_training_content.sql.
Deployment applies these additive tables, including SMS secrets and training
assignment events. Roll back code without dropping history tables. Database
acceptance must precede deployment. Fake provider tests do not prove live SMS
acceptance; training content/qualification approval and real-device offline
acceptance remain open. Admin/member, organization isolation and Enterprise-only
dispatch are preserved. No paid resources, customer sends or production changes.

## Cloud/browser checkpoint

Candidate 9c331c4 was pushed. The full native PostgreSQL harness was submitted in a new owned Cloud Shell checkout ~/wzos-modules-20261010. Output is ~/wzos-modules-pg-20261010.log. Browser control timed out while collecting it; result and independent /tmp/wzos-pg-gate.* cleanup verification are unconfirmed. The harness has an EXIT cleanup trap. No live app deployment occurred. The local synthetic admin sign-in reached organization selection, but browser module acceptance is not complete. Local fixture restarted on8083 (session11680). Next: read the cloud log, verify cleanup, then browser module/download checks.
