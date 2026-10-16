# Corrected security workflow acceptance - October 16, 2026

## Change

Source9ffb411 changes test tooling only. The detection upload is now an admin-created
Forms Hub document with the intact standard68-byte EICAR fixture as a ZIP member.
It uses the existing supported DOCX upload route; no file-type or malware protection
is bypassed. The invalid PDF wrapper is retained only as an engine diagnostic.
The mocked scanner reads the intact member instead of searching arbitrary bytes.
Failure diagnostics expose only an allowlisted scan-status label, never file contents,
provider bodies, credentials or identity claims.

The workflow now has29 checks: the previous26 with detection exercised through the
supported team-document path, plus publication rejection, member rejection for the
unpublished detected file, and cross-organization file denial. Admin download of
the infected file returns423; publication and release return409. Members receive404
for an unpublished team form rather than access to its metadata. Existing member423
checks on held work-order files remain intact. The final other-org incident-list
check now completes after detection and release prevention.

## Completed validation

- Python syntax and Bash syntax PASS.
- Corrected mocked workflow29 PASS in the existing Cloud Shell test environment.
- Real local ClamAV engine workflow29 PASS, with injected app identities and
  temporary SQLite/local files. Actual output identifies mode=engine and
  identity="local engine; injected app identities"; this is not Google metadata
  authentication or a deployed browser/CloudSQL/GoogleStorage acceptance claim.
- The outage remains an explicitly injected503, not an observed production outage.
- Isolated daemon is stopped on completion. No customer files/messages, production
  schema, IAM grant, public service configuration or traffic changes.
- Application dependencies and source unchanged;695 PostgreSQL/108 Node results
  remain applicable. No redundant full suite or application rebuild.

Private cloud evidence pointer: $HOME/wzos-fixture-workflow-latest.txt.
Files: mocked.log, workflow.log, engine-results.json, engine.log, engine.exit,
clamd.log, package-download.log, freshclam.log and launch.log.
Owned source worktree: /tmp/wzos-fixture-workflow.IrVkGbjG/source.

## Final remote-path check

Preparing a new test-only derivative using Dockerfile.security-workflow and the
unchanged reviewed app parent ef31216b. The build itself runs29 mocked checks.
Do not deploy this image as a web service. No new live job has been created.

The previous single fb0ef792 execution approval is consumed. A new live job with
the corrected immutable image and existing app identity needs scoped action-time
approval: wzos-security-workflow, us-central1, one task, parallelism1, retries0,
1CPU/512MiB,300s; no secrets/SQL/bucket configuration, no public endpoint or
customer sends; immediate removal and independent absence verification.
The existing identity retains its effective permissions while attached. This is
not a scanner-only identity. Updated helper requires29 live checks and Google
metadata identity. No grant expansion or public cutover is part of this check.

Engine evidence: ClamAV1.5.4/28155; engine.exit0; daemon_stopped true;
workflow_checks29; child_peak_rss_kib999216. Build453c0c18-30b8-476d-915d-3f1763bb7647 submitted.


## Immutable corrected image ready

Build453c0c18-30b8-476d-915d-3f1763bb7647 SUCCESS. Its Docker build runs the
corrected29 mocked checks. Exact immutable test-only image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-security-workflow@sha256:4d90f2dde45188afddc4cec5256fcb3a8c16bbcd53c5466073127b616c18927d`

The parent application image and dependencies are unchanged. Only the synthetic
harness/transport source is overlaid, so no new package-inventory review or IAM
review grant was requested. This is not an application vulnerability waiver.

Use the corrected helper copied into the cloud evidence directory as
run_security_workflow_job.sh. build-final.json and image.txt preserve the exact
artifact. No job has launched; approval is pending for this new image/workload.
