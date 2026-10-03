# Codex and Claude implementation boundaries

Agreed with Ray October 3, 2026. Read the latest SESSION_HANDOFF.md and REMAINING_TASKS.md before starting; older checkpoints are historical.

## Ownership

- Codex: Atlas/source references; shared accounts, permissions and backend contracts; Maps/placements; Work Zone Report/PDF/delivery; integration and shared cloud deployments.
- Claude: Time Clock first, then assigned work orders, Forms, messaging/Twilio, scheduling/Enterprise dispatch, training and navigation increments.
- Claude handles module UI polish; Codex handles Atlas context/actions. Release/pilot validation combines both, coordinated through focused handoffs.

## Git and integration

Codex's checkout uses enterprise-v2. Claude uses the separate `Enterprise Gemma v2 - claude-time-clock` worktree and `claude/time-clock` branch. Do not switch or modify the other checkout, cherry-pick unfinished work, or edit another agent's uncommitted files. Submit focused commits/PRs with tests. Codex coordinates merges, shared staging and migration application. A Git push is not deployment acceptance.

## Shared contracts

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
