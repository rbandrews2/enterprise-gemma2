# WZOS current session handoff - October 18, 2026

## Bulk employee accounts — October23 (latest development checkpoint)

User requested bulk CSV and spreadsheet account creation. Implemented admin-only
Organization management / Team access action; CSV, single-sheet XLSX and pasted
spreadsheet rows; review duplicates/errors/access/seats, then explicit creation.
Five-row requests reuse managed account idempotency; same-admin unchanged uploads
recover pending reservations after a reload. No automatic invitations, no password
resets or saved upload credentials. No schema, dependency or IAM changes.
22 distinct focused Python checks and 185 Node checks PASS (affected cases rerun
following final repairs); synthetic browser review PASS. See
BULK_MANAGED_ACCOUNTS_20261023.md for exact evidence/reuse and constraints.
NOT DEPLOYED. Cloud Shell requires user authorization; PostgreSQL full integration
gate has not started. Run that gate and release checks before deployment. Do not
repeat accepted provider/SMS/Voice tests. Current live release remains 7a674b3.

## Managed onboarding LIVE — October23 (latest checkpoint)

Source 7a674b3 deployed as wzos-v2-accounts-ui-7a674b3 at100%; independent
readback PASS. Image6ee61100026337be919f39ccd1d3d3a55238dfdf2d0ed4c5bd636796354887e8;
version58a02875ab79dd307750c54a.937PostgreSQL/181Node PASS, zero skips.
Admin Team access can create Google-backed employee username/password accounts
with admin/member access. Invitations remain optional; first employee sign-in
requires own password. Existing identities are never overwritten. Three additive
tables reviewed; no passwords persisted. Approved create/update Google role bound
only to existing runtime, project-wide IAM scope disclosed and readback verified.
Ray email-bound Enterprise25 grant issued for ray@workzoneos.org, expiresOct30
05:31UTC; no activation code needed after email verification. CSV email replaced;
backup in Downloads. No real employee accounts created, no customer sends.
Provider transport/anonymous boundaries and schema/config/public gates PASS;
first real employee provisioning/password-change acceptance remains human work.
Details MANAGED_ONBOARDING_20261023.md. Evidence cloud
$HOME/wzos-managed-evidence-20261023. Operator helper d6cbc78 does not change
runtime candidate; no need to rerun accepted suites for documentation-only changes.


## Available updates LIVE — October23 (latest checkpoint)

User authorized release of available tested updates. App content b693d8b plus
release tooling a1d24d1 is deployed as wzos-v2-accounts-ui-a1d24d1 at100%.
Image e29aeee408ea92f2372774a8fa9562e6b2b05b8dc9efa9be49c6bc2fc0cff7dc;
version e83ce03ec082a537e4795648. Independent traffic readback PASS.
919PostgreSQL checks/430.662s and179Node checks Windows/Linux PASS, zero skips.
Schema compatibility/recent backup, staged settings and public asset/API gates
PASS. Includes header notifications, Enterprise communications guards, CSP and
dependency repairs, admin employee CSV roster import. Import's two additive
tables reviewed; rollback retains them and returns to pins-1022181839.
Narrow390px synthetic import and signed-in live dashboard/dialog/roster read PASS.
No live data imported or customer sends. No inference pilots repeated.
Prior checkpoint's additional-name fragment was a typo; user confirmed disregard.
Evidence $HOME/wzos-release-evidence-20261023; details AVAILABLE_UPDATES_RELEASE_20261023.md.
Cloud source /tmp/wzos-release-20261023.RFKngPNY/source contains checker72aef6b
as an operational-only overlay. Runtime/tests identical to tested candidate.
Remaining source/provider/human prelaunch checks are not claimed complete.

## Employee import — October22 (latest development checkpoint)

Admin-only Import employees implemented locally under Organization management,
Account and Employees: template, bounded UTF-8 upload, duplicate/error review,
explicit confirm, idempotent receipt and paginated organization-private roster.
No memberships/invitations/sends/seat charges created by import. Two additive
tables; review SQL and rollback in EMPLOYEE_IMPORT_20261022.md.16unique focused
backend and26existing account Node checks PASS; desktop synthetic browser receipt
accepted. PostgreSQL and integrated mobile/release gates remain open. Two Cloud
Shell binding attempts failed with stale-page capture; no cloud mutation/deploy.
Live app remains the configuration-only pins revision below. Additional-name
clarification requested; no name inferred. Do not rerun unrelated paid tests.

## Operational follow-ups / Voice human acceptance — October 22 (latest)

User confirms Smart Field Voice incident numbers/wording correct, notification
delivered inside WZOS, form reviewed and notification cleared afterward. Checked
off this exact scenario in main/human/Codex prelaunch lists. Do not repeat it
without a changed component/new concern; phone permission/offline/PDF acceptance
remain distinct. See VALIDATION_LEDGER_20261022.md for all accepted suite evidence,
repaired failures, source/image provenance and reuse rules. Durable cloud sweep1
folder has validation-index.json with log hashes,891full/119affected named cases
and Node174 totals. Never sum overlapping/repeated checks as unique coverage.

Numeric secret pinning is LIVE: wzos-v2-accounts-pins-1022181839 at100%, image
80c3819aa9e8d3ce38ccf47e87bd4015b40875768a54604e994da9674cb3c054 unchanged;
public marker7e5e09892935f9d2ba1ba6d6. Database/auth refs now1, with same runtime
spec except those keys, same policy/scaling, assets/auth/security/public401PASS.
Prior ui-16d0905 retained. This is a config-only repair, not deployment of the
development branch's UI/security/dependency code. New source tool50557db.

Initial marker literal comparison and first nonce literal comparison conservatively
rolled back. Both receipts retained; corrected guard allows K_REVISION marker and
per-request nonce changes while preserving all security directives/content checks.
Five focused guard checks PASS. Reused the same staged revision; no image build,
broad suite, paid inference or customer-report rerun. Independent readback PASS.

Other two requested repairs are now COMPLETE after Ray supplied info@workzoneos.org
and explicitly approved the scoped cleanup access. Four existing policies point
to enabled channel6122258028509790755 with all other policy fields unchanged
except provider mutation metadata. wzosFileCleanup contains only
storage.objects.delete and is bound only on the file bucket to the existing app
runtime. Exact additive binding/previous-grant comparison PASS, October22
8:31:59p.m.Eastern. No test alert, customer cleanup or API enablement. Email
verificationStatus was not returned; delivery is not claimed. All three
configuration follow-ups checked off; broader device/retention/launch decisions
remain open. Evidence: $HOME/wzos-followups-evidence-20261022, including
operational-final-result.json. Old /tmp evidence path has expired; use durable copy.
Both configuration completion boxes are supported by the actual readback above.

Evidence root /tmp/wzos-followups-20261022.dBAoYjzD, home pointer
wzos-followups-latest-path.txt, durable $HOME/wzos-followups-evidence-20261022.
pins-resume2.exit0/pins-result.json/public comparison/independent-final-service.json
confirm final state; resume-attempt1-evidence archives the failed guard attempt.
See OPERATIONAL_FOLLOWUPS_20261022.md. Verify fresh auth/project on resume;
use the completed email/access evidence without replaying passed app suites.

## Unassisted sweep 2 — October 22

18 focused checks passed, zero skips: seven GoogleFiles adapter checks and
eleven cache/update-flow checks (five new). Only tests, read-only audit tooling
and documentation changed; production remains ui-16d0905 at 100% traffic.
Source e8d455e and b16ed82; no runtime code or migration changes this sweep.

Read-only direct-principal audit: runtime has SQL client and single-permission
auth lookup/session/Speech project roles; ten bound secrets have secret-scoped
read access. Scanner/model invocation checks remain enabled with runtime-only
service-level invocation bindings. No public principal grants found in captured
policies; effective group/deny/conditional/resource access is not fully attested.

Three follow-ups: four enabled operational policies have no notification channels
(monitored-email question pending); two secrets use latest (each currently has
only enabled version1); bucket roles lack delete permission used by Forms cleanup.
Policy Troubleshooter is disabled, so effective delete evaluation remains open.
No IAM/API/config changes or customer deletion performed. Narrow proposal saved
in FILE_CLEANUP_ACCESS_PROPOSAL_20261022.md, not applied. Failed cleanup stays
hidden/queued; never promise completed physical erasure from that result.

Daily0.93.0 matches published npm bytes/integrity, direct-package advisory query
empty; full bundled/transitive and container/OS review remain open. Redacted
24h ERROR/5xx app log query returned zero. Bucket lifecycle: noncurrent30days,
soft delete7days; timing asynchronous, no real managed-object restore accepted.

Cloud Shell reconnected and existing credential authorization restored; fresh
admin@workzoneos.org / enterprise-gemma2 verified. Private evidence
`/tmp/wzos-sweep2-20261022.M8CLjJ0U` and $HOME/wzos-sweep2-evidence-20261022; pointer
wzos-sweep2-latest-path.txt. Local .local-data/prelaunch-sweep2-20261022 has SDK
audit JSON/script. See PRELAUNCH_SWEEP2_20261022.md; prior full gates stay below.

## Unassisted prelaunch sweep 1 — October22

Source repairs pushed through8d29bbf on codex/preproduction-modules: enforce
Enterprise messages/meetings/SMS controls while retaining opt-out on downgrade;
fix stale Node fakeDOM/unified-demo fixtures; explicit CSP object-src none.
Shared header notification change remains local/development only. Live unchanged:
ui-16d0905 at100%, public version5821810b858f1f58b45af012.

Node174PASS on Windows/Linux; focused backend38PASS. Full disposable PostgreSQL
at90fdc43 ran890:889passed,one stale Core-message demo error,zero skips. Corrected
fixture and header delta six checks PASS locally/cloud at8d29bbf. Do not claim a
failed gate passed: subsequent full gate at8d29bbf passed891zero-skips in399.936s.
Dependency-only pins updated separately indfef889 after audit found30advisories
in3packages; affected checks/advisory recheck recorded in results note. Native
synthetic signed-form dump/restore PASS, hashes
and tenant/auth denials preserved; disposable cluster cleanup verified.

Read-only runtime/public checks: hourly weather last3executions succeeded;
SMS remains test mode; Voice targetwzos-atlas-inference20CPU/80Gi/1GPU,max1,
no min-instance annotation; existingUSD50budget alerts50/80/100%,not a cap.
SQL backup success07:05UTC Oct22,7retained; bucket public-access prevention,
uniform access/versioning/7day soft delete. No live sends/charges/inference,
IAM/secret/weather changes or deployment. DOT derivative schema5->6 rebuilt
from unchanged7sources/2627pages; every page visually unreviewed,flags defaultoff.

Evidence: local.local-data/prelaunch-20261022; cloud/tmp/wzos-prelaunch-20261022.aRppkWeT,
home pointerwzos-prelaunch-latest-path.txt and private durable copy
$HOME/wzos-prelaunch-evidence-20261022. Verify auth/project/live on resume;
activity does not guarantee persistent authentication. Results/remaining gates:
PRELAUNCH_ENGINEERING_RESULTS_20261022.md; updated Codex/human checklists and
unpublished PRELAUNCH_PRIVACY_DECISIONS_DRAFT_20261022.md. Fresh vulnerability/
effective IAM review, managed/object restore, device/provider/business acceptance
and immutable candidate release gates remain; do not repeat paid model pilots.

Dependency follow-up accepted atdfef889:119affected PostgreSQL checks PASS,zero
skips in49.621s; repaired pip-audit exit0/no known vulnerabilities in inspected
Python environment. certifi2026.10.19(app/scanner),Pillow13.0.0,pypdf6.21.1(app).
No OS/container/browser-vendor clearance claim. Final891fullgate at8d29bbf
precedes these dependency-only updates; next release requires exact-candidate
gates/staging/image review. All runners completed; private evidence copied home.

## LOCAL shared header notifications — October22

Dedicated responsive header area replaces floating/content-level form alert;
assignment and Atlas Security notices share it. Amber beacon runs without hover
until clicked, retains required review actions; reduced motion is static amber.
Navigation/polling preserve visual acknowledgement; account/page restart resets it.
21 focused Node PASS, no skips; mobile Home/training, desktop and Review forms
navigation/pulse-stop browser checks PASS. No backend/schema/customer-record changes.
Not deployed; live remainsui-16d0905. See HEADER_NOTIFICATIONS_20261022.md.

## LIVE training and footer — October22

Source16d09056ccf31ee8f144b70353b0b657a527dd63 deployed100% as
wzos-v2-accounts-ui-16d0905. Build083d777a-73cc-4f6e-9f39-cc7a803b27ed SUCCESS;
digest80c3819aa9e8d3ce38ccf47e87bd4015b40875768a54604e994da9674cb3c054;
public version5821810b858f1f58b45af012. 16PostgreSQL +10Node focused checks PASS,
zero skips/failures. Preflight/build/drift/staged-runtime/public six asset hashes,
footer/update-marker/auth denial/traffic PASS; deploy.exit0. Priorui-358cf45 retained.
No schema, identity, secret, weather, model or customer-record changes. Evidence
/tmp/wzos-training-footer-20261022.y7ej7c0f; home pointer
wzos-training-footer-release-path.txt. See TRAINING_FOOTER_RELEASE_20261022.md.
Earlier LOCAL entries below are superseded by this deployment.

## LOCAL global footer — October22

Shared black footer outside the app content includes copyright, Molecular Project
Development LLC ownership and tap-to-call 844-685-7207. Uses theme font/amber text,
wraps on mobile and remains on mobile Home; account/staging scripts no longer
replace its content. Bottom clearance protects the phone link from Atlas's dock.
Browser verified visible black footer at 390px mobile and 1150px desktop; syntax
and diff checks passed. Evidence .local-data/global-footer-mobile.png. Local only.

## LOCAL numbered course links — October22

Ten admin-only numbered course URL fields/cards, direct per-course Save link with
feedback, organization-scoped versioned persistence in existing training tables;
reserved links stay separate from assessments. Catalog had nine courses; tenth
Organization Training added. Unrelated office alert/disclaimer hidden/removed on
Training; smaller gaps/bottom padding. 16 focused SQLite +10 Node PASS, no skips;
browser synthetic admin save/member visibility accepted. No schema/IAM/weather
configuration change or deployment. PostgreSQL/release gates remain pending.
Details and rollback: TRAINING_COURSE_LINKS_20261022.md. Prior prelaunch checklist
split remains an independent uncommitted documentation change; preserve it.

## LIVE signatures, compact weather and explicit review - October22

Final358cf452cf465c8727687d204f167f526fb6ec8a is serving100% as
wzos-v2-accounts-ui-358cf45. Build0e7a95d0-e79d-4818-aabc-700c218c0f5f;
image digest d1f7e2009eb186e2d9b9c36be732c7ed8baada8be93bdd50b66f2fe4646705a1;
version bd666b58478cbe553f66dd85. Preflight/build/drift/staged/public6asset hashes/
CSP/version/traffic PASS, deploy.exit0. Evidence /tmp/wzos-office-focus-20261022.cONJeqXR;
home pointer wzos-forms-weather-release-path.txt. Immediate rollback ui-60f7b99;
original design ui-bc0f30a retained. Final adds office-alert scroll/focus/feedback
after initial60f7b99 release (buildbfc5dd98-7269-4ffc-ba11-0a106646e535).
18unique focused Node +8SQLite +8PostgreSQL checks PASS, no skips. Final frontend
focus adjustment reran6related Node checks; PostgreSQL evidence reused only after
byte comparison of the unchanged backend and submission tests (provenance saved).
No broad model/SMS tests or customer sends. No schema, IAM, secret, GPU or monitor
changes. Weather permission/watch behavior unchanged. Authenticated browser confirms
signing controls, received-form modal and office alert focus at list top with message.
Prelaunch checklist: PRELAUNCH_REQUIREMENTS_20261022.md. Actual-phone handwriting/PDF
acceptance remains for user testing now that the pad is deployed. Do not submit or
mark reviewed any customer draft as part of acceptance. Synthetic local test only.

## Local forms signing pad - ready for review

Optional drawn/typed signature added to all WZOS printable forms, with signer name,
Clear, bounded vector capture and print/download/office-review presentation.
CompletedForm has a validated optional signature stored in existing JSON payload;
no schema/startup migration. Existing unsigned records and submission retries work.
Four Node + eight SQLite-backed submission tests PASS; syntax/diff PASS. Simulator
shows signing area and successful synthetic typed submission receipt. Browser SVG
hidden attribute issue repaired. Actual phone handwriting/exported PDF visual and
focused PostgreSQL submission checks remain before deployment. Not deployed.
See FORM_SIGNATURES_20261020.md. Current live design release remains unchanged.

## LIVE design update - October20

Design candidate bc0f30aa440e69ca84fec056fcf3bfbe5e57f0de deployed as
wzos-v2-accounts-ui-bc0f30a100%. Cloud Build e35b254f-0cf0-400b-9cab-406e9454d92f;
immutable digest a730f7f0f7b3d6a6a43a88f07a915ad8c07856687e02f5e0619afab3b5d8b178.
Public version f1def98aa29861b9697daeba. Preflight/build/drift/staged/public5asset
hashes/CSP/version/traffic PASS, deploy.exit0. Only5static files overlaid on prior
live image; runtime spec unchanged. Rollback prior wzos-v2-accounts-ui-3737af7.
Evidence /tmp/wzos-design-20261020.PGnPtVIs; home pointer wzos-design-release-path.txt.
Authenticated live browser confirms black glass, filled icons, badges and ordering;
Messaging focus animates atlas-orbit while ordinary Forms remains unanimated.
Focused16Node checks PASS; no broad Postgres/provider suites rerun per user scope.
User sign-in restored; do not repeat auth/tests/build. See DESIGN_RELEASE_20261020.md.

## Design deployment prepared - CLI sign-in pending

User authorized live design deployment with focused tests only. Candidate
bc0f30aa440e69ca84fec056fcf3bfbe5e57f0de is committed/pushed.16focused Node
checks PASS; JS/release Python/Bash syntax and diff checks PASS. See DESIGN_RELEASE.
New release_design_update.sh overlays only5frontend assets on the current live
immutable image, preserves runtime policy and stages before traffic/asset checks.
No full Postgres/provider suites needed or rerun for static-only replacement.
Cloud Shell reconnected but active CLI account is absent. Google Cloud SDK sign-in
opened in browser tab11; waiting terminal tab4 for user-entered verification code.
User was asked asynchronously to finish directly in terminal. Do not read/repeat
the code. No build or deploy launched; live remains unchanged this turn.
Resume: verify CLI project/account and actual current revision. Create private
evidence dir with source clone at bc0f30a, write source-commit.txt; run the new
build phase, then deploy only after successful build. Do not reuse stale cloud
baseline assumptions. Weather/backend/model/IAM remain untouched.

## Local follow-up - Messaging and Video meetings badges

User confirms Messaging and Video meetings are Enterprise options and requests
the Enterprise pill plus existing hover/edge glow, retaining their positions.
They now receive the Enterprise decoration marker independently of the sort list.
Existing shared hover and Enterprise orbit/pill CSS supplies the appearance.
Local-only styling update; no access/backend/weather changes or live deployment.

## Latest local preview - black glass restored

User rejected bronze surfaces. All cards are black glass again, with the first
three Enterprise mobile launch cards (Voice, Guardian, My jobs) full width; shared
cards inset6px each side. Filled module icons are shared through project icon
tokens and desktop dashboard launch cards. Amber hover/focus glow applies across
interactive controls. Moving edges are limited to Enterprise-marked navigation
options and Enterprise AI hub cards; Core assistant has no edge animation. Atlas
circle retains its Enterprise-only idle/hover effect. Reduced motion respected.
Browser verified black mobile cards, focus glow, Enterprise badges and Core-member
absence of Enterprise controls. Local server ready on8083, launcher1308/worker5124.
No live deployment, weather, permission or backend changes. Earlier bronze-menu
CSS archived in design/theme-previews/bronze-menu-orbit.css. Syntax/diff checks pass.
See BLACK_GLASS_REVIEW_20261020.md. Enterprise admin preview restored for review.

## Latest local preview - bronze menu and orbit glow

All vertical navigation cards now share bronze glass, silver-white labels and
filled icons. Actual DOM order groups Enterprise-only Voice, Guardian, My jobs
and legacy report (if available) first. Only Voice/Guardian use Enterprise AI;
other Enterprise controls use Enterprise. Access/role checks remain unchanged.
Only those two AI cards animate an amber edge with a green-gold highlight on
hover/focus. Atlas circle also orbits on hover/focus and gently pulses occasionally
while idle. Reduced motion disables animation. Decorative Guardian dot removed;
this is not a verified security/protection status. Original bronze is archived
with cyan/platinum under design/theme-previews. No live/backend/weather changes.
Browser confirms grouping, badges and shared bronze cards; JS syntax/diff checks
pass. See BRONZE_MENU_ORBIT_20261020.md. Preview remains on port8083.

## Local UI experiment - Midnight Amber (active)

Theme 3 is the current local preview: dark bronze glass with 5%-alpha gold mesh
layers, silver-white text/pills, amber-to-platinum interaction glow and filled
icons with subtle shadow. Guardian has an aria-hidden decorative breathing dot;
not a claim of continuous protection. Reduced motion disables animation.
Platinum preserved at design/theme-previews/enterprise-ai-platinum.css; cyan
also retained. No live deployment, feature activation, permission or weather
changes. Preview launcher PID20168, port8083. Browser refreshed and bronze card
rendered; JS syntax and diff checks pass. See AI_BRONZE_PREVIEW_20261020.md.

## Local UI experiment - Reflective Silver and Platinum (active)

Theme 2 replaces the cyan preview locally: thin silver borders, gray-to-white
hover/focus text, restrained white glow, filled microphone/shield masks, and
silver Enterprise AI badges/ring. Black glass and amber utility controls retained.
Cyan preserved in design/theme-previews/enterprise-ai-cyan.css, not loaded.
No live deployment, backend, permissions or weather changes. Preview restarted
on port 8083 (owned launcher PID9668). Browser simulator loaded updated labels
and silver cards; mobile wrapping adjusted with a two-column icon/label grid.
JS syntax and diff checks pass. See AI_PLATINUM_PREVIEW_20261020.md.

## Local UI experiment - High-Viz Safety Cyan

User requested cyan styling for the two Enterprise AI launch controls, ENTERPRISE
AI pills and the floating Atlas ring. Additive workspace-layout.css changes only;
no live deployment or feature/permission/weather changes. Simulator restarted on
8083 (ownedPID20008), HTTP/assets/diff checks pass. Browser control reset again;
visual acceptance remains pending. See AI_CYAN_PREVIEW_20261020.md. Preserve this
local preview diff for user review; do not describe it as deployed or visually
accepted, and do not rerun the completed cloud release gates for this preview.

## Latest serving code - office alert placement follow-up

Final3737af7 corrects dashboard content burying the office alert: above main on
desktop/module pages and after the organization card on mobile Home. Final full
PostgreSQL878/Node163PASS,0failures/errors/skips; schema/backup preflight PASS.
Builde8e2f67d-f6f9-4123-b816-f04ad924d863 submitted. Final public code/assets/auth/
CSP/version checks independently PASS; version06cb438e96196bd4b724c67b. The home
pointer now targets/tmp/wzos-office-alert-20261020.Y6Db8vH3. Cloud Shell browser
disconnected after submission and CUA recovery reset; final image/traffic/exit JSON
not reread. Do not start duplicate jobs to recover logs. See OPERATIONS_RELEASE.
Authenticated alert/link accepted on the first live update; final visual placement
needs a recovered browser. User has confirmed sign-in ready. The October19 report
remains a draft; do not submit it for the user. DOT source/model acceptance remains
open and DOT flags off. Existing Voice/weather/security settings preserved.

## LIVE operations release - October20 (supersedes local-only receipt status)

Runtime edd310b deployed as wzos-v2-accounts-ui-edd310b100%, version
2444c54a1b7aac271259373c. PostgreSQL878/Node163PASS, no failures/errors/skips.
Backup/schema/preflight/build/drift/stage/public assets/auth/version/traffic PASS.
See OPERATIONS_RELEASE_20261020.md for immutable image, logs and rollback baseline.
Voice remains active; weather/runtime/IAM/secrets unchanged; DOT flags stay off.
Read-only live check confirms the user's October19 Voice report remains a saved
draft, not an office submission. No actual user report was edited or sent.
Receipt UI verified with synthetic data on desktop and390px mobile iframe; no
horizontal overflow. User sign-in is requested after reload for authenticated
live browser acceptance. DOT source review and bounded provider pilot remain open.

## Latest user steering - October20 Voice receipt

User confirms correct Smart Field Voice objects/counts but no visible office receipt
or admin notice. Local repair and exact validation: FIELD_VOICE_RECEIPTS_20261020.md.
Reports go to organization Forms hub; notices are in-app, never email/SMS. Actual
user submission state is not yet verified. Four Node receipt/alert checks and13
Python checks passed; this repair is not deployed. Preserve separate uncommitted
Ask Atlas source refinements. Full cloud gate at bc7394d:874 PostgreSQL tests PASS,
zero skips/failures/errors; Node exit0. That gate predates the receipt repair.


## Start here

Owned checkout: `.local-data/integration-release`, branch `codex/preproduction-modules`.
Read COLLABORATION_CONTRACT.md and REMAINING_TASKS.md; inspect Git before edits.
Historical checkpoints were preserved under docs/history; they are not current blockers.

## Latest release - October18

Core upgrade implementation is LIVE: wzos-v2-accounts-upgrade-live-bf9f524,100%,
source bf9f524304a994bc9ff9cb54b795271510df8491, image sha256:f347f6901acb223b412ae729aa52afc47a1210804b861916ecfc18f46f5e3873.
See CORE_UPGRADE_RELEASE_20261018.md for exact gates, rollout and schema evidence.
Stripe two-resource Write save independently confirmed; non-persisted live preview
passed$20 credit/tax, no payment/subscription change. Deployment exit0; post-schema
compatible/missing[]/conflicts[]; proxy independently absent; browser admin entered
Molecular Enterprise dashboard. Runtime/secrets/weather/media policy preserved.
Rollback MUST use upgrade-hold-bf9f524 on the same image to preserve paid-upgrade
webhooks. Paid existing-Core acceptance is still a user action, not yet passed.
Atlas private31B pilot COMPLETE:8/8 synthetic operator responses, warm2.064-4.017s,
mean2.860;4823 input/466 output tokens. Guard->cleanup351.13s, compute-window estimate
$0.311 (not verified billing). Model service absence, stopped guard, unchanged app
spec and Atlas=0 independently verified. See ATLAS_PILOT_RESULTS_20261018.md.
Local context correction prepared after the live replies exposed stale messaging
help; updates embedded meetings/SMS/form delivery/navigation and fixes cross-page
time matching.27 focused mocked context/transport checks pass. Not yet deployed;
Full integration gates now PASS on c18951e:811 PostgreSQL/136 Node, no failures
or skips. Local synthetic app harness in c6bfa69 passes; derivative build
74a46069-95f9-41e9-9965-c97ded5610d1 SUCCESS, digest eaa44f814c0917c2719ba0c09a1b34849145f2cc27ba9130a16153a094d4571d. See
ATLAS_APP_WORKFLOW_SCOPE_20261018.md for evidence and proposed identity test.
Separate app-path pilot COMPLETE:2/2 real metadata-authenticated requests through
the app/VLLM adapter,4.832s saved synthetic job/source and2.679s member SMS guidance.
Stale409/cross-tenant404/Core-report403 precede inference. Pilot and observer exit0;
model/job absent, guard stopped, production spec unchanged/Atlas=0 independently
verified. See ATLAS_APP_WORKFLOW_RESULTS_20261018.md and cloud pointer
$HOME/wzos-atlas-app-live-path.txt. No active GPU/job remains; no automatic replay.
Actual reviewed source coverage, browser inference and ongoing hosting remain open.
The older development section below is historical; its deployment blocker is closed.

## Completed this session

- Ray confirmed installed Android WZOS opens without a browser address bar and does
  not repeat the install prompt. Update/draft-preservation acceptance stays open.

- User completed phone ownership verification in the live app. Browser showed
  "Number verified. Text messages are on."
- Sent one normal, non-sensitive WZOS test notification to the previously approved
  recipient. User confirmed phone receipt. This closes controlled verification
  and normal-notification delivery acceptance for that recipient only.
- No further verification codes requested by agent; user consent/code entry stayed
  with the user. SMS mode remains test; broad organization sending is not activated.
- Removed generated tests/__pycache__ from the owned checkout. Git stayed clean.
- Fresh Cloud Shell read-only process/directory check found no owned test PostgreSQL
  clusters, deployment helpers, SQL proxy or /tmp/wzos-pg-gate.* residue.
- No user's tabs, recovery files, credentials, offline drafts or release evidence removed.
- Live public app version endpoint returned HTTP200/version b6ef659d4ed7394960cda60d.

## Previous weather baseline (superseded by October18 release above)

Previous weather deployment: sourcec6adf9f36b6c2ed25882785b5abe96e4b1ba8224,
revision wzos-v2-accounts-weather-hourly-1017,100% traffic, image
sha256:edb4a3c4dde24cb6fe57d65ad79f1cfd611ab507d1d1bf03ea70e18f972e92ed.
Guarded deployment exited0; runtime preserved;28 public assets matched source hashes,
exact Daily permissions, weather markup, anonymous weather401 and version passed.
Validation: full cloud PostgreSQL769, weather PostgreSQL23, local Node133/Cloud Node6.
Three additive weather tables/index applied at startup; no existing-table alteration.
Rollback: brand-4e281c6, image14b89663d97726b12f5173163ba31aa94ebf8bb7be85da3c4fb2be06fda51da1.

Source2f44ed3 ASCII-only SMS request guidance correction is included in this release.
New documentation commits do not imply a new deployment.

## Cloud connection checkpoint

CLI sign-in restored by user. Independently verified active account
admin@workzoneos.org, project enterprise-gemma2, latest ready revision
wzos-v2-accounts-weather-hourly-1017 and actual traffic100% on that revision.
No current cloud connection blocker. Weather card/manual checks/arrival update deployed.
Public app/sign-in/SMS working; earlier CLI-auth blocker is closed.

## Previous Core upgrade development checkpoint (superseded above)

Candidate bf9f524 is pushed on codex/preproduction-modules. New organization_upgrades
startup table/Stripe adapter/paid webhook transition/admin-only quote and confirmation
UI are documented in CORE_UPGRADE_IMPLEMENTATION_20261017.md. Upgrade charging remains
OFF by default. Original purchases preserved; one subscription, one $20 credit,
Stripe tax/proration, paid-only Enterprise seats and bounded unpaid Core continuity.
Final focused local19 billing +6 Node UI cases PASS; synthetic desktop/mobile browser
flow passed. Baseline2febb92 cloud PostgreSQL804 PASS/no skips; SDK dependency install
then blocked on an old commerce crypto declaration. Repaired to>=49,<51 to match the
already validated accounts graph (webauthn3.0.1,cryptography50.0.2,pyOpenSSL26.4.0).
Reconnected final bf9f524 gate PASS: PostgreSQL810 in392.190s,0 failures/errors/skips;
Node136 PASS/no skips; Stripe SDK7 PASS; pip check clean. Earlier paste was truncated
before checkout; recovered clean source-final and submitted an encoded script.
Pointer$HOME/wzos-core-upgrade-path.txt; validation-final.exit=0,final-sdk.log,
final-postgres.log,final-node.log. Image build helper prepared/pushed5274351. Initial
attempt stopped on the disposable venv symlink; first submitted build37d23fe9… was
cancelled to correct compile ordering before dropping to the non-root runtime.
Corrected builda651a66a-82eb-43c9-8193-621029f2ab77 SUCCESS; immutable digestf347f690…
recorded in CORE_UPGRADE_IMPLEMENTATION_20261017.md and upgrade-build.json. Schema
preflight PASS: only organization_upgrades missing, conflicts[]. SQL backup today
1792216800000 SUCCESSFUL. Owned proxy EXIT trap stopped it. No live DDL/deploy or
Stripe financial write submitted.
Public app remains weather-hourly-1017, same accepted image.

Resume: inspect corrected build status, verify Stripe preview/key permissions
without charging, then guarded
rollout/activation. Live payment requires user action; never charge for acceptance.
Stripe authenticated in-app tab7 now available. Existing key Subscriptions/Invoices
Read; Ray approved only changing these to Write. Apply changes navigated to Webhooks
without first persisted readback showing Write. User asked to apply those same two
settings directly and leave tab open. Verify persistence before activation; no new
credential or broad grant. See CORE_UPGRADE_ACCESS_20261017.md. No secret revealed.
Next Atlas finding: live app selects private_vllm but enabled=0; configured endpoint
wzos-atlas-inference is absent from current Run service inventory. Legacy failed
Gemma2-2B service is separate and is not the configured WZOS engine. HF_TOKEN secret
exists; do not bind it indiscriminately. Existing31B GCS/Run:ai deployment script
should be reused after fresh bucket/manifest/IAM/network/quota/budget verification.
No GPU/model workload or new IAM grant created during this development increment.
Read-only preflight confirmed retained31B directory10 objects/62,578,670,545 bytes;
isolated subnet Private Google Access=true. Fresh object metadata/bucket policy
saved in the same cloud evidence root. Counts alone are not integrity acceptance.
Mobile-wide UI redesign remains deferred until the remaining integration list is done.

## Next work

Weather/geofencing implemented in c6adf9f after read-only GEMINI_WZOS_V1 review.
See WEATHER_IMPLEMENTATION_20261017.md: full cloud PostgreSQL769 PASS, final weather
PostgreSQL23 PASS, local Node133 and Cloud Node6 PASS/no skips. Final backend unchanged
from23-test candidate; frontend privacy fix verified. Build/public deployment complete.
Ray-approved once-hourly monitor is ACTIVE; weather SMS remains OFF.
Cloud evidence: $HOME/wzos-weather-path.txt. No new scheduler/IAM grants applied.
Hourly pilot ACTIVE: cron `0 * * * *`, America/New_York. Private job first run
wzos-weather-monitor-tpbhg succeeded, checked0/notices0/unavailable0 (zero configured
sites). Dedicated scheduler identity has invocation only on this job; authenticated
Scheduler test returnedHTTP200 at2026-10-17T19:51:52Z; its execution m5fcz also succeeded. Web coverage exact-org allowlist
is deployed as weather-hourly-1017 at100%, same image/runtime except3 weather flags.
SMS staysOFF. See WEATHER_MONITOR_ACTIVATION_20261017.md. NEXT: admin configures
reviewed job-site coordinates/windows; actual hazard/mobile-arrival acceptance remains
open. No synthetic live sites or device GPS collection. Evidence$HOME/wzos-weather-path.txt;
proof release-20261017/live-weather-hourly.png. No broad IAM/SMS changes.
Owned local preview/test processes stopped; source and reference checkouts clean.
Ray's card preference: fixed compact basic-weather card that follows user location
after permission, refreshes on meaningful movement, and labels stale/fallback data.
Confirmed combined scope: retain assigned-site alerts for affected workers/admins
alongside the card; distinguish current-location hazards from named job-site alerts.

1. Supplied logo is live across shell/auth/dashboard/favicon/install assets;
   see WZOS_BRANDING_20261017.md. Browser confirmed original319x355 artwork loaded.
2. Daily first five-minute test schedule cancelled after laptop blank iframe.
   Ray reported meeting inside TV; two-way media remains unaccepted. Exact fallback
   media-origin repair and bounded join timeout are now DEPLOYED after exact user
   approval. See DAILY_FRAME_REPAIR_20261017.md. Two-device media retest remains open.
3. Run the next remaining integration gate from REMAINING_TASKS.md, coordinating
   device tests with Ray. No automatic new texts or media sessions.
4. Preserve admin/member, tenant and Core/Enterprise boundaries. Do not enable broad
   customer SMS or charge a card as a side effect of acceptance work.
5. Save actual capabilities, remaining gaps and evidence. Keep current docs concise;
   append detailed evidence to the relevant dated task document.

## Evidence and history

SMS: SMS_CHALLENGE_REPAIR_20261017.md; FORMS_SMS_PWA_UPDATE_20261016.md.
Earlier live form receipt: ignored .local-data/release-20261017/live-office-receipt.png.
Live logo proof: ignored .local-data/release-20261017/live-logo-release.png.
Cloud evidence: directory referenced by $HOME/wzos-daily-frame-path.txt; deploy.exit0.
Historical full handoff: history/SESSION_HANDOFF_before_sms_acceptance_20261017.md.
Historical full checklist: history/REMAINING_TASKS_before_sms_acceptance_20261017.md.
Archives preserve the complete earlier text; paths in them refer to the original docs root.


## October 18 personal weather / permission / mobile menu increment
See WEATHER_MOBILE_UPDATE_20261018.md. Current local changes separate location weather from job tools, add four-day high/low forecasts, guard geolocation calls in weather/navigation/time, and reuse desktop cards as a visible vertical mobile list (drawer rejected). Focused checks:23 Node +27 offline Node +11 Python PASS. Public app unchanged; integrated release gates and real mobile acceptance remain open. Smart Field Voice f176c53 cloud results not yet read: Cloud Shell page binding stale after reconnect/reload. Preserve existing fixture/audio helper files; they belong to earlier voice work. No native app packaging started; user chose PWA + Android first, then iOS.


## Mobile simulator — October 18
Local simulator implemented in scripts/run_mobile_preview.py and scripts/mobile_preview/. Open http://127.0.0.1:8083/__simulator; see MOBILE_PREVIEW.md for restart and isolation. Six focused checks PASS; actual iframe and rotation observed. Original foreground exec session94769 ended; earlier voice preview stopped. Browser automation repeatedly timed out during final screenshot/interaction, so no final screenshot acceptance claim. Fixed dashboard single-column selector specificity after simulator revealed two columns. Public site unchanged; prior voice/audio fixtures remain separate unfinished work. Continue preview review before release gates/deployment.


### Simulator loading repair
Added scripts/start_mobile_preview.ps1, with hidden background launch, readiness check, saved process/log pointers, and guarded -Stop. The new launcher returned SIMULATOR_READY and independent HTTP checks returned200 for simulator/app. State: .local-data/mobile-simulator/server-8083.json. Keep this process available for user preview. Browser URL policy blocked automated visual verification; ask user to refresh the existing simulator tab, do not bypass the block. Live site unchanged.

## Mobile Home clarification — October 18
Implemented shared mobile Home for admins/members with authorized card content, module-only pages and Home return. Desktop unchanged. See MOBILE_HOME_20261018.md: 11 focused Node checks pass; actual browser Home/Time Tracker/return/Core member filtering verified. Simulator running; local only, no deployment. Preserve untracked voice fixtures/helper.

## October 18 mobile Home / weather release — LIVE
Ray authorized public update. Exact source c944173 passed cloud PostgreSQL831 and Node148, no failures/skips. Schema/recent-backup and immutable-image/config preservation checks PASS. Revision mobile-c944173 is100%; version4ac54119f08f1aea7fc1152f. Live mobile Home -> Navigation -> Home observed. See MOBILE_RELEASE_20261018.md for image, rollback and screenshot. Voice processing remains OFF pending separate service/pilot activation. Real Android permission/weather acceptance remains open. Simulator stays available; untracked voice fixtures/helper preserved.

## Smart Field Voice activation work — in progress
User asked to make Field Voice operational while available remotely for approvals. Final source95bc0f8 separates voice model flags from ordinary Atlas chat and adds cloud-processing notices. Scope/rollback: FIELD_VOICE_ACTIVATION_20261018.md. User approved scoped Speech setup and bounded model pilot. Speech API and exact one-permission role/binding are verified. No GPU/job creation, customer send or public activation has occurred. Live stays mobile-c944173.
Cloud pointer: $HOME/wzos-field-voice-path.txt. Synthetic audio uploaded with verifiedSHA256 f70a0cdae930dc9b315d2a47660f3a7b8f54e17452b81e42373b0e545c200436. Prior1b7c2b3 passed832 PostgreSQL/148 Node; mocked harness needed its own model URL, fixed in95bc0f8. Final frozen source95bc0f8 passed832 PostgreSQL and149 Node checks without failures or skips; mocked workflow PASS. App/pilot images are building. After successful build, prepare_field_voice_release.sh build produces separate app and synthetic-job images. A new job-identity approval is required before run_field_voice_pilot.sh (one task,15minutes,1CPU/512MiB,no retries; app identity retains existing permissions; no DB/secret/bucket binding). After real pilot acceptance, request ongoing hosting/production activation scope and operating budget. Do not consume prior Atlas pilot approvals again. Real Android permission/recording acceptance remains user-led.

Latest: Cloud Build0b19c5a6-5fbe-4700-88e5-bf2ee6d8b39b SUCCESS; immutable app798c479c…/pilot5f666853… verified. Root /tmp/wzos-field-voice.7uMHJJrD has app-image.txt/job-image.txt, Speech verification and complete gate results. Source checkout remains95bc0f8, helpers copied outside it from86011b2 and bash/Python syntax checked. Exact pilot-job approval question sent; answer pending. Do not launch GPU before this answer. No model/job remains running and production is unchanged. On approval, write job-approved timestamp and pilot-nonce.txt v20261018-RANDOM; run source/scripts/run_field_voice_pilot.sh run ROOT in background with pilot-runner.log, monitor completion and verify cleanup. No automatic paid repeat on failure. Ongoing production helper requires activation-approved only after real acceptance and separate operating approval. Build screenshot: ignored .local-data/field-voice-pilot/build-verified.png.

Superseding pilot state: user approved exact disposable job. First model startup failed because pinned vLLM rejects obsolete --disable-log-requests; no job or paid provider requests ran. Cleanup independently verified. Repair79c332e uses supported --no-enable-log-requests; runtime/test images unchanged. User approved one repaired bounded model pilot. New evidence root /tmp/wzos-field-voice-repaired.BtRxb572 (current $HOME/wzos-field-voice-path.txt) symlinks frozen95bc0f8 source, copies verified gate/image approvals, and owns new deployment helpers/nonce/guard. Guarded run launched PID42017, model deployment in progress. Continue reading pilot-runner.log/model-deploy.log/execution.log/pilot.exit and cleanup.verified; do not launch another pilot automatically. Deployment helpers are root/run_pilot.sh, root/deploy_model.sh, root/deploy_activation.sh and root/check_activation.py from79c332e. No public activation or ongoing hosting approval yet. Prior failure evidence is retained in original /tmp root, including startup-error.log; screenshot .local-data/field-voice-pilot/startup-repair.png.

LATEST, supersedes running-pilot statement: repaired model startup/private policy checks passed; job26998 transcribed first audio successfully but extraction hit Cloud Run authentication/IAM rejection. Actual model output/schema remains untested. Pilot.exit1 and cleanup.verified0; both workloads absent. Correct app invoker binding, job identity and canonical model URL saved; permission propagation is a hypothesis, not proven. Harness-only repairf0ea5e8 adds token routing/identity checks and bounded GET /health readiness before paid calls, without inference/transcription retries. Six guard checks and ten-case mocked workflow PASS in Cloud Shell (set PYTHONPATH=frozen source only for this development invocation). Test image10382d00e3a792c41f17829b3262048173713711218d735c87dfa97ff29f1ed8 built SUCCESS, builda84f9c27-61a1-4abe-a688-de0aac3e92a1. App798c479c…/runtime95bc0f8 unchanged,832 PostgreSQL/149 Node gates remain valid. New exact-image bounded job/model approval requested, answer pending; no GPU currently running. New helpers in current root/repair-helpers (fromf0ea5e8), new image saved retest-job-image.txt. On approval create a fresh owned evidence root, retain frozen source symlink/gate/app-before/Speech verification/app image, copy reviewed helpers plus repaired deploy_model.sh; use the new job image and fresh approval markers/nonce/guard, preserving both failed roots. Do not reuse consumed job/model approvals or automatically rerun. After real PASS+verified cleanup, request ongoing hosting/public activation budget; installed Android recording acceptance remains user-led.

CURRENT superseding checkpoint: user Approved readiness-repaired image10382d00…; run root /tmp/wzos-field-voice-ready.QK378RxF (current cloud pointer). Execution xf8hz PASSED metadata routing/identity, private HTTP readiness, real transcription and structured schema parsing, then FAILED semantic check "50 drums". Absence of model/job independently verified; cleanup.verified0/pilot.exit1. No more GPU currently running; live remains mobile-c944173 and voice OFF. It is not yet known whether recognition, extraction or a term synonym caused the mismatch: no raw transcript/report was logged. Harness-only824634e adds boolean ASR cues and synthetic structured quantity diagnostics; semantic failures remain overallFAIL, failed reports are not saved/submitted, independent fixtures continue within10Speech/10model bounds, no retry. Focused failure-path checker5e32ad1 and plain mocked workflow are running in Cloud Shell, then a new test-only image build. Artifacts in current root/diagnostic-helpers, diagnostic-check.log, diagnostic-mocked.json and retest-build*. Read outcomes and immutable digest, record scope, request NEW exact-image bounded job/model approval before another real run. Do not reuse consumed approval. App/source95bc0f8/image798c479c… unchanged; full832/149 gates still apply. Future live activation helpers froma9c158a in root/activation-helpers are syntax checked; add readiness-only job to eventual ongoing hosting approval. No ongoing/public activation permission yet. Source working branch clean except this checkpoint update; no customer sends/audio.

Diagnostic build closure: focused continuation test PASS (forced failure remainsFAIL,10 fixtures/0paid calls), plain mocked workflow PASS. Build8c532f56-e430-4220-9beb-d927496c5732 SUCCESS; diagnostic imageeb8cd6d7ea2230d48d1b0aee91f3f11d998fbbfada30ad81a7f3283cab17959a saved in current root/retest-job-image.txt. Exact new-image bounded pilot approval question sent, answer pending. All GPU/job workloads are absent. After approval, create another fresh owned root with frozen source/gates/app-before/Speech verification/app image and repaired deploy_model.sh; job image comes from retest-job-image.txt, run helper remains f0ea5e8 (current root/run_pilot.sh), fresh job/model markers/nonce. Preserve past failure roots. On failure, read only latest execution stdout using resource.job_name and freshness10m (or saved execution label filter correctly quoted); summaries contain synthetic quantities/ASR booleans, never raw transcript/token/audio. Future production helper updated locally to expecteb8cd6d7… readiness-only image; copy latest reviewed helper after real acceptance and before asking ongoing activation approval. No automatic paid rerun/public feature activation.

LATEST RUNNING: user Approved diagnostic piloteb8cd6d7…. Cloud Shell reset tocloudshell-19434 deleted all prior/tmp evidence/source/venvs. Reverified admin@workzoneos.org/project, retained synthetic ZIP checksum and absence of model/job. Recoverye405608 restored frozen95bc0f8 source and latest reviewed ops helpers to /tmp/wzos-field-voice-diagnostic.C7R4kjru (current pointer), verified original0b19c5a6… app build and8c532f56… diagnostic build immutable images. Prior runtime832/149 acceptance is explicitly restored from committed certificate, not newly run tests; no fabricated exit files. Speech setup reverified. Guarded diagnostic model deployment is RUNNING, shell backgroundPID2180. Read pilot-runner.log/model-deploy.log/execution.log/pilot.exit and cleanup.verified until completion. On failure read latest execution stdout; all independent semantic cases now collect bounded synthetic diagnostics and preserve overallFAIL. No paid automatic rerun. Latest helpercheck_runtime.py supports prior accepted immutable app evidence. After exit, small private evidence archive is written to home and pointed by $HOME/wzos-field-voice-evidence-latest.txt, excluding source/audio. Ongoing/public activation remains unapproved, app unchanged. Do not rerun scripts/prepare_field_voice_retest.sh against lost old hardcoded audio/tmp path without recovery; diagnostic image already built.

## Latest Field Voice diagnosis (supersedes running diagnostic checkpoint)
Diagnostic eb8cd6d7… completed FAIL4 semantic cases, ten Speech/eight Gemma/zeroSMS; metadata/private auth/schema transport passed. Both workloads removed and absence verified. Later-sentence cue loss suggests transcription cutoff. Runtime35b409f adds reviewed US long selection, defaultshort unchanged; focused transport6PASS, fresh cloud PostgreSQL/Node gates running. Cloud root /tmp/wzos-field-voice-utterance.zHedHtgA, pointer $HOME/wzos-field-voice-utterance-path.txt. Preparing CPU-only four-recording Speech job before spending more GPU time. No approval yet for long/new job; no model running, production unchanged/VoiceOFF. See FIELD_VOICE_ACTIVATION_20261018.md. Prior private diagnostic archive retained in home, excluding source/audio.

Latest acceptance:35b409f cloud PostgreSQL834/Node149 PASS, no failures/skips; mocked workflowPASS. Buildb8708313-b6f3-45b3-8db1-1c0cc1dd57b7 SUCCESS, appa8ab3dd6…/testf6b132f6… digests verified. Helpers copied outside frozen source, syntaxPASS. Home gate/build archives saved. CPU-only long-recognition approval pending (exact imagef6b132f6…, four synthetic Speech calls, five-minute app-identity job, no GPU/data bindings/sends). Do not launch before answer. No model running or production changes. Next on approval: create speech-pilot-approved timestamp and speech-pilot-nonce.txt s20261018-RANDOM in current root, background run_speech.sh run ROOT, inspect speech-result.json/speech-pilot.exit/speech-cleanup.verified; preserve FAIL diagnostics if needed. No automatic paid retry. Root pointer $HOME/wzos-field-voice-utterance-path.txt. Scope FIELD_VOICE_ACTIVATION_20261018.md.

Superseding result: approved long Speech-only pilot ran four requests, three casePASS/oneFAIL (arrow_boards cuefalse; fifty/drums/fourtrue),0model/0SMS. Job deleted, absence verified, exit1/cleanup0. No paid repeat/GPU launch. Fixed road-work vocabulary repairc7669cc local transport6PASS; new cloud integrated gates running, pointer $HOME/wzos-field-voice-vocabulary-path.txt. Prior utterance root retains real Speech diagnostics and independent cleanup. Prepare combined CPU-then-conditional-GPU acceptance with exact new image; request one combined approval after gates/build, no public/ongoing hosting authorization yet. See FIELD_VOICE_ACTIVATION_20261018.md.

Latest ready-for-approval checkpoint: c7669cc cloud PostgreSQL834/Node149/mockedworkflowPASS,0failures/skips. Guard helper2fb1d41 four inert checksPASS; existing scoped Speech permission verified without IAM change. Build64e756ce-ddbc-4951-8dfc-dd46c0f271b6 SUCCESS; appc6e687b8…/test86c814b8… digests verified. New root /tmp/wzos-field-voice-vocabulary.fwGAduXY, pointer $HOME/wzos-field-voice-vocabulary-path.txt, persistent gates/build home archives retained. Review exact-image combined CPU4 then conditionalGPU10 approval request; no new pilot has launched. On both approvals, write combined-pilot-approved/speech-pilot-approved/model-approved/job-approved, speech-model.txt long, new owned s20261018-RANDOM and v20261018-RANDOM nonce files. Run root/run_field_voice_acceptance.sh ROOT in background. CPU stage mustPASS+cleanup0 beforeGPU; guard rejects rerun. Read speech/pilot results, exitfiles and cleanup independently; no automatic paid repeat. Production unchanged, ongoing/public hosting not approved. Latest scope FIELD_VOICE_ACTIVATION_20261018.md.

Superseding outcome: combined86c814b8… CPU executionfzr47 completed3/4PASS with only arrow_boards cuefalse. Four real Speech,0model/0SMS; exit1/cleanup0; model absent. Original conditional GPU approval unused (conditionfalse), no new paid rerun permitted automatically. Exact failed result saved by execution label to speech-result.json; prior-execution logging rows must not be confused. Fixture integrity/format verified; raw Google misrecognition unknown. Preparing fresh approval for full unchanged semantic assertions (including4arrowboards), bypassing only the literal-ASR success prerequisite after explicit review. New semantic-review helper validates exactly this single-cue failure and accepted image/gates/cleanup, refuses duplicate run; local5inert checksPASS. Same root vocabulary.fwGAduXY, production unchanged. See FIELD_VOICE_ACTIVATION_20261018.md. Do not rerun original combined sequence.

FINAL TEST IN PROGRESS: user approved one full unchanged86c814b8… semantic workflow despite isolated lexical mismatch, explicitly prohibiting repeated test cycles. Current root/run_semantic_review.py started with new owned nonce and semantic approval. semantic-runner.log shows gate/classification checksPASS and model deployment underway; one-hour cleanup guard owns model/job removal. No transcription/extraction yet observed. Do not rerun original combined sequence, start another paid pilot, or create speculative fixes/tests after this outcome. Finish cleanup, save actual result and stop testing; production/ongoing hosting remains unapproved.

## Latest stop point — repaired configuration, tests deferred by user
Finaln9c5h completed10Speech/8Gemma/0SMS,9/10expected cases; overallFAIL remains4Aero boards instead of4arrow boards.50drums/counts/othercases worked. Model/job removed, independent absence verified, guard stopped, pilot.exit1/cleanup0. Private final evidence $HOME/wzos-field-voice-final-result.tgz, root/final-result.json; no raw transcripts. User explicitly stopped repeated test cycles, then requested configuration repairs and testing afterward.
Repair now implemented locally: long default/required (runtime+pilot+activation), boost10 onlyarrowboardterms, extractor equipment ambiguity guidance, deterministic visible warning for exact Aero board(s) without changing quantity/name/transcript. Existing review UI displays warnings. Regression cases updated/added but NOT RUN; only static Python AST/diff review. No new DDL/IAM/secret changes. Save/push repair, then hold testing and deployment. Older834/149 gates and c6e687b8…/86c814b8… images are pre-repair and cannot be reused as repair acceptance. No new pilot or public activation approval. Production unchanged/VoiceOFF. Next testing requires user instruction after repairs; no automatic paid rerun.

## Latest release checkpoint — repaired gates PASS, CLI sign-in handoff pending
Frozen1d2da6b validated: PostgreSQL836/Node149PASS(no failures/skips), local focused8PASS, original mockedworkflowPASS, new one-recording mockedworkflowPASS(0real provider calls). Root /tmp/wzos-field-voice-release.yfHTUAtb; pointer $HOME/wzos-field-voice-release-path.txt; private home gate archive saved. Helpers198e397 outside frozen source add one-case actual acceptance before conditional activation; no runtime changes after1d2da6b. Do not repeat completed suites.
Build is blocked by Cloud CLI credential refresh, not app test failure. Account selection had been unset; restoredexistingadmin, but API refresh still fails metadata email. gcloudauthlogin awaiting verification code in Cloud Shell TERMINAL0. Google SDK IABtab5 open atContinue withadmin selected; user must finish and enter code directly interminal0, neverchat. Checks useTERMINAL1 (two Terminal input/list DOMlocators; both reportvisible, use observedsecond). Current browserIAB2 CloudShelltab2. Do not send commands into code prompt. User sign-in question pending.
After sign-in verifyAPIaccess, build root/prepare_release.sh againstfrozen1d2da6b once; collect app/test exactdigests and persistbuild evidence. Then obtain explicit ongoing-hosting/conditionalactivation approval, including private1GPU20CPU80GiBmin0max1 onlyWZOSinvocation (aboutUSD3.19/allocatedh,USD76.48/daycontinuous, notspendcap), one disposableappidentityjob1CPU512MiB10min/no retries/oneSpeech+oneGemma synthetic recording. Job removed, publiccutoveronlyifPASS, rollbackprepared; modelremainsongoingonlyonsuccess/approval. No newDDL/secrets/ordinaryAtlaschat change. PriorUSD5approvalsnotongoingpermission. Productionunchanged; noGPU/job/realproviderrequests/buildyet. Details FIELD_VOICE_ACTIVATION_20261018.md.

## Latest checkpoint — repaired build SUCCESS, activation approval pending
User completed CLI sign-in. Verified existing live mobile-c944173 and existing single-permission Speech role/sole runtime binding read-only. Build0584eee5-1623-48ef-9e6d-38ffc33aa5b1 SUCCESS; app238ef05b223064ca0393f6ce99efb7cb392357671b619b4ff18d0e74705f218d, acceptanceb564dfa153564a9b139040fe3a84ac55d5ae54e7da59c90bb846fd1716570a31. Frozen runtime1d2da6b and helper198e397; completed836PostgreSQL/149Node gates NOT repeated. Build archive $HOME/wzos-field-voice-1d2da6b-build.tgz; same release root/pointer. No model/job/real provider calls/public changes. Fresh ongoing-hosting plus exact-image one-recording acceptance/conditional public activation approval required; full scope/cost/rollback in FIELD_VOICE_ACTIVATION_20261018.md. Prior USD5 pilots do not authorize ongoing hosting. Resume by recording explicit approvals only when received, then root/deploy_activation.sh ROOT once; no ten-recording repeat or paid retry loop.

## User decision — hosting OFF; conditional acceptance approval unused
User explicitly selected Keep hosting off for ongoing private Field Voice model hosting. They separately approved exact app238ef05b/testb564dfa1 one-check conditional activation scope. That approval is recorded but UNUSED: it does not override the hosting refusal or authorize a replacement temporary model pilot. Do not create ongoing-hosting-approved or run deploy_activation.sh. No model, acceptance job, real provider requests or public cutover launched. Voice remains OFF; validated build and existing gate evidence retained. Activation requires a separately agreed model-hosting arrangement before the dependent check can run; do not repeat completed tests or infer hosting consent from conditional activation approval.

## L4 cost investigation — no hosting activated
User requested investigation of8CPU/32GiB L4. See ATLAS_L4_FEASIBILITY_20261018.md: verified official1.42092USD/allocatedhour,55.41% lower thanRTX; project read-only quota confirms3non-zonal L4 GPUs inus-central1, not reserved capacity. Official Google31B QAT W4A16 checkpoint exists, but its23.3GB weight file plus runtime/cache makes24GB fit unverified; current31B onlineFP8 setup cannot move unchanged. Pin/runtime/loading/context/audit/model-specific acceptance changes documented, not implemented. SmallerE4B is an explicit fallback choice only. No downloads/GPU/IAM/provider tests/public changes. HostingOFF decision remains controlling; conditional prior activation approval unused and not transferable blindly toL4.

## Original configuration activation in progress
Ray now understands scale-to-zero and explicitly approved original RTX private ongoing hosting and activation, superseding Keep hosting off for that original configuration. Existing exact-image conditional approval retained. Started root/deploy_activation.sh once with activation-started guard; source1d2da6b/app238ef05b/testb564dfa1. One synthetic acceptance recording only, no retries or full-suite repeat. Read activation-runner.log/activation.exit and cleanup evidence before any claim/retry. Model may remain only on successful approved ongoing activation; ordinary Atlas chat unchanged. L4 not deployed.

## Latest result — activation failed exact equipment check; cleanup
OriginalRTX deployment/metadata auth succeeded. Exact synthetic acceptance5sq9s FAIL:50drums/4Aero boards/1incident/3unresolved warnings; speech arrow cuefalse.1Speech+1Gemma/0SMS, no raw transcript/audio logs. New ambiguity warnings worked; exact4arrowboards gate remainsfailed. No cutover or automatic repeat. Job/model deleted; verify independent finalabsence/config files and activation.exit1 in release root. Public remainsmobile-c944173/VoiceOFF. Prior836/149 gates remainpassed; no repeated suites. Full details FIELD_VOICE_ACTIVATION_20261018.md. Do not silently weaken acceptance; recognition repair or explicit review-policy decision required.

## Editable-draft policy approved and verified offline
Ray accepted clearlyflagged editableequipment drafts with mandatoryreview. Helpers now require exact confirmationwarning forknownAero board(s) count4, retain correctcounts/incidentassertions and simulate explicitreviewercorrection before sending; runtime/app238ef05b unchanged.7inertchecksPASS + final focusedmockedworkflowPASS,0realprovider/0SMS. Activation requires reviewed-equipment-v1 resultmarker. ExistingrealFAIL preserved; no paidretest/model/publicchange started. Build new helper-only testimage, then obtain new exact-image workload/retest scope before liveexecution; original ongoingRTXhosting approval remainsrecorded.

Review-policy candidate BUILT: test6346e8f1d9e4e4f15bb05df712d87ad47d61664f20b4a1da00840ee3b8b75b9c, build3807b8bf-c361-4b11-9599-c7dca9ea5954SUCCESS; originalapp238ef05b unchanged. Newroot/tmp/wzos-field-voice-review.q9HbA9LQ, pointer$HOME/wzos-field-voice-review-path.txt, archivewzos-field-voice-review-build.tgz. Checkerbed32b5 requiresreviewed-equipment-v1, bash/ASTsyntaxPASS. Freshscopeapprovalpending forone6346job/1Speech1Gemma/10min/no retries andconditionalcutover. ExistingongoingoriginalRTXapprovalrecorded; L4notused. NoGPU/job/newpaidtestlaunched. Do notreuseoldrootactivationmarkers/results orreclassifypreviousFAIL. Afterexplicitapproval writeactivation-approved/ongoing-hosting-approved inNEWroot, guardactivation-started, runroot/deploy_activation.shonce; readexit/result/cleanup beforeclaim. RealAndroidmicrecordingremainsuser-led.

## Review-policy live check approved and started
Ray approved exact6346e8f1 one-recording livecheck and conditional238ef05b activation. Original ongoingRTXhosting approval retained. Newreviewroot activation-started guard set; deploy_activation.sh started once, activation.exit/result pending. No additional requests/retries or oldresults reused. Read newroot via$HOME/wzos-field-voice-review-path.txt; preserve priorfailedroot. IfPASS removejob and activateonlyafterstagedchecks; otherwisecleanupmodel/job,publicunchanged.

## LATEST — Smart Field Voice LIVE
Userapproved6346review-policycheck/conditionalactivation completedPASS, execution5dt2w,1Speech1Gemma0SMS; app238ef05b/source1d2da6b now100% revisionwzos-v2-accounts-voice-live-1d2da6b. Version0d1aaad29aceb5c98c94772b; voiceflagsON/Speechlong. PrivateoriginalRTX31B remainsmin0max1 underongoingapproval, onlyappinvocation; ordinarychatOFF. Temporaryjobabsenceverified. Stagingconfig/publicassets/anonymousauth/trafficPASS; browserEnterpriseSmartFieldVoice controlsobserved, no usermic/location access. Runtime/DB/storage/secrets preserved, noDDL. Priorfailed5sq9snotreclassified; newreviewpolicyPASS. Do not rerun completedtests/activation.
Evidence$HOME/wzos-field-voice-live-1d2da6b.tgz, pointer$HOME/wzos-field-voice-review-path.txt; sourceownershipunchanged. SameimageVoiceOFF rollbackrevisionwzos-v2-accounts-voice-hold-1d2da6b; scriptroot/voice-rollback.sh. Screenshot.local-data/field-voice-pilot/live-voice-enabled.png. NEXT: user-ledinstalledAndroid microphone-onboarding/30secrecording/review/send/stoptracks acceptance; no unsolicited recording or SMS. DocsFIELD_VOICE_ACTIVATION_20261018.md has fullprovenance.


## Latest - October 20 local UI / launch / shortcut review
Owned integration-release checkout, branch codex/preproduction-modules, started
clean at dcc6052. See UI_ORGANIZATION_20261020.md. Layout/text organization, stray
mobile Home removal, launch ordering/public-shell worker and supplied shortcut
artwork reference refresh are LOCAL ONLY; no production/model/permission changes.
152Node plus3startup checks and3publicshell/brand Python checks PASS;4simulator
checks PASS. Full Python/PostgreSQL release gates not rerun. Browser synthetic
mobile/desktop review partly complete; final simulator tab stuck on browser error
after server restart, user says unresponsive. Owned server returned SIMULATOR_READY
and remains available; do not bypass error-page policy. Reopen URL manually to finish
visual check. Preserve live Voice238ef05b flags/privateRTXmin0max1. Photo concept
saved in FUTURE_PHOTO_REPORTS.md. Never infer installed-device splash acceptance
from simulator or cache checks.


## Simulator recovery / mobile review follow-up - October 20
Ray reopened simulator; normal UI control restored. Inspected final1b3cca8 Home,
Forms hub, training and route planner;390px and360px checks have no horizontal
page overflow. Route fields16px/equalwidth. Core member Home filters Enterprise
and admin options; restored Enterprise admin Home. Correct logo brand20261020
and absent standalone Home label verified. Ignored screenshot mobile-home.png in
.local-data/ui-sweep-20261020. No restart, sends, permission prompt or provider test.
Simulator intentionally remains running. Browser recovery blocker cleared; full
release gates/build/staging verification and installed-device splash/icon checks
remain. No live deployment or cloud configuration change.


## Mobile Home weather placement - October 20
Ray requested weather above menu options with darker glass. Same weather node now
moves between organization card and nav on mobile Home; returns to its original
app position on module/desktop views. Separate job tools stay in app. Home-only
charcoal glass styling; no geolocation, polling, provider or permission changes.
12 focused weather/mobileHome Node checks PASS. Browser confirms sidebar -> NAV
placement/darker background,375px no-overflow; Forms restores original app position
and previous styling. Screenshot .local-data/ui-sweep-20261020/weather-home.png.
Simulator ready and left at100% size for readable review. LOCAL ONLY, live unchanged.


## My jobs preview, top account strip and Clock In copy - October 20
Ray requested populated My jobs review, removal of text under Clock In, and account/
test-identity strip consistently near page top. Home now places that same strip
below the organization card; module/desktop restore it directly after topbar.
Removed the specific explanatory paragraph below Clock In; device setup/offline
behavior remains intact. No weather configuration changes: Ray explicitly put
weather configuration on hold, and the discarded tracking experiment stays reverted.

Cause of blank My jobs in simulator: dispatch registers only for verified account
workspaces, while simulator is synthetic. Added read-only GET assignment/notification
fixtures ONLY in loopback simulator wrapper, Enterprise/identity/origin constrained.
One accepted synthetic assignment per identity; no live dispatch, mutation, SMS or
production route/DDL change. Production empty-list state is not reclassified as a
production defect.6Python simulator and7Node mobile checks PASS. Browser opened
assignment details/navigation action, verified top strip on Home/My jobs/Time
Tracker, removed paragraph absent and375px no horizontal overflow. Evidence ignored
.local-data/ui-sweep-20261020/my-jobs.png. Local preview only; release gates remain.


## Smart Field Voice preview visibility - October 20
Voice was hidden by disabled local processing flags, not removed by layout work.
Loopback simulator now serves Enterprise-only read-only config/jobs/drafts fixtures
with preview_only=true and speech_enabled=false. UI exposes the menu/dashboard
card and job selection, explicitly marks layout-only mode, disables microphone/
permission setup/extraction controls. Live config/routes/hosting remain unchanged;
no provider request or real recording.7simulator Python checks PASS;JS syntax PASS;
browser opened card and verified job selection/disabled controls/preview notice.
Evidence.local-data/ui-sweep-20261020/field-voice-preview.png. Weather config hold
remains in force. Release gates/deployment still pending for the UI candidate.


## Smart Field Voice copy - October 20
User requested basic instructions and removal of layout-only wording. Replaced
intro with job -> record/type -> review/correct -> Send to office instructions,
and removed the extra layout-preview status sentence. Preview-only disabled
controls/backend guards remain unchanged. Provider/privacy disclosure remains
in device onboarding. JS syntax/diff checks PASS; no provider/recording tests.
Weather configuration remains on hold; live unchanged.

## LATEST - October20 UI release LIVE and approved Cloud Shell cleanup

Source6047e5ba5a70e366088c88b280e23bf6f631e1dc is deployed as
wzos-v2-accounts-ui-6047e5b100%, image2b1943521f78f9421d67003847b2723aaa24f84d69fab6a778f30761c1518561,
version270e2a2ea96f733144a59d9b. Full cloud gates155Node/849PostgreSQL pass, no
failures/skips. Backup/schema/build/staged runtime/public assets/auth/traffic PASS;
existing organization dashboard and updated Smart Field Voice instructions observed.
Voice remains enabled with existing private RTX31B min0/max1; ordinary Atlas chat
unchanged. Weather configuration remains on hold. No new IAM/DDL/provider retests,
microphone/location grant or customer sends. Rollback voice-live-1d2da6b100%.
See UI_RELEASE_20261020.md for full build/image/evidence and device-acceptance limits.

After deployment Ray approved safe2GB Cloud Shell cleanup. Removed twelve reviewed
unused old .venv-accounts-test folders only; active-process/path/ownership guards
passed. Actual2,128,019,456bytes reclaimed; home now52% used, about2.2GiB free.
No source/log/credential/scanner database removal; laptop unchanged. Private archive
$HOME/wzos-ui-6047e5b-evidence.tgz includes release+cleanup evidence (40KB).
Cloud root/tmp/wzos-ui-20261020.XC9Of8g4; pointer$HOME/wzos-ui-release-path.txt.
No automatic test/deploy replay. Remaining: installed-device splash/icon/update and
pending-draft acceptance; user-led Voice recording/review/send checks. Simulator
remains synthetic and cannot perform paid Voice processing. Live browser left open.

## Latest local development - Atlas DOT knowledge foundation October20

Ray requested manual-grounded Ask Atlas and report diagram discovery. Initially
prioritized supplied Virginia MUTCD, then supplied Road and Bridge VolumesI/II and
TEDM. Four pinned user-import PDFs ingested locally:2117pages/3361legacypassages.
2019 pavement training presentation held outside ingestion. Source hashes, actual
editions, official publication pages, Drive provenance and usage limits are curated
in sources.json; no user copy is silently labeled verified official/current.

Code extends existing knowledge Store/operator CLI with hash-pinned import; adds
manuals.py/manual_cli.py page index, outline, literal keyword/diagram discovery,
whole-page context, integrity checks, image review flags and revision-bound search
tags. Disabled Enterprise DOT search/context/ask routes and private metadata-auth
Gemma structured adapter added; existing chat/Voice/weather/report schema unchanged.
No new dependencies, customer DDL, IAM, cloud resources or public activation.

42 focused tests PASS (20.053s), including existing source/package/Atlas reference
regressions; mocked model only. Workspace factory auth/entitlement/OFF smoke returns
401/403/503 before inference. Real examples prioritize Figure3B-2 at MUTCDp621
(printed585; visual caption tag) and PM-1 at VolumeIIp315.154 pages are blank/low-body
text/image-heavy and remain review-needed; full index is not full visual/OCR review.
VDOT usage policy requires standard references rather than insertion/modification
in plan assemblies. Plan report citations/links; reuse-rights review before embedding.

See docs/ATLAS_DOT_KNOWLEDGE_20261020.md for architecture, commands, provenance,
validation and rollout. Ignored.local-data/knowledge and.local-data/dot-manuals hold
originals/manifests/annotations/indexes/results. Preserve together. Production still
ui-6047e5b100%, active Voice preserved; weather configuration remains on hold.
Next: source/currency/diagram review, actual Ask Atlas/report UI and snapshot citation
selection, release gates and separately approved bounded model acceptance/activation.
No automatic paid calls, source approval or live cutover authorized by local success.

## LATEST local development - Enterprise Ask Atlas context-first implementation

User superseded the diagram/report idea: Smart Field Voice and Ask Atlas - Work
Zone Guardian are the highlighted Enterprise features, kept separate. Voice report
fields/submission are stable; maps/navigation is unrelated; weather hold remains.
Legacy Work Zone Report launch cards/navigation are retired, with Previous reports
and existing PDF/ownership checks preserved as read-only history under Voice.

Local implementation adds a dedicated Ask Atlas page, typed/recorded questions,
review-before-Ask, local-device optional Read aloud, cited text/source search and
clear cancellation. Complete sections, continuations, explicit referenced pages
and mandatory pinned corrections form model context. Gemma reasoning is enabled
only on the new transport. Tokenizer measurement enforces the existing ~32K server
window; no assumption of advertised 256K, model resize or ordinary-chat activation.
Reviewed formula rules provide explicit units/ranges and server Decimal arithmetic;
no model code/functions execute and no real engineering formula is registered yet.

Fresh official VDOT downloads match all three new user PDFs exactly: VWAPM414pages,
Field Guide93, known-errors3. Together with four existing copies the local index
has2627pages. Sources remain individually unreviewed pending visual page/table/OCR
checks. Known errors are mandatory context; undated/provisional items are not
silently applied. A caption, complete index or matching official hash is not page
review or field approval. See ASK_ATLAS_ENTERPRISE_20261020.md for hashes/commands.

OCR/review/formula sidecars are original/text-hash-bound and included in verified
source snapshots. OCR is an operator-only, bounded CPU/Tesseract workflow; not run
in API requests. Global sampled extraction review no longer approves every page.
No cloud OCR/model call has run in this increment. Source originals and evidence
remain ignored under.local-data/knowledge and.local-data/dot-manuals.

DOT routes enforce Enterprise and exact organization allowlisting through
WZOS_ATLAS_DOT_ORGANIZATIONS in addition to independent search/inference flags.
The existing atlas_requests table tracks IDs/state only, with shared duplicate/
cancel/admission controls before expensive processing. LIKE patterns are bound
parameters for PostgreSQL compatibility. No customer DDL, IAM, secret, resource,
SMS/email send, public deployment or Voice activation change.

Browser attachment to Cloud Shell failed twice with stale-page capture, then a
fresh tab timed out. A remote reconnection question is pending. Do not claim the
PostgreSQL gate, CPU OCR or real model pilot accepted from local mocked checks.
User chose one bounded $5 synthetic pilot, no repeated paid testing or new GPU.
Resume by reading the latest validation note below, verifying Git and fresh cloud
account/project/live state, then completing source review and the frozen-candidate
PostgreSQL gate before any model acceptance or organization-scoped activation.

### Connection recovery / local checks

Cloud Shell tab6 was authorized; direct DOM terminal fill with a leading space
then Enter works, while AX input and sequential typing were unreliable. Fresh
readback verifies admin@workzoneos.org, enterprise-gemma2, pg_config/python3/git,
home52%used/2.2GiBfree and/tmp33GiBfree. Tesseract is not installed. Latest ready
service revision is still wzos-v2-accounts-ui-6047e5b; no traffic change was made.
The earlier reconnection question is superseded by this recovery.

Local broader checks58Python/158Node PASS; subsequent affected11Python/17Node
PASS, all synthetic/mocked, no skips/failures. Syntax/diff PASS. Real library
rebuilt2627pages. Current next step is disposable cloud release gates and bounded
CPU OCR, not replaying the local suites or issuing paid requests. See ignored
.local-data/dot-manuals/{final-focused,final-node,frozen-backend,frozen-node}.log.
