# Remaining release work after the two review workflows

Updated October 8, 2026. Local integration candidate only; no production deployment.

Completed this pass: immutable saved-form internal submissions/admin review; self-reported training study records/admin review. Admin/member and organization checks remain enforced. Neither workflow sends external messages or issues qualifications.

## Sequential remaining tasks

1. COMPLETED October8:337PostgreSQL tests/zero skips, private-GCS gate/cleanup and enterprise-v2 merge. See RELEASE_GATES_20261008.md.
2. IN PROGRESS: restricted HTTPS sign-in/server signing passed; Ray reported Android remembered-session refresh/reopen and real passkey enrollment/login passed. Android cancellation/password fallback also passed per Ray. Device removal and continued password access passed per Ray. Finish re-enrollment confirmation, session revocation, desktop reload follow-up, real-email recovery and iOS coverage.
3. Finish organization setup, invitations, account recovery, employee profiles/qualifications and Core/Enterprise entitlement acceptance.
4. Finish Forms Hub attachments, private uploads, signatures, templates, exports and cloud acceptance; connect approved external delivery.
5. Complete Work Zone Report generation, cited Atlas recommendations, annotated imagery, PDF/private download, review and delivery records.
6. Complete Google Maps/imagery placement and measured-geometry acceptance, licensing checks and navigation field/offline validation.
7. Verify Atlas production-sized inference reliability, cancellation/concurrency, IAM, cost controls and all-module behavior.
8. Review Virginia/federal/locality source editions, extraction accuracy, applicability and operation coverage, including pavement marking.
9. Finish Time Clock real-device/cloud acceptance, offline reconciliation, timesheets and policy decisions.
10. Connect messaging/Twilio with approved credentials, delivery/retry handling and tenant isolation; no customer sends during validation.
11. Complete schedule management and Enterprise dispatch proposal, admin approval, sending and employee acknowledgement.
12. Finish Google Meet organizer integration/acceptance; admins create/manage and members join only.
13. Supply reviewed/authorized training videos and assessments; implement verified qualification records separately from self-reported study.
14. Finish cross-module phone/desktop accessibility, loading/error recovery and responsive design acceptance.
15. Complete operational readiness: secrets/IAM, CI/security checks, backups/restore, retention, monitoring/alerts, budgets and rollback.
16. Run a restricted multi-organization pilot with role/edition, device, failure and load scenarios; repair findings.
17. Obtain production cutover approval and execute the verified release/rollback plan.

See REMAINING_TASKS.md for the detailed historical checklist and SESSION_HANDOFF.md for current evidence. Existing implementation is reused; an open item may require acceptance and remaining integration rather than a rewrite.

