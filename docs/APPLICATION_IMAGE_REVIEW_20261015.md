# Application image review - October 15, 2026

## Verified outcome

Reviewed immutable application image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:ef31216bc772a0233b7c59a9e219dcd9b17f6c6f2c8ed058270a9a009676ab9d`

- Image build `ed80918c-ca2d-48d1-921f-8dafab07ab29`: SUCCESS.
- Vulnerability review `7c7076f5-e5a9-4443-a502-40e633b3ad7d`: SUCCESS, review.exit=0.
- Findings: 67 total; critical 0, high 5, medium 1, low 36, minimal 25.
- fixAvailable=0; no pip findings. All six installer findings from parent
  `73e47d4d...` are absent. This is an advisory snapshot, not security clearance.
- Dependency consistency, source verification (139 files), synthetic HTTP/role/
  origin checks and uid10001 passed inside the repaired image. Source4380849's
  694 PostgreSQL/no skips and 108 Node results remain applicable; no app logic,
  requirements or DDL changed in the installer repair.

## Permission cleanup

Ray explicitly approved this repaired-image review within the original expiry.
The existing four-permission wzosImageReview binding used the original condition
ending `2026-10-16T00:26:17Z`; no extension was applied. The harness removed the
binding immediately after review. Independent project IAM read returned
`REMAINING_SCAN_BINDINGS []`. No temporary scan permission remains.

## Runtime applicability evidence

Inventory build `4b7b05b3-4905-4510-9025-9f26a161b105`: SUCCESS, config43c05ee.
It ran the exact digest above with network disabled, read-only root filesystem,
capabilities dropped, no-new-privileges, uid10001 and no credentials/customer data.
Those are diagnostic job controls, not a claim about the production configuration.

| Finding | Actual image evidence | Assessment still required |
| --- | --- | --- |
| CVE-2026-9538 (Perl Archive::Tar) | perl-base5.40.1-6+deb13u1 exists; loading Archive::Tar fails | Vulnerable module absent in this image. Retain evidence and recheck if image/dependencies change. |
| CVE-2026-54371 (attr tools) | getfattr/setfattr absent; libattr1 remains1:2.5.2-3 | Command-line exploit prerequisites absent; do not equate this with removal of the library. |
| CVE-2026-54369/54370 (ACL) | getfacl/setfacl absent; libacl1 remains2.3.2-2+b1 | Library-based pathname functions still require reachability/privilege assessment. Open. |
| CVE-2026-85091 (zlib) | Python compile/runtime1.3.1; linked to /lib/x86_64-linux-gnu/libz.so.1; distro1:1.3.dfsg+really1.3.1-1+b1 | Debian reporting and upstream affected-range discussion need disposition. Do not suppress solely on version text. Open. |

Static search of tracked services/shared Python found no Perl Archive::Tar,
getfattr/setfattr/getfacl/setfacl, ACL pathname or gzprintf/gzvprintf/gzwrite calls.
This does not establish native/transitive dependency reachability or rule out
other attack paths. Non-root execution reduces privileges but does not eliminate
all consequences. No unstable distro packages or speculative patches installed.

Primary issue references inspected during the preceding review:

- https://security-tracker.debian.org/tracker/CVE-2026-9538
- https://security-tracker.debian.org/tracker/CVE-2026-54371
- https://security-tracker.debian.org/tracker/CVE-2026-54369
- https://security-tracker.debian.org/tracker/CVE-2026-54370
- https://security-tracker.debian.org/tracker/CVE-2026-85091

## Evidence and next checkpoint

Cloud pointer: `$HOME/wzos-security-app-release-latest.txt`.
Review: `repaired-image-review/build.log`, `findings.json`, `review.exit`,
`condition.txt`, `after-iam.json`. Inventory: `runtime-inventory.log` and
`runtime-inventory-build.id`. Parent findings remain in `application-review/`.
Preserve these private evidence files outside Git; no secret values were printed.

Next finish high-finding applicability/disposition, then the real app metadata-
token and synthetic upload/hold/admin-alert/rescan/release acceptance, including
tenant/member boundaries. Follow reviewed schema, fresh backup and security-capable
rollback gates before cutover. Deployment applies additive startup DDL. Retain
holds/audits and never roll back to code that ignores them after activation.

No public deployment, schema writes, app configuration, DNS or customer sends
occurred in this review. The public hub remains unchanged. Live Atlas31B inference,
Daily two-device media acceptance and checkout remain separate unfinished gates.
