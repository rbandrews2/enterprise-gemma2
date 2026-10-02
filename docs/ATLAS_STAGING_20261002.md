# Atlas staging session — October 2, 2026 UTC

## Verified preparation

- Reconnected Chrome Cloud Shell as admin@workzoneos.org; previous app revision 00015-qfq, inference service absent.
- Synced cloud checkout to a5f9fdb9bf19. Source ZIP 77,843,099 bytes; SHA256 6b99042d47adeda3bd8af6b67ce510e8570ac86f267aac0d379be884617d8781 matched after browser upload.
- Verified scoped source snapshot in Cloud Shell; Cloud Build 280d6e87-8b77-473f-bef4-1d09fadb4285 SUCCESS, image a5f9fdb9bf19-sources.
- App source update 00016-g5r; restricted trial enabled at 00017-54l. These are intermediate revisions, not cleanup state.
- Recorded prior inference billable time: 2,572.515 seconds over six series, no remaining page; approximately $2.28 at the previously recorded compute rate. Excludes builds, storage and billing lag; not an invoice.
- Fresh disposable managed-account validation passed: IAM, sign-in/refresh, verified-email, admin/member, tenant separation and last-admin protection. Fixtures must be disabled after tests.
- 20-minute fallback guard installed before model deployment; normal cleanup must still be verified.

## Live results

Private Gemma 4 31B revision `00001-x2r` reached Ready. Synthetic marking preparation returned eight topic groups, including base Section 704, the conditional 2024 resurfacing provision, marking materials/removal/visibility, and federal references. Saved-job inference returned HTTP 200 in 7.419 seconds; stale version and tenant denials passed. The answer identified missing authority, date, geometry, permits and contract evidence without invented placements or performed actions.

The model's three selected citations were VDOT MUTCD physical page 761, dated GPO OSHA 1926.200 page 1 and VWAPM page 55. Marking-specific candidates existed in preparation but were excluded by first-three-topic selection. Therefore marking-specific grounding is NOT accepted.

| Reliability case | Result |
| --- | --- |
| Concurrent A | 503, busy, 1.760 seconds; correlation cf3246660a0c4808bbc275adf1be8efc |
| Concurrent B | 200, real reply, 6.850 seconds |
| Client cancellation | Client cancelled at 0.25 seconds; provider stop unverified |
| Recovery after 3 seconds | 503, busy, 0.829 seconds; correlation 895c9eb434074024bee94193ae2c2742 |
| Separate later recovery observation | 200, real reply, 5.818 seconds; saved version 1 |

Cloud logs matched both busy correlation IDs. This identifies the app request gate as the immediate rejection reason; it does not prove when Cloud Run forwarded disconnect or when GPU work ended. Immediate cancellation recovery remains FAILED/open. Deployment initialization is not accepted scale-from-zero testing.

## Local repair after the live trial

Citation selection now prioritizes two task-related passages and retains one safety/context reference, deduplicates passages, preserves applicability notes and keeps the three-result bound. Specific question topics take precedence over the work-type default. Marking/material/retroreflectivity questions now trigger reference retrieval. Real local library selects base704, conditional2024 and OSHA for the tested marking question; the 2024 restriction remains attached. The stop control now says "Stop waiting" and explains Atlas may still be finishing, matching the observed cloud behavior. These repairs are not deployed or tested against the real model yet.

Validation: 5 selection regressions and 12 existing Atlas tests passed; full suite 200 tests, 184 passed, 16 database-dependent skips, 53.156 seconds. Five existing Node navigation/reply tests also passed after the stop-label edit. Real-library selection evidence: `knowledge/atlas-selection-20261002.json`.

## Cleanup and next checkpoint

Verified final staging app revision `00018-lgr` Ready=True, Atlas enabled=0; trial inference service deleted and listing empty. Synthetic users disabled, tokens revoked, organizations disabled. Proxy and fallback guard stopped only after cleanup. Model weights retained.

Next: deploy the selection repair and run one targeted marking-scope reply; address cloud cancellation with an instance-safe design before claiming immediate recovery. True cold start, capacity, numerical/model quality, source applicability and visual extraction review remain open. Keep subsequent GPU trials bounded by remaining approved spend.

Evidence remains in `/home/admin_/wzos-evidence/`: marking-result-20261002.jsonl, marking-preparation-20261002.json, reliability-20261002.jsonl, recovery-20261002.json, usage-20261002.json, usage-after-20261002.json and deployment/cleanup logs. Disposable fixture state is private in `/home/admin_/wzos-grounding-ZCyfzy/fixtures-20261002.json` and is disabled. Do not commit credential state. Source originals are preserved in Cloud Shell under /home/admin_/wzos-evidence/source-deployment-20261001-scoped, in addition to the local snapshot. No production or V1/DNS changes.

Startup logs include default FP8 scaling warnings indicating possible accuracy impact. Record this as a model-quality evaluation concern; this session does not establish numerical equivalence or field suitability.

Post-cleanup monitored cumulative inference time: 3,060.471 seconds, approximately $2.712 compute at the recorded rate; no additional metric pages. Excludes storage/builds and may lag billing. Recheck before another trial.
