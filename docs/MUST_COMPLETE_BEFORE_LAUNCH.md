# Must complete before launch

Owner: Molecular Project Development LLC. Product: WZOS / Atlas powered by Gemma.
Updated 2026-09-20. Open checklist; no production date or deployment approval is implied. Close an item only with recorded evidence. Explicitly defer optional modules when defining the pilot scope.

## Verified Google Maps credential findings

Read-only live inspection of `enterprise-gemma2` (project number 910004733138) on 2026-09-20 found:

- Secret Manager contains `GOOGLE_MAPS_API_KEY`, with version 1 **Enabled**, created June 13, 2026. The secret value was not revealed, copied or tested.
- APIs & Services > Credentials displayed **No API keys to display** in this project. This does not prove the stored key is invalid: its issuing project, restrictions and usability remain unverified.
- The complete 59-service enabled inventory included **Geocoding API**, **Maps Static API** and **Street View Static API**. **Maps JavaScript API was not listed**. The V2 interactive map uses Maps JavaScript, so existing static API enablement alone does not finish its setup.
- Local V2 has no configured `WZOS_GOOGLE_MAPS_BROWSER_KEY`. The existing secret must not be exposed to browsers until its intended use and restrictions are established.
- No credentials, permissions, billing or deployed services were changed during this inspection.

Follow-up: authenticated Cloud Shell could read the secret in memory, but API Keys lookup returned HTTP 403 / `PERMISSION_DENIED`: `apikeys.keys.lookup` denied for the signed-in `admin@workzoneos.org` account. The key value was not printed or saved locally. Ownership/restrictions remain unresolved. Either obtain authorized lookup access in the owning project or approve a separate restricted V2 browser key. Do not alter the V1 key to work around this.

Approved setup completed 2026-09-20: enabled Maps JavaScript and API Keys API in `enterprise-gemma2`; created `projects/910004733138/locations/global/keys/wzos-v2-browser`, display name `WZOS V2 Browser Maps`. Independent metadata describe verified Maps JavaScript-only restriction and website referrers `http://localhost:8081/*`, `http://127.0.0.1:8081/*` and `https://app.workzoneos.org/*`. Key value was not printed or committed. Legacy credentials and deployed applications were unchanged. Local configuration and live imagery validation remain pending. Add staging origins explicitly when they exist. Live use may incur Maps charges.

## 1. Credentials, Google APIs and costs

- [ ] Identify the stored Maps key's issuing project, current validity, application restrictions, allowed APIs and existing V1 use. Reuse appropriate existing resources before creating replacements.
- [x] Create a separate website-restricted Maps JavaScript key with authorized localhost and app.workzoneos.org referrers; verified by metadata describe on 2026-09-20.
- [ ] Connect the new browser key to local V2 securely and add a staging referrer when selected. Keep server credentials separate.
- [ ] Verify Maps JavaScript and required Street View/geocoding APIs, billing, quotas and live success/error behavior in the correct key-owning project.
- [ ] Test hybrid/satellite imagery, marker/work-limit overlays and Street View against representative Virginia sites, including missing imagery and incorrect nearby panoramas.
- [ ] Verify permitted Google imagery display, retention, annotation and PDF/email export; preserve attribution. Implement only permitted exports.
- [ ] Set budgets/alerts, service quotas, Cloud Run scale limits and measured per-job cost targets. Budget alerts are not spending caps.
- [ ] Confirm least-privilege service identities, Secret Manager access, secret injection and credential rotation procedure; keep secrets out of Git and logs.

## 2. Atlas intelligence and official knowledge

- [ ] Select, benchmark and connect a functioning Gemma inference deployment; pin model/runtime versions and test timeouts, failures and output validation. Current Atlas is deterministic preparation, not model inference.
- [ ] Verify governing road authority and applicable document editions by location, date, contract and permit conditions; add locality coverage, including Norfolk where relevant.
- [ ] Fill OSHA/VOSH coverage gaps, resolve unavailable sources and add an official form inventory. Track existing/equivalent customer records and applicability rather than recommending duplicates.
- [ ] Implement controlled official-source discovery/update checks, edition/revision review and stale-source handling. Operator ingestion exists; automatic updates do not.
- [ ] Validate extraction of relevant tables and diagrams and implement reviewed placement rules/calculations with citations. Keyword matches alone cannot choose sign or flagger positions.
- [ ] Integrate measured road/lane geometry, verified posted speeds, dated traffic evidence, pedestrian/access constraints and site conditions. Reported work-limit lines are not a complete road model.
- [ ] Produce actual proposed annotated site imagery and explanations with traceable assumptions, source passages and review status. Validate results with qualified reviewers on representative jobs.
- [ ] Preserve reproducible recommendation snapshots tying model/rule/source versions to the project revision. Current preparation results are not saved as immutable decision records.

## 3. Complete the customer workflow

- [ ] Build/review the final customer UI, including project creation, evidence/form attachments, correction flows, progress/error handling, mobile use and accessibility. The current workspace is a local development editor.
- [ ] Implement evidence uploads, file validation, provenance and durable artifact storage with appropriate access controls.
- [ ] Implement V2 package composition and PDF generation; test citations, layout, missing-data indicators and permitted imagery handling.
- [ ] Implement email delivery with approved recipients/sender setup, duplicate-send protection, retries and delivery records. V1 preview data does not prove delivery.
- [ ] Implement identity-bound qualified review/approval and a clear distinction between customer reports, Atlas proposals and approved field documents.

## 4. Production security and operations

- [ ] Replace the local-only boundary with tested customer authentication, organization isolation, roles and record-level authorization. Decide customer access beyond the current workzoneos.org-only V1 access.
- [ ] Choose production persistence and migration strategy; test concurrency, backups, restore, retention and data deletion. Local SQLite and ignored data are not backed up by GitHub.
- [ ] Back up preserved recovery archives and source/project data to a durable approved location and verify restoration.
- [ ] Reconcile current Cloud Run, model endpoint, buckets, domains, IAM and build triggers. Replace stale V1 deployment configuration through a separate reviewed V2 release process.
- [ ] Establish staging, CI checks, dependency/security review, monitoring, sanitized error logs, readiness checks, job recovery and rollback.
- [ ] Validate quotas/load, cold starts, latency and cost per successful workflow; test partial provider outages.
- [ ] Review applicable customer terms, privacy, location/employee-data handling and provider obligations for the chosen launch scope.
- [ ] Run an end-to-end pilot: intake → evidence → cited recommendations → human review → annotated output/PDF → delivery → audit/history.
- [ ] Agree launch scope, acceptance criteria, support ownership and production date with Ray; explicitly approve rollout after readiness evidence.

## 5. Unified WZOS modules — implement or explicitly defer for the pilot

- [ ] Time clock and tracking, including permissions and retention.
- [ ] Employee messaging and notification preferences.
- [ ] Dispatch, navigation/access instructions and schedule management.
- [ ] Video training, completion records and qualification tracking.
- [ ] App integrations and reliable data exchange.

These remain part of the product vision. Their appearance in Atlas advice is not implementation of the underlying module. Record an explicit pilot inclusion/defer decision for each.

## Live Maps verification — 2026-09-20

The dedicated browser key is configured locally in `.local-data/credentials/wzos-v2-browser-key.txt` (Git ignored). Run `./scripts/start_v2_local.ps1` from PowerShell; it loads the key into the child server environment without printing it, binds to 127.0.0.1:8081, and restores the prior environment on exit. An alternate key file can be supplied with `-BrowserKeyFile`.

Live browser checks against an isolated synthetic Norfolk project (36.8508, -76.2859) successfully loaded Google's hybrid map with attribution and a nearby Street View panorama. Street View reported capture date 2022-09 and a nearby location, not the exact requested coordinate. No customer project was created or changed. The test server was stopped. All 76 tests passed; launcher syntax parsing passed. No imagery was downloaded or exported. Production referrer behavior, quotas/cost limits, marker overlays, missing imagery cases and export permissions still need validation.
