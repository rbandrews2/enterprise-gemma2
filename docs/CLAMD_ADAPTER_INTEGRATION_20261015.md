# Atlas streamed ClamAV adapter

## Reuse and scope

Ray approved reusing Claude's scanner approach after the archive review. The
INSTREAM chunk framing is adapted into the existing Python backend. Claude's
Supabase authority, Render listener, Netlify policies, automatic deletions and
client-only telemetry are not introduced. Existing Google-backed accounts/files,
organization access, incidents, admin notifications and reviewed recovery remain
the enforcement boundary. No added API, schema or Python dependency.

`services/workspace_preview/clamd_scanner.py` provides a local Unix-socket adapter.
It streams bytes, never file names or storage paths, and accepts only a complete,
bounded response. One active scan per application process; 10MiB input limit;
20-second total transport deadline; 4KiB maximum reply. Engine/database identity
and a signature timestamp within the past24 hours are required before each scan.
Raw signatures/output are not returned to users or the model. A limit/encryption/
macro alert is held like other suspicious content; this is not a forensic verdict.

## Configuration (disabled by default)

- `WZOS_CLAMD_SOCKET`: absolute private Unix socket path.
- `WZOS_CLAMD_CONFIG`: absolute path to the generated daemon configuration.
- `WZOS_FILE_SCAN_REQUIRED=1`: mandatory scan gate, enabled only after acceptance
  and legacy inventory review. Configured-engine failures already retain holds.

When either daemon variable is supplied, the daemon is selected; malformed or
partial configuration fails closed without falling back to the CLI adapter.
With neither variable present the existing `WZOS_CLAMSCAN_PATH` CLI adapter remains.
No service is started automatically by an app request.

Operator must use `daemon_config(socket_path, database_directory)` and launch
`clamd --config-file=<that file>` in UTC. Config must be a regular, trusted-owner,
non-group/world-writable file; socket parent must not be group/world writable;
socket must be trusted-owner and mode600. Policy rejects duplicate/extra options,
TCP listeners, weakened alerts/limits and symlinks at the checked locations.
For versions requiring detached CVD code-signature certificates, the optional
third `daemon_config` argument supplies `CVDCertsDirectory`. This must be a trusted,
non-group/world-writable directory of vendor certificates. The acceptance helper
uses the certificate bundle extracted from the same signed distro packages and
passes it to both Freshclam and clamd. It never disables signature verification.
The config includes official-database-only, bounded unpacking, one worker and
alerts for exceeded limits, encrypted content and Office macros.

The client validates the operator config, not a remote attestation of how an
arbitrary daemon was launched. Deployment must bind the socket to the process
started with that exact file and protect its parent paths. Production process/
container isolation, signature updates, memory, health and restart supervision
still require acceptance. Do not colocate the engine in the small web container
without sizing. No public raw clamd TCP endpoint is supported.

## Validation and operation

### Archive completeness guard

Real ClamAV 1.5.4/28154 returned clean for a ZIP containing an 11MiB member
despite the configured 10MiB file limit and AlertExceedsMax. Both adapters now
apply an independent ZIP completeness guard before contacting the engine.
This returns an error/hold, not a malware diagnosis: no clean release is allowed.
The guard bounds central-directory parsing before allocation, checks member CRCs
in memory without filesystem extraction, and enforces 1000 entries, 10MiB per
member, 50MiB total expansion and a five-second checking deadline. Malformed,
encrypted, nested and unsupported-compression ZIPs remain held for review.
Ordinary stored/deflated ZIPs still require a fresh engine clean verdict.
This is not proof of complete inspection for every archive/document format;
other container formats, real encrypted/macro fixtures and production isolation
remain separate acceptance work. No heuristic or engine guarantee is universal.

- `tests/test_clamd_scanner.py`: protocol framing, fragmented replies, strict
  verdicts, stale/future signatures, missing engine, bounded work and Linux policy.
- `tests/test_security.py`: daemon verdict persists the existing incident/hold;
  release stays blocked. Existing suite covers org/member/admin containment.
- `scripts/check_clamav_engine.py --database-dir <official-db-directory>
  --evidence-dir <private-evidence-directory>`: explicit Linux real-engine check.
  Requires already-installed clamd and fresh official databases. Starts its own
  foreground daemon in mode700 temporary directory, scans benign bytes, the
  harmless standard antivirus test fixture and a bounded compressed-size-limit
  fixture, then verifies unavailable-engine behavior. Stops owned daemon even on
  failure; evidence includes statuses, version and child peak RSS, never file bytes.
  No customer files, public endpoint, cloud provisioning or credentials involved.

Real engine acceptance is separate from mocked protocol tests. Do not mark
production scanning active before engine and integrated release gates pass.
This increment is backend only; no dashboard/UI changes. Existing-file backfill,
signature updater supervision, infrastructure feeds and external admin delivery
remain tracked work. Keep scan holds enforced during rollback; old pre-security
images do not understand these holds.

Official references:

- https://docs.clamav.net/manual/Usage/ClamdProtocol.html
- https://docs.clamav.net/manual/Usage/Scanning.html
- https://docs.clamav.net/manual/Usage/SignatureManagement.html
- https://github.com/Cisco-Talos/clamav/blob/main/docs/man/freshclam.conf.5.in

Provenance: local `security-kit.zip`, SHA256
`da19cb8a022bdc4807922c22df52658876aef3481d3177680ebae1e24b8b0bd5`.
See `CLAUDE_SECURITY_KIT_REVIEW_20261015.md` for defects and provider audit.
