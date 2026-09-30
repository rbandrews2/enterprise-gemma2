# Federal reference coverage

September 29, 2026 Eastern. Customer requirement: Atlas must cover federal worker safety alongside state/local traffic-control requirements.

- **FHWA (USDOT):** MUTCD, including Part 6 temporary traffic control. Preserved and searchable locally and in the last source-enabled staging image. Project/state applicability remains unapproved.
- **OSHA (USDOL):** workplace safety standards. Catalog now includes the highway-work-zone standards directory and 29 CFR 1926.200 (signs/tags), .201 (signaling/flaggers), .202 (barricades), alongside the fact sheet. Local downloads returned HTTP403; no searchable OSHA originals are present. Confirm incorporated MUTCD edition under 1926.6 rather than assuming OSHA incorporates the newest FHWA edition.
- **NIOSH (CDC):** highway-worker injury-prevention research and guidance. Added agency/filter support and official CDC source to catalog. This guidance must not be presented as an enforceable OSHA standard. Local download returned HTTP403; no searchable NIOSH original is present.
- **Virginia VOSH:** resolve state-plan jurisdiction, exclusions and adopted/additional standards before applying federal requirements to a Virginia job.

Official discovery links:
- https://mutcd.fhwa.dot.gov/kno_11th_Editionr1.htm
- https://www.osha.gov/highway-workzones/standards
- https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.201
- https://www.cdc.gov/niosh/motor-vehicle/highway/

## Access status and completion gate

`federal-access-20260929.json` records actual failed attempts. Catalog inclusion does not mean Atlas can quote or retrieve those documents. New sources are unreviewed and not deployed. Source API reports unavailable; preserve this explicitly in answers. No access controls were bypassed.

Next: obtain publisher-permitted accessible official originals (or verified official eCFR equivalents for regulations), ingest them with origin/hash/section metadata, check extraction and role labeling, test filtered retrieval and Atlas grounding, then package a new staging source snapshot. Also curate work-type-specific hazards such as excavation, equipment/backovers and electrical exposure; this initial set is not complete safety coverage.

## Follow-up: planning integration repaired

Added the April 10, 2024 NIOSH internal traffic control planning bulletin as a separate guidance source; its local download also returned403. No new federal originals became searchable. Existing failures remain visible.

Fixed shared planning response schemas to accept NIOSH and included NIOSH in worker-safety discovery. Previously a real catalog containing NIOSH would fail planning validation even without downloaded text. Added an unavailable-then-searchable fixture test and an explicit guidance-versus-standard statement in planning/model context. In-process HTTP endpoint check using the actual catalog/index returned200 and both NIOSH entries as not_downloaded/unavailable. This verifies the access-gap presentation, not a live model response.

Discovery exclusion: CDC's archived publication page marks *Building Safer Highway Work Zones*, publication2001-128, withdrawn August2025. Do not ingest it as current guidance simply because its PDF remains discoverable. The 2024 bulletin links older material; each linked source requires separate review.
Evidence: https://archive.cdc.gov/www_cdc_gov/niosh/docs/2001-128/default.html
Bulletin: https://www.cdc.gov/niosh/bulletin/2024/struck-by.html

Next access path: verify accessible official eCFR equivalents for OSHA; obtain publisher-permitted originals for NIOSH. Do not bypass403 or substitute web search snippets for preserved originals. Cloud source snapshot and live model verification remain pending.

Validation: full local discovery suite189 total,173 passed/16 database skips (46.805 seconds). No paid model calls.
