# Local annotation editor

Start the V2 server using the existing README command and visit `/v2/workspace` on its loopback address. This is a development editor, not the final WZOS interface.

Load an existing project, add or edit markers, choose evidence references, apply edits to the draft, then save a new project revision. Marker IDs cannot be renamed after selection; remove and recreate if needed. A save preserves the loaded intake, evidence and applicability notes. Concurrent edits return a conflict and retain the local draft; reload to inspect the latest project. There is no automatic merge. Unapplied marker edits must be applied or discarded before saving; leaving the page with edits prompts for confirmation.

The preview plots numbered coordinates with independently scaled axes. It contains no basemap, road geometry or imagery, and is not a distance or placement tool. Future Google map integration will replace this preview. Labels are rendered as text. All annotations remain proposed and unverified.

No external scripts, fonts, maps, analytics or APIs load. No new dependencies or paid calls were added. Projects must currently be created through the API (`/docs`); this page edits annotations only. Project discovery reads all pages of the local project list and is intended for a small development workspace.

Validation: browser inspection verified the empty state, loading a synthetic project, applying a sign marker and saving revision 2. The browser displayed the successful save and unapproved status. Automated tests cover serving assets and rejecting remote clients, alongside the existing annotation/history/conflict tests. The coordinate preview was visually inspected; mobile-device and full accessibility testing remain pending.
