# Latest local additions: restricted staging release preparation

Application candidate: `cf357802f6d979667225ebb0eed3ce5cea19d826`, branch
`codex/preproduction-modules`. This is a preparation record, not deployment
acceptance or production readiness.

## Included workflows

- Reviewed module foundations: employees, training, messaging and Enterprise dispatch.
- Employee My jobs inbox, frozen assignment details, in-app notifications,
  acknowledgement and navigation links.
- Assigned-job integration with own Time Clock, Navigation, saved forms and
  read-only dispatch cards in Schedule, preserving private original job access.
- Saved report PDF exports and scoped Atlas context/corrected module help.
- Existing role, organization and edition enforcement, revision checks and
  offline draft boundaries remain in force.

Closed-app push, durable completed printable forms/signatures, verified provider
delivery and full live Atlas acceptance remain separate work. See
TEST_MODEL_ASSEMBLY.md and ATLAS_CONTEXT_INTELLIGENCE.md.

## Package

The ignored local directory `.local-data/release-cf35780` contains a verified
official-source snapshot, an allowlisted container context and a ZIP transfer
bundle. It includes no local credentials, operational database, recovery files,
test identity data or uncommitted source. The code comes from Git archive at the
exact application SHA above. Source snapshot: 139 hashed files, 32 catalog entries,
25 sources with preserved revisions, 27 total revisions. Seven entries have no
preserved revision; source applicability remains unverified.

Container assembly reuses Dockerfile.accounts and the existing verified-source
packaging workflow. It copies sources to `/app/.local-data/knowledge` and verifies
them during the build. Snapshot coverage is not current-law or field approval.
`release.json` records per-file SHA256 hashes and open gates. The ZIP is outside
Git; GitHub alone cannot recover its original source binaries.

Verified bundle: `wzos-accounts-cf35780.zip`, 80,280,010 bytes,
SHA256 `3b14b7ad59e1cdd73fae531ff431d13e6fc79f68707b5cf953cb610a74d81c17`.
Its 258 context files were rehashed from the completed ZIP; ZIP CRC checks passed.
Verify the same SHA256 after transfer to Cloud Shell before extracting/building.

## Release gates

1. Full local Python regression: 465 tests, 339 passed, 126 PostgreSQL-dependent
   skips, zero failures/errors; 700.656 seconds. This is local acceptance only.
2. Full Node regression: 47 passed, zero failures/skips.
3. Exact-candidate PostgreSQL: pending Cloud Shell control/manual operator run.
   Earlier 444-test acceptance predates this candidate and cannot substitute.
4. Refresh live service/configuration, IAM, secret-version metadata, cost ledger,
   database backup and previous immutable image/revision for rollback.
5. Build the verified context, check its digest and source verification, and
   deploy only to the existing restricted account staging service.
6. Verify authenticated/anonymous behavior, two organizations, both roles and
   editions, assigned-job workflows and private file/report access on desktop
   and Android before calling the release accepted.

Logs: `.local-data/deployment-local-gate.log`, `deployment-node-gate.log`,
`deployment-source-package.log` and `deployment-artifact.log`. The separate
`release-validation.json` records results against the immutable ZIP hash.
The bundle's embedded release manifest remains conservative (not deployment-ready)
and is not rewritten after tests. Nothing has been deployed or merged to
enterprise-v2; the primary checkout remains clean at 2dc5935.

## Disposable PostgreSQL operator command

This checks the exact code in a new checkout, creates a local Docker PostgreSQL
database, runs the full suite and removes its test container through the script's
EXIT trap. It does not call Google APIs, change the shared checkout or deploy.

```bash
bash -c 'set -euo pipefail; release_dir=$(mktemp -d /tmp/wzos-release-cf35780.XXXXXXXX); test -d "$release_dir"; git clone --quiet --single-branch --branch codex/preproduction-modules https://github.com/rbandrews2/enterprise-gemma2.git "$release_dir"; cd -- "$release_dir"; git checkout --quiet --detach cf357802f6d979667225ebb0eed3ce5cea19d826; bash scripts/test_postgres_accounts.sh'
docker ps -a --filter name=wzos-db-test --format '{{.Names}} {{.Status}}'
```

Stop if clone/checkout fails; confirm HEAD before running. A zero-skip PASS and
independent test-container cleanup evidence are required. Supply no real database
connection string. The existing script reuses the cached PostgreSQL image.
The first operator attempt reported an empty clone destination and did not run
tests. The revised single-line command confines variables to one Bash process,
uses an explicit /tmp destination and stops immediately on a failed step.
The revised Docker attempt was blocked downloading postgres:16-alpine after
300 seconds; no test result was produced. Use the existing
scripts/test_postgres_native.sh harness in the verified candidate checkout when
native PostgreSQL binaries are available. That harness previously passed an
older candidate in Cloud Shell; current installation and this candidate's result
still require verification. It avoids Docker and uses a temporary private UTF8
Unix-socket cluster with automatic cleanup. Do not replace this with the staging DB.

## Configuration and migration controls

Do **not** run the historical deploy_accounts_staging.sh unchanged: its fresh
image excludes downloaded sources, and its `--set-env-vars` can replace settings
now used by session/passkey authentication and provider integrations.

Capture the live configuration privately first. Preserve the runtime service
account, IAM-only access, Cloud SQL attachment, Secret Manager bindings, file
bucket, trusted origins, auth header, passkey origin/RP ID, session configuration,
scaling/timeouts and any existing provider configuration. Never print secret
values or copy the service export into Git. Do not enable providers to make a
deployment look operational. Use an image-only staging update and check the
resulting effective configuration against the private pre-deployment export.

Startup DDL is a migration when deploying, even with IF NOT EXISTS. Review
docs/migrations/20261009_employee_directory.sql,
20261009_messaging_sms.sql, 20261009_enterprise_dispatch.sql and
20261009_training_content.sql alongside existing account, time-correction,
form-submission and report-snapshot startup definitions. Verify compatibility
against the disposable PostgreSQL database before shared deployment. Confirm
actual live schema before deciding which statements are new; this preparation
does not claim a schema diff against the live service.

## Rollback

The [Cloud Run CLI](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update)
supports image updates with `--no-traffic`. Google's
[environment configuration guide](https://docs.cloud.google.com/run/docs/configuring/services/environment-variables)
documents replacement versus incremental environment updates. These commands
are a reviewed deployment sequence, **not executed by this preparation**:

```bash
umask 077
rollback_dir=$(mktemp -d "$HOME/wzos-rollback-cf35780.XXXXXXXX")
gcloud run services describe wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$rollback_dir/service-before.json"
gcloud run services get-iam-policy wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --format=json > "$rollback_dir/iam-before.json"
# After verified transfer, all release gates and budget/configuration review:
gcloud builds submit context --project=enterprise-gemma2 --tag=us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts:cf35780-sources
# Resolve and record the build's immutable digest before this image-only update:
# gcloud run services update wzos-v2-accounts --project=enterprise-gemma2 --region=us-central1 --image=VERIFIED_IMAGE_AT_DIGEST --no-traffic
```

Keep the prior staging traffic target until candidate acceptance. An image update
still starts the application and can run startup DDL; no-traffic does not remove
the migration/backup gate. No IAM/origin/provider change is part of these commands.

Record the current immutable image digest and traffic target before updating.
On failed acceptance, restore the previous staging image/traffic and exact saved
configuration. Keep additive tables and audit history; do not drop tables as a
code rollback. Preserve Ray's existing passkey/test identity. V1, DNS, production
and customer delivery are outside this release.
