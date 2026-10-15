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
