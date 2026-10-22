# Unassisted prelaunch testing — October 22, 2026

## Outcome and release status

Engineering found and repaired the Core communications entitlement mismatch,
two synthetic-test fixtures and an outdated local DOT search index. Added an
explicit browser plugin restriction and prepared dependency security updates.
These repairs and the shared header
notifications are committed locally/on the development branch; **not deployed**.
Production remains `wzos-v2-accounts-ui-16d0905` at 100% traffic, public version
`5821810b858f1f58b45af012`. No customer records, provider messages, real payments,
model requests, IAM, secrets or weather configuration were changed by this sweep.

## Test evidence and limits

| Check | Result / provenance |
| --- | --- |
| Complete Node suite | 174 passed, zero skipped; Windows and Cloud Shell Linux. Initial two harness failures fixed by adding the real DOM's `dataset` property to the fake element. |
| Focused communications backend | 38 passed, zero skipped locally, including opt-out after downgrade. |
| Full PostgreSQL sweep at `90fdc43` | 890 run: 889 passed, one error, zero failures/skips. The synthetic demo attempted a now-forbidden Core message. |
| Corrected demo and browser-policy tests at `8d29bbf` | Six passed locally and six passed in Cloud Shell using the disposable PostgreSQL harness; zero skips. |
| Repaired full PostgreSQL gate at `8d29bbf` | **891 passed, zero failures/errors/skips**, 399.936 seconds. This supersedes the earlier failed gate for that repaired application code. Later dependency-only changes are tested separately below. |
| Signed-form dump/restore at `8d29bbf` | PASS. Two private disposable native PostgreSQL databases, real `pg_dump`/`pg_restore`; form, drawn signature and payload hashes preserved, received status preserved, anonymous/foreign-org access denied. Restore cluster cleanup verified. |
| Live public smoke | Eight private APIs returned anonymous 401/no-store; foreign Origin returned 403 without permissive CORS. HTML and version release markers match; correct footer and standalone manifest; 192/512 icons have correct dimensions. No authenticated customer writes. |
| Dependency consistency | `pip check` passed. This is not a current vulnerability assessment. TestClient emits an httpx deprecation warning; no acceptance failure. |
| Patched dependency compatibility at `dfef889` | **119 passed, zero skips**, Cloud Shell disposable PostgreSQL, 49.621 seconds. PDF export, submissions/signatures, Forms, knowledge/manual/source package and scanner transport/runtime. |
| Repaired Python advisory scan at `dfef889` | `pip-audit` exit0: **no known vulnerabilities found** in the inspected app environment. Does not cover OS/container or bundled browser dependencies. |

### Dependency advisory follow-up

Installed-environment `pip-audit` inspected57packages and reported30advisories
across certifi(1), Pillow(24) and pypdf(5). The audit is an advisory match, not proof
that WZOS exposes every affected code path or has been exploited. Never execute
reproducer code from advisory descriptions. The initial audit invocation used an
incompatible flag; corrected invocation completed and produced the findings.

Pinned repairs in `dfef889`: certifi2026.10.19 in app/scanner requirements,
Pillow13.0.0 and pypdf6.21.1 in the app. Official published releases verified:
[certifi](https://pypi.org/project/certifi/2026.10.19/),
[Pillow](https://pypi.org/project/pillow/13.0.0/),
[pypdf](https://pypi.org/project/pypdf/6.21.1/).
These updates do not change production's existing image. Local compatibility
initially ran93checks with23PostgreSQL skips and one test-import harness error;
the source-package test expects the tests directory on PYTHONPATH. Its two tests
pass with that invocation corrected. Scanner transport/runtime17PASS; `pip check`
still passes. Cloud PostgreSQL compatibility then passed119checks with zero
skips and the repaired advisory scan exited0 with no known vulnerabilities found.
These focused results accept the dependency repair for development; the full
891gate predates these dependency-only pins. OS/container-image vulnerabilities
are outside this Python audit and remain a separate review.

The broad sweep exercises existing synthetic account/seat boundaries, commerce
webhook/retry/upgrade rules, forms/signatures, Voice drafts/receipts/non-retention,
assignments, weather states, routes, time/offline records, training, meetings,
security and integration API tests. Mocked providers do not establish real carrier
delivery, Daily media, live billing, managed recovery or current DOT applicability.

## Repairs

1. **Enterprise communications:** Core's menu and server previously allowed
   Messaging and Video meetings despite the approved edition matrix. Dashboard,
   navigation and API guards now require Enterprise. SMS verification/send/admin
   endpoints follow that boundary. A previously verified person can still opt out
   after downgrade; ordinary Core training and form delivery are preserved.
2. **Synthetic fixtures:** the dashboard fake DOM lacked `dataset`; the unified
   demo created a Core message. Both now match actual DOM/approved entitlements.
   Added explicit tests for Core denial and the Enterprise demo message.
3. **Browser hardening:** add `object-src 'none'` after Maps/Daily policy assembly
   so every shell policy blocks unused legacy object/embed plugins. Local checks
   cover both Maps-key configurations and public version responses. Live does not
   yet have the explicit directive; no exploit was demonstrated by this finding.
4. **DOT derivative index:** rebuilt schema 5 to expected schema 6 from unchanged
   originals; seven PDFs / 2,627 physical pages, database integrity and source/index
   fingerprint validation pass. Local retrieval runs without inference. All page
   review flags remain false and no engineering formula is registered. Rebuilding
   an index does not approve its sources or make DOT answers field-ready.

### Integration and rollback

No startup DDL, schema or data migration. The intentional API change is403 for
Core access to communications and provider SMS operations; existing verified
recipients retain opt-out. Core form-to-office receipt/storage and training are
unchanged. No subscription upgrade or permission grant is performed by a guard.
The CSP addition blocks only unused object/embed plugins; Daily remains an
authorized iframe flow. Source rollback restores the prior commit; a future
production release must retain its existing revision for traffic rollback.
Neither rollback may pretend to delete submitted reports or reverse user consent.

## Read-only live configuration

- SMS mode is **test**. General customer texting still needs activation and
  carrier/business acceptance; do not infer availability from code verification.
- Voice and Speech flags are enabled. Active Voice target is
  `wzos-atlas-inference`, one GPU, 20 CPU / 80 GiB, max one instance and no minimum
  instance annotation (default zero). Separate `gemma-inference` also exists with
  min zero/max one; it is not the app's current Voice target. No inference run here.
- Hourly weather schedule `0 * * * *`, America/New_York, enabled. Three most
  recent inspected executions completed successfully at 06:02, 07:02 and 08:00 UTC
  October 22. No permission/tracking or monitor configuration changes.
- Project monthly budget currently USD50, thresholds 50/80/100% actual spend. Alerts are
  not a spending cap; receipt/owner and suitability still need Product acceptance.
- Latest inspected SQL backup succeeded October22 at07:05UTC (03:05 Eastern).
  Automated backups enabled, seven retained. Log-retention configuration alone
  does not establish point-in-time recovery acceptance.
- File bucket has public-access prevention enforced, uniform access, versioning,
  seven-day soft-delete retention. SQL backup does not include object bytes.
- Application ingress is `internal-and-cloud-load-balancing`; service-level
  invocation policy has no bindings. This does not establish inherited IAM,
  invoker-check settings, effective runtime permissions or complete secret scope.
- DOT inference flags were absent from the runtime environment and default off
  in code; source review and provider acceptance remain open. QuickBooks/Workday
  are not accepted connectors.

## Evidence and next steps

Local ignored evidence: `.local-data/prelaunch-20261022/`, including Node logs,
communications tests, public smoke, DOT hashes/inventory and mobile screenshot.
Cloud evidence: `/tmp/wzos-prelaunch-20261022.aRppkWeT`; pointer
`$HOME/wzos-prelaunch-latest-path.txt`. Top-level logs/results/metadata also copied
to private `$HOME/wzos-prelaunch-evidence-20261022` to survive /tmp loss. Do not
commit those runtime snapshots or private environment configuration. Shell
authentication can expire despite activity; verify account/project on resumption.

Before another release, run its required immutable-candidate release gates and
stage/rollback checks, including any dependency changes after the full-gate commit.
Preserve the original failed gate and its repair provenance.
Remaining human/provider checks and business decisions are in
[the human checklist](PRELAUNCH_HUMAN_20261022.md). Customer notices are prepared
in [the unpublished decision draft](PRELAUNCH_PRIVACY_DECISIONS_DRAFT_20261022.md).
Fresh container/OS and bundled-browser dependency assessment, effective IAM/secret review,
managed Cloud SQL plus object recovery and recovery ownership remain open.
