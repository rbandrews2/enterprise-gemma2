# WZOS app-style workspace preview

## Run locally

From the repository root:

```powershell
.venv/Scripts/python.exe scripts/start_workspace_preview.py
```

Open `http://127.0.0.1:8083`. Stop with Ctrl+C. The launcher binds only to loopback, disables proxy-header trust and explicitly opts into the separate preview service. Cloud runtime markers cause startup refusal. This service is not imported by V1 or the V2 application factory.

## Working scope

- Task-focused desktop sidebar, mobile job/Atlas navigation, compact summary counts, searchable work-order board and detail editor.
- Four selectable synthetic identities: Core/general, Core/admin, Enterprise/general and Enterprise/admin, across two synthetic organizations.
- General users see and edit their own records. Admins see and edit their test organization's records. Backend checks scope on reads and writes; payloads cannot choose an owner, role, edition or organization.
- Create, save, edit, reload and search draft work orders. Saved fields: title, work type, address/road segment, Virginia locality, optional date and notes. New records belong to the selected test identity. Assignment, dispatch status and coordinate intake are not added in this increment.
- SQLite persistence in ignored `.local-data/workspace-preview/orders.sqlite`, separate from existing V2 projects. Seeded examples are synthetic and survive restarts without overwriting edits. The list is capped at the 100 most recently updated visible records; displayed counts cover that list, not a production-wide total.
- Retry identifiers prevent duplicate creation for identical retry requests. Changed-content retries are rejected by the API. Optimistic version checks prevent stale writes; drafts remain in the browser form on save errors and reload requires confirmation if dirty.
- Enterprise's **Let Atlas help** reads a saved work-order revision and reuses existing V2 intake rules to identify missing site information. Unsaved edits clear prior preparation and disable the button. Preparation is not persisted; it is tied to the revision in the response. No model call, official source retrieval, verified placements, images or compliance approval occurs.
- Core's existing assistant remains part of the integration plan; it is not implemented by this preview. Forms, time clock, dispatch, maps, messaging and training are displayed as unavailable modules, not simulated success flows.

## Identity and safety boundary

The identity selector and `X-Preview-Actor` header are **test fixtures, not authentication**. Any local user can switch among them. The server enforces role/organization rules for these fixed fixtures to exercise the intended contracts, not to prove production identity or tenant security. Never deploy this service or feed it customer data. Explicit opt-in, loopback client/Host checks, same-origin checks and restrictive CSP provide the local inspection boundary; they do not replace customer authentication.

No Supabase, Google Maps, model, billing or email credentials are loaded. The recovered React application remains preserved separately. This lightweight, dependency-free browser shell establishes interaction and API contracts while live recovery is blocked; it is not the clean React Core import, a second production frontend, or a replacement for the source-reuse plan. Carry the validated workflow into the shared React app once the import/security gates pass.

## Validation

- Existing suite plus eight preview tests: 92 passing tests. Preview tests cover opt-in/cloud refusal, remote/Host/origin rejection, invalid identities, all four combinations, cross-organization read/write/list isolation, general-user restrictions, payload spoofing, idempotent creation, stale edits, restart persistence and Enterprise preparation controls.
- Browser: create a synthetic Norfolk utility job, save, reload, edit to revision 2, run preparation on the saved job, switch to Core/general and verify advanced preparation is unavailable.
- Desktop and 390-pixel mobile viewport checked; no horizontal overflow in the mobile DOM. JavaScript syntax check passed. No new JavaScript packages were needed.

## Next

1. Add a saved form/checklist linked to the work order and retain its revision relationship.
2. Connect the richer V2 project/geometry and cited-reference workflow through an adapter instead of maintaining two independent job records.
3. Complete the reviewed React import and router upgrade; replace fixture identity with server-verified identity before any deployment.
4. Resume actual backend inventory/backup after Ray resolves Supabase 2FA; no workaround or repeated sign-in request is needed now.

The final functional app remains targeted at `app.workzoneos.org`; public module explanations remain on `workzoneos.org`. Existing live services are unchanged.
