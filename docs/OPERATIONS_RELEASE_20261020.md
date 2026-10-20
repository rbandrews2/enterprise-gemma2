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
