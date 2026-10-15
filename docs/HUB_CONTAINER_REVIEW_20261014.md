# Hub container security review

## Findings and repair

Google On-Demand Scanning of image4cc2f391 reported74 occurrences: five HIGH,
six MEDIUM,37 LOW,25 MINIMAL and one without a severity classification. This
does not contradict the57-package active Python audit: the container scanner
also inspected Debian packages and the obsolete pip25.0.1 wheel bundled with
Python's offline ensurepip bootstrap.

Repair build76510b57-38b2-48fd-8bf8-9a990cd23df7 SUCCESS. New immutable digest:
`sha256:fc87869680a0c6948d4116225ddf7ae22de6a659d0264e31351a251367465f06`.
It inherits tested source5a3ac86 and its frozen knowledge library, applies Debian
updates including libpcre2-8-0 version10.46-1~deb13u3, and removes ensurepip
(unused runtime offline package bootstrap). Active pip remains26.2.1. Runtime
creation of pip-equipped virtual environments is intentionally unsupported;
application operation does not require it. No application code or database
contract changed. In-image synthetic acceptance, active package version checks,
pip check, non-root UID10001 and139 frozen-file hashes PASS after the OS update.
Final image rescan must be recorded before release; do not call this zero-CVE.

## Residual high findings: no Debian13 stable fixes currently available

- CVE-2026-9538: Perl Archive::Tar memory exhaustion. Image check confirms the
  Archive::Tar module is absent. The scanner flags its source package perl.
  [Debian record](https://security-tracker.debian.org/tracker/CVE-2026-9538).
- CVE-2026-54371: privileged recursive getfattr/setfattr path traversal. Both
  utilities are absent. [Debian record](https://security-tracker.debian.org/tracker/CVE-2026-54371).
- CVE-2026-54369 and CVE-2026-54370: libacl pathname functions and privileged
  ACL-tool races. getfacl/setfacl are absent, but the library remains; utility
  absence alone does not establish no exposure. Application runs unprivileged
  and does not invoke these ACL functions or privileged path operations.
  [Library record](https://security-tracker.debian.org/tracker/CVE-2026-54369),
  [tool record](https://security-tracker.debian.org/tracker/CVE-2026-54370).
- CVE-2026-85091: zlib nonblocking gzwrite/gzprintf buffer handling. Runtime
  reports zlib1.3.1; upstream description discusses1.3.1.2–1.3.2, while Debian
  still lists the stable source package vulnerable. Applicability is unresolved;
  do not declare a false positive. WZOS does not use those nonblocking gz*
  interfaces. [Debian record](https://security-tracker.debian.org/tracker/CVE-2026-85091).

These are tracked residual risks, not patched findings or a certification.
Do not mix Debian unstable libraries into the production image to silence them.
Recheck stable security updates before subsequent releases; fail the release
gate on any new/unreviewed high, critical or available fix. Existing runtime
has the older affected base plus framework advisories, so the repaired image
improves that baseline while retaining explicit residual risk.

File malware scanning/quarantine, real billing/security feeds and organizational
SOC2 evidence remain separate unfinished work.
