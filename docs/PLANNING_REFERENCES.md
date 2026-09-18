# Job-specific reference discovery

`POST /v2/planning/references` connects the existing intake contract to the local agency index. It runs without model calls, web requests, geocoding, or cloud changes.

## Request and behavior

Use the same body as `/v2/intake/assess`; see `CUSTOMER_WORKFLOW.md`. The response includes that assessment and its proactive JSA recommendation, followed by source topics, cited candidates, source availability, and coverage gaps.

Topics are deterministic: general traffic control and worker safety, plus warning signs/flaggers for setup or annotated imagery; markings for striping; utility references for utility work; excavation when reported; traffic-volume references for traffic overlays; and night, pedestrian, and intersection topics when reported. Unknown conditions remain questions in the assessment. Customer free text does not control search syntax or instructions.

Each topic returns at most two source passages per relevant agency, ranked by keyword match with stable tie-breaking. Citations include the original link, physical PDF page or HTML heading, document title/edition, revision hash, retrieval date, extraction check, and warnings. A passage is a candidate for review, not a governing requirement. Neither keyword rank nor a prior extraction check establishes applicability.

The planner uses only the latest downloaded revision, excludes catalog-marked superseded sources, and checks that the index contains the current download before using it. Historical revisions remain accessible through the general reference search. A later failed network refresh remains visible in `last_attempt_status` even if preserved text is searchable.

## Response states and limits

- `library_status=available`: the local index can be read; this does not mean complete agency or locality coverage.
- `library_status=unavailable`: the assessment is still returned with empty topic results and a library warning. This endpoint returns HTTP 200 for that partial result, unlike the standalone search endpoint's HTTP 503.
- Topic status: `candidates_found`, `no_candidates`, or `library_unavailable`. No match is not evidence that no requirement exists.
- Source status: `searchable`, `not_downloaded`, `extraction_unavailable`, `superseded`, `index_stale`, or `index_unavailable`.
- Invalid intake returns HTTP 422. The existing local-only boundary applies.

`project_date` is retained for the next applicability stage. This increment does not select a legally governing edition, infer location from coordinates, establish required forms, calculate sign/flagger positions, or produce traffic measurements. `requirements_determined` and `approved_for_field_use` always remain false. All candidate applicability remains `unresolved`.

## Validation

Automated tests cover omitted JSA, topic selection, unknown conditions, traffic-overlay requests, missing indexes, stale and superseded sources, latest-revision filtering, dates, and invalid requests. Tests also confirm customer text cannot approve placements or modify search instructions.

A real loopback HTTP request for a night striping job with reported pedestrians returned seven topics and 19 cited candidates from the locally ingested library, while retaining the OSHA download gap and unapproved status. Existing intake, ingestion, search, and preview tests remain part of the full suite.

## Remaining workflow

Next implement verified project evidence and applicability review, including roadway authority, work/permit/contract dates, official forms, and coverage beyond the seed documents. Actual imagery/traffic collection and reviewed annotation placement follow those contracts. The live V1 application remains separate.
