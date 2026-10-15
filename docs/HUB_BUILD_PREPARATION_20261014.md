# Tested hub image preparation — October 14, 2026

Scope: build/validate only. Ray asked to resume preparing the tested build while
away briefly. No runtime deployment, production traffic, new API credential,
IAM/secrets change or customer communication is performed by these helpers.

Application revision650aa5aa4127d190a92295f90ea6a1da162297c3 has passed native
PostgreSQL594/Node96/HTTP7; dependency audit57 packages, zero findings/skips.
Existing frozen-library base is the Daily immutable digest648516f7dd97505a1c7f5d2feb40bc013b2aea572ca84fd589dd8c51914cd2fb.

scripts/build_organization_hub.sh requires saved exact gate evidence and no active
PostgreSQL gate processes, verifies current production base/traffic, copies only
Git-tracked runtime sources and the image check helper, and submits a Cloud Build
with a20-minute overall timeout. It reinstalls patched requirements/pip as root,
restores non-root wzos UID10001 and verifies every frozen-library hash/index.
No downloaded documents, customer data, local credentials or environment files
are copied from the laptop or Cloud Shell into the build context.

Before the registry image is published, build steps check exact framework/pip
versions, synthetic admin/member/anonymous/cross-origin/body-limit boundaries,
new static assets, then audit installed image packages using an isolated temporary
tool environment inside a disposable container. The API token is not created.
Dependency inventory and audit JSON go to Cloud Build logs (package metadata only).
Known vulnerabilities or skipped audit packages must block release acceptance.
A dependency scan does not establish OS-image/CVE coverage or malware protection;
those are distinct release controls and remain explicitly recorded.

The script does not deploy/apply startup DDL. After SUCCESS, save the immutable
digest, verify audit/inventory/source provenance, refresh SQL backup/schema/budget
checks and prepare an exact config-preserving deployment/rollback. Publishing the
integration-key access paths requires applicable activation approval before any
production change. Do not assume an image tag, old shell session or Git push is
proof of a deployed/accepted application. Existing live service remains unchanged.

## Pre-build hardening and first build outcome

Initial build93fb2a80-da77-4260-8fd4-3f17b6fd7b53 failed before publication:
private build-context file modes prevented non-root access to the copied library
verification script. Patched Docker steps normalize root ownership and read/execute
permissions for runtime sources and script access, without making source writable
by the application user. Patched package reinstall and pip check had already passed.
No live revision or traffic changed; this failure did not publish a candidate.

Final review also found that unknown integration keys took the database's shared
write lock before authentication. Runtime5a3ac868085685a5e71169ceac21fa618cc405e9
rejects unknown/expired keys before that lock, then rechecks valid keys under lock
for revocation safety. Added SQLite/PostgreSQL regression coverage; full596-test
cloud gate is required, with the exact source recorded in final-gate-source.txt.
Dependencies remain identical to the audited650aa5a candidate; the image still gets
its own fresh audit. Do not use650aa5a as the final release source.

Container OS scanning APIs were not enabled in the read-only service query. The
Python package audit is not an OS-image scan. Google lists automatic/on-demand
scanning at$0.26 per scan: https://cloud.google.com/artifact-analysis/pricing .
No API/paid scanning feature was enabled during preparation. Before rollout,
record OS-image coverage and review the scoped setup if activation is required.

## Final built artifact

Source5a3ac868085685a5e71169ceac21fa618cc405e9: full cloud native596 PASS210.852s,
Node96 PASS/no skips. Cloud Build1685f954-4c4f-4f0a-9729-28c36871c0c1 SUCCESS:

us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:4cc2f391151e1aaf00d9ad29bc68c57779b808f75ed9034f23e3bcbb3af71bdd

Actual image checks PASS: exact patched framework/installer versions; UID10001;
139 source-library files; isolated route/security/asset checks. Installed-image
pip-audit57 packages, zero known findings and zero skipped packages. All build steps
SUCCESS; registry publication follows successful checks. This does not establish
OS-layer or malware-scan acceptance. App source is root-owned/readable, non-writable
by the app user. No production environment/secrets were supplied to the build.

Before/after Cloud Run spec and traffic match exactly; live Daily revision remains.
No deployment/DDL application or new key/IAM/secret/DNS/customer-send change occurred.
Next gates and applicable public API activation review: HUB_ROLLOUT_REVIEW_20261014.md.
Cloud evidence/private service snapshots: $HOME/wzos-hub-build-20261014; retain
failed first-build evidence separately. Local screenshot is ignored under
.local-data/hub-evidence/build-ready.png when captured; no credentials included.
