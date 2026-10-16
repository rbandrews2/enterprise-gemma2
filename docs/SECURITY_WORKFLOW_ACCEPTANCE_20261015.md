# Atlas security workflow acceptance

## Assessment completed; production clearance remains conditional

Image `ef31216b...` still has five HIGH findings; no finding is silently suppressed.
The exact digest and raw scan/inventory evidence are in
`APPLICATION_IMAGE_REVIEW_20261015.md`. Six fixable pip findings were removed.

| CVE | Assessment for this image | Release treatment |
| --- | --- | --- |
| 2026-9538 | The affected Perl Archive::Tar module is absent. | Recorded as component absent for this exact image; re-evaluate on dependency changes. |
| 2026-54371 | Affected getfattr/setfattr utilities are absent. The libattr library is present. | Normal app upload path does not invoke those tools. Retain vendor finding and package watch. |
| 2026-54370 | getfacl/setfacl are absent; reviewed app code has no ACL command or pathname-function calls. | Reduced reachability; no claim that libacl itself is fixed. |
| 2026-54369 | libacl is present. The described privilege-escalation prerequisite is a privileged caller acting on an attacker-controlled path; the app runs uid10001 and does not invoke the affected functions in reviewed Python paths. | Mitigated in reviewed normal upload workflow, not proof about every native/transitive path. Retain residual risk pending package update/release review. |
| 2026-85091 | Actual linked zlib is1.3.1. Debian still marks its package vulnerable. Upstream's issue includes disagreement about earlier versions and a maintainer fix for the later writer implementation. | Classification unresolved; do not dismiss on version alone or apply an unreviewed custom patch. Keep production finding open. |

Primary sources re-read October15:

- https://security-tracker.debian.org/tracker/CVE-2026-54369
- https://security-tracker.debian.org/tracker/CVE-2026-54370
- https://security-tracker.debian.org/tracker/CVE-2026-85091
- https://github.com/madler/zlib/issues/1310 (including October4 affected-range question)
- https://github.com/madler/zlib/commit/81cc0bebedd935daeb81b0b6e475d8786b51af3d
- https://raw.githubusercontent.com/madler/zlib/v1.3.1/gzwrite.c

This assessment permits continuing isolated synthetic validation. It is not a
blanket production vulnerability waiver or a claim of zero attack surface.

## Harness and completed preliminary validation

`scripts/check_security_workflow.py` creates temporary SQLite/local-file persistence,
injects synthetic verified claims into an in-process TestClient and never opens a
listener. Test claims are not accepted by the public application. Existing app
code, roles and organization/edition contracts are reused without modifications.

Mocked mode passed26 checks against source4380849 and existing cloud dependencies:
member join/upload/download, anonymous/member admin rejection, separate Core and
Enterprise organizations, quarantine and held download, cross-tenant rejection,
injected HTTP503 and blocked release, application recreation with durable holds/
admin alerts, red dashboard, clean rescan retaining hold, stale-action rejection,
explicit release, original-byte match, resolution, audit and detected-file hold.
This is harness/contract validation; scanner verdicts and Google identity were
mocked. Evidence: existing app release pointer, workflow-mocked.log/exit.

## Proposed live runtime test - approval required

Build a test-only derivative of exact imageef31216b containing the reviewed harness.
The Docker build runs mocked mode again inside that exact parent environment.
Do not deploy the test image to a web service. Its only command is the test harness.

Proposed disposable Google Cloud Run job `wzos-security-workflow`, us-central1:

- One task, parallelism1, max retries0, timeout300seconds, 1CPU/512MiB; no GPU.
- Use existing app service account
  `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com` so the existing
  RemoteScanner obtains its ID token from Google's runtime metadata service.
- No new IAM role/binding, secret attachment, SQL connection, bucket configuration,
  public endpoint, scheduling or model call. Temporary SQLite/files only.
- Live clean and harmless EICAR-containing synthetic PDF fixtures go only to the
  already private WZOS scanner. An explicitly injected HTTP503 tests failure handling;
  do not misreport that injection as an observed scanner outage.
- Account verification is injected for this in-process test; production Firebase
  login, Cloud SQL and private Google Storage acceptance remain separate gates.
- SMS/Daily/model actions disabled. No customer messages, files or live schema writes.
- Save results, remove the newly created job immediately afterward and verify absence.
  Refuse to overwrite a pre-existing job. Failure does not justify broader IAM.

Assigning the app identity to a new job is security-sensitive: the identity retains
its existing effective project/service permissions. Lack of secret bindings does
not remove those permissions, and metadata could issue tokens using that identity.
The reviewed harness does not call those other APIs. Action-time confirmation is
required before creating/executing this workload; the previous scan-only approvals
do not authorize it. The exact helper is scripts/run_security_workflow_job.sh.
Public traffic/configuration and scanner IAM stay unchanged.

## Completion limits and next gates

A live PASS accepts the real metadata-token/remote-scanner path plus in-process
upload/hold/notification/recovery/audit control flow with disposable persistence.
It does not replace the694 PostgreSQL regression evidence or actual cloud-storage,
Firebase/browser and full deployed-app acceptance. Preserve these distinctions.
Retain held files/audits during any later rollout/rollback and never disable scanning
or expose direct ingress to make a candidate easier to test.

## Test-only image ready; live job not created

Build09622ebb-2e0e-4b48-9a85-204b14e8c177 SUCCESS, source2cbb7b4.
Immutable test-only image (never a public web-service release):
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-security-workflow@sha256:53b5189b78f9d766c42b83bdc6025a72159a727fa0f9295292e2165231bab0ec`
Mocked26-check workflow passed both existing Cloud Shell dependencies and inside
this exact derivative of reviewed appimageef31216b. Shell identity/project freshly
verified admin@workzoneos.org / enterprise-gemma2, configcloudshell-2562.
Full unfiltered jobs list returned[]; proposed job name currently unused.
Helper bash syntax passed. Source application4380849 remains unchanged.
No live job/new workload identity, IAM grant, schema or public traffic change.
Next action requires approval for one300-second job using existing app identity,
with immediate job removal and independent absence verification. No new IAM roles
or secret bindings. The runtime identity retains all of its existing effective
permissions, so this is not described as a scanner-only identity.
