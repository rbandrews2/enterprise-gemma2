# October 11 preparation — historical

Superseded by STAGING_DEPLOYMENT_20261011.md for deployment, Maps and provider
entry status. The paragraphs below describe the earlier pre-build checkpoint.

Ray resumed and authorized replacing V1 with V2 after release acceptance, verifying
Maps/Twilio/SendGrid and other integrations, and protecting organization data.
UI/workflow changes remain expected. This supersedes older no-cutover scope;
it does not claim provider readiness or authorize widening IAM without required
confirmation. Existing150USD October8-17 cap remains. Ray reports about35USD
current billing; use115USD planning headroom with billing lag, not a live ledger.

## Verified in this session

- Read-only live schema comparison on exact applicationcf35780: no incompatible
  existing columns. Missing module tables match reviewed additive migrations.
  Evidence: /home/admin_/wzos-schema-20261011.iinTcucv/schema.json.
- Temporary SQL proxy stopped; no listener on5544 after the check.
- Backup1791698400000 SUCCESSFUL, ended2026-10-11T07:37:03.191Z.
- Fresh service/IAM rollback exports private in /home/admin_/wzos-release-20261011.
- Secret Manager metadata lists GOOGLE_MAPS_API_KEY and staging auth/database
  secrets. No Twilio/SendGrid secret names seen; no values printed.
- Standalone Cloud Shell in the in-app browser works after closing the competing
  embedded shell tab. Native paste must focus the fresh Terminal input index.
-80MB upload stalled atzero and was cancelled. Build instead archives exactcf35780
  and inherits the pinned rollback image's source library. New pinned requirements
  are installed. All source-file hashes/index integrity and snapshot SHA256 must
  pass at build time; mismatch blocks release. No source-status promotion.
- Build66e0492f-c516-48d4-8ae2-0724ab0c3074 started asynchronously. Acceptance,
  immutable result digest, image-only no-traffic deployment and routing remain open.

## Provider and release gaps

Twilio runtime needs SID/token, sender/MessagingService and signed reachable
callback URL plus controlled recipient acceptance. SendGrid has no active adapter
found in current services/shared Python code; requires sender verification, secret
binding and an implemented delivery adapter. Maps adapter exists but runtime
binding/API restrictions and actual imagery remain unaccepted. Google Meet uses
external links; automatic creation needs organizer OAuth. Atlas live inference
must be tested independently; source availability alone is not AI readiness.
Closed-app push and durable completed printable forms/signatures remain open.

Next read the build status, preserve its digest, deploy image-only with no traffic,
verify configuration/IAM/auth/private files, then switch restricted staging traffic
and run integrated admin/member and two-organization scenarios. Resolve public
hostname routing and outstanding provider/security/workflow gates before V1 cutover.
