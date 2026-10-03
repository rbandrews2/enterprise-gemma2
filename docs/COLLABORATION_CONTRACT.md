# Codex and Claude implementation boundaries

Agreed with Ray October 3, 2026. Read the latest SESSION_HANDOFF.md and REMAINING_TASKS.md before starting; older checkpoints are historical.

## Ownership

- Codex: Atlas/source references; shared accounts, permissions and backend contracts; Maps/placements; Work Zone Report/PDF/delivery; integration and shared cloud deployments.
- Claude: Time Clock first, then assigned work orders, Forms, messaging/Twilio, scheduling/Enterprise dispatch, training and navigation increments.
- Claude handles module UI polish; Codex handles Atlas context/actions. Release/pilot validation combines both, coordinated through focused handoffs.

## Git and integration

Codex's checkout uses enterprise-v2. Claude uses the separate `Enterprise Gemma v2 - claude-time-clock` worktree and `claude/time-clock` branch. Do not switch or modify the other checkout, cherry-pick unfinished work, or edit another agent's uncommitted files. Submit focused commits/PRs with tests. Codex coordinates merges, shared staging and migration application. A Git push is not deployment acceptance.

## Coordination and review rules

- **Startup schema changes:** Any PR that adds or changes startup DDL must disclose it and include reviewable SQL, compatibility notes, and rollback implications. Codex treats deployment of that code as applying the migration, even when the statements use `CREATE TABLE IF NOT EXISTS`. Review and PostgreSQL validation precede shared deployment.
- **Later branches:** The current assignment remains `claude/time-clock`. Later assignments use a separate `claude/<module>` branch/worktree cut from the latest `enterprise-v2`, with one focused PR per assigned module increment.
- **Keeping PRs current:** Claude updates its branch and resolves module-owned conflicts on request. Codex resolves conflicts at integration only in Codex-owned files, coordinating intended behavior through the handoff. Mixed-ownership or module behavior conflicts go back to Claude; do not silently rewrite the other contributor's work. Rerun affected checks after conflict resolution.
- **Status documents:** Codex owns `SESSION_HANDOFF.md` and `REMAINING_TASKS.md`. Claude writes `docs/<MODULE>_COMPLETION.md` with actual results and open gaps. Codex links the handoff when integrating and distinguishes reported results from independently verified acceptance.
- **Module help and Atlas:** Claude may propose narrowly scoped module-help wording, including text-only edits in `assistant.js` and `intelligence.py`, explicitly listed in the handoff. Codex reviews placement and accuracy in Atlas context and owns model prompts, retrieval, tools, and actions. The existing Time Clock wording can remain proposed in PR #1 pending that review.
- **Merge gates:** Full Python and Node suites must pass on the integrated candidate, with skips and their reasons recorded. Codex runs the PostgreSQL suite in Cloud Shell against a disposable schema, explicitly including new module tests such as `tests/test_timeclock_corrections.py`; SQLite success or skipped PostgreSQL cases do not satisfy this gate. Validate new authenticated routes, tenant isolation, and admin/member boundaries. UI changes need browser evidence. Documentation-only changes require link/path and diff checks, not unrelated runtime suites. A blocked required check remains open before merge/deployment.
- **Screenshots:** Commit only selected, compressed PNG/WebP evidence with synthetic data and no credentials or private information; avoid duplicate or full-resolution captures that add no review value. Put larger evidence bundles outside Git and document their location. Existing Time Clock screenshots may remain for review; do not rewrite their history solely to reduce size.
- **Product decisions:** Claude lists open questions and current provisional behavior in its module handoff. Codex maintains the consolidated queue under `Additions to review` in `REMAINING_TASKS.md`. Record Ray's decisions there before treating provisional behavior as an approved product policy.

## Application invariants

- Exactly admin and member roles, enforced server-side with organization isolation.
- Preserve Core/Enterprise entitlements; automated dispatch is Enterprise-only and requires admin review before sending assignments.
- Reuse existing Google-backed storage/auth interfaces and version/concurrency protection. Supabase is historical recovery material, not the replacement runtime.
- Document proposed API/schema changes before broad shared-file edits. Keep routing/storage changes narrow; no unrelated rewrites or competing auth/storage layers.
- Customer branding: WZOS powered by Atlas AI Assistant. Keep the established gloss-black, subtle amber/gold, road-work imagery and accessible/reduced-motion behavior.
- Offline estimates/notes must remain visibly unverified until an explicit, audited reconciliation; never silently fabricate server-verified attendance.
- Atlas source retrieval and suggested placements do not establish applicability or approval. Preserve edition, revision and review status.
- No credentials, private fixture tokens or downloaded source originals in Git. No V1/DNS/production changes, customer sends or additional paid provisioning without the applicable authorization.

## Handoff for each completed increment

List branch/commit/PR, changed files, actual behavior, migrations, tests/results, UI evidence when applicable, remaining gaps, integration steps and rollback. Do not mark a module complete merely because its screen exists. Do not claim direct agent communication unless it occurred; a committed handoff can be relayed by Ray.
