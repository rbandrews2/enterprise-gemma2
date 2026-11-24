# Atlas background research — first increment

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
