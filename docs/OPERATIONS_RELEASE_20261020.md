# Operations release - October 20, 2026

## Candidate and scope

Frozen runtime candidate: edd310b (codex/preproduction-modules). Includes the
31f0e05 persistent Smart Field Voice receipt and admin office-alert repair, plus
the separately gated Ask Atlas context-first implementation and source refinements.
No new customer DDL, IAM, secret grants or provider activation. Preserve active
Voice, existing weather configuration, organization isolation and edition/roles.
DOT search/inference remain off pending actual source and bounded model acceptance.

Rollback baseline: wzos-v2-accounts-ui-6047e5b. The release helper reads and pins its
immutable image, validates unchanged production traffic/configuration, stages the
candidate with no traffic, then verifies runtime identity/resources/secrets/policy.
Public asset/auth/version checks follow cutover; failed public checks restore the
baseline. No forced reload of an unsaved report.

## Verified acceptance before deployment

- Fresh Cloud Shell: admin@workzoneos.org, enterprise-gemma2, baseline at100%.
- PostgreSQL gate:878 tests,397.152seconds,0failures/0errors/0skips.
- Node gate:163tests,0failures/0skips.
- Production preflight PASS; backup/schema compatibility PASS.
- Browser: real receipt code renders a restored immutable synthetic receipt beside
  submission controls. Desktop screenshot and mobile390px iframe evidence saved
  under ignored.local-data/receipt-preview. Mobile content375px equals viewport375px
  (the remaining15px is the iframe scrollbar); no horizontal overflow.
- User report: correct Voice objects/counts. Read-only live inspection found one
  October19 Voice draft and no corresponding received Daily Work Report in Forms
  hub. Do not represent that draft as delivered. No real report was edited/sent.

Cloud evidence pointer: $HOME/wzos-operations-release-path.txt.
This host's directory: /tmp/wzos-operations-20261020.sJ8jY6De.
Gate logs, schema/backups, before/after service configuration, immutable build
identity and rollback command stay in the private evidence directory.

## Deployment outcome

LIVE: wzos-v2-accounts-ui-edd310b at100% traffic; deployment exit0.
Build02e06e97-780d-45c6-aba4-5da764d4aba6 SUCCESS.
Immutable image sha256:067641e5b1f5a44868d6656fd03e3187d505c01227e85a3c3c0b33e5bb2b264d.
Public application version2444c54a1b7aac271259373c.
Build/drift/staged/live/traffic checks all PASS. No rollback was triggered.
Public source assets match the frozen candidate, including field-voice.js/.css,
review-workflows.js and gated Ask Atlas assets. Anonymous account, Voice, DOT and
office-summary requests are denied. Existing Daily origins remain present in CSP.

The signed-in browser was intentionally reloaded with no unsaved edits. It returned
to sign-in (the existing non-remembered-session policy); user sign-in requested for
authenticated browser acceptance. Do not claim a real report was submitted or a
new admin notification was seen after deployment until that check is completed.

## DOT activation boundary

Fresh VDOT publication-page read confirms the governing manual/companion distinction
and project-date exceptions. Existing indexed copies and local page renders remain
preserved. No new extraction/page/formula approvals or paid model calls in this
release step. Some prior Cloud Shell /tmp OCR evidence is no longer present on
this host; do not treat a retained home pointer as proof those artifacts survive.

## Final alert-placement follow-up

Authenticated live acceptance on edd310b confirmed the admin alert and its Open
office forms link work. It also exposed the dashboard initializer prepending its
content ahead of the alert. Repaired in3737af7: anchor the alert before main; on
mobile Home place it after the organization card in the sidebar-based Home list.
This is an in-page office reminder, not an OS push, SMS or email notification.

Final candidate3737af7bd93fda3c45913ffdf284fbefbb74a7a2 passed PostgreSQL878 tests
in387.932seconds and Node163 tests, zero failures/errors/skips. Backup/schema
preflight passed. Final build:e8e2f67d-f6f9-4123-b816-f04ad924d863. Evidence directory
/tmp/wzos-office-alert-20261020.Y6Db8vH3, same home pointer as above. Rollback for
this follow-up is ui-edd310b, preserving the already-live receipt repair.

Cloud Shell's browser connection was lost after build submission; read-only
recovery failed and the CUA runtime reset. No duplicate build/test/deploy was
launched. Final public assets independently match3737af7, including the relocated
alert. The full public live checker passed: asset hashes, unsigned API denial,
Daily CSP origins, public HTML and app version06cb438e96196bd4b724c67b.
Local evidence:.local-data/final-public-3737af7/live-version.json. Windows Git
archive text used CRLF; canonical LF copies were required to compare with the
Linux runtime. Preliminary raw Windows byte/fingerprint comparisons are not
release failures and were not used to identify a revision. The version is opaque;
do not infer its image digest from a local fingerprint reconstruction.

The final image digest, final traffic JSON and final guarded-runner exit were not
independently reread after the browser disconnect. Preserve that distinction from
the directly verified serving code. Post-follow-up visual placement acceptance
remains open; the prior authenticated alert/link acceptance and synthetic receipt
screenshots remain valid for their stated scope. No actual user report was sent.
