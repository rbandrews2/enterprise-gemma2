# Atlas live workflow: observed cold-start timing failure and repair

## Approved exercise and actual outcome

Ray approved one disposable live workflow execution using existing app identity,
test-only image53b5189b, one task/parallelism1/retries0, 1CPU/512MiB, timeout300s,
temporary SQLite/local files and no public endpoint/secret bindings/SQL connection.

The first job creation stopped before execution because the preflight expected
integer300 while Google's JSON returned timeoutSeconds as string"300". Cleanup
removed the job; an independent full jobs list returned[]. Helper646e5fc accepts
the exact string/integer value without relaxing the limit. This was not a test run.

The actual approved execution then failed at `real_clean_upload`. It did NOT pass
the complete workflow. The job was removed; independent jobs list again returned[].
No customer files/messages, production schema, public configuration or IAM change.

Scanner request logs showed one POST/scan HTTP200 at
2026-10-16T03:10:45.052368Z (October15,11:10:45p.m. Eastern), latency31.759528623s.
The caller read timeout was30s, acceptance window35s. This strongly supports a
cold-start read-timeout diagnosis. The response body was not captured, so do not
claim its engine verdict was clean merely from HTTP200. The request did reach the
private scanner's authenticated handler; its exact caller/audience settings match.
The application correctly retained the upload as held rather than declaring clean.

## Narrow repair

Sourcee9ad09a changes scanner HTTP I/O wait30->65s and verdict acceptance35->70s,
matching the receiving service's existing60s request limit plus transport margin.
Connection and metadata HTTP timeouts stay5s. One scan attempt only; no retry,
redirect, fallback, signature/audience/hash/schema/size verification or hold/release
rule is removed. Acceptance window still rejects a late verdict; it is not a hard
interrupt of a blocking socket. Actual worst-case duration can exceed that window
before the bounded I/O timeout returns, as documented in the transport notes.

Regression case models a31.76s valid response and asserts read65/connect5 plus
one request. Existing late-verdict test moves to71s. Full PostgreSQL validation and
the test-only derivative build are required before another live run. Frontend
unchanged; existing108 Node results remain applicable.

## Evidence

Existing `$HOME/wzos-security-app-release-latest.txt`:

- live-workflow/: pre-execution serialized configuration and cleanup evidence.
- live-workflow-execution/: actual execution/configuration/cleanup evidence.
- live-workflow-recent-logs.json: explicit `SECURITY_WORKFLOW_FAILED real_clean_upload`.
- scanner-during-workflow.json: authenticated request status/timing.
- jobs-after-first-create.json and jobs-after-live-workflow.json: independent[].
- cold-start-source/: owned detached source worktree; original source checkout preserved.
- cold-start-postgres.log/exit and cold-start-build.json: repair gate evidence.

Do not rerun the failed image to obtain a warm-only pass. Next test must use the
repaired immutable derivative, preserve min0 scanner behavior and keep failure
cases explicit. A new execution/new test image with the app identity requires
fresh action-time approval; the original single execution was consumed.
Remaining five high OS findings and full deployed browser/Firebase/Cloud SQL/
Google Storage acceptance remain separate release gates. No public cutover here.

## Repair validation complete; next live execution pending approval

Exact sourcee9ad09a passed695 PostgreSQL tests in262.617s: failures0/errors0/
skipped0, cold-start-postgres.exit0. Node sources unchanged;108 prior Node passes
remain applicable. No unrelated source or dependency update.
Buildace779fe-a21d-435b-b8a4-cdbe2d5772bb SUCCESS. Repaired test-only image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-security-workflow@sha256:fb0ef7929cda0530ffad9c03b367c50565731a310e56db7541fb61837d1327ad`
The26 mocked workflow checks passed inside this exact derivative of appimageef31216b.
These are not a live repaired-image PASS. Earlier live attempt consumed the approved
single execution and failed real_clean_upload; don't relabel it or run it again.

Proposed new approval: one execution using repaired imagefb0ef792 and the existing
wzos-v2-accounts service account; same named disposable job, us-central1, task1,
parallelism1,retries0,1CPU/512MiB,300seconds. Use repaired helper646e5fc. Save in a
new private evidence directory, remove job immediately and independently verify
absence. No IAM role changes, secrets, SQL/bucket configuration, customer files,
messages, public endpoint or production traffic/schema updates. The job inherits
its app identity's existing permissions despite not binding secrets; this is the
security-sensitive action requiring confirmation. Old private scanner staysmin0/max1.
Full deployed browser/Firebase/cloud-persistence acceptance remains later work.
