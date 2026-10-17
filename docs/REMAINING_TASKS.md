# WZOS remaining tasks - current October 17, 2026

Use SESSION_HANDOFF.md for source/live provenance and COLLABORATION_CONTRACT.md for
ownership. This checklist supersedes historical status entries, which are preserved
in history/REMAINING_TASKS_before_sms_acceptance_20261017.md. Product decisions and
older evidence remain there; do not silently discard or re-open completed gates.

## Closed latest checkpoint

- [x] Completed-form Send to office, immutable office receipt and admin in-app notice
  validated on the live app with a synthetic form.
- [x] SMS verification completed by Ray; ordinary one-way text notification received
  on the approved phone. Controlled test-recipient acceptance is complete.
- [x] SMS challenge overlap repair deployed;19 local/8 PostgreSQL checks passed.
- [x] Local generated test cache removed; fresh Cloud Shell has no owned temporary
  test cluster, proxy or deployment helper running.

## Next execution order

1. [x] Restore Cloud Shell CLI sign-in and verify project/account/live revision.
   admin@workzoneos.org/enterprise-gemma2; office-8d09c4a ready and100% traffic.
2. [ ] Installed Android PWA acceptance: launch from installed icon without address
   bar; confirm installed-state handling, update prompt and pending-draft preservation.
   Existing standalone metadata is deployed. No forced uninstall/storage clearing.
3. [ ] Daily embedded meetings: admin creates; organization member joins; two consenting
   devices see/hear each other inside WZOS; Leave stops camera/microphone; validate
   cancellation/expiry and participant revocation behavior. Recording/transcription off;
   approved initial session maximum two devices/five minutes. See DAILY_MEETINGS_INTEGRATION_20261014.md.
4. [ ] Atlas actual Gemma inference: verify HF_TOKEN binding and current startup logs;
   repair model startup/configuration, then bounded real module/source/security
   evaluations. Do not equate Atlas UI/retrieval/scanner success with model inference.
   Price resource changes before provisioning; refresh actual budget and limits.
5. [ ] Complete Core-to-Enterprise existing-customer billing upgrade: one-time $20
   credit, existing Core subscription transition, seat/edition consistency and
   webhook retries/rollback. Upgrade prompts admin-only. New-customer checkout is
   integrated; real payment acceptance remains separate. See FINAL_CHECKOUT_VALIDATION_20261016.md.
6. [ ] Finish practical multi-role/multi-organization journeys: dispatch -> My jobs ->
   acknowledgement -> navigation -> time -> completed form -> office review/text;
   course link editing/playback/qualification completion; session/passkey/device
   persistence and offline reconciliation. Reuse accepted tests; focus on real gaps.
   Navigation uses in-PWA routes and Google Maps for active turn-by-turn guidance.
7. [ ] Broader SMS activation only after sender/registration/consent/opt-out and
   tenant coverage review. Current runtime remains approved-recipient test mode.
   Verify office-form SMS and assignment notification delivery without duplicate sends.
8. [ ] Provider connectors: scoped WZOS export API exists; QuickBooks/Workday/payroll
   synchronization is not implemented. Choose actual provider, authorized OAuth and
   field mapping before claiming a connector works. No secrets in chat or Git.
9. [ ] Operational/security release closure: monitor remaining distro-image findings,
   assess patched images, retention/deletion/access reviews, alert delivery, backups,
   object recovery, incident runbook, budget controls, accessibility/load/reconnect
   pilot. Atlas scanning/holds are implemented; no SOC2 certification claim.
10. [ ] Consolidate final acceptance and support/operating-cost documentation, resolve
    or explicitly defer remaining gaps with Ray, then deploy any new accepted updates
    with configuration preservation and billing/security-compatible rollback.

## Pending source-only polish

- 2f44ed3 fixes one encoding artifact in SMS request guidance. Not deployed yet;
  include in the next release with meaningful feature work.

## Rules and product decisions

- Admin high access, member basic access; organization isolation applies to both.
- Core/Enterprise entitlements and all active-login seat counts, including admins.
- Daily meeting creation admin-only; members can join authorized meetings.
- One-way SMS notifications; user-owned consent and verified phone required.
- Existing-Core upgrade credit is one-time $20; Enterprise offer approved in commerce docs.
- Preserve approved black/amber glass design; mobile landing uses its launch cards.
- Later production target dates are unset. Work efficiently; do not manufacture
  readiness claims or repeat large suites for documentation-only changes.
