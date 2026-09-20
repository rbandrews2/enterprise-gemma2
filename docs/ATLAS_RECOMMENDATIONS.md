# Atlas recommendation workflow

## Selected source strategy

Use a maintained official-source library with controlled internet updates. Start with Virginia, then expand by customer demand. Retrieval should prefer preserved, edition-tracked documents. Missing locality coverage and changed editions must be surfaced rather than silently replaced with unrestricted web results. The current implementation has only operator-run approved-source ingestion; automated source discovery and update checks remain to be implemented.

The eventual "Let Atlas help" action will identify the governing authority, gather needed job conditions, retrieve relevant rules/tables/diagrams, use Gemma to explain proposed recommendations, and use validated geometry/calculations for placement. Recommendations must preserve citations, assumptions and review state. Image generation must not invent physical spacing.

## Implemented preparation stage

Atlas reviews the whole project; JSA is one example, not its central purpose. The `project_advice` response groups context, forms, evidence, requested functions and operations. Each item includes a finding, reason, next action, state and priority. Missing inputs, unverified claims, unavailable functions and unknown external arrangements are distinguished. Operational prompts cover crews/equipment/training, scheduling/dispatch/communications/access, and tracking/integrations. They do not claim these capabilities or records already exist in WZOS, or that every job needs them. All current advice is product-policy review guidance, not an agency-backed legal determination.

The form inventory is still incomplete: automated discovery of arbitrary missing forms/functions and Gemma reasoning remain future work. Existing JSA API fields are retained for compatibility, while the interface presents it as one item in the broader review. Customers should be asked about equivalent existing records before being advised to create duplicates.

`POST /v2/projects/{uuid}/atlas/prepare?expected_version=1` prepares the saved revision. A stale version returns 409; missing/invalid version returns 422; missing project returns 404. The normal local-only boundary applies. The response includes project ID, version and payload hash, targeted missing-context questions, JSA recommendation, evidence review, source candidates and explicit blockers. It does not alter the project or persist the response. References reflect the current index, not a frozen historical recommendation snapshot.

The workspace's **Let Atlas help** button calls this endpoint only after pending edits are saved or discarded. It displays source passages, editions, page/section locators, revision hashes, review status and official HTTPS links. A locality name such as Norfolk never causes the system to claim municipal coverage exists.

This stage is deterministic preparation: `model_called=false`, `placements=[]`, and `approved_for_field_use=false`. Neither a complete intake nor abundant keyword matches unlocks automatic placement. Closure geometry, visibility, duration and permit-condition questions are always included because their verified structured contracts are not implemented yet. The UI cannot yet collect answers to all of these questions.

## Validation and next steps

Response capture and follow-up review are now implemented: see [Atlas responses](ATLAS_RESPONSES.md). Customer notes remain unverified; they neither suppress underlying warnings nor approve recommendations.

All 70 V2 tests passed. Tests cover missing library behavior, omitted JSA, missing context, supplied-but-unverified context, version conflicts and unchanged projects. Browser testing against the local indexed library showed 13 reference candidates across five topics for a synthetic Norfolk striping project, with JSA, evidence gaps and no generated placements. No model or external imagery calls were made.

Next: structured closure/geometry inputs and answer capture; locality source verification; reviewed rules with table/diagram extraction; model adapter and output validation; geographic rendering on permitted imagery; persisted recommendation snapshots and qualified review. Production deployment remains separate.
