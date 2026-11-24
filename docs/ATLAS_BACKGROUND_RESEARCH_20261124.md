# Current status: ACTIVE — November 24, 2026

Daily 03:15 America/New_York. First cloud scan 9/9 successful; scheduler delivery
and durable duplicate prevention verified. Earlier sections describe implementation
stages; see Activated below for final evidence.

# Atlas background research â€” first increment

User direction: research VDOT updates during background/free time, preserve cited
accuracy and a patient conversational demeanor. Traffic control remains the scope;
line striping and paving are deferred.

## Implemented locally

`python -m services.v2.knowledge.research --state <persistent-private-directory>`

Operator CLI watches six curated VDOT/FHWA sources and their publication pages.
These include manuals, field guide and separate known-error documents. It detects
changed bytes and collects official links (including new PDF names) for review.
It does not follow discovered links, execute page instructions, query a model,
change catalog pins, ingest evidence, or publish new guidance.

The first fetch is an unreviewed baseline, not a freshness certification of the
existing approved library. Changed originals and metadata are retained by hash.
Existing source review, correction precedence, edition/applicability checks and
release packaging remain required before Atlas can cite the new material.
Navigation links/page markup may produce review noise; no assertion that every
changed HTML hash is a substantive regulatory change.

Once-per-24-hour guard; exclusive run lock; no retries; official HTTPS/redirect
allowlist reused from downloader. Up to 16 targets, 100 MiB per document,
512 MiB archive budget. Four-minute start-work budget; an in-flight download may
finish beyond it (downloader deadline/HTTP timeouts still apply). At archive cap,
defer work for operator review; never erase evidence automatically. A killed run
can leave a lock: verify no process before removing that lock.

## Verification

Five focused unit tests passed: scope, link safety, baseline/change/daily guard,
failure baseline preservation, redirect/size rejection and overlapping-run lock.
Initial live read-only run: seven of nine targets retrieved. VWAPM exceeded the
initial 32 MiB limit; aligned limit with existing downloader's 100 MiB cap.
The catalog's June 15 Virginia MUTCD known-errors URL returns 404. Publication page
was captured successfully; replacement needs review, not silent catalog overwrite.
Downloaded artifacts reside in ignored `.local-data/knowledge/research`.

## Remaining activation work

Not yet scheduled or deployed. Configure a separate daily off-peak CPU-only job
with persistent private state, no GPU and no access to customer records. Confirm
job identity/storage scope before cloud activation. Run one baseline from that
environment; report failures as failures. Validate the replacement known-errors
link and align with the existing review process. Full integrated release gates
remain required; these focused tests are not a production acceptance claim.

Next increment: compact review digest showing new/removed official links and
changed document revisions, then approved-source publication. Background checks
must not contend with user inference. Broader web research can supply leads but
cannot silently become governing VDOT guidance. No automatic learning claim.

No database migrations, IAM changes, customer notifications or production changes.
Rollback: disable the future schedule; keep reviewed sources and staged evidence.

## Daily cloud activation candidate (November 24)

User explicitly requested repairing the link and running daily research. The
replacement linked by VDOT's current publication page is the November 10, 2026
list, SHA256 3f3b7e73c0447f2345ed41b1dd624ecaa2ab701836b57ad026f9cc818da553e8.
Added new catalog ID vdot-mutcd-known-errors-20261110; historical June ID and
reviewed companion pins remain untouched. Watchlist now uses November revision.
All nine targets downloaded successfully in the repaired local baseline.

Cloud scope: project enterprise-gemma2, us-central1, private job
wzos-atlas-research, 1 CPU/1 GiB, one task, 600 seconds, no retries. Dedicated
runtime wzos-atlas-research receives storage.objectUser on only the new
enterprise-gemma2-atlas-research bucket (public originals, hashes, run reports).
Dedicated wzos-research-scheduler receives run.invoker on only this job. Neither
identity receives access to customer databases, secrets, app storage or the model.
Bucket uses uniform access and public-access prevention. Scheduler daily at
03:15 America/New_York, no retries. Small ongoing CPU/storage/scheduler costs.

Generation-checked bucket lease prevents overlapping scans, expires after 30
minutes (job timeout ten minutes). Persist candidates before advancing baseline;
immutable candidate keys make interrupted uploads reusable. UTC-calendar daily
guard handles scheduler jitter and daylight-saving transitions at 03:15 Eastern.
Cloud logs contain only public source URLs and status. No model or customer data.

28 checks passed: research 5, cloud persistence/lease 4, existing knowledge 19.
No application integration, schema or UI change; production WZOS app remains
unchanged. Deployment script runs baseline successfully before creating schedule.
Rollback: pause wzos-atlas-research-daily in us-central1; retain private archive.

Build 45b1936e-6c2b-4981-9d00-226973e4c670 succeeded for ab7c55b.
Image digest: d9c674a1615cf35bc8d75b881a542b12158bbe0666360a716b77695949e3be2b.
Cloud Shell freshly verified admin@workzoneos.org / enterprise-gemma2.
The first scheduler IAM binding saw service-account propagation delay; describe
confirmed existence and the subsequent narrow binding succeeded.

## Activated November 24, 2026

Daily schedule wzos-atlas-research-daily is ENABLED: 15 3 * * *,
America/New_York (03:15 Eastern). Initial cloud execution
wzos-atlas-research-8sdxj succeeded, completed 06:55:34 UTC. Stored baseline
report checked_at 06:55:20 UTC contains all nine targets, all baseline_unreviewed.
Bucket readback confirms public_access_prevention=enforced and uniform access=true.
Job IAM readback contains only the dedicated scheduler as run.invoker.
Scheduler manually triggered at 06:56:44 UTC; API accepted with status {} and
created execution wzos-atlas-research-ck7q9. Completed successfully at 06:58:26 UTC, succeededCount=1. Cloud log status not_due confirms the durable daily guard prevented a duplicate download.
