# Combined roadmap steps 2 and 3

Ray requested one integrated workstream on 2026-09-23. This matrix supersedes treating forms/scheduling and other V1 modules as separate milestones. The combined step remains OPEN; no production parity or approved exclusions are claimed.

| Area | Implemented test workflow | Remaining acceptance work |
|---|---|---|
| Forms | Incident/DVIR drafts; JSA planning worksheet adapted from recovered task/hazard/control/PPE/emergency themes; append-only revisions from new saves, baseline capture on first legacy edit; scoped history | Full recovered JSA structure and verified C85/other official templates; attachments; signatures; print/export; review/submission receipts; DVIR repair/reinspection |
| Scheduling | Organization test roster; multiple assignments; overlap rejection within transaction; UTC start-date filter; cancellations; revision history | Calendar/day presentation; local-day overlap filtering; production roster; notifications/dispatch; advanced conflict review |
| Training | Recovered V1 course catalog; personal study status persistence; certificates explicitly disabled | Review media rights/current links and content; courses/videos; quizzes; audited completion; accredited certificate rules |
| Navigation | Separate module handing saved addresses to Google Maps | Validated destinations/routes; hazard records; offline behavior; in-app integration acceptance |
| Messaging | Separate synthetic inbox; same-organization sender/recipient access; retries deduplicated | Real identity/membership, conversations, realtime/reconnect, read/delivery receipts, retention; no external delivery currently |
| Time clock | Existing shifts/breaks/tasks plus UTC shift-start date filters and bounded CSV export; admin team access enforced, spreadsheet formula prefixes neutralized | Audited corrections, complete exports across large ranges, offline reconciliation, GPS consent/retention, payroll boundaries |
| Report integration | Linked JSA/inspection details and immutable saved report basis | Attachment/export/completion linkage and review acceptance |
| Other V1 functions | Previously preserved source/parity inventory | Dispatch, video meetings, integrations and administrative acceptance still open |

## Validation and boundaries

121 automated tests passed. Added tests for JSA history, private history access, overlapping assignments, cross-organization assignment denial, UTC date filters, synthetic message retries/isolation, study status isolation and rejection of certification status, time export permissions and date validation. Node syntax checks passed. Local HTTP returned 200 for root, roster, training, messages, time export and module script. Chrome again returned ERR_BLOCKED_BY_CLIENT for local preview; browser acceptance is blocked and this pass is not deployed. No real message or certificate was sent/issued. Existing staging remains revision 00007-8fs.

The roadmap's production identity/durable storage milestone is a dependency before real attendance or communications. It does not justify pretending those features are completed. Persisting records in local SQLite or temporary staging is only test workflow validation. Training catalog text comes from recovered V1 data/trainingCatalog.json, commit e5d7167bd1834a393fae8e2e19ed8b515f08c0e9; certification flags were removed and all entries marked content_review_pending. JSA is explicitly a reduced internal planning worksheet, not full recovered form parity.

## Priority update — 2026-09-24

Accounts and durable storage now precede additional parity work. Ray requested local preparation and pricing before provisioning. Enterprise-only dispatch through Messaging is required, tracked in [ENTERPRISE_DISPATCH.md](ENTERPRISE_DISPATCH.md). Neither dispatch nor live Twilio delivery is implemented.

## Previous resume order

1. Restore browser access and test all new views, account switches, dirty-state prompts, saves/retries and errors.
2. Finish forms and scheduling acceptance gaps using preserved V1 source and Netlify references.
3. Verify/import authorized training media and tests; add navigation hazards and message delivery/reconnect workflows against real identity when available.
4. Add attendance correction audit/offline handling and finish other-module parity inventory.
5. Run the complete matrix in restricted staging, then keep production launch gated on roadmap items 4â€“8. Do not mark combined steps 2/3 complete until each row passes or Ray explicitly approves exclusions.
