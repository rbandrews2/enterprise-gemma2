# Atlas responses and follow-up review

Customers can now answer each Atlas project finding in the local workspace. Choose information provided, already handled, not applicable, or needs help, and enter an explanation or existing-record reference. Responses are plain text, never fetched or executed. They are customer reports, not verified completion or regulatory approval.

## Save contract

`POST /v2/projects/{uuid}/atlas/responses` accepts `finding_id`, `context_sha256`, `disposition`, `note`, and `expected_version`. The finding and context hash come from the preparation result. The server checks the latest revision, current finding ID and context hash, then appends a project revision. One response per finding is stored in a revision; earlier responses remain in historical revisions. Blank notes, unsupported dispositions and unknown current finding IDs return 422. Concurrent edits or changed context return 409. The local-only access boundary applies.

Project drafts now contain `review_responses` (maximum 200). Full project PUT replaces this list like other draft fields; callers must retain it if desired. Older records load with an empty list, and empty lists are omitted from canonical writes to preserve historical create retry hashes.

## Follow-up review

The next **Let Atlas help** run joins responses to current findings and reports unanswered, reported-handled, needs-help and stale counts. The UI calls reported-handled items "customer-reported"; they are not resolved or approved. The underlying finding and its warnings remain visible. Responses to findings no longer present are listed as unmatched and retained.

A SHA-256 fingerprint covers the saved project content except responses. Any context change, including project name or marker edits, conservatively requires reconfirmation. Adding another response does not invalidate existing responses. The fingerprint does not currently cover source library updates or rule-code versions; responses never establish source applicability. Evidence finding IDs are derived from finding text rather than list order, avoiding accidental reassignment when another finding is added.

Notes do not automatically change structured intake, geometry or evidence. Saying "speed is 35" records a claim; it does not supply verified posted-speed evidence. Required questions and placement blockers remain until those structured inputs and review capabilities are implemented. Model reasoning, compliance approval and imagery generation remain unconnected.

## Validation

All 73 V2 tests passed. Added checks cover response persistence, re-evaluation, old revision retrieval, unknown findings, invalid dispositions, blank notes, stale context, conflicting versions and needs-help status. A real browser flow loaded a temporary synthetic project, saved a response, then reran Atlas and displayed one customer-reported item in revision 2. No paid calls or cloud changes occurred.
